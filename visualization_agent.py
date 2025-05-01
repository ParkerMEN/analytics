import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
import openai
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class VisualizationAgent:
    """
    Агент для создания визуализаций на основе данных отзывов и рекомендаций GPT.
    Генерирует готовый код для создания визуализаций и сохраняет его в файлы.
    """

    def __init__(self, api_key: str, output_dir: str = "analytics_output/visualizations"):
        """
        Инициализирует агент визуализации.

        Args:
            api_key: API ключ для OpenAI.
            output_dir: Директория для сохранения визуализаций.
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.output_dir = output_dir
        self.ensure_directories()
        
        # Настройка логирования
        self.logger = logging.getLogger('VisualizationAgent')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Создаем файл журнала в директории output
        file_handler = logging.FileHandler(os.path.join(output_dir, "visualization_agent.log"), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

    def ensure_directories(self):
        """Создает необходимые директории, если они не существуют."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "code"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "reports"), exist_ok=True)

    async def generate_visualizations_async(self, data: List[Dict[str, Any]], recommendations: str = None, 
                                     analysis_file: str = "analysis_results/hidden_patterns_analysis.txt"):
        """
        Асинхронно генерирует визуализации на основе данных и рекомендаций.
        """
        # Загружаем рекомендации от GPT, если они не предоставлены
        if not recommendations:
            try:
                recommendations_file = "visualization_recommendations.txt"
                if os.path.exists(recommendations_file):
                    with open(recommendations_file, "r", encoding="utf-8") as f:
                        recommendations = f.read()
                else:
                    self.logger.warning(f"Файл рекомендаций {recommendations_file} не найден, используем файл анализа")
            except Exception as e:
                self.logger.error(f"Ошибка при чтении рекомендаций: {str(e)}")
        
        # Загружаем анализ GPT
        analysis_text = ""
        try:
            if os.path.exists(analysis_file):
                with open(analysis_file, "r", encoding="utf-8") as f:
                    analysis_text = f.read()
        except Exception as e:
            self.logger.error(f"Ошибка при чтении анализа: {str(e)}")
        
        # Извлекаем предложения по визуализациям из рекомендаций или анализа
        visualization_tasks = self._extract_visualization_tasks(recommendations or analysis_text)
        
        # Подготавливаем метаданные для визуализаций
        metadata = self._prepare_metadata(data)
        
        # Асинхронно генерируем код для каждой визуализации
        tasks = []
        for idx, task in enumerate(visualization_tasks, 1):
            tasks.append(self._generate_visualization_code_async(task, metadata, data, idx, len(visualization_tasks)))
        
        # Запускаем все задачи одновременно и ждем их завершения
        results = await asyncio.gather(*tasks)
        
        # Обрабатываем результаты
        generated_files = []
        
        for task, idx, code, report in results:
            try:
                # Сохраняем код в файл
                code_filename = self._safe_filename(f"viz_{idx}_{task.get('title', 'visualization')}.py")
                code_path = os.path.join(self.output_dir, "code", code_filename)
                with open(code_path, "w", encoding="utf-8") as f:
                    f.write(code)
                
                # Сохраняем отчет в файл
                report_filename = self._safe_filename(f"report_{idx}_{task.get('title', 'visualization')}.md")
                report_path = os.path.join(self.output_dir, "reports", report_filename)
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report)
                
                generated_files.append(code_path)
                self.logger.info(f"Создан файл визуализации: {code_path}")
            except Exception as e:
                self.logger.error(f"Ошибка при сохранении файлов визуализации {idx}: {str(e)}")
        
        # Создаем индексный файл со всеми визуализациями
        self._create_index_file(visualization_tasks, generated_files)
        
        return generated_files

    def generate_visualizations(self, data: List[Dict[str, Any]], recommendations: str = None, 
                              analysis_file: str = "analysis_results/hidden_patterns_analysis.txt"):
        """
        Обертка для асинхронной функции, чтобы сохранить совместимость кода.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Если цикла событий нет, создаем новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.generate_visualizations_async(data, recommendations, analysis_file))

    async def _generate_visualization_code_async(self, task: Dict[str, str], metadata: Dict[str, Any], 
                                    raw_data: List[Dict[str, Any]], idx: int, total: int) -> tuple:
        """
        Асинхронная версия метода генерации кода для визуализации.
        """
        try:
            self.logger.info(f"Генерация кода для визуализации {idx}/{total}: {task.get('title', 'Без названия')}")
            self.logger.info(f"Отправка запроса к GPT для генерации кода визуализации: {task['title']}")
            
            # Используем то же содержимое, что и в синхронной версии
            prompt = f"""
            Создай готовый к выполнению Python-код для интерактивной визуализации данных отзывов с использованием plotly и matplotlib.
            
            ИНФОРМАЦИЯ О ВИЗУАЛИЗАЦИИ:
            Название: {task['title']}
            Тип: {task['type']}
            Описание: {task['description']}
            Данные для визуализации: {task['data']}
            Ожидаемые инсайты: {task['insights']}
            
            МЕТАДАННЫЕ ДЛЯ ВИЗУАЛИЗАЦИИ:
            Всего отзывов: {metadata['total_reviews']}
            Средний рейтинг: {metadata['average_rating']}
            Распределение рейтингов: {json.dumps(metadata['ratings_distribution'], ensure_ascii=False)}
            Частота тем: {json.dumps({k: v for k, v in sorted(metadata['topics_frequency'].items(), key=lambda item: item[1], reverse=True)[:15]}, ensure_ascii=False)}
            
            ТРЕБОВАНИЯ К КОДУ:
            1. Код должен использовать plotly для создания интерактивной визуализации.
            2. В коде должно быть две основные части: 
               a) Подготовка данных
               b) Создание визуализации с plotly Express или Graph Objects
            3. Используй русский язык для подписей, заголовков и легенд.
            4. Обеспечь высокое качество и читаемость визуализации.
            5. Предусмотри обработку краевых случаев (например, отсутствие данных).
            6. Добавь интерактивные элементы для исследования данных (наведение, зум, фильтрация).
            7. Добавь комментарии, объясняющие ключевые шаги в коде.
            8. Сохраняй визуализацию в двух форматах:
               - PNG для статической версии: '{self.output_dir}/viz_{task["title"].split(":")[0].strip()}.png'
               - HTML для интерактивной версии: '{self.output_dir}/viz_{task["title"].split(":")[0].strip()}.html'
            9. Для HTML обязательно используй современный метод с CDN:
               ```
               fig.write_html(
                   "output.html",
                   include_plotlyjs="cdn",  # Используй CDN вместо встраивания plotly.js
                   full_html=True,  # Создавай полноценный HTML
                   config={{"displayModeBar": True, "responsive": True}}  # Добавь панель инструментов и адаптивность
               )
               ```
            10. ОЧЕНЬ ВАЖНО: Интерактивный HTML должен открываться и работать автономно в любом браузере.
            
            ФОРМАТ ОТВЕТА:
            Предоставь код в таком формате:
            
            ```python
            # Здесь код для визуализации
            ```
            
            ОТЧЕТ:
            Здесь подробный отчет о визуализации, включающий:
            - Обоснование выбора типа визуализации
            - Ключевые инсайты из данных
            - Рекомендации по интерпретации визуализации
            """
            
            # Делаем запрос к API через ThreadPoolExecutor, чтобы избежать блокировки
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(
                    executor,
                    lambda: self.client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {"role": "system", "content": "Ты опытный специалист по анализу данных и визуализации, создающий интерактивные визуализации на Python для анализа отзывов."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=3000
                    )
                )
                
            response_text = response.choices[0].message.content
            self.logger.debug(f"Получен ответ от GPT для визуализации {task['title']}")
            
            # Извлекаем код и отчет
            code_match = re.search(r'```python(.*?)```', response_text, re.DOTALL)
            code = code_match.group(1).strip() if code_match else ""
            
            # Если код не найден, пробуем другой формат
            if not code:
                code_match = re.search(r'```(.*?)```', response_text, re.DOTALL)
                code = code_match.group(1).strip() if code_match else ""
            
            # Если код все еще не найден, берем весь ответ
            if not code:
                code = "# Не удалось извлечь код\n# Полный ответ GPT:\n\n" + response_text
            
            # Обеспечиваем использование CDN для Plotly
            if "fig.write_html" in code and "include_plotlyjs" not in code:
                code = code.replace("fig.write_html(", "fig.write_html(", 1)
                code = code.replace("fig.write_html(", 
                                    "fig.write_html(", 1)
                code += "\n\n# Добавлено для обеспечения корректной работы интерактивных визуализаций\n"
                code += "if 'fig' in locals():\n"
                code += "    fig.write_html(\n"
                code += f"        '{self.output_dir}/viz_" + "{task['title'].split(':')[0].strip()}.html',\n"
                code += "        include_plotlyjs='cdn',\n"
                code += "        full_html=True,\n"
                code += "        config={'displayModeBar': True, 'responsive': True}\n"
                code += "    )\n"
            
            # Извлекаем отчет
            report_match = re.search(r'ОТЧЕТ:(.*?)$', response_text, re.DOTALL)
            report = report_match.group(1).strip() if report_match else ""
            
            # Если отчет не найден, создаем его из описания визуализации
            if not report:
                report = f"# Отчет по визуализации: {task['title']}\n\n"
                report += f"## Тип визуализации\n{task['type']}\n\n"
                report += f"## Описание\n{task['description']}\n\n"
                report += f"## Ожидаемые инсайты\n{task['insights']}\n\n"
                report += "## Примечание\nОтчет сгенерирован автоматически на основе описания визуализации."
            
            return task, idx, code, report
                
        except Exception as e:
            self.logger.error(f"Ошибка при генерации кода визуализации {idx}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Возвращаем шаблонный код и отчет в случае ошибки
            return task, idx, self._generate_fallback_code(task, metadata), self._generate_fallback_report(task)

    def _extract_visualization_tasks(self, text: str) -> List[Dict[str, str]]:
        """
        Извлекает задачи для создания визуализаций из текста рекомендаций или анализа.
        """
        tasks = []
        
        # Шаблон для формата "## Визуализация N. Название"
        sections = re.findall(r'## Визуализация (\d+)\.\s+(.*?)(?=(?:## Визуализация \d+\.)|$)', text, re.DOTALL)
        
        if not sections:
            # Шаблон для формата "## N. Визуализация №N: Название"
            sections = re.findall(r'## \d+\.\s+Визуализация №\d+:\s+(.*?)(?=(?:## \d+\.)|$)', text, re.DOTALL)
        
        if sections:
            for section_num, section in enumerate(sections, 1):
                section_content = section
                if isinstance(section, tuple):
                    section_content = section[1]  # Для первого шаблона берем содержимое секции
                    
                task = {
                    "title": "",
                    "type": "",
                    "description": section_content.strip(),
                    "data": "",
                    "insights": ""
                }
                
                # Извлекаем заголовок
                title_match = re.search(r'^(.*?)$', section_content.strip(), re.MULTILINE)
                if title_match:
                    task["title"] = title_match.group(1).strip()
                
                # Извлекаем тип диаграммы
                type_match = re.search(r'\*\*Тип:\*\*\s*(.*?)(?=\*\*|\n|$)', section_content, re.DOTALL)
                if not type_match:
                    type_match = re.search(r'[*-]\s*\*\*Тип(?:\sдиаграммы)?:\*\*\s*(.*?)(?=\*\*|\n|$)', section_content, re.DOTALL)
                
                if type_match:
                    task["type"] = type_match.group(1).strip()
                
                # Извлекаем данные
                data_match = re.search(r'\*\*Данные:\*\*\s*(.*?)(?=\*\*|\n\n|$)', section_content, re.DOTALL)
                if data_match:
                    task["data"] = data_match.group(1).strip()
                
                # Извлекаем инсайты
                insights_match = re.search(r'\*\*Инсайты:\*\*\s*(.*?)(?=\*\*|\n\n|$)', section_content, re.DOTALL)
                if not insights_match:
                    insights_match = re.search(r'\*\*(?:Инсайты|Бизнес-польза):\*\*\s*(.*?)(?=\*\*|\n\n|$)', section_content, re.DOTALL)
                
                if insights_match:
                    task["insights"] = insights_match.group(1).strip()
                
                tasks.append(task)
        
        # Если не найдены секции, попробуем извлечь через другие шаблоны
        if not tasks:
            # Поиск по разделам с markdown заголовками
            headers = re.findall(r'(?:###|##)\s*(.*?)\n(.*?)(?=(?:###|##)|$)', text, re.DOTALL)
            for title, content in headers:
                if "визуализаци" in title.lower():
                    task = {
                        "title": title.strip(),
                        "type": "",
                        "description": content.strip(),
                        "data": "",
                        "insights": ""
                    }
                    
                    # Извлекаем тип
                    type_match = re.search(r'\*\*Тип(?:\sдиаграммы)?:\*\*\s*(.*?)(?=\n|$)', content)
                    if type_match:
                        task["type"] = type_match.group(1).strip()
                    
                    # Извлекаем данные
                    data_match = re.search(r'\*\*Данные:\*\*\s*(.*?)(?=\*\*|\n\n|$)', content, re.DOTALL)
                    if data_match:
                        task["data"] = data_match.group(1).strip()
                    
                    # Извлекаем инсайты
                    insights_match = re.search(r'\*\*(?:Инсайты|Бизнес-польза):\*\*\s*(.*?)(?=\*\*|\n\n|$)', content, re.DOTALL)
                    if insights_match:
                        task["insights"] = insights_match.group(1).strip()
                    
                    tasks.append(task)
        
        # Если все еще не найдены визуализации, используем формат из файла visualization_recommendations.txt
        if not tasks:
            sections = re.findall(r'## Визуализация (\d+)\.\s+(.*?)(?=(?:## Визуализация \d+\.)|$)', text, re.DOTALL)
            if not sections:
                sections = re.findall(r'## \d+\.\s+(.*?)(?=(?:## \d+\.)|$)', text, re.DOTALL)
            
            for section in sections:
                section_content = section
                if isinstance(section, tuple):
                    section_content = section[1]
                
                title = ""
                title_match = re.search(r'^(.*?)$', section_content.strip(), re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                
                task = {
                    "title": title,
                    "type": "",
                    "description": section_content.strip(),
                    "data": "",
                    "insights": ""
                }
                
                # Тип
                type_match = re.search(r'- \*\*Тип:\*\*\s*(.*?)(?=\n|$)', section_content)
                if not type_match:
                    type_match = re.search(r'- \*\*Тип диаграммы:\*\*\s*(.*?)(?=\n|$)', section_content)
                
                if type_match:
                    task["type"] = type_match.group(1).strip()
                
                # Данные
                data_match = re.search(r'- \*\*Данные:\*\*\s*(.*?)(?=(?:- \*\*)|$)', section_content, re.DOTALL)
                if data_match:
                    task["data"] = data_match.group(1).strip()
                
                # Инсайты
                insights_match = re.search(r'- \*\*Инсайты:\*\*\s*(.*?)(?=(?:- \*\*)|$)', section_content, re.DOTALL)
                if insights_match:
                    task["insights"] = insights_match.group(1).strip()
                
                tasks.append(task)
        
        # Если все равно не удалось найти визуализации, создаем общую задачу
        if not tasks:
            self.logger.warning("Не удалось извлечь конкретные задачи визуализации, создаем общую задачу")
            tasks.append({
                "title": "Общая визуализация данных отзывов",
                "type": "Комбинированная визуализация",
                "description": "Создать комплексную визуализацию на основе анализа отзывов",
                "data": "Все доступные метрики из анализа отзывов",
                "insights": "Выявление ключевых закономерностей и трендов в отзывах"
            })
        
        return tasks

    def _prepare_metadata(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Подготавливает метаданные для визуализации, включая динамическое выделение тематических групп
        """
        metadata = {}
        
        # Добавляем общее количество отзывов
        metadata['total_reviews'] = len(data)
        
        # Вычисляем средний рейтинг
        ratings = [float(review.get('rating', 0)) for review in data if review.get('rating') is not None]
        metadata['average_rating'] = round(sum(ratings) / len(ratings), 2) if ratings else 0
        
        # Вычисляем распределение рейтингов
        ratings_distribution = {}
        for rating in ratings:
            rating_key = str(int(rating) if rating == int(rating) else rating)
            if rating_key in ratings_distribution:
                ratings_distribution[rating_key] += 1
            else:
                ratings_distribution[rating_key] = 1
        metadata['ratings_distribution'] = ratings_distribution
        
        all_topics = []
        
        # Собираем все темы из отзывов
        for review in data:
            topics = review.get("topics", [])
            if topics:
                all_topics.extend(topics)
        
        # Подсчитываем частоту тем
        topics_freq = {}
        for topic in all_topics:
            if topic in topics_freq:
                topics_freq[topic] += 1
            else:
                topics_freq[topic] = 1
        
        # Сортируем темы по частоте
        sorted_topics = sorted(topics_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Группируем схожие темы с помощью семантического сходства
        topic_clusters = self._cluster_topics(sorted_topics)
        
        # Определяем оптимальное количество групп
        optimal_clusters = self._determine_optimal_clusters(topic_clusters)
        
        # Формируем итоговые тематические группы
        theme_groups = self._form_theme_groups(optimal_clusters, data)
        
        metadata['theme_groups'] = theme_groups
        metadata['topics_frequency'] = topics_freq
        
        return metadata

    def _cluster_topics(self, sorted_topics: List[Tuple[str, int]]) -> List[List[str]]:
        """
        Группирует темы по семантическому сходству
        """
        # Извлекаем только темы
        topics = [t[0] for t in sorted_topics]
        
        # Защита от пустых входных данных
        if not topics:
            return []
        
        # Используем модель для получения векторных представлений тем
        topic_embeddings = self._get_topic_embeddings(topics)
        
        # Защита от недостаточного количества тем для кластеризации
        if len(topics) <= 1:
            return [sorted_topics]  # Возвращаем все темы в одном кластере
        
        try:
            # Пробуем версию с metric
            clusters = AgglomerativeClustering(
                n_clusters=None, 
                distance_threshold=0.4,  
                metric='cosine',  # Используем metric вместо affinity
                linkage='average'
            ).fit(topic_embeddings)
        except TypeError:
            try:
                # Альтернативный вариант для старых версий
                clusters = AgglomerativeClustering(
                    n_clusters=min(10, len(topics) // 3 + 1),  # Динамическое число кластеров
                    linkage='average'
                ).fit(topic_embeddings)
            except Exception as e:
                # В крайнем случае, простая группировка
                self.logger.error(f"Ошибка при кластеризации: {str(e)}")
                return [[t] for t in sorted_topics[:15]]  # Берем топ-15 тем
        
        # Формируем кластеры тем
        try:
            topic_clusters = [[] for _ in range(max(clusters.labels_) + 1)]
            for i, label in enumerate(clusters.labels_):
                topic_clusters[label].append((topics[i], sorted_topics[i][1]))
            return topic_clusters
        except Exception as e:
            self.logger.error(f"Ошибка при формировании кластеров: {str(e)}")
            return [[t] for t in sorted_topics[:15]]  # Простая группировка при ошибке

    def _determine_optimal_clusters(self, topic_clusters: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Определяет оптимальное количество кластеров и их структуру
        """
        # Фильтруем малозначимые кластеры (содержащие мало тем или с низкой частотой)
        significant_clusters = []
        
        for cluster in topic_clusters:
            # Вычисляем общую частоту тем в кластере
            total_frequency = sum(t[1] for t in cluster)
            
            if total_frequency > 5 or len(cluster) > 2:  # Пороговые значения
                # Находим основную тему кластера (с максимальной частотой)
                main_topic = max(cluster, key=lambda x: x[1])[0]
                
                # Создаем представление кластера
                cluster_info = {
                    'main_topic': main_topic,
                    'topics': [t[0] for t in cluster],
                    'frequency': total_frequency
                }
                significant_clusters.append(cluster_info)
        
        # Сортируем кластеры по общей частоте
        significant_clusters.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Ограничиваем до разумного количества (например, 10-15)
        max_clusters = min(15, len(significant_clusters))
        return significant_clusters[:max_clusters]

    def _form_theme_groups(self, optimal_clusters: List[Dict[str, Any]], data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Формирует итоговые тематические группы на основе кластеров
        """
        theme_groups = []
        
        # Для каждого кластера
        for cluster in optimal_clusters:
            # Отбираем отзывы, относящиеся к темам данного кластера
            cluster_reviews = []
            for review in data:
                review_topics = set(review.get("topics", []))
                cluster_topics = set(cluster['topics'])
                
                if review_topics.intersection(cluster_topics):
                    cluster_reviews.append(review)
            
            # Если для кластера достаточно отзывов
            if len(cluster_reviews) >= 3:  # Минимальное количество отзывов для группы
                theme_group = {
                    'name': cluster['main_topic'].capitalize(),
                    'topics': cluster['topics'],
                    'reviews_count': len(cluster_reviews),
                    'avg_rating': sum(r.get('rating', 0) for r in cluster_reviews) / len(cluster_reviews) if cluster_reviews else 0,
                    'reviews': cluster_reviews
                }
                theme_groups.append(theme_group)
        
        return theme_groups

    def _get_topic_embeddings(self, topics: List[str]) -> np.ndarray:
        """
        Создает векторные представления тем для кластеризации.
        
        Args:
            topics: Список тем для векторизации
            
        Returns:
            Матрица векторных представлений
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Создаем векторизатор для преобразования тем в векторы
        # Используем символьные n-граммы для лучшей работы с коротким русским текстом
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',  # Анализ по n-граммам символов
            ngram_range=(2, 4),  # 2-4-граммы символов
            min_df=1,
            max_df=0.9
        )
        
        # Проверяем, есть ли темы для обработки
        if not topics:
            # Возвращаем пустую матрицу, если нет тем
            return np.array([])
        
        # Преобразуем темы в векторы
        X = vectorizer.fit_transform(topics)
        
        # Возвращаем плотную матрицу для использования в кластеризации
        return X.toarray()

    def _generate_visualization_code(self, task: Dict[str, str], metadata: Dict[str, Any], 
                                   raw_data: List[Dict[str, Any]]) -> tuple:
        """
        Генерирует код для создания визуализации на основе задачи и метаданных.
        
        Args:
            task: Задача визуализации.
            metadata: Метаданные для визуализации.
            raw_data: Исходные данные отзывов.
            
        Returns:
            tuple: (код визуализации, отчет по визуализации)
        """
        # Подготавливаем запрос к GPT для генерации кода визуализации
        prompt = f"""
        Создай готовый к выполнению Python-код для интерактивной визуализации данных отзывов с использованием plotly и matplotlib.
        
        ИНФОРМАЦИЯ О ВИЗУАЛИЗАЦИИ:
        Название: {task['title']}
        Тип: {task['type']}
        Описание: {task['description']}
        Данные для визуализации: {task['data']}
        Ожидаемые инсайты: {task['insights']}
        
        МЕТАДАННЫЕ ДЛЯ ВИЗУАЛИЗАЦИИ:
        Всего отзывов: {metadata['total_reviews']}
        Средний рейтинг: {metadata['average_rating']}
        Распределение рейтингов: {json.dumps(metadata['ratings_distribution'], ensure_ascii=False)}
        Частота тем: {json.dumps({k: v for k, v in sorted(metadata['topics_frequency'].items(), key=lambda item: item[1], reverse=True)[:15]}, ensure_ascii=False)}
        
        ТРЕБОВАНИЯ К КОДУ:
        1. Код должен использовать plotly для создания интерактивной визуализации.
        2. В коде должно быть две основные части: 
           a) Подготовка данных
           b) Создание визуализации с plotly Express или Graph Objects
        3. Используй русский язык для подписей, заголовков и легенд.
        4. Обеспечь высокое качество и читаемость визуализации.
        5. Предусмотри обработку краевых случаев (например, отсутствие данных).
        6. Добавь интерактивные элементы для исследования данных (наведение, зум, фильтрация).
        7. Добавь комментарии, объясняющие ключевые шаги в коде.
        8. Сохраняй визуализацию в двух форматах:
           - PNG для статической версии: '{self.output_dir}/viz_{task["title"].split(":")[0].strip()}.png'
           - HTML для интерактивной версии: '{self.output_dir}/viz_{task["title"].split(":")[0].strip()}.html'
        9. Для HTML обязательно используй современный метод с CDN:
           ```
           fig.write_html(
               "output.html",
               include_plotlyjs="cdn",  # Используй CDN вместо встраивания plotly.js
               full_html=True,  # Создавай полноценный HTML
               config={{"displayModeBar": True, "responsive": True}}  # Добавь панель инструментов и адаптивность
           )
           ```
        10. ОЧЕНЬ ВАЖНО: Интерактивный HTML должен открываться и работать автономно в любом браузере.
        
        ФОРМАТ ОТВЕТА:
        Предоставь код в таком формате:
        
        ```python
        # Здесь код для визуализации
        ```
        
        ОТЧЕТ:
        Здесь подробный отчет о визуализации, включающий:
        - Обоснование выбора типа визуализации
        - Ключевые инсайты из данных
        - Рекомендации по интерпретации визуализации
        """
        
        # Отправляем запрос к GPT
        try:
            self.logger.info(f"Отправка запроса к GPT для генерации кода визуализации: {task['title']}")
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Ты опытный специалист по анализу данных и визуализации, создающий интерактивные визуализации на Python для анализа отзывов."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            response_text = response.choices[0].message.content
            self.logger.debug(f"Получен ответ от GPT для визуализации {task['title']}")
            
            # Извлекаем код и отчет
            code_match = re.search(r'```python(.*?)```', response_text, re.DOTALL)
            code = code_match.group(1).strip() if code_match else ""
            
            # Если код не найден, пробуем другой формат
            if not code:
                code_match = re.search(r'```(.*?)```', response_text, re.DOTALL)
                code = code_match.group(1).strip() if code_match else ""
            
            # Если код все еще не найден, берем весь ответ
            if not code:
                code = "# Не удалось извлечь код\n# Полный ответ GPT:\n\n" + response_text
            
            # Обеспечиваем использование CDN для Plotly
            if "fig.write_html" in code and "include_plotlyjs" not in code:
                code = code.replace("fig.write_html(", "fig.write_html(", 1)
                code = code.replace("fig.write_html(", 
                                  "fig.write_html(", 1)
                code += "\n\n# Добавлено для обеспечения корректной работы интерактивных визуализаций\n"
                code += "if 'fig' in locals():\n"
                code += "    fig.write_html(\n"
                code += f"        '{self.output_dir}/viz_" + "{task['title'].split(':')[0].strip()}.html',\n"
                code += "        include_plotlyjs='cdn',\n"
                code += "        full_html=True,\n"
                code += "        config={'displayModeBar': True, 'responsive': True}\n"
                code += "    )\n"
            
            # Извлекаем отчет
            report_match = re.search(r'ОТЧЕТ:(.*?)$', response_text, re.DOTALL)
            report = report_match.group(1).strip() if report_match else ""
            
            # Если отчет не найден, создаем его из описания визуализации
            if not report:
                report = f"# Отчет по визуализации: {task['title']}\n\n"
                report += f"## Тип визуализации\n{task['type']}\n\n"
                report += f"## Описание\n{task['description']}\n\n"
                report += f"## Ожидаемые инсайты\n{task['insights']}\n\n"
                report += "## Примечание\nОтчет сгенерирован автоматически на основе описания визуализации."
            
            return code, report
                
        except Exception as e:
            self.logger.error(f"Ошибка при генерации кода визуализации: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Возвращаем шаблонный код и отчет в случае ошибки
            return self._generate_fallback_code(task, metadata), self._generate_fallback_report(task)

    def _generate_fallback_code(self, task: Dict[str, str], metadata: Dict[str, Any]) -> str:
        """Генерирует резервный код при возникновении ошибок."""
        return f"""
# Шаблон для визуализации: {task['title']}
import matplotlib.pyplot as plt
import pandas as pd
import os

# Создаем простую визуализацию на основе доступных данных
fig, ax = plt.subplots(figsize=(10, 6))

# Пример данных для визуализации
labels = list(metadata['ratings_distribution'].keys())
values = list(metadata['ratings_distribution'].values())

ax.bar(labels, values, color='skyblue')
ax.set_title('{task['title']}')
ax.set_xlabel('Рейтинг')
ax.set_ylabel('Количество отзывов')

# Сохраняем результат
output_dir = '{self.output_dir}'
os.makedirs(output_dir, exist_ok=True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'fallback_visualization.png'), dpi=300)
plt.close()

