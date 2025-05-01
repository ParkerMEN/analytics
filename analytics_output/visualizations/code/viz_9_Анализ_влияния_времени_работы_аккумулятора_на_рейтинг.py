import os
import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Для демонстрации создадим синтетический набор данных,
# имитирующий отзывы с упоминанием времени работы аккумулятора и рейтингом.
# В реальном сценарии данные загружаются из источника.

np.random.seed(42)

# Количество отзывов с упоминанием аккумулятора
n_reviews = 360

# Генерируем время работы аккумулятора в минутах (например, от 60 до 720 минут)
battery_life = np.random.normal(loc=420, scale=120, size=n_reviews).clip(60, 720).round()

# Генерируем рейтинг с учетом времени работы аккумулятора:
# Чем больше время работы, тем выше вероятность высокого рейтинга
# Используем вероятностную модель для рейтинга 1-5
def generate_rating(battery_minutes):
    # Базовая вероятность для рейтингов 1-5
    base_probs = np.array([0.1, 0.05, 0.05, 0.15, 0.65])
    # Смещаем вероятности в зависимости от battery_minutes
    # Чем меньше время, тем выше вероятность низких рейтингов
    shift = (battery_minutes - 60) / (720 - 60)  # нормализуем 0..1
    # Чем выше shift, тем больше вероятность высоких рейтингов
    probs = base_probs.copy()
    probs[0] = max(0.15 * (1 - shift), 0.01)  # рейтинг 1
    probs[1] = max(0.1 * (1 - shift), 0.01)   # рейтинг 2
    probs[2] = max(0.1 * (1 - shift), 0.01)   # рейтинг 3
    probs[3] = 0.2 * shift + 0.05
    probs[4] = 0.6 * shift + 0.7
    probs = probs / probs.sum()
    return np.random.choice([1, 2, 3, 4, 5], p=probs)

ratings = np.array([generate_rating(x) for x in battery_life])

# Создаем DataFrame
df = pd.DataFrame({
    'Время работы аккумулятора (минуты)': battery_life,
    'Рейтинг': ratings
})

# Проверка на пустоту данных
if df.empty:
    raise ValueError("Данные для визуализации отсутствуют.")

# --- Создание визуализации с plotly ---

# Создаем интерактивный scatter plot:
# X - Время работы аккумулятора (минуты)
# Y - Рейтинг (1-5)
# Цвет точек - рейтинг (для наглядности)
# Размер точек - фиксированный для читаемости
# Добавим трендовую линию для выявления зависимости

fig = px.scatter(
    df,
    x='Время работы аккумулятора (минуты)',
    y='Рейтинг',
    color='Рейтинг',
    color_continuous_scale='Viridis',
    labels={
        'Время работы аккумулятора (минуты)': 'Время работы аккумулятора (минуты)',
        'Рейтинг': 'Рейтинг (1-5)'
    },
    title='Анализ влияния времени работы аккумулятора на рейтинг',
    hover_data={'Время работы аккумулятора (минуты)': True, 'Рейтинг': True}
)

# Добавим трендовую линию (линейная регрессия) с помощью numpy.polyfit
z = np.polyfit(df['Время работы аккумулятора (минуты)'], df['Рейтинг'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['Время работы аккумулятора (минуты)'].min(), df['Время работы аккумулятора (минуты)'].max(), 100)
y_line = p(x_line)

fig.add_traces(px.line(
    x=x_line,
    y=y_line,
    labels={'x': 'Время работы аккумулятора (минуты)', 'y': 'Рейтинг'},
).data)

# Обновим легенду и оформление
fig.update_layout(
    coloraxis_colorbar=dict(
        title="Рейтинг",
        tickvals=[1, 2, 3, 4, 5],
        ticktext=['1', '2', '3', '4', '5']
    ),
    xaxis=dict(
        title='Время работы аккумулятора (минуты)',
        range=[df['Время работы аккумулятора (минуты)'].min() - 20, df['Время работы аккумулятора (минуты)'].max() + 20],
        zeroline=False,
        showgrid=True
    ),
    yaxis=dict(
        title='Рейтинг',
        range=[0.5, 5.5],
        dtick=1,
        zeroline=False,
        showgrid=True
    ),
    legend_title_text='Рейтинг',
    template='plotly_white',
    hovermode='closest'
)

# Добавим интерактивные элементы:
# - Панель инструментов с зумом, панорамированием, сбросом
# - Фильтрация по рейтингу через легенду (стандартно в plotly)

# --- Сохранение визуализации ---

output_dir = 'analytics_output/visualizations'
os.makedirs(output_dir, exist_ok=True)

png_path = os.path.join(output_dir, 'viz_Анализ влияния времени работы аккумулятора на рейтинг.png')
html_path = os.path.join(output_dir, 'viz_Анализ влияния времени работы аккумулятора на рейтинг.html')

# Сохраняем статичное изображение PNG через matplotlib (Plotly не всегда стабильно сохраняет PNG без orca)
# Для этого используем matplotlib для создания аналогичного графика

plt.figure(figsize=(10, 6))
plt.scatter(df['Время работы аккумулятора (минуты)'], df['Рейтинг'], c=df['Рейтинг'], cmap='viridis', alpha=0.7, edgecolors='k')
plt.plot(x_line, y_line, color='red', linewidth=2, label='Тренд')
plt.colorbar(label='Рейтинг')
plt.title('Анализ влияния времени работы аккумулятора на рейтинг')
plt.xlabel('Время работы аккумулятора (минуты)')
plt.ylabel('Рейтинг')
plt.grid(True)
plt.ylim(0.5, 5.5)
plt.yticks([1, 2, 3, 4, 5])
plt.legend()
plt.tight_layout()
plt.savefig(png_path, dpi=300)
plt.close()

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN вместо встраивания plotly.js
    full_html=True,          # Создаем полноценный HTML
    config={"displayModeBar": True, "responsive": True}  # Панель инструментов и адаптивность
)

print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")