import os
import pandas as pd
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Данные по факторам, среднему рейтингу и количеству отзывов
data = {
    "Фактор": [
        "Положительное качество",
        "Отрицательное качество",
        "Аккумулятор заряжается быстро",
        "Аккумулятор не заряжается",
        "Повреждения упаковки",
        "Не работает/не включается",
        "Легкость сборки",
        "Рекомендации"
    ],
    "Средний рейтинг": [4.8, 1.0, 4.8, 1.0, 1.7, 1.4, 4.7, 5.0],
    "Количество отзывов": [8, 2, 15, 5, 7, 7, 10, 6]
}

df = pd.DataFrame(data)

# Проверка на пустой датафрейм (краевой случай)
if df.empty:
    raise ValueError("Данные для визуализации отсутствуют.")

# --- Создание интерактивной визуализации с plotly ---

# Настройка размера точек: масштабируем для лучшей визуализации
# Минимальный размер 10, максимальный 50
size_ref = 2.0 * max(df["Количество отзывов"]) / (50**2)

fig = px.scatter(
    df,
    x="Фактор",
    y="Средний рейтинг",
    size="Количество отзывов",
    size_max=50,
    color="Средний рейтинг",
    color_continuous_scale=px.colors.sequential.Viridis,
    hover_name="Фактор",
    hover_data={
        "Средний рейтинг": ':.2f',
        "Количество отзывов": True,
        "Фактор": False  # уже в hover_name
    },
    labels={
        "Фактор": "Фактор",
        "Средний рейтинг": "Средний рейтинг",
        "Количество отзывов": "Количество отзывов"
    },
    title="Влияние упоминаний факторов на средний рейтинг"
)

# Настройка осей
fig.update_layout(
    xaxis_title="Фактор",
    yaxis_title="Средний рейтинг",
    yaxis=dict(range=[0, 5.5], dtick=0.5),
    coloraxis_colorbar=dict(
        title="Средний рейтинг",
        ticks="outside"
    ),
    plot_bgcolor="white",
    margin=dict(l=60, r=40, t=80, b=120),
    hovermode="closest"
)

# Улучшаем читаемость подписей по оси X (поворот)
fig.update_xaxes(tickangle=45, tickfont=dict(size=11))

# Добавим горизонтальную линию среднего рейтинга по всем отзывам (4.45)
fig.add_hline(
    y=4.45,
    line_dash="dash",
    line_color="red",
    annotation_text="Средний рейтинг всех отзывов (4.45)",
    annotation_position="top left",
    annotation_font_color="red"
)

# --- Сохранение интерактивной визуализации в HTML ---

output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

html_path = os.path.join(output_dir, "viz_Влияние упоминаний факторов на средний рейтинг.html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# --- Создание статической версии с matplotlib ---

plt.figure(figsize=(12, 6))
scatter = plt.scatter(
    df["Фактор"],
    df["Средний рейтинг"],
    s=[n * 20 for n in df["Количество отзывов"]],  # масштабируем размер точек
    c=df["Средний рейтинг"],
    cmap="viridis",
    alpha=0.8,
    edgecolors="black",
    linewidth=0.7
)

plt.xticks(rotation=45, ha="right", fontsize=11)
plt.yticks(fontsize=11)
plt.ylim(0, 5.5)
plt.ylabel("Средний рейтинг", fontsize=13)
plt.xlabel("Фактор", fontsize=13)
plt.title("Влияние упоминаний факторов на средний рейтинг", fontsize=15)

# Добавляем цветовую шкалу
cbar = plt.colorbar(scatter)
cbar.set_label("Средний рейтинг", fontsize=12)

# Добавляем горизонтальную линию среднего рейтинга
plt.axhline(4.45, color="red", linestyle="--", linewidth=1)
plt.text(
    0, 4.55, "Средний рейтинг всех отзывов (4.45)",
    color="red", fontsize=11, va="bottom", ha="left"
)

plt.tight_layout()

png_path = os.path.join(output_dir, "viz_Влияние упоминаний факторов на средний рейтинг.png")
plt.savefig(png_path, dpi=300)
plt.close()

print(f"Визуализация успешно сохранена:\n- HTML: {html_path}\n- PNG: {png_path}")