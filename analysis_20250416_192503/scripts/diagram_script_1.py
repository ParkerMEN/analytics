import matplotlib.pyplot as plt
import numpy as np

# Данные
ratings = [25, 20, 11, 5, 33]
labels = ['1/5', '2/5', '3/5', '4/5', '5/5']

# Круговая диаграмма
plt.figure(figsize=(6, 6))
plt.pie(ratings, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0'])
plt.title('Распределение рейтингов отзывов')
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.