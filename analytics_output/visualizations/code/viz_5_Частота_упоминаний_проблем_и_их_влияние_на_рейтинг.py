import os
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# --- Подготовка данных ---

# Данные о проблемах: название, частота упоминаний, средний рейтинг
problems = [
    {"проблема": "Не работает / не включается", "упоминания": 7, "рейтинг": 1.3},
    {"проблема": "Повреждённая упаковка", "упоминания": 7, "рейтинг": 2.1},
    {"проблема": "Проблемы с аккумулятором", "упоминания": 6, "рейтинг": 1.5},
    {"проблема": "Отсутствие комплектующих", "упоминания": 5, "рейтинг": 3.0},
    {"проблема": "Слабые колёса / детали", "упоминания": 5, "рейтинг": 3.5},
]

# Проверка наличия данных
if not problems:
    raise ValueError("Нет данных для визуализации.")

# Извлекаем списки для построения графика
labels = [item["проблема"] for item in problems]
frequencies = [item["упоминания"] for item in problems]
ratings = [item["рейтинг"] for item in problems]

# --- Создание цветовой шкалы по рейтингу ---
# Используем matplotlib для создания градиента от красного (низкий рейтинг) к зелёному (высокий рейтинг)
# Рейтинги варьируются примерно от 1.3 до 3.5, нормализуем для colormap
rating_min = min(ratings)
rating_max = max(ratings)
norm = mpl.colors.Normalize(vmin=rating_min, vmax=rating_max)
cmap = mpl.cm.get_cmap('RdYlGn_r')  # Обратная RdYlGn: красный - низкий рейтинг, зелёный - высокий

# Получаем цвета для каждого рейтинга в формате hex для plotly
colors = [mpl.colors.rgb2hex(cmap(norm(r))) for r in ratings]

# --- Создание интерактивной визуализации с plotly ---

fig = go.Figure()

# Добавляем столбцы с цветовой кодировкой по рейтингу
fig.add_trace(go.Bar(
    x=labels,
    y=frequencies,
    marker_color=colors,
    text=[f"Средний рейтинг: {r:.2f}" for r in ratings],
    hovertemplate=(
        "<b>%{x}</b><br>" +
        "Упоминаний: %{y}<br>" +
        "%{text}<br>" +
        "<extra></extra>"
    ),
))

# Настройка цветовой шкалы для легенды (создадим отдельный цветовой бар)
# Для этого добавим скрытый scatter с цветовой шкалой
colorbar_trace = go.Scatter(
    x=[None],
    y=[None],
    mode='markers',
    marker=dict(
        colorscale='RdYlGn_r',
        cmin=rating_min,
        cmax=rating_max,
        color=[rating_min, rating_max],
        colorbar=dict(
            title="Средний рейтинг",
            titleside="top",
            tickvals=[rating_min, rating_max],
            ticktext=[f"{rating_min:.1f}", f"{rating_max:.1f}"],
            len=0.5,
            y=0.75,
            yanchor="middle",
            thickness=15,
        ),
        showscale=True,
    ),
    hoverinfo='none',
    showlegend=False,
)

fig.add_trace(colorbar_trace)

# Настройка макета графика
fig.update_layout(
    title="Частота упоминаний проблем и их влияние на рейтинг",
    xaxis_title="Проблемы",
    yaxis_title="Количество упоминаний",
    yaxis=dict(dtick=1, rangemode="tozero"),
    template="plotly_white",
    hovermode="x unified",
    margin=dict(t=80, b=100),
    font=dict(family="Arial, sans-serif", size=14),
)

# Добавим интерактивные элементы: зум, панель инструментов включена по умолчанию

# --- Сохранение визуализации ---

output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

png_path = os.path.join(output_dir, "viz_Частота упоминаний проблем и их влияние на рейтинг.png")
html_path = os.path.join(output_dir, "viz_Частота упоминаний проблем и их влияние на рейтинг.html")

# Сохраняем PNG статическую версию
# Для сохранения PNG используем kaleido (установите через pip install -U kaleido)
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print(f"Не удалось сохранить PNG: {e}")

# Сохраняем интерактивный HTML с CDN plotly.js
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

print(f"Визуализация сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")