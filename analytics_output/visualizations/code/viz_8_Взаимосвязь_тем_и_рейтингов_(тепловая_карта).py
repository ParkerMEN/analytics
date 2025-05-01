import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- Часть 1: Подготовка данных ---

# Темы по оси Y
topics = ["качество", "аккумулятор", "упаковка", "доставка", "удобство", "недостатки", "прочее"]

# Рейтинги по оси X
ratings = [1, 2, 3, 4, 5]

# Для демонстрации создадим примерную матрицу количества упоминаний тем по рейтингам.
# В реальной задаче эти данные должны быть получены из анализа отзывов.
# Здесь мы имитируем данные с учетом распределения рейтингов и логики, что негативные отзывы чаще упоминают "недостатки",
# а позитивные — "качество", "удобство" и "аккумулятор".

# Инициализация пустой матрицы (темы x рейтинги)
mentions = np.zeros((len(topics), len(ratings)), dtype=int)

# Примерные распределения упоминаний (искусственные данные для демонстрации)
# Кол-во упоминаний примерно пропорционально количеству отзывов с таким рейтингом,
# с добавлением тематической специфики.

rating_counts = {1: 29, 2: 8, 3: 15, 4: 28, 5: 280}

# Заполним матрицу вручную, чтобы показать смысл:
# Для 1 и 2 звезд — много "недостатков", "упаковка", "доставка"
# Для 4 и 5 звезд — много "качество", "аккумулятор", "удобство"
# Для 3 звезд — средние значения по всем темам
mentions_dict = {
    "качество":    [2, 1, 3, 20, 150],
    "аккумулятор": [1, 0, 2, 15, 130],
    "упаковка":    [10, 3, 5, 5, 20],
    "доставка":    [8, 2, 3, 10, 30],
    "удобство":    [1, 1, 3, 18, 140],
    "недостатки":  [20, 7, 5, 3, 10],
    "прочее":      [5, 2, 4, 7, 20],
}

for i, topic in enumerate(topics):
    mentions[i, :] = mentions_dict.get(topic, [0]*5)

# Создаем DataFrame для удобства и подписей
df_mentions = pd.DataFrame(
    mentions,
    index=topics,
    columns=[str(r) for r in ratings]
)

# Проверка на пустые данные — если все нули, создадим заглушку
if df_mentions.values.sum() == 0:
    print("Внимание: данные для визуализации отсутствуют. Отображается пустая тепловая карта.")
    df_mentions.loc[:, :] = 0

# --- Часть 2: Создание интерактивной тепловой карты с plotly ---

# Создаем фигуру
fig = go.Figure(
    data=go.Heatmap(
        z=df_mentions.values,
        x=[f"{r} звезда" for r in ratings],
        y=topics,
        colorscale='RdYlGn_r',  # Красно-желто-зеленая палитра, где красный — низкие оценки/высокие упоминания недостатков
        colorbar=dict(title="Количество упоминаний", titleside='right'),
        hovertemplate="<b>Тема:</b> %{y}<br><b>Рейтинг:</b> %{x}<br><b>Упоминаний:</b> %{z}<extra></extra>",
        zmin=0,
        zmax=np.max(df_mentions.values)*1.1 if np.max(df_mentions.values) > 0 else 1,
    )
)

# Настройка макета
fig.update_layout(
    title="Взаимосвязь тем и рейтингов (тепловая карта)",
    xaxis_title="Рейтинг (звёзды)",
    yaxis_title="Темы отзывов",
    yaxis=dict(autorange="reversed"),  # Чтобы темы шли сверху вниз в заданном порядке
    template="plotly_white",
    width=900,
    height=500,
    margin=dict(l=100, r=50, t=80, b=80),
)

# Добавим интерактивные возможности:
# - Наведение показывает точные значения
# - Зум и панорамирование по осям
fig.update_xaxes(fixedrange=False, zeroline=False)
fig.update_yaxes(fixedrange=False, zeroline=False)

# Создаем папку для сохранения, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
html_path = os.path.join(output_dir, "viz_Взаимосвязь тем и рейтингов (тепловая карта).html")
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Сохраняем статическую версию в PNG через kaleido (нужно установить kaleido: pip install -U kaleido)
png_path = os.path.join(output_dir, "viz_Взаимосвязь тем и рейтингов (тепловая карта).png")
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print("Ошибка при сохранении PNG. Убедитесь, что установлен пакет 'kaleido'.", e)

# --- Дополнительно: Статическая визуализация с matplotlib для сравнения (не обязательно) ---
# Создаем статическую тепловую карту с matplotlib для визуальной проверки

plt.figure(figsize=(9, 5))
plt.title("Взаимосвязь тем и рейтингов (тепловая карта) — статическая версия", fontsize=14)
plt.xlabel("Рейтинг (звёзды)")
plt.ylabel("Темы отзывов")
im = plt.imshow(df_mentions.values, aspect='auto', cmap='RdYlGn_r')

# Подписи осей
plt.xticks(ticks=np.arange(len(ratings)), labels=[f"{r} звезда" for r in ratings])
plt.yticks(ticks=np.arange(len(topics)), labels=topics)

# Добавим цветовую шкалу
cbar = plt.colorbar(im)
cbar.set_label('Количество упоминаний')

# Подписи значений в ячейках
for i in range(len(topics)):
    for j in range(len(ratings)):
        val = df_mentions.iloc[i, j]
        if val > 0:
            plt.text(j, i, str(val), ha='center', va='center', color='black', fontsize=9)

plt.tight_layout()

# Сохраняем статическое изображение matplotlib (дублирует PNG plotly, но для надежности)
matplotlib_png_path = os.path.join(output_dir, "viz_Взаимосвязь тем и рейтингов (тепловая карта)_matplotlib.png")
plt.savefig(matplotlib_png_path, dpi=150)
plt.close()

print(f"Интерактивная визуализация сохранена в: {html_path}")
print(f"Статическая визуализация (plotly) сохранена в: {png_path}")
print(f"Статическая визуализация (matplotlib) сохранена в: {matplotlib_png_path}")