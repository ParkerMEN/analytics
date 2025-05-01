import os
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import numpy as np

# --- Подготовка данных ---

# Данные по упоминаниям веса и рейтингам
data = {
    "Упоминание веса": ["Легкий", "Тяжелый", "Не упоминается"],
    "Количество упоминаний": [25, 5, 330],  # Добавим примерные данные для "Тяжелый" и "Не упоминается"
    "Средний рейтинг": [4.7, 3.8, 4.4],  # Примерные средние рейтинги для остальных категорий
    "Процент 5-звездочных": [88, 20, 75]  # Дополнительная информация для всплывающих подсказок
}

# Проверка на отсутствие данных (краевые случаи)
if not data["Упоминание веса"] or not data["Количество упоминаний"] or not data["Средний рейтинг"]:
    raise ValueError("Отсутствуют необходимые данные для визуализации.")

# Создаем DataFrame для удобства работы с plotly
import pandas as pd

df = pd.DataFrame(data)

# --- Создание интерактивной визуализации с plotly ---

# Создаем столбчатую диаграмму с цветовой кодировкой по среднему рейтингу
fig = px.bar(
    df,
    x="Упоминание веса",
    y="Количество упоминаний",
    color="Средний рейтинг",
    color_continuous_scale=px.colors.sequential.Viridis,
    labels={
        "Упоминание веса": "Упоминание веса",
        "Количество упоминаний": "Количество упоминаний",
        "Средний рейтинг": "Средний рейтинг"
    },
    title="Частота упоминаний и влияние легкости веса на рейтинг",
    text="Количество упоминаний",
    hover_data={
        "Средний рейтинг": ':.2f',
        "Процент 5-звездочных": True,
        "Количество упоминаний": True,
        "Упоминание веса": False
    }
)

# Настройка текста на столбцах (отображать количество упоминаний)
fig.update_traces(textposition='outside')

# Настройка цветовой шкалы и легенды
fig.update_coloraxes(colorbar_title="Средний рейтинг")

# Настройка осей
fig.update_layout(
    yaxis=dict(title="Количество упоминаний", rangemode="tozero"),
    xaxis=dict(title="Упоминание веса"),
    uniformtext_minsize=8,
    uniformtext_mode='hide',
    margin=dict(t=80, b=50, l=60, r=40),
    template="plotly_white",
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial")
)

# Добавим интерактивные элементы: зум, панель инструментов уже включены по умолчанию

# --- Сохранение визуализации ---

# Создаем директорию для сохранения, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
html_path = os.path.join(output_dir, "viz_Частота упоминаний и влияние легкости веса на рейтинг.html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Для сохранения PNG используем kaleido (обеспечивает высокое качество)
png_path = os.path.join(output_dir, "viz_Частота упоминаний и влияние легкости веса на рейтинг.png")
try:
    fig.write_image(png_path, scale=2)  # scale=2 для высокого разрешения
except ValueError as e:
    print("Ошибка при сохранении PNG. Убедитесь, что установлен пакет 'kaleido'.")
    print("Ошибка:", e)

# --- Дополнительно: Статическая версия с matplotlib для сравнения качества (не обязательно) ---

# Создаем столбчатую диаграмму matplotlib с цветовой кодировкой по среднему рейтингу
fig_mpl, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(
    df["Упоминание веса"],
    df["Количество упоминаний"],
    color=plt.cm.viridis((df["Средний рейтинг"] - df["Средний рейтинг"].min()) /
                         (df["Средний рейтинг"].max() - df["Средний рейтинг"].min()))
)

# Добавляем подписи с количеством упоминаний над столбцами
for bar, count in zip(bars, df["Количество упоминаний"]):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + 0.5, str(count),
            ha='center', va='bottom', fontsize=10)

# Настройка осей и заголовка
ax.set_xlabel("Упоминание веса", fontsize=12)
ax.set_ylabel("Количество упоминаний", fontsize=12)
ax.set_title("Частота упоминаний и влияние легкости веса на рейтинг", fontsize=14)
ax.set_ylim(0, max(df["Количество упоминаний"]) * 1.15)

# Добавляем цветовую шкалу для среднего рейтинга
sm = plt.cm.ScalarMappable(cmap='viridis', 
                           norm=plt.Normalize(vmin=df["Средний рейтинг"].min(), vmax=df["Средний рейтинг"].max()))
sm.set_array([])
cbar = fig_mpl.colorbar(sm, ax=ax)
cbar.set_label('Средний рейтинг', fontsize=12)

plt.tight_layout()

# Сохраняем matplotlib PNG (альтернативный вариант)
mpl_png_path = os.path.join(output_dir, "viz_Частота упоминаний и влияние легкости веса на рейтинг_matplotlib.png")
fig_mpl.savefig(mpl_png_path, dpi=300)

plt.close(fig_mpl)

# --- Конец кода ---