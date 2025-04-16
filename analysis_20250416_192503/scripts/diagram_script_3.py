import matplotlib.pyplot as plt
import numpy as np

# Данные
categories = ['Проблемы с грунтовкой', 'Нормальное качество грунтовки', 'Нет упоминаний']
counts = [17, 15, 62]

# Линейный график
plt.figure(figsize=(8, 6))
plt.plot(categories, counts, marker='o', linestyle='-', color='b')
plt.xlabel('Категории')
plt.ylabel('Количество отзывов')
plt.title('Восприятие грунтовки по отзывам')
plt.grid(True)