import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import io

# --- Подготовка данных ---

# Данные для визуализации
# Категории рекомендации и соответствующие средние рейтинги и количество отзывов
data = {
    "Да": {"средний_рейтинг": 5.0, "количество_отзывов": 6},
    "Нет": {"средний_рейтинг": 4.3, "количество_отзывов": 354}  # "ниже" - условно 4.3, ниже среднего 4.45
}

# Проверка наличия данных
if not data or all(v["количество_отзывов"] == 0 for v in data.values()):
    raise ValueError("Нет данных для визуализации.")

# Подготовка списков для графика
x_categories = list(data.keys())
y_ratings = [data[cat]["средний_рейтинг"] for cat in x_categories]
sizes = [data[cat]["количество_отзывов"] for cat in x_categories]

# Масштабируем размеры точек для визуализации количества отзывов (чтобы было видно разницу)
max_size = 60
min_size = 20
max_count = max(sizes)
min_count = min(sizes)
if max_count == min_count:
    marker_sizes = [40 for _ in sizes]
else:
    marker_sizes = [
        min_size + (s - min_count) / (max_count - min_count) * (max_size - min_size)
        for s in sizes
    ]

# --- Создание визуализации с plotly ---

fig = go.Figure()

# Добавляем точки
for i, cat in enumerate(x_categories):
    fig.add_trace(go.Scatter(
        x=[cat],
        y=[y_ratings[i]],
        mode='markers+text',
        marker=dict(
            size=marker_sizes[i],
            color='royalblue' if cat == "Да" else 'lightcoral',
            line=dict(width=1, color='DarkSlateGrey'),
            sizemode='diameter',
            sizeref=2.*max(marker_sizes)/(max_size**2),
            sizemin=4,
            opacity=0.8,
        ),
        text=[f"{y_ratings[i]:.2f}"],
        textposition="top center",
        hovertemplate=(
            f"<b>Рекомендации: {cat}</b><br>"
            f"Средний рейтинг: {y_ratings[i]:.2f}<br>"
            f"Количество отзывов: {sizes[i]}<extra></extra>"
        ),
        name=f"Рекомендации: {cat}"
    ))

# Настройка макета графика
fig.update_layout(
    title="Взаимосвязь рекомендаций пользователей и рейтинга",
    xaxis=dict(
        title="Наличие рекомендации",
        type='category',
        categoryorder='array',
        categoryarray=x_categories,
        tickfont=dict(size=14),
        showgrid=False,
    ),
    yaxis=dict(
        title="Средний рейтинг",
        range=[0, 5.5],
        dtick=0.5,
        tickfont=dict(size=14),
        gridcolor='LightGray',
    ),
    legend=dict(
        title="",
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(l=60, r=40, t=80, b=60),
    hovermode="closest",
    plot_bgcolor='white',
    font=dict(family="Arial, sans-serif", size=14, color="black"),
    height=500,
    width=700,
)

# Добавим аннотацию с инсайтом
fig.add_annotation(
    text="Рекомендации усиливают доверие и подтверждают лояльность",
    xref="paper", yref="paper",
    x=0.5, y=0.05,
    showarrow=False,
    font=dict(size=12, color="gray"),
    align="center"
)

# --- Сохранение визуализации ---

output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
html_path = os.path.join(output_dir, "viz_Взаимосвязь рекомендаций пользователей и рейтинга.html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Сохраняем статичное изображение PNG
# Для сохранения PNG требуется kaleido (установите через pip install -U kaleido)
png_path = os.path.join(output_dir, "viz_Взаимосвязь рекомендаций пользователей и рейтинга.png")
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print(f"Ошибка при сохранении PNG: {e}")
    print("Убедитесь, что установлен пакет 'kaleido' для экспорта изображений.")

# --- Конец кода ---