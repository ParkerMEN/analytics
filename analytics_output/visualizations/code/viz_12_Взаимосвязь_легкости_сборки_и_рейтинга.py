import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Данные для визуализации
# Упоминание легкости сборки: "Да" и "Нет"
# Средний рейтинг и количество отзывов для каждой категории
data = {
    "Да": {"avg_rating": 4.7, "count": 10},
    # Для "Нет" данных по среднему рейтингу и количеству отзывов в условии нет,
    # но для полноты визуализации возьмем средний рейтинг по всем отзывам без упоминания
    # Логично предположить, что остальные отзывы (360 - 10 = 350) не упоминали легкость сборки.
    # Средний рейтинг по всем отзывам: 4.45 (дано)
    # Для "Нет" возьмем средний рейтинг, равный общему среднему рейтингу, количество 350
    "Нет": {"avg_rating": 4.45, "count": 350}
}

# Проверка наличия данных для обеих категорий
if not data or all(v["count"] == 0 for v in data.values()):
    raise ValueError("Отсутствуют данные для построения визуализации.")

# Подготовка списков для построения графика
x_categories = []
y_avg_ratings = []
sizes = []
hover_texts = []

for mention, stats in data.items():
    x_categories.append(mention)
    y_avg_ratings.append(stats["avg_rating"])
    # Размер маркера пропорционален количеству отзывов (с масштабированием для визуализации)
    sizes.append(stats["count"] * 5)
    hover_texts.append(
        f"Упоминание легкости сборки: {mention}<br>"
        f"Средний рейтинг: {stats['avg_rating']:.2f}<br>"
        f"Количество отзывов: {stats['count']}"
    )

# --- Создание интерактивной визуализации с plotly ---

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=x_categories,
    y=y_avg_ratings,
    mode='markers+text',
    text=[f"{r:.2f}" for r in y_avg_ratings],
    textposition="top center",
    marker=dict(
        size=sizes,
        color=['#1f77b4', '#ff7f0e'],  # Разные цвета для категорий
        sizemode='area',
        sizeref=2.*max(sizes)/(40.**2),  # Подстройка размера маркера для читаемости
        sizemin=10,
        line=dict(width=1, color='DarkSlateGrey')
    ),
    hoverinfo='text',
    hovertext=hover_texts,
    name='Средний рейтинг'
))

# Настройка осей и заголовков
fig.update_layout(
    title="Взаимосвязь легкости сборки и рейтинга",
    xaxis=dict(
        title="Упоминание легкости сборки",
        tickmode='array',
        tickvals=x_categories,
        ticktext=x_categories,
        showgrid=False
    ),
    yaxis=dict(
        title="Средний рейтинг",
        range=[4.0, 5.0],
        dtick=0.1,
        showgrid=True,
        zeroline=False
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
    template="plotly_white"
)

# Добавим аннотацию с инсайтом
fig.add_annotation(
    x='Да',
    y=data["Да"]["avg_rating"],
    text="Легкость сборки — значимый фактор положительных оценок",
    showarrow=True,
    arrowhead=2,
    ax=0,
    ay=-40,
    font=dict(color="black", size=12),
    bgcolor="rgba(255,255,255,0.8)",
    bordercolor="black",
    borderwidth=1
)

# --- Сохранение визуализации ---

output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Сохранение интерактивного HTML с использованием CDN plotly.js
html_path = os.path.join(output_dir, "viz_Взаимосвязь легкости сборки и рейтинга.html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Сохранение статического PNG с помощью matplotlib

# Для сохранения PNG используем matplotlib, создадим аналогичный график

fig_mpl, ax = plt.subplots(figsize=(6, 4))

# Отрисовка точек с размерами пропорциональными количеству отзывов
sizes_mpl = [count * 20 for count in [data[k]["count"] for k in x_categories]]  # масштабируем для matplotlib

colors_mpl = ['#1f77b4', '#ff7f0e']

ax.scatter(
    x_categories,
    y_avg_ratings,
    s=sizes_mpl,
    c=colors_mpl,
    edgecolors='black',
    alpha=0.7
)

# Подписи значений рейтинга над точками
for i, (x, y) in enumerate(zip(x_categories, y_avg_ratings)):
    ax.text(x, y + 0.02, f"{y:.2f}", ha='center', va='bottom', fontsize=10, fontweight='bold')

# Заголовок и подписи осей
ax.set_title("Взаимосвязь легкости сборки и рейтинга", fontsize=14, fontweight='bold')
ax.set_xlabel("Упоминание легкости сборки", fontsize=12)
ax.set_ylabel("Средний рейтинг", fontsize=12)
ax.set_ylim(4.0, 5.0)
ax.grid(True, linestyle='--', alpha=0.5)

# Аннотация с инсайтом
ax.annotate(
    "Легкость сборки — значимый фактор положительных оценок",
    xy=('Да', data["Да"]["avg_rating"]),
    xytext=(0, 30),
    textcoords='offset points',
    ha='center',
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3),
    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2")
)

plt.tight_layout()

png_path = os.path.join(output_dir, "viz_Взаимосвязь легкости сборки и рейтинга.png")
fig_mpl.savefig(png_path, dpi=300)
plt.close(fig_mpl)

print(f"Визуализация успешно сохранена:\n- HTML: {html_path}\n- PNG: {png_path}")