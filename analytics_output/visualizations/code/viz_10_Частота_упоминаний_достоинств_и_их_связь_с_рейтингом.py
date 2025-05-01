import os
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# --- Часть 1: Подготовка данных ---

# Данные по достоинствам и их упоминаниям (в процентах)
dostoinstva = ["Работоспособность", "Легкость", "Быстрая сборка"]
# Частота упоминаний достоинств (в процентах)
mentions_pct = [44, 26, 16]
# Процент 5-звездочных отзывов среди упоминаний достоинств (только для "Работоспособность" известен)
five_star_pct = [90, None, None]

# Проверка на наличие данных
if not dostoinstva or not mentions_pct or len(dostoinstva) != len(mentions_pct):
    raise ValueError("Данные о достоинствах и упоминаниях отсутствуют или некорректны.")

# Создаем абсолютные значения упоминаний для наглядности (например, из 360 отзывов)
total_reviews = 360
mentions_abs = [round(total_reviews * (pct / 100)) for pct in mentions_pct]

# --- Часть 2: Создание интерактивной визуализации с plotly ---

# Создаем горизонтальную столбчатую диаграмму
fig = go.Figure()

# Добавляем столбец с количеством упоминаний достоинств
fig.add_trace(go.Bar(
    y=dostoinstva,
    x=mentions_abs,
    orientation='h',
    name='Количество упоминаний',
    text=[f"{pct}%" for pct in mentions_pct],
    textposition='auto',
    marker_color='steelblue',
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Упоминаний: %{x} из 360<br>"
        "Доля упоминаний: %{text}<br>"
        "%5-звездочных (если известно): %{customdata}%<extra></extra>"
    ),
    customdata=[str(five_star_pct[i]) if five_star_pct[i] is not None else "нет данных" for i in range(len(dostoinstva))]
))

# Добавляем дополнительный слой с процентом 5-звездочных для "Работоспособность"
# Для наглядности можно добавить отдельные аннотации
for i, val in enumerate(five_star_pct):
    if val is not None:
        fig.add_annotation(
            x=mentions_abs[i] + 10,
            y=dostoinstva[i],
            text=f"90% 5-звездочных",
            showarrow=False,
            font=dict(color="darkgreen", size=12),
            bgcolor="rgba(0,255,0,0.1)",
            bordercolor="darkgreen",
            borderwidth=1,
            borderpad=4,
            yshift=0
        )

# Настройка макета графика
fig.update_layout(
    title="Частота упоминаний достоинств и их связь с рейтингом",
    xaxis_title="Количество упоминаний",
    yaxis_title="Достоинства",
    yaxis=dict(autorange="reversed"),  # Чтобы первый элемент был сверху
    bargap=0.5,
    template="plotly_white",
    hoverlabel=dict(font_size=14),
    margin=dict(l=120, r=40, t=80, b=60),
    legend=dict(title="Легенда", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Добавляем интерактивные элементы:
# - Наведение показывает подробности
# - Панель инструментов по умолчанию с зумом, панорамой и сохранением

# --- Сохранение визуализации ---

# Создаем папку для сохранения, если не существует
output_dir = "analytics_output/visualizations"
os.makedirs(output_dir, exist_ok=True)

# Путь для PNG (статическая версия)
png_path = os.path.join(output_dir, "viz_Частота упоминаний достоинств и их связь с рейтингом.png")
# Путь для HTML (интерактивная версия)
html_path = os.path.join(output_dir, "viz_Частота упоминаний достоинств и их связь с рейтингом.html")

# Сохраняем PNG через matplotlib (Plotly напрямую в PNG требует kaleido или orca)
# Для этого создадим аналогичный график matplotlib

fig_mpl, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.barh(dostoinstva, mentions_abs, color='steelblue')
ax.set_xlabel("Количество упоминаний")
ax.set_title("Частота упоминаний достоинств и их связь с рейтингом")
ax.invert_yaxis()  # Чтобы первый элемент был сверху
ax.grid(axis='x', linestyle='--', alpha=0.7)

# Добавляем подписи процентов на бары
for bar, pct in zip(bars, mentions_pct):
    width = bar.get_width()
    ax.text(width + total_reviews*0.01, bar.get_y() + bar.get_height()/2,
            f"{pct}%", va='center', fontsize=10, color='black')

# Добавляем аннотацию для "Работоспособность" 5-звездочных
ax.annotate("90% 5-звездочных",
            xy=(mentions_abs[0], 0), xycoords='data',
            xytext=(mentions_abs[0] + total_reviews*0.05, -0.3), textcoords='data',
            arrowprops=dict(arrowstyle="->", color='darkgreen'),
            fontsize=10, color='darkgreen')

fig_mpl.tight_layout()
fig_mpl.savefig(png_path, dpi=300)
plt.close(fig_mpl)

# Сохраняем интерактивный HTML с использованием CDN и полной страницы
fig.write_html(
    html_path,
    include_plotlyjs="cdn",  # Используем CDN для plotly.js
    full_html=True,          # Полный HTML-документ
    config={"displayModeBar": True, "responsive": True}  # Панель инструментов и адаптивность
)

# Выводим сообщение об успешном сохранении
print(f"Визуализация успешно сохранена:\n- PNG: {png_path}\n- HTML: {html_path}")