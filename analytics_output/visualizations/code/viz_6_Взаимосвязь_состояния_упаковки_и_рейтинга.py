import os
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Данные отзывов по состоянию упаковки и рейтингу
# Учитываем количество отзывов и средний рейтинг для каждой категории упаковки
data = {
    "Состояние упаковки": ["Целая упаковка", "Повреждённая упаковка"],
    "Количество отзывов": [9, 7],
    "Средний рейтинг": [5.0, 2.1]
}

# Проверяем, что данные не пустые и содержат необходимые поля
if not data["Состояние упаковки"] or not data["Средний рейтинг"]:
    raise ValueError("Отсутствуют данные для визуализации.")

# Создаем DataFrame для удобства работы с plotly
import pandas as pd

df = pd.DataFrame(data)

# Для точечного графика с бинарной переменной по оси Y создадим числовое отображение:
# "Целая упаковка" -> 1, "Повреждённая упаковка" -> 0
df["Упаковка (число)"] = df["Состояние упаковки"].map({
    "Целая упаковка": 1,
    "Повреждённая упаковка": 0
})

# --- Создание визуализации с plotly ---

# Создаем интерактивный точечный график
fig = px.scatter(
    df,
    x="Средний рейтинг",
    y="Упаковка (число)",
    size="Количество отзывов",  # Размер точки отражает количество отзывов
    color="Состояние упаковки",
    color_discrete_map={"Целая упаковка": "green", "Повреждённая упаковка": "red"},
    labels={
        "Средний рейтинг": "Рейтинг",
        "Упаковка (число)": "Состояние упаковки",
        "Состояние упаковки": "Состояние упаковки",
        "Количество отзывов": "Количество отзывов"
    },
    title="Взаимосвязь состояния упаковки и рейтинга",
    hover_name="Состояние упаковки",
    hover_data={
        "Средний рейтинг": True,
        "Количество отзывов": True,
        "Упаковка (число)": False  # Скрываем числовое значение упаковки в подсказке
    },
)

# Настроим ось Y для отображения категорий вместо чисел
fig.update_yaxes(
    tickmode="array",
    tickvals=[0, 1],
    ticktext=["Повреждённая упаковка", "Целая упаковка"],
    title="Состояние упаковки",
    range=[-0.5, 1.5]
)

# Настроим ось X (рейтинг) с диапазоном от 0 до 5.5 для лучшей читаемости
fig.update_xaxes(
    range=[0, 5.5],
    dtick=0.5,
    title="Рейтинг"
)

# Добавим сетку для удобства восприятия
fig.update_layout(
    yaxis=dict(showgrid=True),
    xaxis=dict(showgrid=True),
    legend_title_text="Состояние упаковки",
    font=dict(family="Arial, sans-serif", size=14),
    margin=dict(l=60, r=40, t=80, b=60),
    hovermode="closest"
)

# Добавим аннотацию с ключевым инсайтом
fig.add_annotation(
    x=3.5,
    y=1.3,
    text="Сильная корреляция между целостностью упаковки и удовлетворённостью",
    showarrow=False,
    font=dict(size=12, color="black"),
    bgcolor="rgba(255,255,255,0.8)",
    bordercolor="black",
    borderwidth=1,
    borderpad=4
)

# --- Сохранение визуализации ---

output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Сохраняем интерактивную версию в HTML с использованием CDN plotly.js
html_path = os.path.join(output_dir, "viz_Взаимосвязь состояния упаковки и рейтинга.html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Для сохранения PNG используем kaleido (встроенный в plotly >=4.9)
png_path = os.path.join(output_dir, "viz_Взаимосвязь состояния упаковки и рейтинга.png")
fig.write_image(png_path, scale=2)

# --- Дополнительно: Статическая визуализация с matplotlib для сравнения ---

# Создаем статический точечный график с matplotlib
fig_mpl, ax = plt.subplots(figsize=(8, 4))

# Отобразим точки с размерами, пропорциональными количеству отзывов
sizes = [count * 50 for count in df["Количество отзывов"]]  # масштабируем для видимости

# Отобразим точки
colors = ["green" if state == "Целая упаковка" else "red" for state in df["Состояние упаковки"]]
y_ticks = [0, 1]
y_labels = ["Повреждённая упаковка", "Целая упаковка"]
y_values = df["Упаковка (число)"]

scatter = ax.scatter(
    df["Средний рейтинг"],
    y_values,
    s=sizes,
    c=colors,
    alpha=0.7,
    edgecolors="black"
)

# Настроим оси
ax.set_yticks(y_ticks)
ax.set_yticklabels(y_labels, fontsize=12)
ax.set_xlabel("Рейтинг", fontsize=14)
ax.set_title("Взаимосвязь состояния упаковки и рейтинга", fontsize=16)
ax.set_xlim(0, 5.5)
ax.grid(True, axis='x', linestyle='--', alpha=0.7)

# Добавим подписи к точкам с количеством отзывов
for i, row in df.iterrows():
    ax.text(
        row["Средний рейтинг"],
        row["Упаковка (число)"] + 0.1,
        f"{row['Количество отзывов']} отзывов",
        ha='center',
        fontsize=11
    )

plt.tight_layout()

# Сохраняем matplotlib-график рядом с plotly PNG для сравнения
mpl_png_path = os.path.join(output_dir, "viz_Взаимосвязь состояния упаковки и рейтинга_matplotlib.png")
fig_mpl.savefig(mpl_png_path, dpi=150)

plt.close(fig_mpl)  # Закрываем фигуру, чтобы не отображать в интерактивных средах