import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# --- Подготовка данных ---

# Создаем директорию для сохранения визуализаций, если не существует
output_dir = 'analytics_output/visualizations'
os.makedirs(output_dir, exist_ok=True)

# Генерируем примерные данные для демонстрации
# Предполагается, что у нас есть данные за 12 месяцев
dates = pd.date_range(start='2023-01-01', periods=12, freq='M')

# Частота упоминаний "быстрой доставки" (в процентах от всех отзывов в месяце)
# Для демонстрации создадим тренд с небольшими колебаниями
np.random.seed(42)
freq_mentions = np.clip(np.linspace(20, 50, 12) + np.random.normal(0, 3, 12), 0, 100)

# Средний рейтинг отзывов с упоминанием доставки (от 1 до 5)
# Учитывая, что 67% упоминаний связаны с рейтингом 5, средний будет около 4.7-4.8
avg_ratings = np.clip(np.linspace(4.6, 4.85, 12) + np.random.normal(0, 0.05, 12), 1, 5)

# Собираем данные в DataFrame
df = pd.DataFrame({
    'Дата': dates,
    'Частота упоминаний быстрой доставки (%)': freq_mentions,
    'Средний рейтинг отзывов с упоминанием доставки': avg_ratings
})

# Проверка на пустые данные
if df.empty:
    raise ValueError("Данные для визуализации отсутствуют.")

# --- Создание визуализации с plotly ---

# Создаем фигуру с двумя осями Y
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Добавляем линию для частоты упоминаний
fig.add_trace(
    go.Scatter(
        x=df['Дата'],
        y=df['Частота упоминаний быстрой доставки (%)'],
        mode='lines+markers',
        name='Частота упоминаний быстрой доставки (%)',
        line=dict(color='royalblue', width=3),
        marker=dict(size=8),
        hovertemplate='%{x|%b %Y}<br>Частота: %{y:.1f}%<extra></extra>'
    ),
    secondary_y=False,
)

# Добавляем линию для среднего рейтинга
fig.add_trace(
    go.Scatter(
        x=df['Дата'],
        y=df['Средний рейтинг отзывов с упоминанием доставки'],
        mode='lines+markers',
        name='Средний рейтинг с упоминанием доставки',
        line=dict(color='firebrick', width=3, dash='dash'),
        marker=dict(size=8),
        hovertemplate='%{x|%b %Y}<br>Средний рейтинг: %{y:.2f}<extra></extra>'
    ),
    secondary_y=True,
)

# Настройка осей
fig.update_xaxes(
    title_text='Дата',
    tickformat='%b %Y',
    showgrid=True,
    zeroline=False,
    rangeslider_visible=True,  # Добавляем слайдер для удобства зума по времени
)

fig.update_yaxes(
    title_text='Частота упоминаний (%)',
    secondary_y=False,
    showgrid=True,
    zeroline=False,
    range=[0, max(60, df['Частота упоминаний быстрой доставки (%)'].max() * 1.1)],
)

fig.update_yaxes(
    title_text='Средний рейтинг',
    secondary_y=True,
    showgrid=False,
    zeroline=False,
    range=[4, 5],  # Диапазон рейтинга с упоминанием доставки (ориентировочно)
)

# Заголовок и легенда
fig.update_layout(
    title={
        'text': "Тренд упоминаний быстрой доставки и их связь с рейтингом",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=22, family="Arial, sans-serif")
    },
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=14)
    ),
    hovermode='x unified',
    template='plotly_white',
    margin=dict(t=100, b=60, l=70, r=70),
    height=600,
)

# Добавляем аннотацию с ключевым инсайтом
fig.add_annotation(
    x=df['Дата'].iloc[-3],
    y=df['Средний рейтинг отзывов с упоминанием доставки'].iloc[-3],
    text="67% упоминаний доставки связаны с рейтингом 5",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor='firebrick',
    ax=0,
    ay=-40,
    font=dict(color='firebrick', size=14, family="Arial, sans-serif"),
    bgcolor='rgba(255,255,255,0.8)',
    bordercolor='firebrick',
    borderwidth=1,
    borderpad=4,
)

# --- Сохранение визуализации ---

# Путь для сохранения PNG и HTML
png_path = os.path.join(output_dir, 'viz_Тренд упоминаний быстрой доставки и их связь с рейтингом.png')
html_path = os.path.join(output_dir, 'viz_Тренд упоминаний быстрой доставки и их связь с рейтингом.html')

# Сохраняем статическую версию PNG через matplotlib (Plotly напрямую не сохраняет PNG без kaleido/orca)
# Для этого отрисуем аналогичный график matplotlib

plt.figure(figsize=(12, 6))
plt.title("Тренд упоминаний быстрой доставки и их связь с рейтингом", fontsize=16, fontweight='bold')

# Линия частоты упоминаний
plt.plot(df['Дата'], df['Частота упоминаний быстрой доставки (%)'], color='royalblue', marker='o', label='Частота упоминаний (%)')

# Линия среднего рейтинга (вторичная ось)
plt.ylabel('Частота упоминаний (%)', color='royalblue')
plt.xlabel('Дата')
plt.grid(True, which='both', axis='y', linestyle='--', alpha=0.5)

ax2 = plt.gca().twinx()
ax2.plot(df['Дата'], df['Средний рейтинг отзывов с упоминанием доставки'], color='firebrick', marker='o', linestyle='--', label='Средний рейтинг')
ax2.set_ylabel('Средний рейтинг', color='firebrick')
ax2.set_ylim(4, 5)

plt.gcf().autofmt_xdate()

# Добавляем легенду
lines, labels = plt.gca().get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
plt.legend(lines + lines2, labels + labels2, loc='upper left')

# Добавляем аннотацию
last_date = df['Дата'].iloc[-3]
last_rating = df['Средний рейтинг отзывов с упоминанием доставки'].iloc[-3]
plt.annotate(
    "67% упоминаний доставки связаны с рейтингом 5",
    xy=(last_date, last_rating),
    xytext=(last_date, last_rating - 0.15),
    arrowprops=dict(facecolor='firebrick', shrink=0.05, width=1.5),
    fontsize=12,
    color='firebrick',
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="firebrick", lw=1)
)

plt.tight_layout()
plt.savefig(png_path, dpi=300)
plt.close()

# Сохраняем интерактивную версию HTML с использованием CDN plotly.js
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,  # Полноценный HTML документ
    config={"displayModeBar": True, "responsive": True}  # Панель инструментов и адаптивность
)

print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")