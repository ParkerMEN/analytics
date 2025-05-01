import os
import plotly.graph_objects as go
import plotly.io as pio

# --- Подготовка данных ---

# Данные по факторам: название, количество упоминаний, средний рейтинг
factors_data = [
    {"фактор": "Упоминание качества (положительный контекст)", "упоминания": 5, "рейтинг": 4.8},
    {"фактор": "Легкость сборки и управления", "упоминания": 5, "рейтинг": 5.0},
    {"фактор": "Аккумулятор без проблем", "упоминания": 17, "рейтинг": 5.0},
    {"фактор": "Проблемы с аккумулятором", "упоминания": 6, "рейтинг": 1.5},
    {"фактор": "Повреждения упаковки", "упоминания": 7, "рейтинг": 2.1},
    {"фактор": "Проблемы с надежностью двигателя", "упоминания": 2, "рейтинг": 1.0},
]

# Проверка наличия данных
if not factors_data:
    raise ValueError("Отсутствуют данные для визуализации.")

# Извлечение списков для построения графика
факторы = [item["фактор"] for item in factors_data]
упоминания = [item["упоминания"] for item in factors_data]
рейтинги = [item["рейтинг"] for item in factors_data]

# --- Создание визуализации с plotly ---

# Создаем цветовую схему: положительные факторы — зеленые, негативные — красные
# Критерий: рейтинг >=4 — положительный, рейтинг <4 — негативный
colors = ['green' if r >= 4 else 'red' for r in рейтинги]

# Размер маркера пропорционален количеству упоминаний (с масштабированием для читаемости)
marker_sizes = [max(10, min(50, u * 3)) for u in упоминания]

fig = go.Figure()

# Добавляем точки
fig.add_trace(go.Scatter(
    x=упоминания,
    y=рейтинги,
    mode='markers+text',
    text=факторы,
    textposition='top center',
    marker=dict(
        size=marker_sizes,
        color=colors,
        line=dict(width=1, color='DarkSlateGrey'),
        sizemode='diameter',
        sizeref=2.*max(marker_sizes)/(100.**2),
        sizemin=10,
        opacity=0.8,
    ),
    hovertemplate=(
        "<b>%{text}</b><br>" +
        "Количество упоминаний: %{x}<br>" +
        "Средний рейтинг: %{y:.2f}<extra></extra>"
    ),
    name="Факторы"
))

# Добавляем горизонтальную линию среднего рейтинга по всему набору отзывов (4.45)
fig.add_hline(
    y=4.45,
    line_dash="dash",
    line_color="blue",
    annotation_text="Средний рейтинг всех отзывов (4.45)",
    annotation_position="bottom right",
    annotation_font_color="blue"
)

# Настройка осей
fig.update_xaxes(
    title_text="Количество упоминаний фактора",
    zeroline=True,
    zerolinewidth=1,
    zerolinecolor='LightGrey',
    showgrid=True,
    gridcolor='LightGrey',
    rangemode='tozero',
    dtick=1,
)

fig.update_yaxes(
    title_text="Средний рейтинг",
    range=[0, 5.5],
    zeroline=True,
    zerolinewidth=1,
    zerolinecolor='LightGrey',
    showgrid=True,
    gridcolor='LightGrey',
    dtick=0.5,
)

# Заголовок и оформление
fig.update_layout(
    title={
        'text': "Влияние упоминаний факторов на средний рейтинг (корреляция)",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=20)
    },
    plot_bgcolor='white',
    hovermode='closest',
    legend=dict(
        title="Тип фактора",
        itemsizing='constant',
        traceorder='normal',
        font=dict(size=12),
        bgcolor='rgba(0,0,0,0)'
    ),
    margin=dict(l=60, r=40, t=80, b=60),
)

# Добавим легенду вручную (поскольку цвета заданы напрямую)
fig.add_trace(go.Scatter(
    x=[None], y=[None],
    mode='markers',
    marker=dict(size=15, color='green'),
    legendgroup="Положительные факторы",
    showlegend=True,
    name="Положительные факторы (рейтинг ≥ 4)"
))
fig.add_trace(go.Scatter(
    x=[None], y=[None],
    mode='markers',
    marker=dict(size=15, color='red'),
    legendgroup="Негативные факторы",
    showlegend=True,
    name="Негативные факторы (рейтинг < 4)"
))

# --- Сохранение визуализации ---

output_dir = 'analytics_output/visualizations'
os.makedirs(output_dir, exist_ok=True)

png_path = os.path.join(output_dir, 'viz_Влияние упоминаний факторов на средний рейтинг (корреляция).png')
html_path = os.path.join(output_dir, 'viz_Влияние упоминаний факторов на средний рейтинг (корреляция).html')

# Сохраняем статическую версию в PNG (через kaleido)
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print(f"Ошибка при сохранении PNG: {e}. Убедитесь, что установлен пакет 'kaleido'.")

# Сохраняем интерактивную версию в HTML с использованием CDN
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,          # Полноценный HTML документ
    config={"displayModeBar": True, "responsive": True}  # Панель инструментов и адаптивность
)

print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")