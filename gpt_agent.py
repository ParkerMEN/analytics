from collections import Counter, defaultdict
from typing import List, Dict, Any, Union, Optional
from datetime import datetime
import json
import copy
import os
import logging
import re
import glob

# Попытка импортировать библиотеку tiktoken для точного подсчета токенов
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Библиотека tiktoken не установлена. Будет использоваться приблизительная оценка токенов.")

import openai

class GPTAgent:
    """
    Агент для взаимодействия с GPT, предоставляющий аналитические рекомендации
    и предложения по визуализациям на основе данных отзывов.
    """

    def __init__(self, api_key: str):
        """
        Инициализирует агент для взаимодействия с GPT.

        Args:
            api_key: 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.
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        
        # Установка логирования
        self.logger = logging.getLogger('GPTAgent')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def analyze_reviews(self, reviews: List[Dict[str, Any]]) -> str:
        """
        Анализирует отзывы и предоставляет рекомендации по визуализациям.

        Args:
            reviews: Список отзывов в формате словарей.

        Returns:
            Результаты анализа и рекомендации по визуализациям.
        """
        # Подготовка всех доступных данных и метаданных из отзывов
        all_metadata = self._gather_all_metadata(reviews)
        summary_data = self._prepare_summary_data(reviews)
        
        # Формируем запрос к GPT с полным комплексом данных
        prompt = (
            "Ты опытный аналитик данных. На основе предоставленных данных отзывов предложи "
            "подробные рекомендации по визуализациям, которые наилучшим образом представят данные. "
            "Особое внимание удели мелким деталям и скрытым закономерностям в данных.\n\n"
            "Учитывай, что приоритет у столбчатых и круговых диаграмм, но рассмотри также: "
            "Line Chart, Horizontal Bar Chart, Stacked Bar Chart, Cumulative Line, Dual Axis Plot, "
            "Bar + Line Plot, Donut Chart, Area Plot, Color-encoded Scatter Plot.\n\n"
            "Для каждой рекомендуемой визуализации укажи:\n"
            "1. Тип диаграммы\n"
            "2. Какие данные на ней отобразить\n"
            "3. Почему именно эта визуализация эффективна для этих данных\n"
            "4. Какие инсайты можно получить из этой визуализации\n\n"
            f"Сводные данные:\n{summary_data}\n\n"
            f"Все метаданные из отзывов:\n{all_metadata}\n\n"
        )

        # Логируем сформированный запрос
        self._log_to_file("gpt_prompt_log.txt", prompt)

        # Отправляем запрос к GPT
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты опытный аналитик данных, специализирующийся на визуализации данных."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Получаем результат анализа
        result = response.choices[0].message.content
        
        # Сохраняем результат в файл
        self._log_to_file("gpt_response.json", result)
        
        # Возвращаем результат анализа
        return result

    def analyze_batch(self, batch: List[Dict[str, Any]], batch_idx: int) -> Dict[str, Any]:
        """
        Анализирует одну партию отзывов с помощью GPT.

        Args:
            batch: Список отзывов в партии.
            batch_idx: Индекс партии.

        Returns:
            Результаты анализа партии.
        """
        # Формируем данные для GPT
        data = {
            "batch_idx": batch_idx,
            "reviews": [
                {
                    "review_idx": review.get("review_idx"),
                    "meta": review.get("meta", {}),
                    "raw_analysis": review.get("raw_analysis", ""),
                    "raw_response": review.get("raw_response", "")
                }
                for review in batch
            ]
        }

        # Отправляем данные в GPT
        response = openai.ChatCompletion.create(
            model="gpt-4-mini",
            messages=[
                {"role": "system", "content": "Ты аналитик данных. Определи ключевые метаданные и подходящие графики для анализа."},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
            ]
        )

        # Извлекаем содержимое ответа
        result_content = json.loads(response["choices"][0]["message"]["content"])

        # Сохраняем ответ в файл
        output_file = f"analytics_output/batch_{batch_idx}_analysis.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_content, f, ensure_ascii=False, indent=4)

        # Возвращаем результат
        return result_content

    def analyze_hidden_patterns(self, reviews: List[Dict[str, Any]]) -> str:
        """
        Проводит глубокий анализ скрытых закономерностей и паттернов в отзывах.
        Применяет тематическую сегментацию для более эффективного анализа.
        """
        self.total_reviews = len(reviews)
        self.logger.info(f"Анализ скрытых закономерностей для {self.total_reviews} отзывов")

        # Установим реальное ограничение токенов
        # Для GPT-4-1106-preview оптимальный размер составляет около 25000 токенов
        # чтобы оставить место для ответа модели
        max_tokens_per_request = 25000
        
        # Агрегирование данных для анализа с сохранением полного текста каждого отзыва
        aggregated_data = self._aggregate_reviews_data(reviews)
        
        # Выполняем подсчет токенов
        aggregated_json = json.dumps(aggregated_data, ensure_ascii=False)
        tokens_count = 0
        
        if TIKTOKEN_AVAILABLE:
            try:
                tokenizer = tiktoken.get_encoding("cl100k_base")
                tokens_count = len(tokenizer.encode(aggregated_json))
                self.logger.info(f"Размер агрегированных данных: {tokens_count} токенов (точная оценка)")
            except Exception as e:
                self.logger.error(f"Ошибка при инициализации токенизатора: {str(e)}")
                tokens_count = len(aggregated_json) // 3
                self.logger.info(f"Размер агрегированных данных: {tokens_count} токенов (приблизительная оценка)")
        else:
            tokens_count = len(aggregated_json) // 3
            self.logger.info(f"Размер агрегированных данных: {tokens_count} токенов (приблизительная оценка)")

        # Применяем тематическую сегментацию, если данные превышают лимит токенов
        if tokens_count > max_tokens_per_request:
            self.logger.info(f"Размер данных превышает лимит ({max_tokens_per_request} токенов). Применяем тематическую сегментацию.")
            return self._analyze_with_thematic_segmentation(aggregated_data, max_tokens_per_request)
        else:
            self.logger.info("Анализ данных в одном запросе")
            return self._analyze_data_with_gpt(aggregated_data)

    def _analyze_with_thematic_segmentation(self, data: Dict[str, Any], max_tokens: int) -> str:
        """
        Проводит анализ с применением тематической сегментации для больших объемов данных.
        Включает улучшенное балансирование групп по размеру и объединение маленьких групп.
        Гарантирует, что каждый отзыв анализируется только один раз.
        """
        # Базовая информация о всех отзывах (всегда включается в каждый запрос)
        base_info = {
            "total_reviews": data["total_reviews"],
            "ratings_distribution": data["ratings_distribution"],
            "average_rating": data["average_rating"]
        }
        
        # Извлекаем все отзывы и их тексты
        all_reviews = data.get("all_review_texts", [])
        
        # Множество для отслеживания уже распределенных отзывов
        used_review_indices = set()
        
        # Извлекаем топ-темы из данных
        top_themes = {}
        if "top_topics" in data:
            # Берем самые популярные темы
            top_themes = dict(sorted(data["top_topics"].items(), 
                                    key=lambda item: item[1], 
                                    reverse=True)[:30])
        
        # Создаем тематические группы
        thematic_groups = []
        
        # 1. Распределяем отзывы по темам, гарантируя, что каждый отзыв используется только один раз
        for theme, count in top_themes.items():
            theme_group = {
                "name": theme,
                "reviews": []
            }
            
            # Проходим по всем отзывам и ищем подходящие для темы
            for i, review_text in enumerate(all_reviews):
                # Пропускаем уже использованные отзывы
                if i in used_review_indices:
                    continue
                
                # Проверяем, соответствует ли отзыв теме
                if theme.lower() in review_text.lower():
                    theme_group["reviews"].append(review_text)
                    used_review_indices.add(i)
                    
                    # Ограничиваем количество отзывов на тему для контроля размера группы
                    if len(theme_group["reviews"]) >= 50:  # Максимум 50 отзывов на тему
                        break
            
            # Если для темы найдены отзывы, добавляем группу
            if theme_group["reviews"]:
                theme_data = base_info.copy()
                theme_data["analysis_focus"] = f"Тематическая группа: {theme}"
                theme_data["top_topics"] = {theme: count}
                theme_data["review_texts_for_theme"] = theme_group["reviews"]
                
                # Оцениваем токены перед добавлением группы
                theme_json = json.dumps(theme_data, ensure_ascii=False)
                token_count = len(theme_json) // 3  # Примерная оценка
                
                # Проверяем размер токенов для группы
                if token_count < max_tokens:
                    thematic_groups.append((theme_data, token_count, len(theme_group["reviews"])))
        
        # 2. Распределяем оставшиеся отзывы по другим критериям
        remaining_reviews = [review for i, review in enumerate(all_reviews) if i not in used_review_indices]
        
        # Если остались нераспределенные отзывы, создаем для них группы
        if remaining_reviews:
            # Группируем по рейтингам
            rating_groups = defaultdict(list)
            for review in remaining_reviews:
                # Извлекаем рейтинг из текста отзыва
                rating_match = re.search(r'\[Рейтинг: (\d+\.\d+)\]', review)
                if rating_match:
                    rating = float(rating_match.group(1))
                    rating_int = int(rating)
                    rating_groups[rating_int].append(review)
            
            # Создаем группы по рейтингам
            for rating, reviews in rating_groups.items():
                if reviews:  # Если есть отзывы для этого рейтинга
                    rating_data = base_info.copy()
                    rating_data["analysis_focus"] = f"Группа отзывов с рейтингом {rating} звезд"
                    rating_data["review_texts_for_rating"] = reviews[:100]  # Ограничиваем для контроля размера
                    
                    # Оцениваем токены
                    rating_json = json.dumps(rating_data, ensure_ascii=False)
                    token_count = len(rating_json) // 3
                    
                    if token_count < max_tokens:
                        thematic_groups.append((rating_data, token_count, len(reviews[:100])))
        
        # 3. Сортируем группы по размеру токенов для лучшего управления
        thematic_groups.sort(key=lambda x: x[1])
        
        # 4. Объединяем маленькие группы для эффективного использования токенов
        final_groups = []
        current_group = None
        current_token_count = 0
        current_reviews_count = 0
        
        for group_data, token_count, reviews_count in thematic_groups:
            # Если группа слишком мала, пытаемся объединить с другими
            if token_count < max_tokens * 0.1:  # Маленькие группы < 10% от максимума
                self.logger.info(f"Группа '{group_data['analysis_focus']}' слишком мала ({token_count} токенов), буфферизуем для объединения")
                
                # Если текущей группы нет, создаем новую
                if current_group is None:
                    current_group = group_data
                    current_token_count = token_count
                    current_reviews_count = reviews_count
                else:
                    # Объединяем фокусы анализа
                    themes = [current_group["analysis_focus"].replace("Тематическая группа: ", ""),
                              group_data["analysis_focus"].replace("Тематическая группа: ", "")]
                    new_focus = f"Тематические группы: {', '.join(themes)}"
                    
                    # Объединяем отзывы
                    combined_reviews = []
                    if "review_texts_for_theme" in current_group:
                        combined_reviews.extend(current_group["review_texts_for_theme"])
                    if "review_texts_for_rating" in current_group:
                        combined_reviews.extend(current_group["review_texts_for_rating"])
                    if "review_texts_for_theme" in group_data:
                        combined_reviews.extend(group_data["review_texts_for_theme"])
                    if "review_texts_for_rating" in group_data:
                        combined_reviews.extend(group_data["review_texts_for_rating"])
                    
                    # Обновляем текущую группу
                    current_group = base_info.copy()
                    current_group["analysis_focus"] = new_focus
                    
                    # Обновляем темы
                    current_topics = current_group.get("top_topics", {})
                    current_topics.update(group_data.get("top_topics", {}))
                    if current_topics:
                        current_group["top_topics"] = current_topics
                    
                    # Добавляем объединенные отзывы
                    if combined_reviews:
                        current_group["review_texts_for_themes"] = combined_reviews
                    
                    # Пересчитываем токены и количество отзывов
                    current_json = json.dumps(current_group, ensure_ascii=False)
                    current_token_count = len(current_json) // 3
                    current_reviews_count += reviews_count
                
                # Если объединенная группа достигла оптимального размера, добавляем ее к финальным
                if current_token_count >= max_tokens * 0.5 or current_reviews_count >= 100:
                    final_groups.append(current_group)
                    current_group = None
                    current_token_count = 0
                    current_reviews_count = 0
            else:
                # Группа достаточно большая, добавляем как есть
                final_groups.append(group_data)
        
        # Добавляем последнюю объединенную группу, если она осталась
        if current_group is not None:
            final_groups.append(current_group)
        
        # 5. Проверяем, все ли отзывы распределены
        distributed_reviews_count = sum(
            len(group.get("review_texts_for_theme", [])) + 
            len(group.get("review_texts_for_rating", [])) + 
            len(group.get("review_texts_for_themes", []))
            for group in final_groups
        )
        
        # Если остались нераспределенные отзывы, создаем для них отдельную группу
        if distributed_reviews_count < len(all_reviews):
            self.logger.info(f"Распределено {distributed_reviews_count} из {len(all_reviews)} отзывов. Создаем дополнительную группу для оставшихся.")
            
            remaining_group = base_info.copy()
            remaining_group["analysis_focus"] = "Анализ оставшихся отзывов"
            remaining_group["review_texts"] = [review for i, review in enumerate(all_reviews) 
                                              if i not in used_review_indices][:100]  # Ограничиваем для контроля размера
            final_groups.append(remaining_group)
        
        # 6. Анализируем каждую группу отдельно
        self.logger.info(f"Создано {len(final_groups)} тематических групп для анализа")
        results = []
        total_analyzed_reviews = 0
        
        for i, group_data in enumerate(final_groups):
            self.logger.info(f"Анализ группы {i+1} из {len(final_groups)}: {group_data['analysis_focus']}")
            
            # Подсчитываем отзывы в этой группе
            group_reviews_count = (
                len(group_data.get("review_texts_for_theme", [])) + 
                len(group_data.get("review_texts_for_rating", [])) + 
                len(group_data.get("review_texts_for_themes", [])) +
                len(group_data.get("review_texts", []))
            )
            total_analyzed_reviews += group_reviews_count
            
            # Анализируем группу
            group_result = self._analyze_data_with_gpt(group_data)
            results.append(group_result)
        
        # 7. Объединяем результаты анализа
        final_result = self._synthesize_segmented_results(results)
        
        # Добавляем информацию о полноте анализа
        final_result += f"\n\n### Статистика анализа\nВсего проанализировано {total_analyzed_reviews} из {len(all_reviews)} отзывов в {len(final_groups)} тематических группах."
        
        return final_result

    def _synthesize_segmented_results(self, results: List[str]) -> str:
        """
        Объединяет результаты тематического анализа в единый детальный отчет.
        После синтеза также генерирует рекомендации по визуализациям на основе финального анализа.
        """
        # Проверяем, что у нас есть хотя бы один результат
        if not results:
            return "Не удалось выполнить анализ: отсутствуют результаты по группам."
        
        # Если только один результат, возвращаем его
        if len(results) == 1:
            final_synthesis = results[0]
        else:
            # Объединяем все результаты с сохранением структуры и разделением
            combined_results = "\n\n===== РЕЗУЛЬТАТЫ ТЕМАТИЧЕСКОГО АНАЛИЗА =====\n\n" + "\n\n----- СЛЕДУЮЩАЯ ТЕМАТИЧЕСКАЯ ГРУППА -----\n\n".join(results)
            
            # Сохраняем промежуточные результаты для отладки
            with open("combined_group_results.txt", "w", encoding="utf-8") as f:
                f.write(combined_results)
            
            # Создаем запрос для финального синтеза
            synthesis_prompt = """
            Ты опытный аналитик данных и специалист по визуализации. Тебе предоставлены результаты анализа отзывов, 
            разбитые на тематические группы. Твоя задача - создать единый аналитический отчет высокого качества с 
            акцентом на конкретные визуализируемые метрики, который:
            
            1. Объединит все значимые количественные и качественные данные из разных групп
            2. Выявит взаимосвязи между различными аспектами продукта
            3. Представит глубокие инсайты, подкрепленные конкретными числовыми данными
            
            Структура отчета должна включать:
            
            ## 1. Общий обзор ключевых метрик и закономерностей
            Представь основные количественные показатели и их значение.
            
            ## 2. Факторы, влияющие на удовлетворенность пользователей
            Объедини данные о факторах влияния из всех групп, укажи конкретные цифры и проценты.
            
            ## 3. Взаимосвязи между темами и оценками
            Приведи конкретные корреляции и зависимости в числовой форме.
            
            ## 4. Часто упоминаемые проблемы и их влияние
            Проранжируй проблемы по частоте и серьезности, используя числовые данные.
            
            ## 5. Скрытые паттерны в отзывах
            Выдели обнаруженные закономерности с подтверждающими их количественными показателями.
            
            ## 6. Рекомендации по визуализациям
            Предложи конкретные визуализации на основе проанализированных данных:
            - Для каждой визуализации: тип диаграммы, конкретные данные для осей/категорий, ожидаемые инсайты
            - Используй конкретные числовые данные из анализа
            - Предложи столько визуализаций, сколько считаешь необходимым для полного представления данных
            
            ## 7. Итоговые рекомендации
            Предложи конкретные действия на основе анализа всех данных.
            
            Важно: сосредоточься на конкретных, визуализируемых метриках и числовых данных, 
            избегая общих формулировок.
            """
            
            try:
                # Отправляем запрос к GPT для финального синтеза
                response = self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "Ты аналитик данных и специалист по визуализации, создающий детальные отчеты с конкретными метриками и рекомендациями по визуализациям."},
                        {"role": "user", "content": synthesis_prompt + f"\n\nРезультаты анализа по группам:\n\n{combined_results}"}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                
                final_synthesis = response.choices[0].message.content
                
                # Добавляем информацию о методе анализа
                final_synthesis += "\n\n### Примечание по методологии\nДанный анализ выполнен с использованием тематической сегментации для обеспечения полноты и глубины обработки всех отзывов, с особым акцентом на извлечение конкретных, визуализируемых метрик."
                
            except Exception as e:
                error_message = f"Ошибка при синтезе результатов: {str(e)}"
                self.logger.error(error_message)
                
                # В случае ошибки возвращаем все результаты последовательно с пометкой
                final_synthesis = f"ОШИБКА СИНТЕЗА: {error_message}\n\nНиже представлены результаты анализа каждой группы без синтеза:\n\n" + combined_results
        
        # Сохраняем финальный синтез в файл
        with open("final_synthesis_result.txt", "w", encoding="utf-8") as f:
            f.write(final_synthesis)
        
        # Генерируем расширенные рекомендации по визуализациям на основе финального анализа
        visualization_recommendations = self.generate_visualization_recommendations(final_synthesis)
            
        return final_synthesis

    def generate_visualization_recommendations(self, final_analysis: str) -> str:
        """
        Генерирует рекомендации по визуализациям на основе полного анализа отзывов.
        Использует результаты глубокого анализа всех тематических групп для создания
        конкретных, основанных на данных рекомендаций по визуализациям.
        
        Args:
            final_analysis: Результат финального синтеза анализа всех тематических групп.
            
        Returns:
            Детальные рекомендации по визуализациям с конкретными данными.
        """
        # Собираем все файлы с результатами анализа тематических групп
        analysis_files = glob.glob("analysis_result_*.txt")
        
        # Извлекаем предложения по визуализациям из всех файлов анализа
        all_visualizations = []
        for file_path in analysis_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Ищем разделы с визуализациями
                    viz_sections = re.findall(r'##?\s*\d*\.*\s*(Предложени[яе] по визуализаци[яи]м|Визуализаци[яи]|Рекомендации по визуализаци[яи]м).*?\n(.*?)(?=\n##?\s|\n---|\Z)', 
                                              content, re.DOTALL)
                    
                    # Извлекаем отдельные визуализации из найденных разделов
                    for _, section_content in viz_sections:
                        # Ищем отдельные визуализации
                        individual_viz = re.findall(r'(###?\s*\d*\.*\d*\.*\s*.*?:|#### Визуализация \d+:|#### [^:]+:|### \d+\.\d+\.|[•*-]\s*\*\*Тип.*?:)[^#]+?(?=###?\s|\*\*Тип|\n\n[•*-]\s*\*\*Тип|\Z)', 
                                                  section_content, re.DOTALL)
                        all_visualizations.extend(individual_viz)
            except Exception as e:
                self.logger.warning(f"Ошибка при обработке файла {file_path}: {str(e)}")
        
        # Формируем запрос для GPT для создания улучшенных рекомендаций по визуализациям
        prompt = f"""
        Ты опытный аналитик данных и специалист по визуализации. На основе предоставленного финального анализа отзывов и 
        извлеченных предложений по визуализациям, создай детальные рекомендации по визуализациям с конкретными данными.
        
        Твоя задача:
        
        1. Собрать и объединить все предложения по визуализациям, исключив дублирование
        2. Ранжировать их по информационной ценности и значимости для бизнеса
        3. Для КАЖДОЙ визуализации указать:
           - Тип диаграммы/графика (с обоснованием выбора)
           - КОНКРЕТНЫЕ данные, которые должны быть отражены (с числовыми показателями из анализа)
           - Какие инсайты эта визуализация должна показать
           - Как эта визуализация поможет в принятии бизнес-решений
        
        ВАЖНО:
        - НЕ ограничивай количество визуализаций искусственно, предлагай столько, сколько действительно полезно
        - Используй ТОЛЬКО конкретные данные из анализа (не упоминай визуализации без конкретных данных)
        - Для КАЖДОЙ визуализации укажи конкретные числовые показатели (проценты, частоты, средние значения)
        - Убедись, что каждая визуализация дает уникальную информацию, не повторяющуюся в других
        
        Финальный анализ отзывов:
        {final_analysis}
        
        Извлеченные предложения по визуализациям:
        {all_visualizations}
        """
        
        # Сохраняем промпт для отладки
        self._log_to_file("visualization_recommendations_prompt.txt", prompt)
        
        try:
            # Отправляем запрос к GPT
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Ты опытный аналитик данных и специалист по визуализации данных, ориентированный на конкретные, основанные на данных рекомендации."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Получаем результат
            visualization_recommendations = response.choices[0].message.content
            
            # Сохраняем результат в файл
            with open("visualization_recommendations.txt", "w", encoding="utf-8") as f:
                f.write(visualization_recommendations)
            
            return visualization_recommendations
            
        except Exception as e:
            error_message = f"Ошибка при генерации рекомендаций по визуализациям: {str(e)}"
            self.logger.error(error_message)
            return error_message

    def _aggregate_reviews_data(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Агрегирует данные отзывов для анализа, сохраняя полные тексты всех отзывов.
        """
        ratings = []
        topics_frequency = Counter()
        pros_by_rating = defaultdict(list)
        cons_by_rating = defaultdict(list)
        all_review_texts = []
        
        for review in reviews:
            # Рейтинг
            rating = review.get("rating")
            if rating:
                rating_val = float(rating)
                ratings.append(rating_val)
                rating_group = round(rating_val)
            else:
                rating_group = None
                
            # Темы
            topics = []
            if "all_topics" in review and review["all_topics"]:
                topics = review["all_topics"]
                for topic in topics:
                    topics_frequency[topic] += 1
            
            # Достоинства
            if "pros" in review and review["pros"]:
                pros = review["pros"]
                if isinstance(pros, list):
                    for item in pros:
                        pros_by_rating[rating_group].append(item)
                elif isinstance(pros, str) and pros.strip():
                    pros_by_rating[rating_group].append(pros.strip())
            
            # Недостатки
            if "cons" in review and review["cons"]:
                cons = review["cons"]
                if isinstance(cons, list):
                    for item in cons:
                        cons_by_rating[rating_group].append(item)
                elif isinstance(cons, str) and cons.strip():
                    cons_by_rating[rating_group].append(cons.strip())
            
            # Полный текст отзыва (с рейтингом для контекста)
            review_text = ""
            if "combined_text" in review and review["combined_text"]:
                review_text = f"[Рейтинг: {rating}] {review['combined_text']}"
                all_review_texts.append(review_text)
        
        # Формируем структуру данных для анализа
        result = {
            "total_reviews": len(reviews),
            "ratings_distribution": dict(Counter([round(r) for r in ratings])) if ratings else {},
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "top_topics": dict(topics_frequency.most_common()),
            "all_review_texts": all_review_texts,
            "pros_by_rating": {k: v for k, v in pros_by_rating.items()},
            "cons_by_rating": {k: v for k, v in cons_by_rating.items()}
        }
        
        return result

    def _analyze_data_with_gpt(self, data: Dict[str, Any]) -> str:
        """
        Отправляет данные в GPT для анализа с акцентом на извлечение визуализируемых метрик.
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
        log_file = f"analysis_query_{self.slugify(analysis_focus)}.txt"
        self._log_to_file(log_file, instructions + example_reviews + f"\n\nПолные данные для анализа:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
        
        try:
            # Отправляем запрос к GPT
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Ты аналитик данных, специализирующийся на извлечении конкретных, визуализируемых метрик из текстовых отзывов."},
                    {"role": "user", "content": instructions + f"\nДанные для анализа:\n{json.dumps(data, ensure_ascii=False, indent=2)}"}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            
            # Логируем ответ
            result_log_file = f"analysis_result_{self.slugify(analysis_focus)}.txt"
            self._log_to_file(result_log_file, result)
            
            return result
        
        except Exception as e:
            error_message = f"Ошибка при анализе данных: {str(e)}"
            self.logger.error(error_message)
            return error_message

    def _log_to_file(self, filename: str, content: str):
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