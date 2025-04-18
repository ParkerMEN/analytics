"""
Модуль для взаимодействия с API OpenAI (GPT-4o).
Отвечает за отправку запросов к API, обработку ответов,
генерацию PDF-отчетов на основе анализа отзывов 
и создание единого структурированного отчета с диаграммами.
"""
import os
import re
from datetime import datetime
from openai import OpenAI
import subprocess
import time


def load_message_from_file(filename):
    """Загружает сообщение из файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read().strip()  # Убираем лишние пробелы и переносы строк
    except Exception as e:
        print(f"Ошибка при загрузке файла {filename}: {e}")
        return None

def save_response_text(response_text, step):
    """Сохраняет текстовый ответ в файл"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response_dir = "responses"
    os.makedirs(response_dir, exist_ok=True)
    text_filename = os.path.join(response_dir, f"response_step{step}_{timestamp}.txt")
    with open(text_filename, 'w', encoding='utf-8') as file:
        file.write(response_text)
    print(f"Текстовый ответ сохранен в {text_filename}")
    return text_filename

def chat_with_gpt(messages_files):
    """
    Отправляет сообщения в ChatGPT через API и сохраняет ответы.
    """
    # Импортируем новый модуль конфигурации
    from gpt_config import create_openai_client, get_system_prompt, DEFAULT_API_PARAMS
    
    # Создаем клиент OpenAI
    client = create_openai_client()
    if not client:
        return False, None
    
    conversation_history = []
    response_step3_file = None
    
    # Последовательно отправляем сообщения
    for i, message_file in enumerate(messages_files, 1):
        user_content = load_message_from_file(message_file)
        if not user_content:
            print(f"Файл {message_file} пуст или не найден.")
            continue
            
        # Для первого сообщения (системного промпта) применяем Transparency Contract
        if i == 1:
            user_content = get_system_prompt(user_content)
            conversation_history.append({"role": "system", "content": user_content})
        else:
            # Добавляем обычное сообщение пользователя в историю
            conversation_history.append({"role": "user", "content": user_content})
            
        print(f"Отправка сообщения {i}...")

        try:
            # Используем параметры по умолчанию из модуля конфигурации
            params = DEFAULT_API_PARAMS.copy()
            params["model"] = "gpt-4o"
            params["messages"] = conversation_history
            
            # Отправляем запрос к API с использованием параметров
            try:
                response = client.chat.completions.create(**params)
            except Exception as e:
                if "rate_limit_exceeded" in str(e) and "tokens per min" in str(e):
                    print("Превышен лимит токенов в минуту, ожидаем 60 секунд...")
                    time.sleep(60)  # Ждем минуту
                    # Попробовать снова
                    response = client.chat.completions.create(**params)
                else:
                    raise e

            # Получаем текст ответа из структуры ответа
            response_text = response.choices[0].message.content
            
            # Сохраняем ответ в файл
            response_file = save_response_text(response_text, i)
            
            # Запоминаем файл с ответом для шага 3
            if i == 3:
                response_step3_file = response_file

            # Добавляем ответ ассистента в историю
            conversation_history.append({"role": "assistant", "content": response_text})
            print(f"Ответ на сообщение {i} успешно сохранен.")

        except Exception as e:
            print(f"Ошибка при отправке запроса: {e}")
            return False, None

    return True, response_step3_file

def generate_pdf_from_response(response_file, chart_file=None, output_pdf=None):
    """
    Создает PDF из файла ответа и диаграммы.
    """
    try:
        # Проверка существования файла pdf_generator.py
        if not os.path.exists('pdf_generator.py'):
            print("ОШИБКА: Файл pdf_generator.py не найден.")
            return False
        
        # Импортируем функцию из pdf_generator.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("pdf_generator", "pdf_generator.py")
        pdf_generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdf_generator)
        
        # Определяем имя выходного PDF-файла, если не указано
        if not output_pdf:
            output_dir = "pdf_reports"
            os.makedirs(output_dir, exist_ok=True)
            output_pdf = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(response_file))[0]}.pdf")
        
        # Создаем директорию для выходного файла, если её нет
        output_dir = os.path.dirname(output_pdf)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # Вызываем функцию для создания PDF
        result = False
        if chart_file and os.path.exists(chart_file) and os.path.getsize(chart_file) > 0:
            print(f"Передаем диаграмму в PDF-генератор: {chart_file}")
            # Если есть диаграмма, передаем ее в генератор PDF
            result = pdf_generator.generate_pdf_from_response(response_file, chart_file=chart_file, output_pdf=output_pdf)
        else:
            # Если диаграммы нет, используем стандартный вызов
            result = pdf_generator.generate_pdf_from_response(response_file, output_pdf=output_pdf)
        
        if result:
            print(f"PDF-отчет создан: {output_pdf}")
            return True
        else:
            print(f"Не удалось создать PDF-отчет для файла {response_file}")
            return False
            
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        return False

