import asyncio
import httpx
import json
import logging
import time
from typing import Dict, Any, List, Tuple, Optional

class ThematicGroupAnalyzer:
    """
    Класс для асинхронного анализа тематических групп отзывов.
    Работает совместно с GPTAgent, но выполняет анализ групп параллельно.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        """
        Инициализирует анализатор тематических групп.
        
        Args:
            api_key: Ключ API OpenAI
            model: Название модели для использования
        """
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger('ThematicGroupAnalyzer')
        self.logger.setLevel(logging.INFO)
        
        # Проверяем, есть ли уже обработчики логирования
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
    
    async def analyze_groups(self, final_groups: List[Dict[str, Any]], max_concurrent: int = 3) -> Tuple[List[str], int]:
        """
        Асинхронно анализирует все группы с ограничением на количество одновременных запросов.
        
        Args:
            final_groups: Список групп для анализа
            max_concurrent: Максимальное количество одновременных запросов
            
        Returns:
            Tuple с результатами анализа и общим количеством проанализированных отзывов
        """
        # Создаем семафор для ограничения количества параллельных запросов
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Создаем и запускаем задачи анализа
        self.logger.info(f"Запуск асинхронного анализа {len(final_groups)} тематических групп (макс. {max_concurrent} одновременно)")
        
        tasks = []
        for i, group_data in enumerate(final_groups):
            task = self.analyze_group_with_semaphore(i, len(final_groups), group_data, semaphore)
            tasks.append(task)
        
        # Запускаем все задачи параллельно и ждем их выполнения
        results = await asyncio.gather(*tasks)
        
        # Разделяем результаты и количество отзывов
        result_texts = [result for result, _ in results]
        total_analyzed_reviews = sum(reviews_count for _, reviews_count in results)
        
        return result_texts, total_analyzed_reviews
    
    async def analyze_group_with_semaphore(self, index: int, total: int, 
                                          group_data: Dict[str, Any], 
                                          semaphore: asyncio.Semaphore) -> Tuple[str, int]:
        """
        Анализирует группу с использованием семафора для ограничения параллелизма.
        
        Args:
            index: Индекс группы
            total: Общее количество групп
            group_data: Данные группы для анализа
            semaphore: Семафор для ограничения параллелизма
            
        Returns:
            Tuple с результатом анализа и количеством отзывов в группе
        """
        async with semaphore:
            start_time = time.time()
            self.logger.info(f"Анализ группы {index+1} из {total}: {group_data.get('analysis_focus', 'Неизвестная группа')}")
            
            # Подсчитываем отзывы в этой группе
            group_reviews_count = (
                len(group_data.get("review_texts_for_theme", [])) + 
                len(group_data.get("review_texts_for_rating", [])) + 
                len(group_data.get("review_texts_for_themes", [])) +
                len(group_data.get("review_texts", []))
            )
            
            # Анализируем группу
            result = await self.analyze_data_with_gpt(group_data)
            
            elapsed = time.time() - start_time
            self.logger.info(f"Анализ группы {index+1} из {total} завершен за {elapsed:.1f} секунд")
            
            return result, group_reviews_count
    
    async def analyze_data_with_gpt(self, data: Dict[str, Any]) -> str:
        """
        Асинхронно отправляет данные в GPT для анализа.
        
        Args:
            data: Данные для анализа
            
        Returns:
            Результат анализа
        """
        # Определяем фокус анализа
        analysis_focus = data.get("analysis_focus", "Полный анализ отзывов")
        
        # Извлекаем ключевую информацию о данных
        total_reviews_in_group = 0
        if "review_texts_for_theme" in data:
            total_reviews_in_group = len(data["review_texts_for_theme"])
        elif "review_texts_for_rating" in data:
            total_reviews_in_group = len(data["review_texts_for_rating"])
        elif "review_texts_for_themes" in data:
            total_reviews_in_group = len(data["review_texts_for_themes"])
        elif "review_texts" in data:
            total_reviews_in_group = len(data["review_texts"])
        
        # Определяем тему анализа для специфических инструкций
        theme_specific_instructions = ""
        if "Группа отзывов с рейтингом" in analysis_focus:
            rating = analysis_focus.split("рейтингом")[1].strip().split()[0]
            theme_specific_instructions = f"""
            Для анализа группы с рейтингом {rating}:
            1. Определи ключевые факторы, которые приводят к этой оценке
            2. Выяви частотность упоминания конкретных особенностей продукта
            3. Проанализируй эмоциональные паттерны в отзывах
            """
        elif "Тематическая группа:" in analysis_focus:
            theme = analysis_focus.split("Тематическая группа:")[1].strip()
            theme_specific_instructions = f"""
            Для анализа тематической группы "{theme}":
            1. Определи, как эта тема влияет на общее восприятие продукта
            2. Выяви взаимосвязь между этой темой и рейтингами
            3. Подсчитай частоту упоминания смежных тем и проблем
            """
        
        # Формируем базовые инструкции для анализа
        base_instructions = f"""
        Ты опытный аналитик данных, специализирующийся на извлечении визуализируемых метрик и закономерностей из отзывов. 
        Твоя текущая задача: {analysis_focus}.
        
        Проанализируй предоставленные данные ({total_reviews_in_group} отзывов) и:
        
        1. ИЗВЛЕКИ КОНКРЕТНЫЕ ЧИСЛОВЫЕ ДАННЫЕ для построения визуализаций:
           - Подсчитай частоту упоминания ключевых слов и концепций
           - Определи процентное соотношение различных аспектов продукта
           - Выяви корреляции между различными факторами
           - Проанализируй тренды и закономерности в числовом выражении
        
        2. Выяви ключевые факторы, влияющие на удовлетворенность, с указанием их частоты и влияния
        
        3. Определи взаимосвязи между упоминаемыми темами и оценками, представь их в количественной форме
        
        4. Подсчитай и ранжируй частоту упоминания проблем и их влияние на восприятие продукта
        
        5. Выяви неочевидные характеристики продукта, важные для пользователей, с указанием частоты их упоминания
        
        6. САМОСТОЯТЕЛЬНО ОПРЕДЕЛИ 3-5 дополнительных метрик или аспектов, уникальных для данной группы отзывов
        
        7. ПРЕДЛОЖИ КОНКРЕТНЫЕ ВИЗУАЛИЗАЦИИ на основе твоего анализа:
           - Укажи тип диаграммы/графика (столбчатая, круговая, линейная и т.д.)
           - Опиши данные для осей или сегментов
           - Объясни, какие инсайты эта визуализация должна показать
        
        Представь анализ в структурированной форме, сочетая качественные наблюдения с КОНКРЕТНЫМИ ЧИСЛОВЫМИ ДАННЫМИ.
        """
        
        # Объединяем базовые и специфические инструкции
        instructions = base_instructions + theme_specific_instructions
        
        # Создаем строку с примерами отзывов (не более 10 для читаемости)
        example_reviews = ""
        if "review_texts_for_theme" in data:
            examples = data["review_texts_for_theme"][:10]
            example_reviews = "\n\nПримеры отзывов в этой группе:\n" + "\n".join(examples)
        elif "review_texts_for_rating" in data:
            examples = data["review_texts_for_rating"][:10]
            example_reviews = "\n\nПримеры отзывов в этой группе:\n" + "\n".join(examples)
        elif "review_texts_for_themes" in data:
            examples = data["review_texts_for_themes"][:10]
            example_reviews = "\n\nПримеры отзывов в этой группе:\n" + "\n".join(examples)
        elif "review_texts" in data:
            examples = data["review_texts"][:10]
            example_reviews = "\n\nПримеры отзывов в этой группе:\n" + "\n".join(examples)
        
        # Логируем запрос для отладки
        analysis_focus_safe = self.slugify(analysis_focus)
        log_file = f"analysis_query_{analysis_focus_safe}.txt"
        self.log_to_file(log_file, instructions + example_reviews + f"\n\nПолные данные для анализа:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # Делаем несколько попыток с экспоненциальной задержкой при ошибках
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Выполняем асинхронный запрос к OpenAI API
                async with httpx.AsyncClient(timeout=60.0) as client:
                    request_data = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Ты аналитик данных, специализирующийся на извлечении конкретных, визуализируемых метрик из текстовых отзывов."},
                            {"role": "user", "content": instructions + f"\nДанные для анализа:\n{json.dumps(data, ensure_ascii=False, indent=2)}"}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4000
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=request_data
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    
                    result = response_data["choices"][0]["message"]["content"]
                    
                    # Логируем ответ
                    result_log_file = f"analysis_result_{analysis_focus_safe}.txt"
                    self.log_to_file(result_log_file, result)
                    
                    return result
            
            except Exception as e:
                self.logger.error(f"Ошибка при анализе данных (попытка {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    self.logger.info(f"Повтор через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    error_message = f"Не удалось выполнить анализ после {max_retries} попыток: {str(e)}"
                    return error_message
        
        return "Ошибка анализа данных после всех попыток повтора"
    
    def log_to_file(self, filename: str, content: str):
        """
        Логирует содержимое в файл.
        
        Args:
            filename: Имя файла для лога
            content: Содержимое для записи
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Ошибка при записи лога в файл {filename}: {str(e)}")
    
    def slugify(self, text: str) -> str:
        """
        Преобразует текст в slug для использования в имени файла.
        """
        import re
        
        # Транслитерация кириллицы
        trans_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
            'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        
        # Преобразуем в нижний регистр и транслитерируем
        slug = ''.join(trans_map.get(c, c) for c in text.lower())
        
        # Заменяем не буквенно-цифровые символы на дефис
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        
        # Удаляем начальные и конечные дефисы
        slug = slug.strip('-')
        
        # Ограничиваем длину
        return slug[:50]