import matplotlib.pyplot as plt
import numpy as np

# Данные
categories = ['Дефекты', 'Отсутствие дефектов']
counts = [30, 64]

# Столбчатая диаграмма с накоплением
plt.figure(figsize=(8, 6))
plt.bar(categories, counts, color=['#ff9999', '#66b3ff'])
plt.xlabel('Категории')
plt.ylabel('Количество отзывов')
plt.title('Наличие дефектов по отзывам')
plt.xticks(rotation=45, ha='right')