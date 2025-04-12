import matplotlib.pyplot as plt

# Данные
problems = [
    'Натяжка холста', 
    'Упаковка/Доставка', 
    'Качество материала', 
    'Дефекты холста', 
    'Возврат товара'
]
counts = [28, 22, 20, 12, 9]
colors = ['#ff6666', '#ff9966', '#ffd966', '#a3d977', '#66b3ff']

# Построение столбчатой диаграммы
plt.figure(figsize=(10, 6))
bars = plt.bar(problems, counts, color=colors)

# Добавление подписей над столбцами
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height + 0.8, f'{height}', 
             ha='center', va='bottom', fontsize=11)

plt.title('Частота упоминания типов проблем в отзывах', fontsize=16)
plt.ylabel('Количество отзывов', fontsize=12)
plt.xticks(rotation=20)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
