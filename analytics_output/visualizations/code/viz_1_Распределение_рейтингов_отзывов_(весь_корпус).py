import os
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Рейтинги и соответствующие количества отзывов
ratings = [1, 2, 3, 4, 5]
counts = [29, 8, 15, 28, 280]

# Проверка наличия данных: если все значения 0 или список пуст, обработать как отсутствие данных
if not counts or all(c == 0 for c in counts):
    raise ValueError("Данные для визуализации отсутствуют или все значения равны нулю.")

# Общие параметры
total_reviews = sum(counts)
average_rating = round(
    sum(r * c for r, c in zip(ratings, counts)) / total_reviews, 2
)

# Подписи с процентами для всплывающих подсказок
percentages = [count / total_reviews * 100 for count in counts]
hover_texts = [
    f"{rating} звезда{'а' if rating == 1 else 'ы' if rating in [2,3,4] else 'звезд'}: {count} отзывов ({percent:.1f}%)"
    for rating, count, percent in zip(ratings, counts, percentages)
]

# --- Создание интерактивной визуализации с plotly ---

fig = go.Figure()

# Добавляем столбцы
fig.add_trace(
    go.Bar(
        x=[f"{r} ⭐" for r in ratings],
        y=counts,
        text=[f"{count}" for count in counts],
        textposition='auto',
        hovertext=hover_texts,
        hoverinfo="text",
        marker_color=['#d62728', '#ff7f0e', '#bcbd22', '#2ca02c', '#1f77b4'],  # Цвета от красного к синему
        name="Количество отзывов"
    )
)

# Настройка макета
fig.update_layout(
    title="Распределение рейтингов отзывов (весь корпус)",
    xaxis_title="Рейтинг",
    yaxis_title="Количество отзывов",
    yaxis=dict(
        dtick=20,
        gridcolor='LightGray',
        zeroline=True,
        zerolinecolor='LightGray'
    ),
    xaxis=dict(
        tickmode='array',
        tickvals=[f"{r} ⭐" for r in ratings],
        ticktext=[f"{r} звезда{'а' if r == 1 else 'ы' if r in [2,3,4] else 'звезд'}" for r in ratings],
        showgrid=False
    ),
    bargap=0.3,
    plot_bgcolor='white',
    hovermode='x unified',
    font=dict(family="Arial, sans-serif", size=14),
    margin=dict(l=60, r=40, t=80, b=60)
)

# Добавим аннотацию с ключевыми инсайтами
positive_pct = percentages[3] + percentages[4]  # 4 и 5 звезд
negative_pct = percentages[0] + percentages[1]  # 1 и 2 звезды

insight_text = (
    f"Общее количество отзывов: {total_reviews}<br>"
    f"Средний рейтинг: {average_rating}<br>"
    f"Положительные отзывы (4-5 звезд): {positive_pct:.1f}%<br>"
    f"Отрицательные отзывы (1-2 звезды): {negative_pct:.1f}%"
)

fig.add_annotation(
    x=4.5,
    y=max(counts)*0.9,
    text=insight_text,
    showarrow=False,
    align="left",
    bordercolor="black",
    borderwidth=1,
    borderpad=5,
    bgcolor="white",
    font=dict(size=12)
)

# --- Сохранение визуализации ---

# Создаем папку, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Путь для файлов
png_path = os.path.join(output_dir, "viz_Распределение рейтингов отзывов (весь корпус).png")
html_path = os.path.join(output_dir, "viz_Распределение рейтингов отзывов (весь корпус).html")

# Сохраняем интерактивный HTML с использованием CDN plotly.js
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Для сохранения в PNG используем matplotlib (через fig.to_image требует kaleido или orca)
# Проверим, доступен ли kaleido
try:
    import kaleido  # noqa: F401
    # Сохраняем PNG через plotly (более качественно и проще)
    fig.write_image(png_path, scale=2)
except ImportError:
    # Если kaleido не установлен, используем matplotlib для статичной версии
    plt.figure(figsize=(8, 6))
    bars = plt.bar(
        [str(r) + " ⭐" for r in ratings],
        counts,
        color=['#d62728', '#ff7f0e', '#bcbd22', '#2ca02c', '#1f77b4'],
        edgecolor='black'
    )
    plt.title("Распределение рейтингов отзывов (весь корпус)", fontsize=16)
    plt.xlabel("Рейтинг", fontsize=14)
    plt.ylabel("Количество отзывов", fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # Добавим подписи значений на столбцах
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height + 3, str(count),
                 ha='center', va='bottom', fontsize=12)

    # Добавим текст с инсайтами внизу графика
    insight_str = (
        f"Всего отзывов: {total_reviews} | Средний рейтинг: {average_rating}\n"
        f"Положительные (4-5 звезд): {positive_pct:.1f}% | Отрицательные (1-2 звезды): {negative_pct:.1f}%"
    )
    plt.figtext(0.5, -0.05, insight_str, wrap=True, horizontalalignment='center', fontsize=12)

    # Создаем папку, если не существует
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.close()

print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")