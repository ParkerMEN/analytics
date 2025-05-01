import os
import plotly.graph_objects as go
import plotly.io as pio
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Частота упоминаний достоинств (примерные данные)
# В реальной задаче данные могут поступать из анализа отзывов
features = [
    "Работоспособность",
    "Удобство",
    "Легкость сборки",
    "Аккумулятор",
    "Быстрая доставка",
    "Качество материалов",
    "Дизайн",
    "Поддержка",
    "Цена/качество",
    "Функциональность"
]

mentions = [120, 95, 80, 75, 60, 50, 45, 40, 35, 30]  # Количество упоминаний достоинств

# Проверка на пустые данные
if not features or not mentions or len(features) != len(mentions):
    raise ValueError("Данные для визуализации отсутствуют или некорректны.")

# Создаем директорию для сохранения, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# --- Создание интерактивной визуализации с plotly ---

# Создаем столбчатую диаграмму с горизонтальными столбцами для удобства чтения длинных названий
fig = go.Figure()

fig.add_trace(go.Bar(
    x=mentions,
    y=features,
    orientation='h',
    marker_color='rgba(58, 123, 213, 0.8)',
    hovertemplate='<b>%{y}</b><br>Упоминаний: %{x}<extra></extra>',
))

# Настройка макета графика
fig.update_layout(
    title="Частота упоминаний достоинств (положительных аспектов)",
    xaxis_title="Количество упоминаний",
    yaxis_title="Достоинства",
    yaxis=dict(autorange="reversed"),  # Чтобы самый популярный был сверху
    template="plotly_white",
    margin=dict(l=140, r=40, t=80, b=60),
    hovermode="y unified",
    font=dict(family="Arial, sans-serif", size=14),
)

# Добавляем интерактивные элементы:
# - панель инструментов с зумом, масштабированием, сохранением
# - hover с подробной информацией
# - возможность скрывать/показывать категории (через легенду, но у нас один trace, поэтому не нужно)

# --- Сохранение визуализации ---

# Сохраняем интерактивный HTML с использованием CDN plotly.js
html_path = os.path.join(output_dir, "viz_Частота упоминаний достоинств (положительных аспектов).html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Сохраняем статичное изображение PNG через kaleido
png_path = os.path.join(output_dir, "viz_Частота упоминаний достоинств (положительных аспектов).png")

# Проверяем, что kaleido установлен и доступен
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print("Не удалось сохранить PNG изображение через plotly. Попробуйте установить пакет 'kaleido'.")
    print("Ошибка:", e)

# --- Дополнительно: создадим аналогичный график через matplotlib для сравнения качества ---

plt.figure(figsize=(10, 6))
bars = plt.barh(features, mentions, color='#3a7bd5', alpha=0.8)
plt.gca().invert_yaxis()  # Чтобы самый популярный был сверху
plt.title("Частота упоминаний достоинств (положительных аспектов)", fontsize=16, fontweight='bold')
plt.xlabel("Количество упоминаний", fontsize=14)
plt.ylabel("Достоинства", fontsize=14)
plt.grid(axis='x', linestyle='--', alpha=0.7)

# Подписи значений справа от столбцов
for bar in bars:
    width = bar.get_width()
    plt.text(width + 2, bar.get_y() + bar.get_height()/2,
             f'{int(width)}', va='center', fontsize=12)

plt.tight_layout()

# Сохраняем matplotlib PNG (не обязательно, но для контроля качества)
matplotlib_png_path = os.path.join(output_dir, "viz_Частота упоминаний достоинств (положительных аспектов)_matplotlib.png")
plt.savefig(matplotlib_png_path, dpi=150)
plt.close()

print(f"Визуализация успешно сохранена:\n- HTML: {html_path}\n- PNG (plotly): {png_path}\n- PNG (matplotlib): {matplotlib_png_path}")