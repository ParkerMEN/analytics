import matplotlib.pyplot as plt
import numpy as np

# Данные
categories = ['Положительное', 'Негативное', 'Нейтральное']
counts = [33, 45, 16]

# Площадная диаграмма
plt.figure(figsize=(8, 6))
plt.fill_between(categories, counts, color="#66b3ff", alpha=0.5)
plt.plot(categories, counts, marker='o', color='b')
plt.xlabel('Общее впечатление')
plt.ylabel('Количество отзывов')
plt.title('Общее впечатление от продукта по отзывам')
plt.grid(True)