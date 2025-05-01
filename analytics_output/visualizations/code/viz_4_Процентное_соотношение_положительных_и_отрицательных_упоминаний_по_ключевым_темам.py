import os
import plotly.graph_objects as go

# --- Подготовка данных ---

# Исходные данные по темам и тональности (положительные и отрицательные упоминания)
data = {
    "аккумулятор": {"положительные": 17, "отрицательные": 6},
    "упаковка": {"положительные": 9, "отрицательные": 7},
    "доставка": {"положительные": 14, "отрицательные": 2},
}

# Проверка наличия данных
if not data:
    raise ValueError("Нет данных для визуализации.")

# Формируем списки для построения круговой диаграммы с сегментами по темам и тональности
labels = []
values = []
colors = []

# Цвета для тональностей
color_positive = "#2ca02c"  # зеленый
color_negative = "#d62728"  # красный

for topic, sentiments in data.items():
    pos = sentiments.get("положительные", 0)
    neg = sentiments.get("отрицательные", 0)
    total = pos + neg
    if total == 0:
        # Пропускаем темы без упоминаний
        continue
    # Добавляем положительные сегменты
    if pos > 0:
        labels.append(f"{topic} — положительные")
        values.append(pos)
        colors.append(color_positive)
    # Добавляем отрицательные сегменты
    if neg > 0:
        labels.append(f"{topic} — отрицательные")
        values.append(neg)
        colors.append(color_negative)

if not labels:
    raise ValueError("Нет положительных или отрицательных упоминаний для визуализации.")

# --- Создание визуализации с plotly ---

fig = go.Figure()

# Добавляем круговую диаграмму
fig.add_trace(go.Pie(
    labels=labels,
    values=values,
    marker_colors=colors,
    hoverinfo='label+percent+value',
    textinfo='label+percent',
    textposition='inside',
    sort=False,  # сохранить порядок добавления
    insidetextfont=dict(size=14, color='white'),
    hole=0.3,  # для более современного вида (пончиковая диаграмма)
))

# Настройка макета
fig.update_layout(
    title="Процентное соотношение положительных и отрицательных упоминаний по ключевым темам",
    title_x=0.5,
    legend_title_text="Тональность",
    legend=dict(
        y=0.5,
        traceorder="normal",
        font_size=12,
        bgcolor="rgba(0,0,0,0)",
    ),
    margin=dict(t=80, b=40, l=40, r=40),
    font=dict(family="Arial, sans-serif", size=14),
)

# Добавим легенду с пояснением цветов тональностей
# (Plotly автоматически показывает легенду по меткам, но можно добавить пояснение)
# Здесь достаточно легенды по сегментам, так как цвет однозначно соответствует тональности.

# Создаем папку для сохранения, если ее нет
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Сохраняем статическую версию в PNG
png_path = os.path.join(output_dir, "viz_Процентное соотношение положительных и отрицательных упоминаний по ключевым темам.png")
fig.write_image(png_path, scale=2)  # scale=2 для высокого качества

# Сохраняем интерактивную версию в HTML с использованием CDN
html_path = os.path.join(output_dir, "viz_Процентное соотношение положительных и отрицательных упоминаний по ключевым темам.html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Выводим информацию о сохранении
print(f"Визуализация сохранена в:\n- PNG: {png_path}\n- HTML: {html_path}")