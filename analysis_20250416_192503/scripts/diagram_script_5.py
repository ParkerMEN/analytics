import matplotlib.pyplot as plt
import numpy as np

# Данные
categories = ['Недостаточная упаковка', 'Хорошая упаковка', 'Нет упоминаний']
counts = [28, 15, 51]

# Горизонтальная столбчатая диаграмма
plt.figure(figsize=(8, 6))
plt.barh(categories, counts, color=['#ff9999', '#66b3ff', '#99ff99'])
plt.xlabel('Количество отзывов')
plt.title('Проблемы с упаковкой и доставкой')
plt.gca().invert_yaxis()  # Инвертировать ось Y для лучшей читаемости