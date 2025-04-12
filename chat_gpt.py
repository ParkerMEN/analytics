import os
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
    # Проверка наличия API ключа
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # Попытка прочитать ключ из файла, если переменная окружения не найдена
    if not api_key:
        try:
            with open('api_key.txt', 'r') as f:
                api_key = f.read().strip()
        except:
            pass
    
    if not api_key:
        print("ОШИБКА: API ключ OpenAI не найден.")
        print("Установите переменную окружения OPENAI_API_KEY")
        print("или создайте файл api_key.txt с вашим API ключом")
        print("Например: set OPENAI_API_KEY=your_api_key_here (Windows)")
        return False
    
    client = OpenAI(api_key=api_key)
    conversation_history = []
    response_step3_file = None

    # Последовательно отправляем сообщения
    for i, message_file in enumerate(messages_files, 1):
        user_content = load_message_from_file(message_file)
        if not user_content:
            print(f"Файл {message_file} пуст или не найден.")
            continue

        # Добавляем сообщение пользователя в историю
        conversation_history.append({"role": "user", "content": user_content})
        print(f"Отправка сообщения {i}...")

        try:
            # Отправляем запрос к API с использованием нового интерфейса
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history,
                temperature=0.7,
            )

            # Получаем текст ответа из новой структуры ответа
            response_text = response.choices[0].message.content
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

def generate_pdf_from_response(response_file):
    """
    Запускает pdf_generator.py для создания PDF из файла ответа.
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
        
        # Определяем имя выходного PDF-файла
        output_dir = "pdf_reports"
        os.makedirs(output_dir, exist_ok=True)
        output_pdf = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(response_file))[0]}.pdf")
        
        # Вызываем функцию для создания PDF
        result = pdf_generator.generate_pdf_with_plot(response_file, output_pdf)
        
        if result:
            print(f"PDF-отчет создан: {output_pdf}")
            return True
        else:
            print(f"Не удалось создать PDF-отчет для файла {response_file}")
            return False
            
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        return False

if __name__ == "__main__":
    # Последовательность файлов сообщений
    messages_files = [
        "prompt.txt",       # Системный промпт
        "message1.txt",     # Первое сообщение
        "message2.txt",     # Второе сообщение
    ]

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
