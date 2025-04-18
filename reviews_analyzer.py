"""
Основной модуль для комплексного анализа отзывов через OpenAI API.
Отвечает за разбиение отзывов на партии, последовательную отправку их в GPT-4o,
получение аналитических выводов, формирование итогового отчета
и организацию всего процесса анализа от начала до конца.
"""
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

def split_reviews_into_batches(file_path, max_tokens=2000, min_partitions=5, max_partitions=30):
    """
    Разбивает файл с отзывами на части, учитывая ограничения модели GPT-4.1-mini.
    
    Args:
        file_path: Путь к файлу с отзывами
        max_tokens: Максимальное количество токенов в одной партии (по умолчанию: 2000)
        min_partitions: Минимальное количество партий (по умолчанию: 5)
        max_partitions: Максимальное количество партий (по умолчанию: 30)
    
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
        
        # Параметры модели GPT-4.1-mini
        max_context = 1047576  # Правильный размер контекстного окна для gpt-4.1-mini
        model_output_tokens = 32768  # Правильный максимальный размер ответа для gpt-4.1-mini
        
        # Расчет оптимального количества партий для обработки до 1000 отзывов
        # При работе с большим контекстным окном можем делать партии больше
        
        # Безопасное ограничение для одной партии (с учетом истории)
        system_prompt_estimate = 1500  # Увеличим для возможных сложных промптов
        history_per_batch = 1000       # Увеличим для учета истории
        
        # Вычисляем, сколько отзывов можем поместить в одну партию
        # Для GPT-4.1-mini с большим контекстом можем сделать партии больше
        if total_reviews < 200:
            safe_batch_limit = min(max_tokens, 5000)  # Значительно увеличиваем
        elif total_reviews < 500:
            safe_batch_limit = min(max_tokens, 4000)  # Увеличиваем для среднего объема
        else:
            safe_batch_limit = min(max_tokens, 3000)  # Увеличиваем для большого объема
            
        # Расчет количества партий с учетом ограничений, но оптимизируем для меньшего числа запросов
        # Для 1000 отзывов со средним размером 50 токенов = ~50000 токенов общего объема
        # При контексте в 1M можно значительно уменьшить количество партий
        
        # С новым контекстным окном можем сделать меньше партий
        calculated_partitions = max(min_partitions, (total_tokens + safe_batch_limit - 1) // safe_batch_limit)
        
        # Применяем ограничения на количество партий
        num_partitions = min(max_partitions, max(min_partitions, calculated_partitions))
        
        # Корректируем количество партий в зависимости от объема данных
        # Но с большим контекстным окном нам не нужно так сильно дробить данные
        if total_reviews > 800:
            num_partitions = max(num_partitions, 10)  # Было 15, уменьшаем
        elif total_reviews > 500:
            num_partitions = max(num_partitions, 7)   # Было 10, уменьшаем
        
        # Дополнительный фактор: учитываем максимально допустимый размер запроса для предотвращения ошибок
        max_request_tokens = 900000  # Максимальный безопасный размер запроса (<90% контекста)
        
        # Остальной код функции остаётся без изменений
        target_batch_size = total_tokens // num_partitions
        
        batches = []
        current_batch = []
        current_tokens = 0
        
        for i, review in enumerate(reviews):
            review_tokens = reviews_tokens[i]
            
            # Проверяем условия для создания новой партии
            if current_batch and (
                (current_tokens + review_tokens > safe_batch_limit) or
                (current_tokens >= target_batch_size and len(batches) < num_partitions - 1)
            ):
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            
            # Особый случай: если отдельный отзыв превышает лимит
            if review_tokens > safe_batch_limit:
                print(f"Предупреждение: Отзыв #{i+1} слишком большой ({review_tokens} > {safe_batch_limit})")
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
                
                # Для очень больших отзывов можно добавить логику разделения, пока просто добавляем
                batches.append([review])
                continue
            
            current_batch.append(review)
            current_tokens += review_tokens
        
        # Добавляем последнюю партию
        if current_batch:
            batches.append(current_batch)
        
        # Если получилось слишком мало партий, перераспределяем отзывы
        if len(batches) < min_partitions and len(batches) > 1:
            print(f"Увеличиваем количество партий с {len(batches)} до {min_partitions}...")
            all_reviews = [review for batch in batches for review in batch]
            batches = []
            reviews_per_batch = len(all_reviews) // min_partitions
            extra = len(all_reviews) % min_partitions
            
            start = 0
            for i in range(min_partitions):
                batch_size = reviews_per_batch + (1 if i < extra else 0)
                end = min(start + batch_size, len(all_reviews))
                batches.append(all_reviews[start:end])
                start = end
            
            print(f"Отзывы перераспределены в {len(batches)} партий")
        
        # Если получилось слишком много партий, объединяем некоторые
        if len(batches) > max_partitions:
            print(f"Уменьшаем количество партий с {len(batches)} до {max_partitions}...")
            all_reviews = [review for batch in batches for review in batch]
            batches = []
            reviews_per_batch = len(all_reviews) // max_partitions
            extra = len(all_reviews) % max_partitions
            
            start = 0
            for i in range(max_partitions):
                batch_size = reviews_per_batch + (1 if i < extra else 0)
                end = min(start + batch_size, len(all_reviews))
                batches.append(all_reviews[start:end])
                start = end
            
            print(f"Отзывы перераспределены в {len(batches)} партий (уменьшено)")
        
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

def send_to_gpt(client, messages, model="gpt-4.1-mini"):
    """
    Отправляет сообщения в GPT API и возвращает ответ.
    
    Args:
        client: Клиент OpenAI
        messages: Список сообщений для отправки
        model: Название модели (по умолчанию: gpt-4.1-mini)
    
    Returns:
        str: Ответ от модели или None в случае ошибки
    """
    # Импортируем настройки из модуля gpt_config
    from gpt_config import DEFAULT_API_PARAMS
    
    max_retries = 5  # Увеличено количество попыток
    base_retry_delay = 5
    
    # Оцениваем размер запроса для логирования
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    approx_tokens = total_chars // 4
    
    # Оценка размера запроса и остаточного контекста
    # Актуальные параметры для GPT-4.1-mini
    max_context = 1047576  # Правильный размер контекстного окна для gpt-4.1-mini
    max_output = 32768     # Максимальный размер ответа для gpt-4.1-mini
    
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
    
    # Адаптивное управление повторными попытками
    for retry in range(max_retries):
        try:
            # Используем параметры по умолчанию из gpt_config
            params = DEFAULT_API_PARAMS.copy()
            params["model"] = model
            params["messages"] = messages
            
            # Ограничиваем максимальный размер ответа исходя из оставшегося контекста
            params["max_tokens"] = min(params.get("max_tokens", max_output), remaining_context)
            
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            print(f"Ошибка при обращении к API (попытка {retry+1}/{max_retries}): {e}")
            
            # Расширенная обработка ошибок для разных случаев
            if "maximum context length" in error_msg:
                print("Превышен максимальный размер контекста. Необходимо уменьшить размер партий.")
                return None
            
            elif "too many tokens" in error_msg.lower():
                print("Запрос содержит слишком много токенов. Попробуйте уменьшить размер партии.")
                return None
                
            elif "rate_limit_exceeded" in error_msg and "tokens per min" in error_msg:
                # Специальная обработка для ошибки TPM (tokens per minute)
                wait_time = 65 * (retry + 1)  # Увеличиваем время ожидания с каждой попыткой
                print(f"Превышен лимит токенов в минуту (TPM). Ожидаем {wait_time} секунд...")
                time.sleep(wait_time)
                continue  # Продолжаем после ожидания без увеличения retry_delay
                
            elif "Request too large" in error_msg:
                print("Запрос слишком большой для обработки моделью. Нужно уменьшить размер партий.")
                return None
            
            # Для других ошибок используем экспоненциальное увеличение задержки
            if retry < max_retries - 1:
                retry_delay = base_retry_delay * (2 ** retry)  # Экспоненциальное увеличение
                print(f"Повторная попытка через {retry_delay} секунд...")
                time.sleep(retry_delay)
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
        
        # Если обработали много партий, может накопиться большая история
        # После некоторого количества партий, сжимаем историю
        if len(batches) > 5:  # После обработки 5+ партий
            # Запрашиваем промежуточный итог
            print("Оптимизация контекста диалога...")
            summary_request = "Пожалуйста, дай краткий итог по всем прочитанным отзывам для оптимизации контекста."
            conversation.append({"role": "user", "content": summary_request})
            
            summary = send_to_gpt(client, conversation, model)
            if summary:
                # Создаем новый, более компактный контекст с итогом
                conversation = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Вот итоги предыдущего анализа отзывов:\n\n{summary}"},
                    {"role": "assistant", "content": "Я принял к сведению итоги предыдущего анализа и учту их в дальнейшей работе."}
                ]
                print("Контекст диалога успешно оптимизирован.")
    
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
    
    parser = argparse.ArgumentParser(description="Анализ отзывов с помощью GPT-4.1-mini")
    parser.add_argument("reviews_file", nargs='?', default="reviews_10973496_prepared_for_ai.txt", 
                        help="Путь к файлу с подготовленными отзывами")
    parser.add_argument("-p", "--prompt", default="my_prompt.txt", 
                        help="Путь к файлу с системным промптом")
    parser.add_argument("-t", "--task", default="task_file.txt", 
                        help="Путь к файлу с заданием для финального анализа")
    parser.add_argument("-m", "--max-tokens", type=int, default=4000,  # Увеличено с 2000 до 4000
                        help="Максимальное количество токенов в одной партии (по умолчанию: 4000)")
    parser.add_argument("--min-partitions", type=int, default=3,       # Уменьшено с 5 до 3
                        help="Минимальное количество партий (по умолчанию: 3)")
    parser.add_argument("--max-partitions", type=int, default=20,      # Оптимизировано с 50 до 20
                        help="Максимальное количество партий (по умолчанию: 20)")
    parser.add_argument("--model", default="gpt-4.1-mini",
                        help="Модель GPT для использования (по умолчанию: gpt-4.1-mini)")
    
    args = parser.parse_args()
    
    # Проверка валидности параметров
    if args.max_partitions < args.min_partitions:
        print(f"Ошибка: max_partitions ({args.max_partitions}) не может быть меньше min_partitions ({args.min_partitions})")
        args.max_partitions = args.min_partitions
        print(f"Установлено max_partitions = {args.min_partitions}")
    
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
    
    # Обновляем глобальные переменные для процесса обработки
    global send_to_gpt
    original_send_to_gpt = send_to_gpt
    
    def custom_send_to_gpt(client, messages, model=None):
        if model is None:
            model = args.model
        return original_send_to_gpt(client, messages, model)
    
    send_to_gpt = custom_send_to_gpt
    
    # Обновляем функцию split_reviews_into_batches с новыми параметрами
    global split_reviews_into_batches
    original_function = split_reviews_into_batches
    
    def custom_split(file_path):
        return original_function(file_path, args.max_tokens, args.min_partitions, args.max_partitions)
    
    split_reviews_into_batches = custom_split
    
    # Запускаем процесс анализа
    print(f"Начало анализа файла отзывов: {reviews_file} с моделью {args.model}")
    result_file = process_reviews(reviews_file, args.prompt, args.task)
    
    if result_file:
        print(f"Анализ успешно завершен! Результаты сохранены в файле: {result_file}")
    else:
        print("Анализ не был завершен из-за ошибок.")

if __name__ == "__main__":
    main()