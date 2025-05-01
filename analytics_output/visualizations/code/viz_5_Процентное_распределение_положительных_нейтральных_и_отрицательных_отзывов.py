import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Исходные данные отзывов
reviews_data = {
    "Положительные (4-5 звезд)": 308,
    "Нейтральные (3 звезды)": 15,
    "Отрицательные (1-2 звезды)": 37,
}

total_reviews = sum(reviews_data.values())

# Обработка краевых случаев: если данных нет, создаем заглушку
if total_reviews == 0:
    reviews_data = {"Нет данных": 1}
    total_reviews = 1

# Вычисляем проценты для подписей
labels = list(reviews_data.keys())
values = list(reviews_data.values())
percentages = [v / total_reviews * 100 for v in values]
# Формируем подписи с процентами
hover_texts = [
    f"{label}<br>Количество: {value}<br>Доля: {percent:.1f}%"
    for label, value, percent in zip(labels, values, percentages)
]

# --- Создание интерактивной визуализации с plotly ---

# Цвета сегментов для лучшей читаемости и ассоциации
colors = ['#2ca02c', '#ffbb78', '#d62728']  # Зеленый, желтый, красный

fig = go.Figure(
    data=[go.Pie(
        labels=labels,
        values=values,
        hoverinfo='text',
        textinfo='label+percent',
        textfont_size=14,
        marker=dict(colors=colors, line=dict(color='#000000', width=1)),
        sort=False,  # Сохраняем порядок сегментов как в данных
        pull=[0.05 if label == "Отрицательные (1-2 звезды)" else 0 for label in labels],  # Выделяем негатив
        insidetextorientation='radial',
        hovertext=hover_texts,
    )]
)

# Заголовок и оформление
fig.update_layout(
    title={
        'text': "Процентное распределение положительных, нейтральных и отрицательных отзывов",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=20)
    },
    legend_title_text='Категории отзывов',
    legend=dict(
        font=dict(size=12),
        bordercolor="Black",
        borderwidth=1,
        y=0.5,
        yanchor="middle",
        x=1.05,
        xanchor="left"
    ),
    margin=dict(t=100, b=50, l=50, r=150),
    paper_bgcolor='white',
    hoverlabel=dict(font_size=14)
)

# Добавляем аннотацию с общим количеством отзывов и средним рейтингом
fig.add_annotation(
    dict(
        text=f"Всего отзывов: {total_reviews}<br>Средний рейтинг: 4.45",
        x=0.5,
        y=-0.1,
        showarrow=False,
        font=dict(size=14),
        xref="paper",
        yref="paper"
    )
)

# --- Сохранение визуализации ---

output_dir = 'analytics_output/visualizations'
os.makedirs(output_dir, exist_ok=True)

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
html_path = os.path.join(output_dir, 'viz_Процентное распределение положительных, нейтральных и отрицательных отзывов.html')
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# --- Создание статичной версии с matplotlib ---

# Настройка цветов и подписей для matplotlib
mpl_colors = ['#2ca02c', '#ffbb78', '#d62728']

fig_mpl, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    values,
    labels=labels,
    autopct='%1.1f%%',
    startangle=90,
    colors=mpl_colors,
    wedgeprops=dict(edgecolor='black'),
    textprops=dict(color="black", fontsize=12)
)
ax.set_title(
    "Процентное распределение положительных, нейтральных и отрицательных отзывов",
    fontsize=16,
    pad=20
)

# Добавляем подпись с общим количеством отзывов и средним рейтингом
plt.figtext(
    0.5, 0.02,
    f"Всего отзывов: {total_reviews} | Средний рейтинг: 4.45",
    ha="center",
    fontsize=12
)

plt.tight_layout()

png_path = os.path.join(output_dir, 'viz_Процентное распределение положительных, нейтральных и отрицательных отзывов.png')
fig_mpl.savefig(png_path, dpi=300)
plt.close(fig_mpl)

# --- Конец кода ---