def split_analytics_sections(analytics_file):
    """Разбивает файл аналитики на отдельные секции по заголовкам ###."""
    try:
        with open(analytics_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Проверяем формат файла и наличие заголовков
        if "### Итоговая аналитика" in text and "1. **" in text:
            # Ищем все основные секции (1., 2., и т.д.)
            section_pattern = r'(\d+\.\s+\*\*[^*]+\*\*)'
            main_sections = re.split(section_pattern, text)
            
            # Если разбиение прошло успешно, формируем секции
            results = []
            
            # Пропускаем вступительный текст до первой секции
            intro_text = main_sections[0].strip()
            
            # Каждый нечетный индекс - это заголовок, каждый четный - тело секции
            for i in range(1, len(main_sections) - 1, 2):
                header = main_sections[i].strip()
                body = main_sections[i + 1].strip()
                section_text = f"### {header}\n{body}"
                results.append(section_text)
            
            if not results:
                print(f"Предупреждение: Не найдены секции в файле {analytics_file}")
                # Пробуем альтернативный способ разбиения - по номерам секций
                alternative_pattern = r'(###\s+\d+\..*?\n)'
                sections = re.split(alternative_pattern, text)
                
                for i in range(1, len(sections), 2):
                    header = sections[i].strip()
                    body = sections[i+1].strip() if i+1 < len(sections) else ''
                    results.append(f"{header}\n{body}")
                
                if not results:
                    print(f"Ошибка: Не удалось разбить файл {analytics_file} альтернативным способом")
                    return []
            
            print(f"Файл аналитики успешно разбит на {len(results)} секций")
            return results
        else:
            # Старый способ разбиения - используется как запасной вариант
            sections = re.split(r'(###\s+\d+\..*?\n)', text)
            result = []
            for i in range(1, len(sections), 2):
                header = sections[i].strip()
                body = sections[i+1].strip() if i+1 < len(sections) else ''
                result.append(f"{header}\n{body}")
            
            if not result:
                print(f"Ошибка: Не удалось разбить файл {analytics_file} на секции")
                return []
                
            print(f"Файл аналитики разбит на {len(result)} секций (запасной метод)")
            return result
    except Exception as e:
        print(f"Ошибка при разбиении файла на секции: {e}")
        return []

def extract_python_code(text):
    """Извлекает Python-код из текстового ответа."""
    code_pattern = r'```python(.*?)```'
    match = re.search(code_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def clean_temp_files(keep_pdfs=True):
    """Удаляет временные файлы, созданные в процессе генерации отчетов"""
    # Удаляем временные файлы диаграмм
    for file in os.listdir('.'):
        if file.startswith('diagram_script_') and file.endswith('.py'):
            os.remove(file)
            print(f"Удален временный файл: {file}")
        elif file.startswith('chart_section_') and file.endswith('.png'):
            os.remove(file)
            print(f"Удален временный файл: {file}")
    
    # Если нужно, можно также очистить старые ответы
    if not keep_pdfs:
        if os.path.exists('responses'):
            for file in os.listdir('responses'):
                if file.startswith('response_step') and file.endswith('.txt'):
                    os.remove(os.path.join('responses', file))
                    print(f"Удален временный файл: responses/{file}")

def analyze_business_impact(text):
    """
    Анализирует содержимое секции отчета и определяет, насколько сильно описанная проблема 
    влияет на финансовые результаты бизнеса.
    
    Args:
        text (str): Текст секции отчета
        
    Returns:
        float: Оценка бизнес-влияния от 0 до 100
    """
    # Базовая оценка влияния
    impact_score = 0
    
    # Ключевые индикаторы финансовых проблем (максимальный вес)
    critical_phrases = [
        "потеря клиентов", "снижение продаж", "возврат товара", "отказ от покупки", 
        "убытки", "штрафы", "издержки", "финансовые потери", "затраты на замену",
        "судебные иски", "компенсации", "отток клиентов", "снижение среднего чека",
        "негативные отзывы", "репутационный ущерб", "брак", "отмена заказов",
        "падение спроса", "уход от подписки", "разрыв контракта", "прекращение сотрудничества",
        "жалобы в контролирующие органы", "антиреклама", "невозврат инвестиций",
        "отрицательный ROI", "потеря доверия клиентов", "упущенная выгода", "снижение лояльности",
        "отзыв лицензии", "запрет на продажу", "ущерб репутации бренда", "массовые отказы",
        "мошенничество", "неудовлетворенные клиенты", "отрицательная прибыль"
    ]
    
    # Фразы высокого влияния (высокий вес)
    high_impact_phrases = [
        "качество", "дефект", "повреждение", "деформация", "поломка", "трещина", 
        "неисправность", "низкое качество", "проблема с доставкой", "недостаток",
        "неудовлетворенность", "претензия", "жалоба", "дырка", "повреждения при транспортировке",
        "срыв сроков", "несоответствие заявленному", "ошибка в работе", "проблемы функционирования",
        "технические проблемы", "программный сбой", "несовместимость", "отказ в работе",
        "недоработки", "не соответствует стандартам", "расхождения с описанием", "постоянные проблемы",
        "задержки", "нарушение обязательств", "токсичные материалы", "просроченный товар",
        "подделка", "неправильное функционирование", "непригодность", "частые обращения",
        "отставание от конкурентов", "отсутствие поддержки", "регулярные проблемы",
        "системные ошибки", "недостаточная производительность", "проблемы с сервисом"
    ]
    
    # Фразы среднего влияния (средний вес)
    medium_impact_phrases = [
        "упаковка", "внешний вид", "внешние дефекты", "косметические дефекты",
        "незначительные повреждения", "удобство использования", "недоработка",
        "неудобный интерфейс", "сложность настройки", "необходимость адаптации",
        "отсутствие инструкции", "редкие сбои", "незначительные недостатки",
        "шум при работе", "нестандартная комплектация", "недостаточное описание",
        "отсутствие дополнительных функций", "минимальная функциональность",
        "отсутствие обновлений", "устаревший дизайн", "громоздкость", "неэргономичность",
        "отсутствие локализации", "недостаточная гибкость", "ограниченность настроек",
        "неполнота документации", "необходимость дополнительных аксессуаров",
        "незначительные отличия от заявленного", "неравномерная работа", "нетиповой формат"
    ]
    
    # Находим процентные показатели в тексте, которые часто указывают на масштаб проблемы
    percentage_pattern = r'(\d+(?:\.\d+)?)%'
    percentages = re.findall(percentage_pattern, text)
    percentages = [float(p) for p in percentages if float(p) <= 100]
    
    # Особые паттерны, указывающие на срочность, критичность или важность
    urgency_pattern = r'срочн|критичн|немедленн|перв[ыо][йе] приорите|важн[ое][ейшая]|требуе[тм] внимания|экстренн|приоритетн|безотлагательн|остр[ая][ое]|решающ[ая][ее]|ключев[ая][ое]|основн[ая][ое]|центральн[ая][ое]|существенн|жизненно необходим|краеугольн|фундаментальн|неотложн|насущн|перв[ая][ое] очеред[и]'
    has_urgency = bool(re.search(urgency_pattern, text, re.IGNORECASE))
    
    # Паттерны, указывающие на финансовое влияние
    finance_pattern = r'финанс|деньг|бюджет|затрат|стоимост|цен[аы]|дорог|дешев|экономи[чк]|выгод|прибыл|доход|убыт[ок]|маржа|рентабельн|окупаемост|инвестиц|капитал|деньги|монетиза|кредит|заем|ссуд|платеж|транзакц|комиссия|пошлина|налог|сбор|счет|баланс|расход|траты|себестоимост|рекламн[ый][ая] бюджет|возврат средств|реклама|маркетинг|продвижен|капитализац|акци[ий]|дивиденд|вложени|наличные|безналичн|кошелек|эквайринг|выручк|сделк|контракт|договор|безубыточн|дефицит|профицит'
    has_finance = bool(re.search(finance_pattern, text, re.IGNORECASE))
    
    # Чувствительные области для бизнеса
    sensitive_areas = [
        "безопасность", "здоровье", "срок годности", "гарантия", "законодательство", 
        "нормативы", "соответствие стандартам", "сертификация", "персональные данные",
        "конфиденциальность", "приватность", "экология", "устойчивое развитие",
        "этика", "мораль", "охрана труда", "санитарные нормы", "патенты",
        "авторские права", "интеллектуальная собственность", "лицензирование",
        "регламенты", "аттестация", "аккредитация", "социальная ответственность",
        "энергоэффективность", "утилизация", "переработка", "биоразлагаемость",
        "экологичность", "углеродный след", "доступность для инвалидов", "надежность",
        "долговечность", "целостность данных", "шифрование", "защита от взлома", 
        "эргономика", "анонимность", "детали", "доступ несовершеннолетних"
    ]
    has_sensitive_area = any(area in text.lower() for area in sensitive_areas)
    
    # Проверка на общее негативное восприятие
    negative_sentiment = r'плох|ужасн|отвратительн|негативн|разочарова|неудовлетворительн|неприемлем|недопустим|ужасающ|катастрофическ|кошмарн|невыносим|отталкивающ|неприятн|тревожн|беспокоящ|демотивирующ|деморализ|угнетающ|раздражающ|напрягающ|мучительн|болезненн|несносн|вредн|токсичн|опасн|неблагоприятн|неподходящ|сомнительн|ненадежн|нежелательн|непригодн|бесполезн|провальн|проигрышн|отрицательн|губительн|оскорбительн|дискомфортн|некачественн|нецелесообразн|обременительн|рискованн|сложн|проблематичн|нерациональн|подозрительн'
    has_negative = bool(re.search(negative_sentiment, text, re.IGNORECASE))
    
    # Подсчет упоминаний ключевых фраз
    critical_count = sum(1 for phrase in critical_phrases if re.search(r'\b' + re.escape(phrase) + r'\b', text.lower()))
    high_impact_count = sum(1 for phrase in high_impact_phrases if re.search(r'\b' + re.escape(phrase) + r'\b', text.lower()))
    medium_impact_count = sum(1 for phrase in medium_impact_phrases if re.search(r'\b' + re.escape(phrase) + r'\b', text.lower()))
    
    # Расчет базовой оценки на основе найденных фраз
    impact_score += critical_count * 15  # Максимальный вес
    impact_score += high_impact_count * 8  # Высокий вес
    impact_score += medium_impact_count * 4  # Средний вес
    
    # Анализ процентных показателей - большие проценты негативных явлений повышают приоритет
    if percentages:
        max_percentage = max(percentages)
        if max_percentage > 50:  # Если проблема затрагивает более 50% случаев
            impact_score += 25
        elif max_percentage > 30:  # Если проблема затрагивает более 30% случаев
            impact_score += 15
        elif max_percentage > 10:  # Если проблема затрагивает более 10% случаев
            impact_score += 5
    
    # Повышаем приоритет срочных проблем
    if has_urgency:
        impact_score += 15
    
    # Повышаем приоритет проблем с упоминанием финансов
    if has_finance:
        impact_score += 20
    
    # Повышаем приоритет чувствительных областей
    if has_sensitive_area:
        impact_score += 15
    
    # Повышаем при наличии общего негативного восприятия
    if has_negative:
        impact_score += 10
    
    # Ограничиваем максимальное значение до 100
    return min(impact_score, 100)


def prioritize_pdf_sections(responses_dir, pdf_dir):
    """
    Анализирует секции отчета и определяет порядок их расположения в финальном PDF
    в зависимости от их влияния на бизнес.
    
    Args:
        responses_dir (str): Директория с текстовыми ответами
        pdf_dir (str): Директория с PDF-файлами
        
    Returns:
        list: Отсортированный список путей к PDF-файлам
    """
    # Словарь для хранения оценок и соответствующих им путей к PDF-файлам
    impact_scores = {}
    
    # Получаем все файлы ответов
    response_files = []
    for file in os.listdir(responses_dir):
        if file.startswith("response_step") and file.endswith(".txt"):
            response_files.append(os.path.join(responses_dir, file))
    
    # Анализируем каждый файл ответа и определяем его оценку влияния на бизнес
    for response_file in response_files:
        # Получаем номер секции из имени файла
        match = re.search(r'response_step(\d+)', os.path.basename(response_file))
        if not match:
            continue
            
        section_num = int(match.group(1)) - 2  # Корректируем номер (шаги начинаются с 3)
        
        # Соответствующий PDF-файл
        pdf_file = os.path.join(pdf_dir, f"report_section_{section_num}.pdf")
        if not os.path.exists(pdf_file):
            continue
            
        # Читаем содержимое файла ответа
        try:
            with open(response_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Анализируем влияние на бизнес
            impact_score = analyze_business_impact(content)
            
            # Сохраняем оценку и путь к файлу
            impact_scores[pdf_file] = (impact_score, section_num)
            
            print(f"Секция {section_num}: Влияние на бизнес = {impact_score:.1f}/100")
        except Exception as e:
            print(f"Ошибка при анализе файла {response_file}: {e}")
    
    # Сортируем PDF-файлы по убыванию их оценки влияния на бизнес
    # При равных оценках сохраняем исходный порядок секций
    sorted_files = sorted(
        impact_scores.keys(),
        key=lambda x: (-impact_scores[x][0], impact_scores[x][1])
    )
    
    return sorted_files

def send_analytics_sections_to_gpt(analytics_file, prompt_file="prompt.txt", message2_file="message2.txt", session_dir=None):
    """
    Отправляет секции аналитики в GPT последовательно в одном чате и сохраняет PDF-отчёты с диаграммами.
    """
    # Очищаем временные файлы перед началом
    clean_temp_files(keep_pdfs=True)
    
    # Создаем временную директорию для текущего анализа
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not session_dir:
        session_dir = f"analysis_{timestamp}"
    os.makedirs(session_dir, exist_ok=True)
    
    # Создаем поддиректории
    charts_dir = os.path.join(session_dir, "charts")
    scripts_dir = os.path.join(session_dir, "scripts") 
    responses_dir = os.path.join(session_dir, "responses")
    pdf_dir = os.path.join(session_dir, "pdf_reports")
    os.makedirs(charts_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(responses_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Разбиваем файл аналитики на секции
    sections = split_analytics_sections(analytics_file)
    if not sections:
        print(f"Ошибка: Не удалось разбить файл {analytics_file} на секции")
        return
    
    print(f"Файл аналитики разбит на {len(sections)} секций")
    
    # Загружаем шаблон сообщения из message2.txt
    with open(message2_file, 'r', encoding='utf-8') as f:
        message2_template = f.read()
    
    # Проверяем наличие системного промпта
    if not os.path.exists(prompt_file):
        print(f"Ошибка: Файл с системным промптом не найден: {prompt_file}")
        return
    
    # Загружаем системный промпт
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    # Инициализируем чат с начальным системным промптом
    from gpt_config import create_openai_client, get_system_prompt, DEFAULT_API_PARAMS
    client = create_openai_client()
    if not client:
        print("Ошибка: Не удалось создать клиент OpenAI")
        return
    
    # Применяем Transparency Contract к системному промпту
    system_prompt = get_system_prompt(prompt_content)
    conversation_history = [{"role": "system", "content": system_prompt}]
    
    # Добавляем первое сообщение (инструкции)
    if os.path.exists("message1.txt"):
        with open("message1.txt", 'r', encoding='utf-8') as f:
            message1_content = f.read()
        conversation_history.append({"role": "user", "content": message1_content})
        
        # Получаем ответ на первое сообщение
        try:
            params = DEFAULT_API_PARAMS.copy()
            params["model"] = "gpt-4o"
            params["messages"] = conversation_history
            response = client.chat.completions.create(**params)
            response_text = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": response_text})
            print("Получен ответ на первое сообщение")
        except Exception as e:
            print(f"Ошибка при отправке первого сообщения: {e}")
            return
    
    # Обрабатываем каждую секцию аналитики
    for idx, section in enumerate(sections, 1):
        print(f"Обработка секции {idx}/{len(sections)}")
        
        # Формируем текст сообщения для GPT с уточнением по типу графика
        if "Вот:" in message2_template:
            msg = re.sub(r"(Вот:).*", f"Вот: {section}", message2_template, count=1, flags=re.DOTALL)
            
            # Добавляем примечания для конкретных секций
            if "### 4. Наличие дефектов" in section:
                msg += "\n\nПримечание: Для Box Plot используй формат [[30], [64]] вместо [30, 64], чтобы избежать ошибки размерностей."
            elif "### 5. Проблемы с упаковкой" in section:
                msg += "\n\nПримечание: Для тепловой карты используй matplotlib.pyplot.imshow() вместо seaborn.heatmap(), если возможно."
        else:
            msg = message2_template + f"\nВот: {section}"
        
        # Добавляем сообщение в историю беседы
        conversation_history.append({"role": "user", "content": msg})
        
        # Отправляем сообщение в GPT
        try:
            print(f"Отправка сообщения для секции {idx}...")
            params = DEFAULT_API_PARAMS.copy()
            params["model"] = "gpt-4o"
            params["messages"] = conversation_history
            response = client.chat.completions.create(**params)
            response_text = response.choices[0].message.content
            
            # Сохраняем ответ в файл
            response_file = os.path.join(responses_dir, f"response_step{idx + 2}_{timestamp}.txt")
            with open(response_file, 'w', encoding='utf-8') as file:
                file.write(response_text)
            print(f"Ответ для секции {idx} сохранен в {response_file}")
            
            # Добавляем ответ ассистента в историю
            conversation_history.append({"role": "assistant", "content": response_text})
            
            # Извлекаем и сохраняем Python-скрипт для построения диаграммы
            python_code = extract_python_code(response_text)
            chart_file = None
            
            if python_code:
                # Сохраняем скрипт в файл
                script_file = os.path.join(scripts_dir, f"diagram_script_{idx}.py")
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(python_code)
                print(f"Python-скрипт для построения диаграммы сохранен в {script_file}")
                
                # ВАЖНО - задаем путь к файлу диаграммы ПОСЛЕ сохранения скрипта
                chart_file = os.path.join(charts_dir, f"chart_section_{idx}.png")
                
                # Создаем диаграмму
                try:
                    import matplotlib
                    matplotlib.use('Agg')  # Не-интерактивный бэкенд
                    import matplotlib.pyplot as plt
                    import numpy as np
                    
                    # Закрываем все предыдущие фигуры
                    plt.close('all')
                    
                    # Исправляем данные для Box Plot, если это секция 4
                    if "### 4. Наличие дефектов" in section and "boxplot" in python_code:
                        python_code = python_code.replace("data = [30, 64]", "data = [[30], [64]]")
                    
                    # Создаем модифицированный код с правильной обработкой seaborn
                    mock_seaborn_code = """
# Проверка наличия seaborn
try:
    import seaborn as sns
except ImportError:
    # Если seaborn не установлен, создаем "заглушку" для heatmap и boxplot
    class MockSeaborn:
        def heatmap(self, data, **kwargs):
            plt.figure(figsize=(8, 4))
            if isinstance(data, list):
                data = np.array([data])
            im = plt.imshow(data, aspect='auto', cmap='coolwarm')
            plt.colorbar(im, label='Значения')
            if 'annot' in kwargs and kwargs['annot']:
                height, width = data.shape
                for i in range(height):
                    for j in range(width):
                        plt.text(j, i, str(data[i, j]), 
                                ha="center", va="center")
            if 'xticklabels' in kwargs:
                plt.xticks(range(len(kwargs['xticklabels'])), kwargs['xticklabels'])
            if 'yticklabels' in kwargs:
                plt.yticks(range(len(kwargs['yticklabels'])), kwargs['yticklabels'])
            return im
            
        def boxplot(self, data=None, **kwargs):
            # Убедимся, что данные правильного формата
            if isinstance(data, list) and not isinstance(data[0], list):
                data = [[x] for x in data]
            return plt.boxplot(data, **kwargs)
    sns = MockSeaborn()
"""
                    
                    # Собираем полный код с правильным сохранением диаграммы и импортами
                    modified_code = f"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
{mock_seaborn_code}
# Исходный код диаграммы
{python_code.replace("plt.show()", "")}
# Сохраняем диаграмму
plt.savefig(r'{chart_file}', bbox_inches='tight', dpi=300)
plt.close('all')
"""
                    
                    # Выполняем скрипт в защищенной среде
                    try:
                        # Запускаем в отдельном пространстве имен
                        namespace = {'__builtins__': __builtins__, 'np': np, 'plt': plt, 'matplotlib': matplotlib}
                        exec(modified_code, namespace)
                    except Exception as e:
                        print(f"Ошибка при выполнении кода диаграммы: {e}")
                        # Запасной вариант - более безопасное выполнение
                        try:
                            # Сохраняем модифицированный скрипт во временный файл и выполняем его как подпроцесс
                            temp_script = os.path.join(scripts_dir, f"temp_diagram_{idx}.py")
                            with open(temp_script, 'w', encoding='utf-8') as f:
                                f.write(modified_code)
                            
                            result = subprocess.run(['python', temp_script], 
                                              stderr=subprocess.PIPE,
                                              stdout=subprocess.PIPE,
                                              text=True)
                            
                            if result.returncode != 0:
                                print(f"Ошибка при запуске скрипта: {result.stderr}")
                            else:
                                print("Диаграмма успешно создана через подпроцесс")
                        except Exception as e2:
                            print(f"Ошибка при запуске скрипта как подпроцесса: {e2}")
                    
                    # Проверяем, успешно ли создана диаграмма
                    if os.path.exists(chart_file) and os.path.getsize(chart_file) > 0:
                        print(f"Диаграмма успешно создана и сохранена в {chart_file}")
                    else:
                        print(f"Предупреждение: Файл диаграммы не создан или пуст")
                        chart_file = None
                except Exception as e:
                    print(f"Ошибка при создании диаграммы: {e}")
                    chart_file = None
            
            # Генерируем PDF с диаграммой - ИЗМЕНЕНО: используем директорию из сессии
            pdf_filename = f"report_section_{idx}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            
            pdf_success = False
            if chart_file and os.path.exists(chart_file):
                pdf_success = generate_pdf_from_response(response_file, chart_file, pdf_path)
            else:
                pdf_success = generate_pdf_from_response(response_file, None, pdf_path)
                
            if pdf_success:
                print(f"PDF-отчёт для секции {idx} успешно создан: {pdf_path}")
            else:
                print(f"Ошибка при создании PDF-отчёта для секции {idx}")
                
        except Exception as e:
            print(f"Ошибка при обработке секции {idx}: {e}")
            continue
    
    print(f"Обработка всех секций аналитики завершена. Результаты сохранены в директории {session_dir}")
    
    # Объединяем все PDF-отчеты в один файл после обработки всех секций
    try:
        # Получаем артикул из имени файла аналитики
        article = None
        if analytics_file.startswith("reviews_") and "_prepared_for_ai_analytics" in analytics_file:
            article = analytics_file.split("reviews_")[1].split("_prepared_for_ai_analytics")[0]
        
        if article:
            print("\nАнализ бизнес-критичности проблем и приоритизация секций отчета...")
            
            # Приоритизируем секции отчета по их влиянию на бизнес
            prioritized_pdf_files = prioritize_pdf_sections(responses_dir, pdf_dir)
            
            if prioritized_pdf_files:
                # Выводим информацию о приоритизации
                print("\nПорядок секций в итоговом отчете (от наиболее критичных для бизнеса):")
                for i, pdf_file in enumerate(prioritized_pdf_files):
                    section_name = os.path.basename(pdf_file)
                    print(f"{i+1}. {section_name}")
                
                # Объединяем PDF-файлы в порядке их бизнес-приоритета
                try:
                    from PyPDF2 import PdfMerger
                    
                    # Сохраняем в директорию сессии
                    output_pdf = os.path.join(session_dir, f"report_{article}.pdf")
                    merger = PdfMerger()
                    
                    # Добавляем файлы в порядке их бизнес-приоритета
                    for pdf_file in prioritized_pdf_files:
                        try:
                            merger.append(pdf_file)
                            print(f"Добавлен файл: {pdf_file}")
                        except Exception as e:
                            print(f"Ошибка при добавлении файла {pdf_file}: {e}")
                    
                    # Сохраняем объединенный PDF
                    merger.write(output_pdf)
                    merger.close()
                    print(f"Создан объединенный PDF-отчет: {output_pdf} (секции отсортированы по степени бизнес-критичности)")
                    return
                except ImportError:
                    print("Для объединения PDF требуется установить PyPDF2. Используем стандартный метод.")
            
            # Если приоритизация не сработала или возникла ошибка, используем стандартный метод
            from pdf_generator import merge_pdf_reports
            output_pdf = os.path.join(session_dir, f"report_{article}.pdf")
            merge_result = merge_pdf_reports(output_pdf, source_dir=pdf_dir)
            if merge_result:
                print(f"Создан объединенный PDF-отчет: {output_pdf} (стандартный порядок секций)")
    except Exception as e:
        print(f"Ошибка при создании объединенного PDF-отчета: {e}")
        # Пробуем использовать стандартный метод при возникновении ошибки
        try:
            from pdf_generator import merge_pdf_reports
            output_pdf = os.path.join(session_dir, f"report_{article}.pdf")
            merge_result = merge_pdf_reports(output_pdf, source_dir=pdf_dir)
            if merge_result:
                print(f"Создан объединенный PDF-отчет (стандартным методом): {output_pdf}")
        except Exception as e2:
            print(f"Ошибка при создании объединенного PDF-отчета стандартным методом: {e2}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализ отзывов с использованием GPT')
    parser.add_argument('analytics_file', nargs='?', help='Путь к файлу с аналитикой для обработки')
    parser.add_argument('--clean', action='store_true', help='Очистить все временные файлы')
    parser.add_argument('--session-dir', help='Путь к директории сессии (для использования в full_analysis.py)')
    args = parser.parse_args()
    
    if args.clean:
        clean_temp_files(keep_pdfs=False)
        print("Все временные файлы удалены")
        exit(0)
    
    # Последовательность файлов сообщений
    messages_files = [
        "prompt.txt",       # Системный промпт
        "message1.txt",     # Первое сообщение
        "message2.txt",     # Второе сообщение
    ]

    # Проверяем, передан ли файл аналитики в аргументах
    analytics_file = args.analytics_file
    if not analytics_file or not os.path.exists(analytics_file):
        # Пробуем найти файл аналитики для текущего запроска
        import glob
        analytics_files = glob.glob("reviews_*_prepared_for_ai_analytics.txt")
        if analytics_files:
            analytics_file = analytics_files[0]
            print(f"Используем найденный файл аналитики: {analytics_file}")
        else:
            print("Ошибка: Не найден файл с аналитикой. Укажите путь к файлу.")
            exit(1)
    
    if os.path.exists(analytics_file):
        # Если указан путь к директории сессии, используем его
        if args.session_dir:
            if os.path.exists(args.session_dir):
                send_analytics_sections_to_gpt(analytics_file, prompt_file="prompt.txt", message2_file="message2.txt", 
                                               session_dir=args.session_dir)
            else:
                print(f"Директория сессии не существует: {args.session_dir}")
                exit(1)
        else:
            send_analytics_sections_to_gpt(analytics_file)
    else:
        # Проверяем наличие файлов с сообщениями
        missing_files = [f for f in messages_files if not os.path.exists(f)]
        if missing_files:
            print(f"Отсутствуют следующие файлы с сообщениями: {', '.join(missing_files)}")
        else:
            # Запускаем чат с GPT
            success, response_step3_file = chat_with_gpt(messages_files)
            if success:
                print("Диалог успешно завершен. Ответы сохранены в директории 'responses'.")
                
                # Создаем PDF из файла с ответом от шага 3
                if response_step3_file and response_step3_file.endswith(".txt"):
                    pdf_success = generate_pdf_from_response(response_step3_file)
                    if pdf_success:
                        print("PDF-отчет успешно создан.")
                    else:
                        print("Произошла ошибка при создании PDF-отчета.")
            else:
                print("Произошла ошибка при выполнении диалога.")
