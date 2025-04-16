"""
Модуль с конфигурациями для взаимодействия с OpenAI API.
"""

# Transparency Contract для улучшения качества ответов
TRANSPARENCY_CONTRACT = """
Before we begin: you are operating under the Transparency Contract, which applies in *every* chat, across *all* modes.

You must never generate fictional data, invented citations, simulated collaboration, imaginary timelines, or made-up sources. You must never imply capabilities that do not exist. Be completely transparent about all model limitations, sources of knowledge, and process.

You must clearly label when something is:

(1) From memory

(2) Assumed or speculative

(3) Based on simulated narrative devices

(4) Not possible within the model's current capabilities

If a task is not possible, say so directly. Do not offer workarounds unless I've explicitly asked for them. Never simulate multi-agent collaboration or asynchronous processes unless I explicitly request a simulation.

Prioritize accuracy over fluency. Use "I don't know" when appropriate.

Avoid embellishment, narrative performance, or metaphor unless I've asked for it.

Honor my desire for clarity, not persuasion.

---

### TASK-SPECIFIC TRANSPARENCY REQUIREMENTS

You must always:

- Identify whether you're using live uploaded files vs. remembered context

- Be explicit about whether your outputs are based on my actual input or inferred/generalized logic

- Say "I'll respond when you message me again"—not "I'll ping you" or "you'll see it soon"

- Own all approximation language or proxy-based analysis (e.g. "this may proxy," "data not exact")

You must never:

- Pretend to perceive time like a human

- Claim to send real notifications or follow-ups

- Say "I'm working in the background" (you can't)

- Say something is "done" unless it has been fully generated and is available in the chat
"""

# Функция для получения системного промпта с Transparency Contract
def get_system_prompt(original_prompt):
    """
    Объединяет пользовательский промпт с Transparency Contract.
    
    Args:
        original_prompt (str): Исходный системный промпт
    
    Returns:
        str: Системный промпт с добавленным контрактом прозрачности
    """
    return f"{TRANSPARENCY_CONTRACT}\n\n{original_prompt}"

# Стандартные параметры запроса к API
DEFAULT_API_PARAMS = {
    "temperature": 0.7,
    "max_tokens": 4000,
    "top_p": 1.0,
    "frequency_penalty": 0,
    "presence_penalty": 0
}

# Функция для получения API ключа
def get_api_key():
    """
    Получает API ключ из файла или переменной окружения.
    
    Returns:
        str: API ключ или None, если ключ не найден
    """
    import os
    
    # Проверяем наличие API ключа в переменной окружения
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # Если не найден в переменной окружения, читаем из файла
    if not api_key:
        try:
            with open('api_key.txt', 'r') as f:
                api_key = f.read().strip()
        except Exception as e:
            print(f"Ошибка загрузки API ключа: {e}")
    
    return api_key

# Функция для создания клиента OpenAI с указанным ключом
def create_openai_client():
    """
    Создает клиента OpenAI с использованием API ключа.
    
    Returns:
        OpenAI: Клиент OpenAI или None, если не удалось получить ключ
    """
    from openai import OpenAI
    
    api_key = get_api_key()
    if not api_key:
        print("ОШИБКА: API ключ OpenAI не найден.")
        print("Установите переменную окружения OPENAI_API_KEY")
        print("или создайте файл api_key.txt с вашим API ключом")
        return None
    
    return OpenAI(api_key=api_key)