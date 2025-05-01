import os
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Данные по типам проблем с аккумулятором
data = {
    "Тип проблемы аккумулятора": ["Зарядка быстро", "Не заряжается"],
    "Количество упоминаний": [15, 5],
    "Средний рейтинг": [4.8, 1.0],
}

df = pd.DataFrame(data)

# Обработка краевых случаев: если данных нет, создадим пустой датафрейм с нужными столбцами
if df.empty:
    df = pd.DataFrame({
        "Тип проблемы аккумулятора": [],
        "Количество упоминаний": [],
        "Средний рейтинг": [],
    })

# --- Создание интерактивной визуализации с plotly ---

# Настройка цветовой шкалы для рейтинга: от красного (низкий рейтинг) к зеленому (высокий)
color_scale = [
    [0.0, "red"],
    [0.5, "orange"],
    [1.0, "green"]
]

fig = px.bar(
    df,
    x="Тип проблемы аккумулятора",
    y="Количество упоминаний",
    color="Средний рейтинг",
    color_continuous_scale=color_scale,
    range_color=[1, 5],
    labels={
        "Тип проблемы аккумулятора": "Тип проблемы аккумулятора",
        "Количество упоминаний": "Количество упоминаний",
        "Средний рейтинг": "Средний рейтинг"
    },
    title="Частота упоминаний проблем с аккумулятором и их влияние на рейтинг",
    text="Количество упоминаний",
)

# Улучшаем читаемость текста на столбцах
fig.update_traces(textposition='outside')

# Настройка осей
fig.update_yaxes(title_text="Количество упоминаний", rangemode="tozero")
fig.update_xaxes(title_text="Тип проблемы аккумулятора")

# Настройка цветовой шкалы и легенды
fig.update_coloraxes(
    colorbar_title="Средний рейтинг",
    colorbar_ticks="outside",
    colorbar_tickvals=[1, 2, 3, 4, 5],
    colorbar_ticktext=["1", "2", "3", "4", "5"],
)

# Добавление интерактивных элементов: зум, панорамирование, подсказки уже включены по умолчанию

# --- Сохранение визуализации ---

# Создаем папку для сохранения, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Путь для PNG и HTML файлов
png_path = os.path.join(output_dir, "viz_Частота упоминаний проблем с аккумулятором и их влияние на рейтинг.png")
html_path = os.path.join(output_dir, "viz_Частота упоминаний проблем с аккумулятором и их влияние на рейтинг.html")

# Сохраняем статическую версию в PNG с помощью matplotlib (через fig.to_image требует kaleido)
# Используем plotly для сохранения PNG (требуется kaleido)
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print(f"Ошибка при сохранении PNG: {e}\n"
          "Убедитесь, что установлен пакет 'kaleido' для экспорта изображений.")

# Сохраняем интерактивную версию в HTML с использованием CDN
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN вместо встраивания plotly.js
    full_html=True,          # Создаем полноценный HTML
    config={"displayModeBar": True, "responsive": True}  # Панель инструментов и адаптивность
)

# --- Дополнительно: Статическая визуализация с matplotlib для сравнения (необязательно) ---

# Создаем столбчатую диаграмму с цветовой кодировкой по рейтингу
fig_mpl, ax = plt.subplots(figsize=(8, 5))

# Цвета: зеленый для рейтинга >=4, красный для <4
colors = ['green' if r >= 4 else 'red' for r in df["Средний рейтинг"]]

bars = ax.bar(df["Тип проблемы аккумулятора"], df["Количество упоминаний"], color=colors)

# Добавляем подписи над столбцами
for bar, count in zip(bars, df["Количество упоминаний"]):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + 0.5, str(count), ha='center', va='bottom', fontsize=10)

ax.set_title("Частота упоминаний проблем с аккумулятором и их влияние на рейтинг", fontsize=14)
ax.set_xlabel("Тип проблемы аккумулятора", fontsize=12)
ax.set_ylabel("Количество упоминаний", fontsize=12)
ax.set_ylim(0, max(df["Количество упоминаний"]) * 1.3)

# Легенда для цветов
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='green', label='Средний рейтинг ≥ 4'),
    Patch(facecolor='red', label='Средний рейтинг < 4')
]
ax.legend(handles=legend_elements, title="Средний рейтинг")

plt.tight_layout()

# Сохраняем matplotlib PNG (дополнительно)
mpl_png_path = os.path.join(output_dir, "viz_Частота упоминаний проблем с аккумулятором и их влияние на рейтинг_matplotlib.png")
fig_mpl.savefig(mpl_png_path, dpi=150)
plt.close(fig_mpl)