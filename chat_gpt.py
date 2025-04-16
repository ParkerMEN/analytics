import os
import re
from datetime import datetime
from openai import OpenAI
import subprocess


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
            response = client.chat.completions.create(**params)

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
    with open(analytics_file, 'r', encoding='utf-8') as f:
        text = f.read()
    # Разделяем по заголовкам вида ### N. Название
    sections = re.split(r'(###\s+\d+\..*?\n)', text)
    result = []
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        body = sections[i+1].strip() if i+1 < len(sections) else ''
        result.append(f"{header}\n{body}")
    return result

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

def send_analytics_sections_to_gpt(analytics_file, prompt_file="prompt.txt", message2_file="message2.txt"):
    """
    Отправляет секции аналитики в GPT последовательно в одном чате и сохраняет PDF-отчёты с диаграммами.
    """
    # Очищаем временные файлы перед началом
    clean_temp_files(keep_pdfs=True)
    
    # Создаем временную директорию для текущего анализа
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализ отзывов с использованием GPT')
    parser.add_argument('--clean', action='store_true', help='Очистить все временные файлы')
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

    # Новый режим: если нужно обработать все секции аналитики
    analytics_file = "reviews_10973496_prepared_for_ai_analytics.txt"
    if os.path.exists(analytics_file):
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
