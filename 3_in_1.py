import matplotlib.pyplot as plt

# Настройка общих параметров
plt.figure(figsize=(15, 5))
colors1 = ['#ff6666', '#a3d977']
colors2 = ['#66b3ff', '#d9d9d9']
colors3 = ['#ffcc99', '#b3ffb3']

# График 1: Дефекты
plt.subplot(1, 3, 1)
labels1 = ['С дефектами', 'Без дефектов']
sizes1 = [24, 70]
explode1 = (0.1, 0)
plt.pie(sizes1, labels=labels1, autopct='%1.1f%%', colors=colors1,
        startangle=140, explode=explode1, textprops={'fontsize': 10})
plt.title('Наличие дефектов')

# График 2: Фото в отзывах
plt.subplot(1, 3, 2)
labels2 = ['С фото', 'Без фото']
sizes2 = [12, 82]
explode2 = (0.1, 0)
plt.pie(sizes2, labels=labels2, autopct='%1.1f%%', colors=colors2,
        startangle=140, explode=explode2, textprops={'fontsize': 10})
plt.title('Отзывы с фотографиями')

# График 3: Отказ от товара
plt.subplot(1, 3, 3)
labels3 = ['Отказ/возврат', 'Без отказа']
sizes3 = [8, 86]
explode3 = (0.1, 0)
plt.pie(sizes3, labels=labels3, autopct='%1.1f%%', colors=colors3,
        startangle=140, explode=explode3, textprops={'fontsize': 10})
plt.title('Возвраты и отказы')

plt.tight_layout()
plt.show()
