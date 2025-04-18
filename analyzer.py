"""
Модуль для первичной обработки и подготовки данных отзывов.
Отвечает за загрузку JSON-файлов с отзывами, извлечение значимых данных,
форматирование их для последующего анализа с помощью OpenAI
и сохранение подготовленных данных в новые файлы.
"""
import json
import sys
import os
from datetime import datetime

def load_reviews_from_file(filename):
    """
    Загружает отзывы из JSON-файла
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Ошибка при загрузке отзывов из файла {filename}: {e}")
        return None

def extract_reviews_data(reviews_data):
    """
    Извлекает ключевую информацию из отзывов
    """
    if not reviews_data or 'feedbacks' not in reviews_data:
        print("Нет данных для анализа или неверный формат данных")
        return []

    processed_reviews = []
    feedbacks = reviews_data.get('feedbacks', [])
    
    for feedback in feedbacks:
        # Извлекаем основные поля отзыва
        text = feedback.get('text', '')
        pros = feedback.get('pros', '')
        cons = feedback.get('cons', '')
        
        # Объединяем текст, достоинства и недостатки для полноты отзыва
        full_text = text
        if pros:
            full_text = f"{full_text}\nДостоинства: {pros}"
        if cons:
            full_text = f"{full_text}\nНедостатки: {cons}"
        
        # Определяем рейтинг (оценку)
        rating = feedback.get('productValuation')
        
        # Извлекаем дату создания и форматируем только год-месяц-день
        create_date = None
        if 'createdDate' in feedback:
            try:
                date_str = feedback.get('createdDate')
                # Извлекаем только часть с датой (без времени)
                if 'T' in date_str:
                    create_date = date_str.split('T')[0]
            except:
                pass
        
        # Определяем наличие фото и видео
        has_photos = bool(feedback.get('photo', [])) or bool(feedback.get('photos', []))
        has_videos = bool(feedback.get('video', [])) or bool(feedback.get('videos', []))
        
        # Добавляем обработанный отзыв
        processed_reviews.append({
            'text': full_text.strip(),
            'rating': rating,
            'create_date': create_date,
            'has_photos': has_photos,
            'has_videos': has_videos
        })
    
    return processed_reviews

def prepare_for_openai(processed_reviews, max_reviews=400):
    """
    Подготавливает данные отзывов для передачи в OpenAI API
    Ограничивает количество отзывов, чтобы не превышать лимиты API
    """
    # Ограничиваем количество отзывов
    limited_reviews = processed_reviews[:max_reviews]
    
    # Форматируем отзывы для анализа
    formatted_reviews = []
    for i, review in enumerate(limited_reviews):
        review_text = review['text'].strip()
        
        # Пропускаем пустые отзывы
        if not review_text:
            continue
            
        # Создаем форматированный отзыв
        review_lines = []
        review_lines.append(f"Отзыв #{i+1}")
        review_lines.append(f"Рейтинг: {review['rating'] if review['rating'] is not None else 'Не указан'}/5")
        
        if review['create_date']:
            review_lines.append(f"Дата: {review['create_date']}")
        
        # Добавляем информацию о наличии фото/видео только если они есть
        if review['has_photos']:
            review_lines.append("Есть фото")
        if review['has_videos']:
            review_lines.append("Есть видео")
        
        review_lines.append(f"Текст отзыва: {review_text}")
        review_lines.append("------------------------------")
        
        formatted_reviews.append("\n".join(review_lines))
    
    # Объединяем все в один текст
    all_reviews_text = "\n".join(formatted_reviews)
    
    return all_reviews_text

def save_prepared_data(prepared_data, original_filename):
    """
    Сохраняет подготовленные данные в новый файл для передачи в OpenAI
    """
    # Создаем имя нового файла на основе оригинального
    base_name = os.path.splitext(original_filename)[0]
    new_filename = f"{base_name}_prepared_for_ai.txt"
    
    try:
        with open(new_filename, 'w', encoding='utf-8') as file:
            file.write(prepared_data)
        print(f"Подготовленные данные сохранены в файл {new_filename}")
        return new_filename
    except Exception as e:
        print(f"Ошибка при сохранении подготовленных данных: {e}")
        return None

def create_openai_prompt(prepared_data):
    """
    Создает промпт для OpenAI на основе подготовленных данных
    """
    prompt = (
        f"Проанализируй следующие отзывы покупателей о товаре и предоставь информацию:\n\n"
        f"1. Общее впечатление покупателей о товаре\n"
        f"2. Основные достоинства товара, упоминаемые в отзывах\n"
        f"3. Основные недостатки товара, упоминаемые в отзывах\n"
        f"4. Соотношение положительных и отрицательных отзывов\n"
        f"5. Рекомендации для улучшения товара или обслуживания\n\n"
        f"Отзывы:\n\n{prepared_data}"
    )
    
    return prompt

def extract_product_info(filename, reviews_data):
    """
    Извлекает информацию о товаре из имени файла и данных отзывов
    """
    # Получаем артикул из имени файла
    article = None
    if filename.startswith("reviews_") and filename.endswith(".json"):
        article = filename[8:-5]  # Обрезаем "reviews_" и ".json"
    
    # Получаем количество отзывов
    reviews_count = 0
    if reviews_data:
        reviews_count = reviews_data.get('feedbackCount', 0)
        if reviews_count == 0 and 'feedbacks' in reviews_data:
            reviews_count = len(reviews_data.get('feedbacks', []))
    
    return {
        'article': article,
        'reviews_count': reviews_count
    }

def main():
    # Проверяем наличие аргумента с именем файла
    if len(sys.argv) < 2:
        print("Пожалуйста, укажите имя файла с отзывами в качестве аргумента")
        print("Пример: python analyzer.py reviews_12345678.json")
        return
    
    # Получаем имя файла из аргументов командной строки
    filename = sys.argv[1]
    print(f"Анализ файла с отзывами: {filename}")
    
    # Загружаем отзывы из файла
    reviews_data = load_reviews_from_file(filename)
    if not reviews_data:
        return
    
    # Извлекаем информацию о товаре
    product_info = extract_product_info(filename, reviews_data)
    print(f"Информация о товаре: Артикул {product_info['article']}, {product_info['reviews_count']} отзывов")
    
    # Обрабатываем отзывы
    processed_reviews = extract_reviews_data(reviews_data)
    print(f"Обработано отзывов: {len(processed_reviews)}")
    
    # Подготавливаем данные для OpenAI
    prepared_data = prepare_for_openai(processed_reviews)
    
    # Сохраняем подготовленные данные
    prepared_file = save_prepared_data(prepared_data, filename)
    
    # Создаем промпт для OpenAI
    if prepared_file:
        prompt = create_openai_prompt(prepared_data)
        prompt_file = f"{os.path.splitext(filename)[0]}_openai_prompt.txt"
        with open(prompt_file, 'w', encoding='utf-8') as file:
            file.write(prompt)
        print(f"Промпт для OpenAI сохранен в файл {prompt_file}")
        print("Готово! Теперь вы можете использовать подготовленные данные для анализа через API OpenAI.")

if __name__ == "__main__":
    main()