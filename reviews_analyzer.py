import os
import time
import json
from pathlib import Path
from openai import OpenAI
from datetime import datetime

def load_api_key():
    """Загружает API ключ из файла."""
    try:
        with open("api_key.txt", "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Ошибка загрузки API ключа: {e}")
        return None

def load_prompt(prompt_file):
    """Загружает промпт из файла."""
    try:
        if os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as file:
                return file.read().strip()
        else:
            print(f"Файл с промптом {prompt_file} не найден.")
            return None
    except Exception as e:
        print(f"Ошибка загрузки промпта: {e}")
        return None

def split_reviews_into_batches(file_path, max_tokens=4000):
    """
    Разбивает файл с отзывами на части, учитывая ограничения модели GPT-4o.
    
    Args:
        file_path: Путь к файлу с отзывами
        max_tokens: Максимальное количество токенов в одной партии (по умолчанию: 4000)
    
    Returns:
        Tuple[List[List[str]], int]: Список партий отзывов и общее количество отзывов
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        
        # Разделяем отзывы по разделителю
        reviews = content.split("------------------------------")
        reviews = [review.strip() for review in reviews if review.strip()]
        total_reviews = len(reviews)
        
        if total_reviews == 0:
            print("Файл отзывов пуст или не содержит валидных отзывов.")
            return [], 0
        
        # Расчет токенов для каждого отзыва
        # Для русского текста примерное соотношение: 1 токен ~ 4 символа
        reviews_tokens = [len(review) // 4 for review in reviews]
        total_tokens = sum(reviews_tokens)
        avg_review_tokens = total_tokens // total_reviews
        
        print(f"Средний размер отзыва: ~{avg_review_tokens} токенов")
        print(f"Всего токенов во всех отзывах: ~{total_tokens}")
        
        # Расчет оптимального количества партий
        # Учитываем:
        # 1. Размер системного промпта (~1000 токенов)
        # 2. Историю диалога (~500 токенов на каждую предыдущую партию)
        # 3. Максимальные выходные токены (16,384 для gpt-4o)
        
        # Безопасное ограничение для одной партии (учитывая историю)
        safe_batch_limit = min(max_tokens, 4000)  # Не более 4000 токенов в партии
        
        # Минимальное количество партий
        min_partitions = max(3, (total_tokens + safe_batch_limit - 1) // safe_batch_limit)
        
        # Для качественной аналитики нужно минимум 5-6 партий, если объем большой
        if total_tokens > 10000:
            min_partitions = max(min_partitions, 5)
        
        print(f"Оптимальное количество партий: ~{min_partitions}")
        
        # Формируем партии, стараясь равномерно распределить отзывы
        batches = []
        current_batch = []
        current_tokens = 0
        target_batch_size = total_tokens // min_partitions
        
        for i, review in enumerate(reviews):
            review_tokens = reviews_tokens[i]
            
            # Проверяем условия для создания новой партии:
            # 1. Текущая партия не пуста
            # 2. Добавление отзыва превысит безопасный лимит ИЛИ
            # 3. Текущая партия достигла целевого размера и осталось достаточно отзывов
            if current_batch and (
                (current_tokens + review_tokens > safe_batch_limit) or
                (current_tokens >= target_batch_size and len(batches) < min_partitions - 1)
            ):
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            
            # Особый случай: если отдельный отзыв превышает лимит, его нужно обработать отдельно
            if review_tokens > safe_batch_limit:
                print(f"Предупреждение: Отзыв #{i+1} превышает лимит токенов ({review_tokens} > {safe_batch_limit})")
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
                
                # Добавляем большой отзыв в отдельную партию
                batches.append([review])
                continue
            
            current_batch.append(review)
            current_tokens += review_tokens
        
        # Добавляем последнюю партию, если она не пустая
        if current_batch:
            batches.append(current_batch)
        
        # Выводим детальную информацию о партиях
        batch_info = []
        for i, batch in enumerate(batches):
            batch_tokens = sum(len(r) // 4 for r in batch)
            batch_info.append(f"Партия {i+1}: {len(batch)} отзывов, ~{batch_tokens} токенов")
        
        print("\n".join(batch_info))
        print(f"Создано {len(batches)} партий отзывов из {total_reviews} отзывов")
        
        return batches, total_reviews
    except Exception as e:
        print(f"Ошибка при разбиении отзывов на партии: {e}")
        return [], 0

def send_to_gpt(client, messages, model="gpt-4o"):
    """
    Отправляет сообщения в GPT API и возвращает ответ.
    
    Args:
        client: Клиент OpenAI
        messages: Список сообщений для отправки
        model: Название модели (по умолчанию: gpt-4o)
    
    Returns:
        str: Ответ от модели или None в случае ошибки
    """
    # Импортируем настройки из модуля gpt_config
    from gpt_config import DEFAULT_API_PARAMS
    
    max_retries = 3
    retry_delay = 5
    
    # Оцениваем размер запроса для логирования
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    approx_tokens = total_chars // 4
    
    # Оценка размера запроса и остаточного контекста
    max_context = 128000  # Максимальное контекстное окно для gpt-4o
    max_output = 16384    # Максимальные выходные токены для gpt-4o
    
    # Вычисляем примерный остаток для ответа
    remaining_context = max_context - approx_tokens
    
    print(f"Приблизительный размер запроса: ~{approx_tokens} токенов")
    print(f"Доступно для ответа: ~{remaining_context} токенов")
    
    # Предупреждения о возможных проблемах
    if approx_tokens > max_context * 0.8:
        print("ВНИМАНИЕ: Запрос занимает более 80% контекстного окна модели!")
    elif approx_tokens > max_context * 0.6:
        print("Предупреждение: Запрос занимает более 60% контекстного окна модели.")
    
    # Проверка на возможные проблемы с размером ответа
    if remaining_context < max_output * 0.3:
        print("ВНИМАНИЕ: Оставшегося контекста может не хватить для полноценного ответа!")
    
    for retry in range(max_retries):
        try:
            # Используем параметры по умолчанию из gpt_config
            params = DEFAULT_API_PARAMS.copy()
            params["model"] = model
            params["messages"] = messages
            params["max_tokens"] = min(params["max_tokens"], remaining_context)
            
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            print(f"Ошибка при обращении к API (попытка {retry+1}/{max_retries}): {e}")
            
            # Специальная обработка ошибки превышения контекста
            if "maximum context length" in error_msg:
                print("Превышен максимальный размер контекста. Необходимо уменьшить размер партий.")
                return None
            
            # Обработка ошибок по размеру запроса
            if "too many tokens" in error_msg.lower():
                print("Запрос содержит слишком много токенов. Попробуйте уменьшить размер партии.")
                return None
                
            if retry < max_retries - 1:
                print(f"Повторная попытка через {retry_delay} секунд...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Увеличиваем задержку между попытками
            else:
                print("Исчерпаны все попытки обращения к API.")
                return None

def process_reviews(reviews_file, prompt_file="my_prompt.txt", task_file="task_file.txt"):
    """
    Обрабатывает файл с отзывами, отправляя их партиями в GPT-4o.
    """
    # Импортируем функции из модуля gpt_config
    from gpt_config import create_openai_client, get_system_prompt
    
    # Создаем клиента OpenAI
    client = create_openai_client()
    if not client:
        print("Не удалось создать клиент OpenAI.")
        return None
    
    # Загрузка системного промпта
    system_prompt_original = load_prompt(prompt_file)
    if not system_prompt_original:
        print(f"Не удалось загрузить системный промпт из файла {prompt_file}.")
        return None
    
    # Применяем Transparency Contract к системному промпту
    system_prompt = get_system_prompt(system_prompt_original)
    
    # Разбиение отзывов на партии
    batches, total_reviews = split_reviews_into_batches(reviews_file)
    if not batches:
        print("Не удалось разбить отзывы на партии.")
        return None
    
    print(f"Файл отзывов разбит на {len(batches)} партий. Всего отзывов: {total_reviews}")
    
    # Инициализация диалога с системным промптом (уже с контрактом)
    conversation = [{"role": "system", "content": system_prompt}]
    
    # Отправка партий отзывов
    for i, batch in enumerate(batches):
        batch_number = i + 1
        print(f"Отправка партии {batch_number}/{len(batches)} ({len(batch)} отзывов)...")
        
        # Формируем сообщение с партией отзывов
        batch_message = (
            f"Партия отзывов {batch_number} из {len(batches)}:\n\n" + 
            "\n------------------------------\n".join(batch)
        )
        
        conversation.append({"role": "user", "content": batch_message})
        
        response = send_to_gpt(client, conversation)
        if response:
            print(f"Партия {batch_number} успешно обработана.")
            conversation.append({"role": "assistant", "content": response})
        else:
            print(f"Ошибка при обработке партии {batch_number}. Процесс прерван.")
            return None
    
    # Загружаем финальное задание для анализа
    final_task = load_prompt(task_file)
    
    if not final_task:
        print(f"Не удалось загрузить задание из файла {task_file}, используем стандартное задание.")
        # Стандартное задание, если файл с задачей не найден
        final_task = (
            "Теперь, когда ты ознакомился со всеми отзывами, проведи подробный анализ и предоставь следующую информацию:\n\n"
            "1. Общее впечатление покупателей о товаре\n"
            "2. Распределение оценок (соотношение положительных, нейтральных и отрицательных отзывов)\n"
            "3. Основные достоинства товара, которые чаще всего упоминаются\n"
            "4. Основные недостатки и проблемы, о которых сообщают покупатели\n"
            "5. Качество обслуживания и доставки, если об этом есть информация\n"
            "6. Соотношение цены и качества по мнению покупателей\n"
            "7. Наличие частых жалоб на конкретные аспекты товара\n"
            "8. Предложения по улучшению товара или обслуживания на основе отзывов\n\n"
            "Предоставь подробный и структурированный анализ с конкретными выводами и рекомендациями."
        )
    
    print("Отправка задания для финального анализа...")
    conversation.append({"role": "user", "content": final_task})
    
    # Получаем финальный анализ
    final_analysis = send_to_gpt(client, conversation)
    
    if not final_analysis:
        print("Не удалось получить финальный анализ отзывов.")
        return None
    
    # Сохраняем начальный анализ в conversation для последующих улучшений
    conversation.append({"role": "assistant", "content": final_analysis})
    
    # Запрашиваем самооценку
    print("Запрашиваем самооценку аналитики...")
    conversation.append({"role": "user", "content": "**Оцени свой последний ответ по 10-балльной шкале.**"})
    
    self_assessment = send_to_gpt(client, conversation)
    if self_assessment:
        print("Самооценка получена.")
        conversation.append({"role": "assistant", "content": self_assessment})
    else:
        print("Не удалось получить самооценку.")
    
    # Запрашиваем улучшение аналитики
    print("Запрашиваем улучшение аналитики...")
    conversation.append({"role": "user", "content": "Пожалуйста, улучши свой анализ до 10 из 10. Предоставь самую подробную, точную и полезную аналитику, на которую ты способен. Важно чтобы все данные были верны на 100% Если ты например говоришь, что Анализ рейтингов показывает, что негативные оценки (1/5 и 2/5) составляют почти половину всех отзывов (46.8%), то ты должен быть на 100% уверен, что это истина."})
    
    improved_analysis = send_to_gpt(client, conversation)
    if not improved_analysis:
        print("Не удалось получить улучшенный анализ. Будет использован начальный вариант.")
        improved_analysis = final_analysis
    
    # Сохраняем результат анализа в файл
    output_file = f"{Path(reviews_file).stem}_analytics.txt"
    
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(improved_analysis)
        print(f"Аналитика успешно сохранена в файл: {output_file}")
        
        # Объединяем все PDF-отчеты в один файл после генерации аналитики
        # Получаем артикул из имени файла отзывов
        article = None
        if reviews_file.startswith("reviews_") and reviews_file.endswith(".txt"):
            article = reviews_file[8:-4]  # Обрезаем "reviews_" и ".txt"
        elif reviews_file.startswith("reviews_") and reviews_file.endswith("_prepared_for_ai.txt"):
            article = reviews_file[8:].split("_prepared_for_ai.txt")[0]
        
        if article:
            # Импортируем функцию из pdf_generator.py
            from pdf_generator import merge_pdf_reports
            
            # Получаем имя директории анализа
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = f"analysis_{timestamp}"
            os.makedirs(session_dir, exist_ok=True)
            
            # Создаем объединенный PDF с именем, соответствующим артикулу, в директории анализа
            output_pdf = os.path.join(session_dir, f"report_{article}.pdf")
            merge_result = merge_pdf_reports(output_pdf)
            if merge_result:
                print(f"Создан объединенный PDF-отчет: {output_pdf}")
        
        return output_file
    except Exception as e:
        print(f"Ошибка при сохранении результатов анализа: {e}")
        return None

def main():
    """
    Основная функция для запуска процесса анализа отзывов из командной строки.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Анализ отзывов с помощью GPT-4o")
    parser.add_argument("reviews_file", nargs='?', default="reviews_10973496_prepared_for_ai.txt", 
                        help="Путь к файлу с подготовленными отзывами (по умолчанию: reviews_10973496_prepared_for_ai.txt)")
    parser.add_argument("-p", "--prompt", default="my_prompt.txt", 
                        help="Путь к файлу с системным промптом (по умолчанию: my_prompt.txt)")
    parser.add_argument("-t", "--task", default="task_file.txt", 
                        help="Путь к файлу с заданием для финального анализа (по умолчанию: task_file.txt)")
    parser.add_argument("-m", "--max-tokens", type=int, default=4000,
                        help="Максимальное количество токенов в одной партии (по умолчанию: 4000)")
    parser.add_argument("--min-partitions", type=int, default=5,
                        help="Минимальное количество партий (по умолчанию: 5)")
    
    args = parser.parse_args()
    
    # Если файл не указан явно, используем default
    reviews_file = args.reviews_file
    
    # Проверяем наличие файлов
    if not os.path.exists(reviews_file):
        print(f"Ошибка: Файл с отзывами не найден: {reviews_file}")
        return
    
    if not os.path.exists(args.prompt):
        print(f"Внимание: Файл с системным промптом не найден: {args.prompt}")
        print("Будет использован стандартный промпт.")
    
    if not os.path.exists(args.task):
        print(f"Внимание: Файл с финальным заданием не найден: {args.task}")
        print("Будет использовано стандартное задание для анализа.")
    
    # Обновляем функцию split_reviews_into_batches с новым значением max_tokens
    global split_reviews_into_batches
    original_function = split_reviews_into_batches
    
    # Создаем обертку для функции разбиения с нужными параметрами
    def custom_split(file_path):
        # Изменяем внутреннее поведение функции для учета минимального количества партий
        nonlocal args
        try:
            batches, total = original_function(file_path, args.max_tokens)
            if len(batches) < args.min_partitions and len(batches) > 1 and total > 0:
                print(f"Увеличиваем количество партий до {args.min_partitions}...")
                # Перераспределяем отзывы для достижения минимального количества партий
                all_reviews = [review for batch in batches for review in batch]
                batches = []
                reviews_per_batch = len(all_reviews) // args.min_partitions
                extra = len(all_reviews) % args.min_partitions
                
                start = 0
                for i in range(args.min_partitions):
                    batch_size = reviews_per_batch + (1 if i < extra else 0)
                    end = min(start + batch_size, len(all_reviews))
                    batches.append(all_reviews[start:end])
                    start = end
                
                print(f"Отзывы перераспределены в {len(batches)} партий")
            return batches, total
        except Exception as e:
            print(f"Ошибка при разбиении отзывов: {e}")
            return [], 0
    
    split_reviews_into_batches = custom_split
    
    # Запускаем процесс анализа
    print(f"Начало анализа файла отзывов: {reviews_file}")
    result_file = process_reviews(reviews_file, args.prompt, args.task)
    
    if result_file:
        print(f"Анализ успешно завершен! Результаты сохранены в файле: {result_file}")
    else:
        print("Анализ не был завершен из-за ошибок.")

if __name__ == "__main__":
    main()