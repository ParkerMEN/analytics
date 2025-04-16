import matplotlib.pyplot as plt
import numpy as np

# Данные
problems = ['Натяжка холста', 'Упаковка/Доставка', 'Качество материала', 'Дефекты холста', 'Возврат товара']
counts = [34, 28, 22, 20, 10]

# Столбчатая диаграмма
plt.figure(figsize=(8, 6))
plt.bar(problems, counts, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0'])
plt.xlabel('Типы проблем')
plt.ylabel('Количество отзывов')
plt.title('Распределение проблем по отзывам')
plt.xticks(rotation=45, ha='right')