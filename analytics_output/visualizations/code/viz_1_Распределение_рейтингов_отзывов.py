import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Исходные данные: количество отзывов по рейтингам
ratings_counts = {
    "5": 280,
    "4": 28,
    "3": 15,
    "2": 8,
    "1": 29
}

# Проверка наличия данных
if not ratings_counts or sum(ratings_counts.values()) == 0:
    raise ValueError("Данные о рейтингах отсутствуют или сумма равна нулю.")

# Преобразуем ключи в упорядоченный список рейтингов (от 1 до 5)
ratings_order = ["1", "2", "3", "4", "5"]

# Подготовка списков для построения графика
counts = [ratings_counts.get(r, 0) for r in ratings_order]
total_reviews = sum(counts)
percentages = [count / total_reviews * 100 for count in counts]

# Подписи для оси X с указанием количества и процентов
x_labels = [f"{r} звезда\n{count} ({perc:.1f}%)" for r, count, perc in zip(ratings_order, counts, percentages)]

# --- Создание интерактивной визуализации с plotly ---

# Создаем столбчатую диаграмму с интерактивными элементами
fig = go.Figure()

fig.add_trace(go.Bar(
    x=ratings_order,
    y=counts,
    text=[f"{count} отзывов<br>{perc:.1f}%" for count, perc in zip(counts, percentages)],
    textposition='auto',
    marker_color=['#d62728', '#ff7f0e', '#bcbd22', '#2ca02c', '#1f77b4'],  # Цвета от негативных к позитивным
    hovertemplate="<b>Рейтинг: %{x} звезда</b><br>Количество: %{y}<br>Доля: %{text}<extra></extra>",
))

# Настройка оформления графика
fig.update_layout(
    title="Распределение рейтингов отзывов",
    xaxis_title="Рейтинг",
    yaxis_title="Количество отзывов",
    xaxis=dict(
        tickmode='array',
        tickvals=ratings_order,
        ticktext=x_labels,
        showgrid=False,
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='lightgrey',
        zeroline=True,
        zerolinecolor='lightgrey',
    ),
    bargap=0.3,
    plot_bgcolor='white',
    font=dict(family="Arial, sans-serif", size=14),
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial"),
    margin=dict(l=60, r=30, t=70, b=70),
)

# Добавим аннотацию с ключевыми инсайтами
positive_pct = percentages[ratings_order.index("4")] + percentages[ratings_order.index("5")]
negative_pct = percentages[ratings_order.index("1")] + percentages[ratings_order.index("2")]
avg_rating = sum(int(r) * c for r, c in zip(ratings_order, counts)) / total_reviews

insights_text = (
    f"Всего отзывов: {total_reviews}<br>"
    f"Средний рейтинг: {avg_rating:.2f}<br>"
    f"Положительные отзывы (4-5 звезд): {positive_pct:.1f}%<br>"
    f"Негативные отзывы (1-2 звезды): {negative_pct:.1f}%"
)

fig.add_annotation(
    text=insights_text,
    xref="paper", yref="paper",
    x=1.05, y=0.95,
    showarrow=False,
    bordercolor="black",
    borderwidth=1,
    borderpad=8,
    bgcolor="lightyellow",
    font=dict(size=12),
)

# --- Сохранение визуализации ---

# Создаем папку для сохранения, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Сохраняем интерактивный HTML с использованием CDN plotly.js
html_path = os.path.join(output_dir, "viz_Распределение рейтингов отзывов.html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# --- Создание статической версии с matplotlib ---

# Настройка стиля matplotlib для читаемости
plt.style.use('seaborn-whitegrid')
fig_mpl, ax = plt.subplots(figsize=(8, 6))

bars = ax.bar(ratings_order, counts, color=['#d62728', '#ff7f0e', '#bcbd22', '#2ca02c', '#1f77b4'], edgecolor='black')

# Добавляем подписи с количеством и процентами над столбцами
for bar, count, perc in zip(bars, counts, percentages):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + total_reviews * 0.01,
            f"{count}\n({perc:.1f}%)",
            ha='center', va='bottom', fontsize=11)

# Заголовок и подписи осей
ax.set_title("Распределение рейтингов отзывов", fontsize=16, fontweight='bold')
ax.set_xlabel("Рейтинг", fontsize=14)
ax.set_ylabel("Количество отзывов", fontsize=14)
ax.set_xticks(ratings_order)
ax.set_xticklabels([f"{r} звезда" for r in ratings_order], fontsize=12)

# Добавляем текст с инсайтами справа от графика
insights_text_mpl = (
    f"Всего отзывов: {total_reviews}\n"
    f"Средний рейтинг: {avg_rating:.2f}\n"
    f"Положительные отзывы (4-5 звезд): {positive_pct:.1f}%\n"
    f"Негативные отзывы (1-2 звезды): {negative_pct:.1f}%"
)
plt.gcf().text(0.85, 0.75, insights_text_mpl, fontsize=12, bbox=dict(facecolor='lightyellow', edgecolor='black'))

plt.tight_layout(rect=[0, 0, 0.8, 1])  # Оставляем место справа для текста

# Сохраняем статическое изображение в PNG
png_path = os.path.join(output_dir, "viz_Распределение рейтингов отзывов.png")
fig_mpl.savefig(png_path, dpi=300)

plt.close(fig_mpl)  # Закрываем фигуру matplotlib, чтобы не отображать в интерактивной среде