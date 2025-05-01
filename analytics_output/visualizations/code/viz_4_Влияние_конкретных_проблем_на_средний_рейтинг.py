import os
import plotly.express as px
import pandas as pd

# --- Подготовка данных ---

# Данные по проблемам, количеству упоминаний и среднему рейтингу
data = {
    "Тип проблемы": [
        "Не работает/не включается",
        "Повреждения упаковки",
        "Проблемы с аккумулятором",
        "Комплект неполный",
        "Пластмассовые слабые детали",
        "Недостатки управления"
    ],
    "Количество упоминаний": [7, 7, 10, 3, 4, 3],
    # Для "Недостатки управления" возьмём среднее значение рейтинга (3.5) из диапазона 3.0-4.0
    "Средний рейтинг": [1.4, 1.7, 2.2, 3.0, 3.3, 3.5]
}

df = pd.DataFrame(data)

# Проверка на наличие данных
if df.empty:
    raise ValueError("Данные для визуализации отсутствуют.")

# Создаем папку для сохранения, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# --- Создание интерактивной визуализации с plotly ---

# Создаем столбчатую диаграмму с цветовой кодировкой по среднему рейтингу
fig = px.bar(
    df,
    x="Тип проблемы",
    y="Количество упоминаний",
    color="Средний рейтинг",
    color_continuous_scale="RdYlGn_r",  # Красно-желто-зеленая шкала, где красный - низкий рейтинг
    range_color=[1, 5],  # Диапазон рейтинга от 1 до 5 для единообразия цвета
    labels={
        "Тип проблемы": "Тип проблемы",
        "Количество упоминаний": "Количество упоминаний",
        "Средний рейтинг": "Средний рейтинг"
    },
    title="Влияние конкретных проблем на средний рейтинг",
    text="Количество упоминаний",
)

# Настройка текста на столбцах для лучшей читаемости
fig.update_traces(
    texttemplate='%{y}',
    textposition='outside',
    marker_line_color='black',
    marker_line_width=1.2,
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Количество упоминаний: %{y}<br>"
        "Средний рейтинг: %{marker.color:.2f}<extra></extra>"
    )
)

# Настройка осей
fig.update_layout(
    yaxis=dict(title="Количество упоминаний", rangemode="tozero", dtick=1),
    xaxis=dict(title="Тип проблемы", tickangle=-45),
    coloraxis_colorbar=dict(
        title="Средний рейтинг",
        ticks="outside",
        tickvals=[1, 2, 3, 4, 5],
        ticktext=["1 (низкий)", "2", "3", "4", "5 (высокий)"],
    ),
    margin=dict(t=80, b=120, l=60, r=40),
    template="plotly_white",
    font=dict(family="Arial, sans-serif", size=14),
    hovermode="x unified",
)

# Добавляем интерактивные элементы: зум, панель инструментов уже включены по умолчанию

# --- Сохранение визуализации ---

# Путь для сохранения PNG
png_path = os.path.join(output_dir, "viz_Влияние конкретных проблем на средний рейтинг.png")
# Путь для сохранения HTML
html_path = os.path.join(output_dir, "viz_Влияние конкретных проблем на средний рейтинг.html")

# Сохраняем PNG (требуется kaleido или orca)
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print(f"Не удалось сохранить PNG: {e}. Убедитесь, что установлен пакет 'kaleido'.")

# Сохраняем интерактивный HTML с использованием CDN и настройками для автономной работы
fig.write_html(
    html_path,
    include_plotlyjs="cdn",
    full_html=True,
    config={"displayModeBar": True, "responsive": True}
)

print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")