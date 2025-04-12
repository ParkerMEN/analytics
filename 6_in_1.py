import matplotlib.pyplot as plt

fig, axs = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Итоговая визуализация ключевых метрик по 94 отзывам', fontsize=18)

# Цвета
colors_pos_neg = ['#4dff88', '#ff6666', '#ffe066']
colors_problems = ['#d9d9d9', '#ff6666']
colors_photos = ['#66b3ff', '#d9d9d9']
colors_returns = ['#ffcc99', '#b3ffb3']

# График 1: Рейтинги
labels1 = ['Положительные (5/5)', 'Негативные (1/5, 2/5)', 'Нейтральные (3/5)']
sizes1 = [62, 15, 17]
axs[0, 0].pie(sizes1, labels=labels1, autopct='%1.1f%%', startangle=140, colors=colors_pos_neg,
              explode=(0.1, 0, 0), textprops={'fontsize': 9})
axs[0, 0].set_title('Распределение рейтингов')
axs[0, 0].text(0, -1.3,
               '65.9% отзывов — положительные, только 16% — негативные.\nОтражает общую лояльность клиентов.',
               ha='center', fontsize=9)

# График 2: Упоминание проблем
labels2 = ['Без проблем', 'Упоминают проблемы']
sizes2 = [70, 24]
axs[0, 1].pie(sizes2, labels=labels2, autopct='%1.1f%%', startangle=140, colors=colors_problems,
              explode=(0.05, 0), textprops={'fontsize': 9})
axs[0, 1].set_title('Упоминание проблем')
axs[0, 1].text(0, -1.3,
               'Три четверти отзывов не содержат жалоб — потенциальный индикатор стабильного качества.',
               ha='center', fontsize=9)

# График 3: Проблемы с грунтовкой
labels3 = ['Проблемы с грунтовкой', 'Нормальное качество', 'Нет упоминаний']
sizes3 = [17, 7, 70]
axs[0, 2].pie(sizes3, labels=labels3, autopct='%1.1f%%', startangle=140,
              colors=['#ff9999', '#c2f0c2', '#d9d9d9'], explode=(0.1, 0, 0), textprops={'fontsize': 9})
axs[0, 2].set_title('Качество грунтовки')
axs[0, 2].text(0, -1.3,
               'Проблемы с грунтовкой — 18.1%. Большинство не упоминают —\nвозможно, не замечают или довольны качеством.',
               ha='center', fontsize=9)

# График 4: Наличие дефектов
labels4 = ['С дефектами', 'Без дефектов']
sizes4 = [24, 70]
axs[1, 0].pie(sizes4, labels=labels4, autopct='%1.1f%%', startangle=140,
              colors=['#ff6666', '#a3d977'], explode=(0.1, 0), textprops={'fontsize': 9})
axs[1, 0].set_title('Наличие дефектов')
axs[1, 0].text(0, -1.3,
               'Около 25% пользователей сообщили о физических дефектах —\nкритическая зона контроля качества.',
               ha='center', fontsize=9)

# График 5: Фото в отзывах
labels5 = ['С фото', 'Без фото']
sizes5 = [12, 82]
axs[1, 1].pie(sizes5, labels=labels5, autopct='%1.1f%%', startangle=140,
              colors=colors_photos, explode=(0.1, 0), textprops={'fontsize': 9})
axs[1, 1].set_title('Наличие фото в отзывах')
axs[1, 1].text(0, -1.3,
               'Лишь 12.8% отзывов содержат фото —\nесть возможность мотивировать пользователей к визуальной обратной связи.',
               ha='center', fontsize=9)

# График 6: Возврат товара
labels6 = ['Возврат/отказ', 'Без возврата']
sizes6 = [8, 86]
axs[1, 2].pie(sizes6, labels=labels6, autopct='%1.1f%%', startangle=140,
              colors=colors_returns, explode=(0.1, 0), textprops={'fontsize': 9})
axs[1, 2].set_title('Возвраты и отказы')
axs[1, 2].text(0, -1.3,
               'Менее 9% заказов были возвращены — показатель в пределах нормы,\nно требует наблюдения.',
               ha='center', fontsize=9)

plt.tight_layout(rect=[0, 0.05, 1, 0.95])
plt.show()
