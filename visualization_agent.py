import os
import json
import logging
from typing import List, Dict, Any, Optional
import re
import openai
from datetime import datetime

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

    def generate_visualizations(self, data: List[Dict[str, Any]], recommendations: str = None, 
                              analysis_file: str = "analysis_results/hidden_patterns_analysis.txt"):
        """
        Генерирует визуализации на основе данных и рекомендаций.
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
        
        # Генерируем код для каждой визуализации
        generated_files = []
        
        for idx, task in enumerate(visualization_tasks, 1):
            self.logger.info(f"Генерация кода для визуализации {idx}/{len(visualization_tasks)}: {task.get('title', 'Без названия')}")
            
            try:
                # Генерируем код и отчет для визуализации
                code, report = self._generate_visualization_code(task, metadata, data)
                
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
                self.logger.error(f"Ошибка при генерации визуализации {idx}: {str(e)}")
        
        # Создаем индексный файл со всеми визуализациями
        self._create_index_file(visualization_tasks, generated_files)
        
        return generated_files

    def _extract_visualization_tasks(self, text: str) -> List[Dict[str, str]]:
        """
        Извлекает задачи для создания визуализаций из текста рекомендаций или анализа.
        """
        tasks = []
        
        # Шаблон для извлечения визуализаций из форматированного текста visualization_recommendations.txt
        sections = re.findall(r'## \d+\. Визуализация №\d+: (.*?)(?=## \d+\.|$)', text, re.DOTALL)
        if sections:
            for section in sections:
                task = {"title": "", "type": "", "description": section.strip(), "data": "", "insights": ""}
                
                # Извлекаем заголовок
                title_match = re.search(r'^(.*?)$', section.strip(), re.MULTILINE)
                if title_match:
                    task["title"] = title_match.group(1).strip()
                
                # Извлекаем тип диаграммы
                type_match = re.search(r'\*\*Тип диаграммы:\*\*\s*(.*?)(?=$|\*\*)', section, re.DOTALL)
                if type_match:
                    task["type"] = type_match.group(1).strip()
                
                # Извлекаем данные
                data_match = re.search(r'\*\*Данные:\*\*\s*(.*?)(?=$|\*\*)', section, re.DOTALL)
                if data_match:
                    task["data"] = data_match.group(1).strip()
                
                # Извлекаем инсайты
                insights_match = re.search(r'\*\*Инсайты:\*\*\s*(.*?)(?=$|\*\*)', section, re.DOTALL)
                if insights_match:
                    task["insights"] = insights_match.group(1).strip()
                
                tasks.append(task)
        
        # Если первый шаблон не сработал, пробуем другие форматы
        if not tasks:
            # Шаблон для markdown-списка из visualization_recommendations.txt
            viz_blocks = re.findall(r'## \d+\. Визуализация №\d+: .*?- \*\*Тип диаграммы:\*\*(.*?)(?=## \d+\. Визуализация|$)', text, re.DOTALL)
            if viz_blocks:
                for i, block in enumerate(viz_blocks, 1):
                    title_match = re.search(r'## \d+\. Визуализация №\d+: (.*?)$', text[:text.find(block)], re.MULTILINE)
                    title = title_match.group(1).strip() if title_match else f"Визуализация {i}"
                    
                    type_match = re.search(r'Тип диаграммы:\*\*\s*(.*?)(?=$|\n)', block)
                    viz_type = type_match.group(1).strip() if type_match else "График"
                    
                    data_match = re.search(r'Данные:\*\*\s*(.*?)(?=$|\n|\*\*)', block, re.DOTALL)
                    data = data_match.group(1).strip() if data_match else ""
                    
                    insights_match = re.search(r'Инсайты:\*\*\s*(.*?)(?=$|\n|\*\*)', block, re.DOTALL)
                    insights = insights_match.group(1).strip() if insights_match else ""
                    
                    tasks.append({
                        "title": title,
                        "type": viz_type,
                        "description": block.strip(),
                        "data": data,
                        "insights": insights
                    })
        
        # Если и второй шаблон не сработал, используем оригинальные регулярные выражения
        if not tasks:
            viz_blocks = re.findall(r'(?:###|##)\s*(?:\d+\.\s*)?(?:Визуализация\s*\d*:?\s*|Рекомендуемая визуализация\s*\d*:?\s*)(.*?)(?=(?:###|##|$))', 
                                   text, re.DOTALL)
            
            if not viz_blocks:
                viz_blocks = re.findall(r'(?:\d+\.\s*|•\s*|\*\s*|\-\s*)(?:Тип диаграммы|Тип визуализации|Визуализация).*?(?=(?:\d+\.\s*|•\s*|\*\s*|\-\s*|$))', 
                                       text, re.DOTALL)
            
            for block in viz_blocks:
                task = {
                    "title": "Визуализация данных",
                    "type": "График",
                    "description": block.strip(),
                    "data": "",
                    "insights": ""
                }
                
                title_match = re.search(r'^(.*?)(?:\n|$)', block)
                if title_match:
                    task["title"] = title_match.group(1).strip()
                
                type_match = re.search(r'(?:Тип диаграммы|Тип визуализации|Тип графика):\s*(.*?)(?:\n|$)', block)
                if type_match:
                    task["type"] = type_match.group(1).strip()
                
                data_match = re.search(r'(?:Данные|Данные для визуализации|Что визуализировать):\s*(.*?)(?=(?:Инсайты|Значимость|Почему|$))', block, re.DOTALL)
                if data_match:
                    task["data"] = data_match.group(1).strip()
                
                insights_match = re.search(r'(?:Инсайты|Значимость|Почему|Что позволит увидеть):\s*(.*?)$', block, re.DOTALL)
                if insights_match:
                    task["insights"] = insights_match.group(1).strip()
                
                tasks.append(task)
        
        # Если не нашли визуализации, добавляем общую задачу
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
        Подготавливает метаданные для визуализаций на основе данных.
        
        Args:
            data: Обработанные данные отзывов.
            
        Returns:
            Словарь с метаданными для визуализаций.
        """
        # Базовые метрики
        ratings = [review.get("rating") for review in data if review.get("rating") is not None]
        
        # Распределение рейтингов
        ratings_dist = {}
        for rating in ratings:
            rating_key = str(rating)
            if rating_key in ratings_dist:
                ratings_dist[rating_key] += 1
            else:
                ratings_dist[rating_key] = 1
        
        # Темы
        all_topics = []
        for review in data:
            topics = review.get("all_topics", [])
            if topics:
                all_topics.extend(topics)
        
        topics_freq = {}
        for topic in all_topics:
            if topic in topics_freq:
                topics_freq[topic] += 1
            else:
                topics_freq[topic] = 1
        
        # Достоинства и недостатки по рейтингу
        pros_by_rating = {}
        cons_by_rating = {}
        
        for review in data:
            rating = review.get("rating")
            if rating is not None:
                rating_key = str(int(rating))
                
                # Достоинства
                pros = review.get("pros", [])
                if pros:
                    if rating_key not in pros_by_rating:
                        pros_by_rating[rating_key] = []
                    pros_by_rating[rating_key].extend(pros if isinstance(pros, list) else [pros])
                
                # Недостатки
                cons = review.get("cons", [])
                if cons:
                    if rating_key not in cons_by_rating:
                        cons_by_rating[rating_key] = []
                    cons_by_rating[rating_key].extend(cons if isinstance(cons, list) else [cons])
        
        return {
            "total_reviews": len(data),
            "ratings": ratings,
            "ratings_distribution": ratings_dist,
            "average_rating": sum(ratings) / len(ratings) if ratings else 0,
            "topics_frequency": topics_freq,
            "pros_by_rating": pros_by_rating,
            "cons_by_rating": cons_by_rating
        }

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
        Создай готовый к выполнению Python-код для визуализации данных с использованием matplotlib, seaborn, и plotly.
        
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
        1. Код должен быть полностью рабочим (включая все импорты) и сохранять визуализацию в файл.
        2. Используй русский язык для подписей, заголовков и легенд.
        3. Обеспечь высокое качество и читаемость визуализации.
        4. Предусмотри обработку краевых случаев (например, отсутствие данных).
        5. Используй красивую цветовую схему и современный стиль оформления.
        6. Добавь комментарии, объясняющие ключевые шаги в коде.
        7. Сохраняй результат в папку '{self.output_dir}' в формате PNG и HTML (для интерактивных графиков).
        8. Предоставь краткое описание того, какие инсайты можно извлечь из данной визуализации.
        
        ФОРМАТ ОТВЕТА:
        Предоставь ответ в формате:
        
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
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Ты опытный специалист по анализу данных и визуализации, создающий качественный код на Python для визуализации данных отзывов."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            response_text = response.choices[0].message.content
            
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