print(f'Создан резервный график: {task['title']}')
"""

    def _generate_fallback_report(self, task: Dict[str, str]) -> str:
        """Генерирует резервный отчет при возникновении ошибок."""
        return f"""# Отчет по визуализации: {task['title']}

## Тип визуализации
{task['type']}

## Описание
{task['description']}

## Примечание
Это резервный отчет, созданный из-за ошибки при генерации полноценного отчета.
"""

    def _safe_filename(self, filename: str) -> str:
        """Преобразует строку в безопасное имя файла."""
        # Заменяем запрещенные символы
        safe = re.sub(r'[\\/*?:"<>|]', "", filename)
        # Заменяем пробелы и другие символы на подчеркивания
        safe = re.sub(r'[\s\-,;]', "_", safe)
        # Удаляем множественные подчеркивания
        safe = re.sub(r'_+', "_", safe)
        # Ограничиваем длину
        return safe[:100]

    def _create_index_file(self, tasks: List[Dict[str, str]], files: List[str]) -> None:
        """Создает индексный файл со всеми визуализациями."""
        index_content = "# Индекс визуализаций\n\n"
        
        for idx, (task, file_path) in enumerate(zip(tasks, files), 1):
            base_filename = os.path.basename(file_path)
            index_content += f"## {idx}. {task['title']}\n\n"
            index_content += f"**Тип визуализации:** {task['type']}\n\n"
            index_content += f"**Файл кода:** [`{base_filename}`]({file_path})\n\n"
            index_content += f"**Описание:** {task['description']}\n\n"
            index_content += "---\n\n"
        
        with open(os.path.join(self.output_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(index_content)