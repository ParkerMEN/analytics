import os
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Словарь с факторами и количеством упоминаний
factors_mentions = {
    "Аккумулятор": 25,
    "Недостатки": 37,
    "Достоинства": 50,
    "Качество": 8,
    "Вес": 25,
    "Доставка": 18,
    "Упаковка": 23,
    "Покупка": 14,
    "Рейтинг": 50,
    "Культиватор": 50,
    "Инструмент": 11,
}

# Проверка наличия данных
if not factors_mentions:
    raise ValueError("Данные о частоте упоминаний отсутствуют. Визуализация невозможна.")

# Сортируем факторы по количеству упоминаний для более удобного отображения
sorted_items = sorted(factors_mentions.items(), key=lambda x: x[1])

factors = [item[0] for item in sorted_items]
mentions = [item[1] for item in sorted_items]

# --- Создание интерактивной визуализации с plotly ---

fig = go.Figure()

# Добавляем горизонтальные столбцы
fig.add_trace(go.Bar(
    x=mentions,
    y=factors,
    orientation='h',
    marker=dict(color='rgba(58, 71, 80, 0.8)'),
    hovertemplate='<b>%{y}</b><br>Количество упоминаний: %{x}<extra></extra>',
))

# Настройка макета
fig.update_layout(
    title="Частота упоминаний ключевых факторов в отзывах",
    xaxis_title="Количество упоминаний",
    yaxis_title="Факторы",
    yaxis=dict(tickmode='linear'),
    margin=dict(l=140, r=40, t=80, b=60),
    template='plotly_white',
    height=600,
    hovermode="y unified",
)

# Добавляем интерактивные элементы: панель инструментов с зумом, панорамированием и сбросом
fig.update_layout(
    dragmode='zoom',
    hoverlabel=dict(font_size=14),
)

# --- Сохранение визуализации ---

# Создаем папку для сохранения, если не существует
output_dir = 'analytics_output/visualizations'
os.makedirs(output_dir, exist_ok=True)

# Путь для PNG и HTML
png_path = os.path.join(output_dir, 'viz_Частота упоминаний ключевых факторов в отзывах.png')
html_path = os.path.join(output_dir, 'viz_Частота упоминаний ключевых факторов в отзывах.html')

# Сохраняем интерактивный HTML с использованием CDN plotly.js
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

# Для сохранения PNG используем matplotlib (Plotly требует kaleido или orca, но для универсальности используем matplotlib)

# Создаем статическую горизонтальную столбчатую диаграмму с matplotlib
plt.figure(figsize=(10, 6))
bars = plt.barh(factors, mentions, color='#3a4750')
plt.xlabel('Количество упоминаний')
plt.title('Частота упоминаний ключевых факторов в отзывах')
plt.grid(axis='x', linestyle='--', alpha=0.7)

# Подписываем значения рядом с барами
for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.5, bar.get_y() + bar.get_height()/2,
             f'{int(width)}', va='center', fontsize=9)

plt.tight_layout()
plt.savefig(png_path, dpi=300)
plt.close()

print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")