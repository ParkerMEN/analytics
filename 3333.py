import matplotlib.pyplot as plt

labels = ['1 звезда', '2 звезды', '3 звезды', '4 звезды', '5 звезд']
sizes = [9, 6, 17, 0, 62]
colors = ['#ff4d4d', '#ff944d', '#ffe066', '#a3d977', '#4dff88']
explode = (0, 0, 0, 0, 0.1)

fig, ax = plt.subplots(figsize=(10, 6))
wedges, texts, autotexts = ax.pie(
    sizes,
    labels=labels,
    autopct='%1.1f%%',
    colors=colors,
    explode=explode,
    startangle=140,
    textprops={'fontsize': 12}
)
ax.axis('equal')
ax.set_title('Распределение отзывов по рейтингу', fontsize=16)

# Добавляем текстовую интерпретацию под графиком
description = (
    "65.9% пользователей поставили 5 звёзд — подавляющее большинство положительных отзывов, "
    "формирующее сильный визуальный срез.\n"
    "Отсутствие 4-звёздочных отзывов — потенциальный индикатор бинарного восприятия качества (или отлично, или плохо).\n"
    "Рейтинги 1–3 звезды составляют около 34%, что сигнализирует о наличии значимой доли критических мнений."
)

# Добавим подпись как текстовую аннотацию внизу графика
plt.figtext(0.5, -0.1, description, wrap=True, horizontalalignment='center', fontsize=11)

plt.tight_layout()
plt.subplots_adjust(bottom=0.3)  # Делаем место для текста
plt.show()
