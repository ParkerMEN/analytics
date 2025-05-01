import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Частоты упоминаний ключевых факторов в процентах
# Для удобства и однозначности возьмём средние или наиболее репрезентативные значения, где есть диапазон
factors = {
    "Аккумулятор": 100.0,
    "Комплектность": 90.9,
    "Качество сборки и работы": 87.5,
    "Быстрая доставка": 77.8,
    "Функциональность (рыхление, мощность)": (64.3 + 52.0) / 2,  # среднее между двумя темами
    "Удобство использования (вес, эргономика)": (24 + 38) / 2,    # среднее из диапазона
}

# Проверка на пустоту данных (краевой случай)
if not factors:
    raise ValueError("Данные для визуализации отсутствуют.")

# Сортируем факторы по убыванию частоты для удобства восприятия
factors_sorted = dict(sorted(factors.items(), key=lambda item: item[1], reverse=True))

# Подготовка списков для графика
factor_names = list(factors_sorted.keys())
frequencies = list(factors_sorted.values())

# --- Создание интерактивной визуализации с plotly ---

# Создаем горизонтальную столбчатую диаграмму
fig = go.Figure()

fig.add_trace(go.Bar(
    y=factor_names,
    x=frequencies,
    orientation='h',
    marker=dict(color='rgba(58, 71, 80, 0.8)'),
    hovertemplate='%{y}: %{x:.1f}%',
    name='Частота упоминаний'
))

# Настройка макета графика
fig.update_layout(
    title="Частота упоминаний ключевых факторов в отзывах",
    xaxis=dict(
        title="Частота упоминаний, %",
        range=[0, 110],  # Немного больше 100% для визуального отступа
        showgrid=True,
        zeroline=True,
        zerolinecolor='LightPink',
        zerolinewidth=2,
        dtick=10,
    ),
    yaxis=dict(
        title="Ключевые факторы",
        autorange="reversed"  # Чтобы самый высокий столбец был сверху
    ),
    margin=dict(l=150, r=40, t=80, b=60),
    template='plotly_white',
    hovermode='y unified',
    font=dict(family="Arial, sans-serif", size=14),
)

# Добавим интерактивные элементы: панель инструментов с зумом, сохранением, масштабированием
fig.update_layout(
    dragmode='zoom',
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial")
)

# --- Сохранение визуализации ---

# Создаем папку для сохранения, если не существует
output_dir = 'analytics_output/visualizations'
os.makedirs(output_dir, exist_ok=True)

# Путь для сохранения PNG и HTML
png_path = os.path.join(output_dir, 'viz_Частота упоминаний ключевых факторов в отзывах.png')
html_path = os.path.join(output_dir, 'viz_Частота упоминаний ключевых факторов в отзывах.html')

# Сохраняем PNG (статическое изображение)
# Для сохранения PNG требуется kaleido или orca, проверим наличие
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print(f"Не удалось сохранить PNG: {e}")

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,          # Полноценный HTML
    config={"displayModeBar": True, "responsive": True}  # Панель инструментов и адаптивность
)

# --- Дополнительно: статичная визуализация с matplotlib для сравнения ---

# Для matplotlib создадим горизонтальную столбчатую диаграмму с подписями
plt.figure(figsize=(10, 6))
bars = plt.barh(factor_names, frequencies, color='steelblue')
plt.xlabel('Частота упоминаний, %')
plt.title('Частота упоминаний ключевых факторов в отзывах')

# Добавим подписи значений рядом с барами
for bar in bars:
    width = bar.get_width()
    plt.text(width + 1, bar.get_y() + bar.get_height()/2,
             f'{width:.1f}%', va='center', fontsize=10)

plt.xlim(0, 110)
plt.gca().invert_yaxis()  # Чтобы самый высокий был сверху
plt.grid(axis='x', linestyle='--', alpha=0.7)

# Сохраняем matplotlib изображение рядом с plotly PNG для контроля качества
plt.tight_layout()
matplotlib_png_path = os.path.join(output_dir, 'viz_Частота упоминаний ключевых факторов в отзывах_matplotlib.png')
plt.savefig(matplotlib_png_path, dpi=150)
plt.close()

print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}\n- Matplotlib PNG: {matplotlib_png_path}")