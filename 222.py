import matplotlib.pyplot as plt

# Данные
labels = ['1 звезда', '2 звезды', '3 звезды', '4 звезды', '5 звезд']
sizes = [9, 6, 17, 0, 62]
colors = ['#ff4d4d', '#ff944d', '#ffe066', '#a3d977', '#4dff88']
explode = (0, 0, 0, 0, 0.1)  # Выделим сектор 5/5

# Построение круговой диаграммы
plt.figure(figsize=(8, 6))
plt.pie(
    sizes, 
    labels=labels, 
    autopct='%1.1f%%', 
    colors=colors, 
    explode=explode,
    startangle=140, 
    textprops={'fontsize': 12}
)
plt.title('Распределение отзывов по рейтингу', fontsize=16)
plt.axis('equal')  # Делает диаграмму круглой
plt.tight_layout()
plt.savefig('rating_distribution.png', dpi=300, bbox_inches='tight')
plt.show()
