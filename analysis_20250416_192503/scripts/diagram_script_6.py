import matplotlib.pyplot as plt
import numpy as np

# Данные
categories = ['Жалобы на завышенную цену', 'Удовлетворены соотношением', 'Нет упоминаний']
counts = [12, 20, 62]
colors = ['#ff9999', '#66b3ff', '#99ff99']

# Круговая диаграмма с отверстием (Donut Chart)
plt.figure(figsize=(8, 6))
plt.pie(counts, labels=categories, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'black'})
centre_circle = plt.Circle((0,0),0.70,fc='white')
fig = plt.gcf()
fig.gca().add_artist(centre_circle)
plt.title('Соотношение цены и качества по отзывам')
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.