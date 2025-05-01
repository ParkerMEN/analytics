import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Пример данных: количество упоминаний проблем по месяцам
# В реальной задаче сюда подгружаются данные из источника с временными метками и подсчетом упоминаний
# Для демонстрации создадим искусственный набор данных с временными метками и тремя темами проблем

# Создаем диапазон месяцев (например, за 12 месяцев)
months = pd.date_range(start="2023-01-01", periods=12, freq='MS')

# Генерируем примерные данные с трендами и шумом
np.random.seed(42)
battery_mentions = np.maximum(0, np.round(20 + np.linspace(5, -3, 12) + np.random.normal(0, 2, 12))).astype(int)
packaging_mentions = np.maximum(0, np.round(15 + np.linspace(-2, 4, 12) + np.random.normal(0, 1.5, 12))).astype(int)
delivery_mentions = np.maximum(0, np.round(10 + np.sin(np.linspace(0, 3*np.pi, 12))*5 + np.random.normal(0, 1, 12))).astype(int)

# Формируем DataFrame
df = pd.DataFrame({
    "Месяц": months,
    "Проблемы с аккумулятором": battery_mentions,
    "Проблемы с упаковкой": packaging_mentions,
    "Проблемы с доставкой": delivery_mentions,
})

# Проверяем наличие данных
if df.empty or df[["Проблемы с аккумулятором", "Проблемы с упаковкой", "Проблемы с доставкой"]].sum().sum() == 0:
    raise ValueError("Отсутствуют данные для визуализации упоминаний проблем по месяцам.")

# Преобразуем месяц в строку для удобства отображения на оси
df["Месяц_стр"] = df["Месяц"].dt.strftime("%Y-%m")

# --- Создание интерактивной визуализации с plotly ---

# Создаем фигуру с линиями для каждой темы
fig = go.Figure()

# Добавляем линии для каждой проблемной темы
fig.add_trace(go.Scatter(
    x=df["Месяц_стр"],
    y=df["Проблемы с аккумулятором"],
    mode='lines+markers',
    name='Проблемы с аккумулятором',
    line=dict(color='firebrick', width=3),
    marker=dict(size=8),
    hovertemplate='%{x}<br>Упоминаний: %{y}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=df["Месяц_стр"],
    y=df["Проблемы с упаковкой"],
    mode='lines+markers',
    name='Проблемы с упаковкой',
    line=dict(color='royalblue', width=3),
    marker=dict(size=8),
    hovertemplate='%{x}<br>Упоминаний: %{y}<extra></extra>'
))

fig.add_trace(go.Scatter(
    x=df["Месяц_стр"],
    y=df["Проблемы с доставкой"],
    mode='lines+markers',
    name='Проблемы с доставкой',
    line=dict(color='green', width=3),
    marker=dict(size=8),
    hovertemplate='%{x}<br>Упоминаний: %{y}<extra></extra>'
))

# Настраиваем оформление графика
fig.update_layout(
    title="Временной тренд упоминаний проблем (если доступны даты)",
    xaxis_title="Месяц",
    yaxis_title="Количество упоминаний",
    legend_title="Темы проблем",
    template="plotly_white",
    hovermode="x unified",
    font=dict(family="Arial, sans-serif", size=14),
    margin=dict(l=60, r=40, t=80, b=60),
    xaxis=dict(tickangle=-45, tickmode='array', tickvals=df["Месяц_стр"]),
    yaxis=dict(rangemode='tozero'),
)

# Добавляем интерактивные возможности:
# - Наведение показывает значения всех тем за месяц
# - Зум и панорамирование по оси X и Y включены по умолчанию в plotly

# --- Сохранение визуализации ---

output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

png_path = os.path.join(output_dir, "viz_Временной тренд упоминаний проблем (если доступны даты).png")
html_path = os.path.join(output_dir, "viz_Временной тренд упоминаний проблем (если доступны даты).html")

# Сохраняем статичное изображение с помощью matplotlib через plotly (через kaleido)
# Для этого используем fig.write_image, требует установленный kaleido
try:
    fig.write_image(png_path, scale=2)
except Exception as e:
    print(f"Не удалось сохранить PNG изображение: {e}")

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,          # Полная HTML страница
    config={"displayModeBar": True, "responsive": True}  # Панель инструментов и адаптивность
)

print(f"Визуализация сохранена:\n - PNG: {png_path}\n - HTML: {html_path}")