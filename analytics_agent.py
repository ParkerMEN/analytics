import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Set, Union
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from wordcloud import WordCloud
import numpy as np
from collections import Counter
from openai import OpenAI

class AnalyticsAgent:
    """
    Интеллектуальный агент для динамической аналитики данных отзывов.
    Самостоятельно определяет оптимальные метрики и визуализации без жестких ограничений.
    """
    
    def __init__(self, data_file: str, output_dir: Optional[str] = None, openai_api_key: Optional[str] = None):
        """
        Инициализирует аналитический агент с файлом данных и директорией для вывода.
        
        Args:
            data_file: Путь к JSON-файлу с отзывами
            output_dir: Директория для сохранения отчетов и визуализаций
            openai_api_key: API ключ для OpenAI (если не указан, будет попытка получить из OPENAI_API_KEY)
        """
        self.data_file = data_file
        self.output_dir = output_dir or "analytics_output"
        self.log_file = os.path.join(self.output_dir, "analytics.log")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        os.makedirs(self.output_dir, exist_ok=True)
        self._setup_logging()
        self.reviews = []
        self.df = None
        self.metadata = {}
        self.client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.load_data()
        
    def _setup_logging(self):
        self.logger = logging.getLogger(f"AnalyticsAgent")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(fh)
    
    def load_data(self):
        """Загружает данные отзывов и создает DataFrame для анализа"""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.reviews = json.load(f)
            
            # Собираем все уникальные ключи из 'meta' для дальнейшего анализа
            all_meta_keys = set()
            for review in self.reviews:
                meta = review.get("meta", {})
                all_meta_keys.update(meta.keys())
            
            self.logger.info(f"Обнаружены уникальные ключи в meta: {', '.join(all_meta_keys)}")
            
            # Преобразование в pandas DataFrame для удобства анализа
            reviews_processed = []
            for review in self.reviews:
                # Извлекаем основные поля
                processed_review = {
                    "review_idx": review.get("review_idx", None),
                    "original_text": review.get("original_text", ""),
                    "topics": ", ".join(review.get("topics", [])) if review.get("topics") else "",
                    "raw_analysis": review.get("raw_analysis", ""),
                    "raw_response": review.get("raw_response", "")
                }
                
                # Объединяем метаданные
                meta = review.get("meta", {})
                for k, v in meta.items():
                    # Преобразуем списки в строки для совместимости с DataFrame
                    if isinstance(v, list):
                        processed_review[f"meta_{k}"] = ", ".join(map(str, v))
                    else:
                        processed_review[f"meta_{k}"] = v
                
                # Проверяем рейтинг и стандартизируем его
                rating = None
                for key in ["рейтинг", "rating", "оценка"]:
                    if f"meta_{key}" in processed_review:
                        try:
                            # Обрабатываем случаи типа "5/5" и т.п.
                            rating_str = str(processed_review[f"meta_{key}"])
                            if "/" in rating_str:
                                rating = float(rating_str.split("/")[0])
                            else:
                                rating = float(rating_str)
                            break
                        except (ValueError, TypeError):
                            pass
                
                processed_review["rating_normalized"] = rating
                reviews_processed.append(processed_review)
                
            self.df = pd.DataFrame(reviews_processed)
            self.logger.info(f"Загружено {len(self.reviews)} отзывов")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных: {e}")
    
    def discover_metrics(self) -> Dict[str, Any]:
        """
        Динамически определяет доступные метрики на основе данных.
        Вместо предопределенных функций определяет, что можно анализировать.
        
        Returns:
            Словарь с доступными метриками и их характеристиками
        """
        metrics = {}
        
        # Анализ распределения тем
        if "topics" in self.df.columns and self.df["topics"].notna().sum() > 0:
            # Извлекаем все темы из объединенных строк
            all_topics = []
            for topics_str in self.df["topics"].dropna():
                topics = [t.strip() for t in topics_str.split(",")]
                all_topics.extend([t for t in topics if t])
            
            topic_counts = Counter(all_topics)
            metrics["topics"] = {
                "available": True,
                "unique_count": len(topic_counts),
                "top_topics": dict(topic_counts.most_common(15)),
                "visualization_options": ["bar_chart", "wordcloud", "pie_chart", "horizontal_bar"]
            }
        
        # Анализ рейтингов
        if "rating_normalized" in self.df.columns and self.df["rating_normalized"].notna().sum() > 0:
            metrics["ratings"] = {
                "available": True,
                "mean": float(self.df["rating_normalized"].mean()),
                "median": float(self.df["rating_normalized"].median()),
                "min": float(self.df["rating_normalized"].min()),
                "max": float(self.df["rating_normalized"].max()),
                "distribution": {str(k): int(v) for k, v in self.df["rating_normalized"].value_counts().to_dict().items()},
                "visualization_options": ["histogram", "bar_chart", "pie_chart", "donut_chart"]
            }
            
        # Анализ дат
        date_columns = [col for col in self.df.columns if "дата" in col.lower() or "date" in col.lower()]
        if date_columns:
            date_col = date_columns[0]
            try:
                # Преобразуем строки в даты
                self.df[f"{date_col}_parsed"] = pd.to_datetime(self.df[date_col], errors="coerce")
                if self.df[f"{date_col}_parsed"].notna().sum() > 0:
                    metrics["dates"] = {
                        "available": True,
                        "column": date_col,
                        "min_date": self.df[f"{date_col}_parsed"].min().strftime("%Y-%m-%d"),
                        "max_date": self.df[f"{date_col}_parsed"].max().strftime("%Y-%m-%d"),
                        "visualization_options": ["timeline", "line_chart"]
                    }
                    
                    # Добавляем данные о рейтингах по датам, если доступны оба типа метрик
                    if "rating_normalized" in self.df.columns:
                        date_ratings = {}
                        for date, group in self.df.groupby(self.df[f"{date_col}_parsed"].dt.date):
                            if group["rating_normalized"].notna().any():
                                date_ratings[str(date)] = float(group["rating_normalized"].mean())
                        
                        if date_ratings:
                            metrics["dates"]["ratings_by_date"] = date_ratings
                            metrics["dates"]["visualization_options"].extend(["dual_axis", "area_plot"])
            except Exception as e:
                self.logger.warning(f"Не удалось проанализировать даты: {e}")
        
        # Анализ эмоциональной окраски/сентимента
        sentiment_columns = [col for col in self.df.columns if 
                            any(term in col.lower() for term in 
                               ["sentiment", "эмоц", "тональн", "окрас"])]
        if sentiment_columns:
            sentiment_col = sentiment_columns[0]
            sentiment_values = self.df[sentiment_col].dropna().value_counts().to_dict()
            metrics["sentiment"] = {
                "available": True,
                "column": sentiment_col,
                "distribution": {str(k): int(v) for k, v in sentiment_values.items()},
                "visualization_options": ["pie_chart", "bar_chart"]
            }
        
        # Анализ достоинств и недостатков
        pros_cols = [col for col in self.df.columns if 
                     any(term in col.lower() for term in 
                        ["достоинств", "pros", "advantages", "плюс"])]
        cons_cols = [col for col in self.df.columns if 
                     any(term in col.lower() for term in 
                        ["недостат", "cons", "disadvantages", "минус"])]
        
        if pros_cols or cons_cols:
            # Извлекаем тексты достоинств и недостатков
            pros_texts = []
            cons_texts = []
            
            for col in pros_cols:
                pros_texts.extend([str(t).strip() for t in self.df[col].dropna()])
            
            for col in cons_cols:
                cons_texts.extend([str(t).strip() for t in self.df[col].dropna()])
            
            metrics["pros_cons"] = {
                "available": True,
                "pros_count": len(pros_texts),
                "cons_count": len(cons_texts),
                "pros_sample": pros_texts[:10],  # Ограничиваем выборку для API
                "cons_sample": cons_texts[:10],  # Ограничиваем выборку для API
                "visualization_options": ["wordcloud", "stacked_bar", "comparison_chart"]
            }
        
        return metrics
    
    def get_visualization_recommendations(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Использует GPT для анализа метрик и выбора оптимальных визуализаций.
        
        Args:
            metrics: Словарь метрик из discover_metrics()
            
        Returns:
            Словарь с рекомендуемыми визуализациями и их параметрами
        """
        if not self.client:
            self.logger.warning("API ключ OpenAI не предоставлен. Будут использованы стандартные визуализации.")
            return self._get_default_visualizations(metrics)
        
        # Подготавливаем данные для API запроса
        metrics_sample = {}
        for key, value in metrics.items():
            if isinstance(value, dict) and value.get("available", False):
                metrics_sample[key] = {k: v for k, v in value.items() if k != 'visualization_options'}
                
                # Ограничиваем размер данных если нужно
                if 'top_topics' in metrics_sample[key] and len(metrics_sample[key]['top_topics']) > 10:
                    topics_items = list(metrics_sample[key]['top_topics'].items())
                    metrics_sample[key]['top_topics'] = dict(topics_items[:10])
                    metrics_sample[key]['top_topics_note'] = f"Показаны 10 из {len(topics_items)} тем"
        
        prompt = f"""
        Ты - эксперт по визуализации данных. Проанализируй следующие метрики данных отзывов:
        
        {json.dumps(metrics_sample, indent=2, ensure_ascii=False)}
        
        Выбери оптимальные типы визуализаций для этих данных. Доступные типы:
        
        1. Line Chart - для трендов во времени
        2. Horizontal Bar Chart - для сравнения категориальных данных
        3. Vertical Bar Chart - для распределения числовых данных
        4. Stacked Bar Chart - для отображения частей целого по категориям
        5. Cumulative Line - для накопительных показателей
        6. Dual Axis Plot - для сравнения двух метрик с разными шкалами
        7. Bar + Line Plot - для сравнения абсолютных и относительных значений
        8. Donut Chart - для частей целого (как круговые диаграммы)
        9. Pie Chart - для частей целого (не больше 6-7 частей)
        10. Area Plot - для трендов с накоплением
        11. Scatter Plot - для корреляций
        12. WordCloud - для текстовых данных
        13. Box Plot - для распределения значений
        14. Heatmap - для корреляций между несколькими признаками

        Выбери не более 5-6 самых информативных визуализаций. Круговые и столбчатые диаграммы имеют приоритет.
        
        Результат представь в виде JSON с полями:
        - name: название визуализации
        - type: тип визуализации (точно один из перечисленных выше)
        - data_source: источник данных (например, "ratings.distribution")
        - title: заголовок для графика
        - description: краткое описание того, что показывает график
        - params: словарь дополнительных параметров (цвета, метки осей и т.д.)
        
        Формат результата:
        {{"visualizations": [
            {{"name": "ratings_distribution", "type": "Vertical Bar Chart", "data_source": "ratings.distribution", "title": "Распределение рейтингов", "description": "Показывает, сколько отзывов получило каждую оценку", "params": {{"x_label": "Оценка", "y_label": "Количество отзывов"}} }},
            ...
        ]}}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "Ты эксперт по визуализации данных. Отвечай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            self.logger.info(f"GPT рекомендовал {len(result.get('visualizations', []))} визуализаций")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка при запросе к GPT: {e}")
            return self._get_default_visualizations(metrics)
    
    def _get_default_visualizations(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Возвращает стандартные визуализации при отсутствии API ключа или ошибке.
        """
        visualizations = []
        
        if metrics.get("ratings", {}).get("available", False):
            visualizations.append({
                "name": "ratings_distribution",
                "type": "Vertical Bar Chart",
                "data_source": "ratings.distribution",
                "title": "Распределение рейтингов",
                "description": "Показывает, сколько отзывов получило каждую оценку",
                "params": {"x_label": "Оценка", "y_label": "Количество отзывов"}
            })
        
        if metrics.get("topics", {}).get("available", False):
            visualizations.append({
                "name": "top_topics",
                "type": "Horizontal Bar Chart",
                "data_source": "topics.top_topics",
                "title": "Популярные темы в отзывах",
                "description": "Показывает наиболее часто упоминаемые темы",
                "params": {"x_label": "Количество упоминаний", "y_label": "Тема"}
            })
            
            visualizations.append({
                "name": "topics_wordcloud", 
                "type": "WordCloud",
                "data_source": "topics.top_topics",
                "title": "Облако тем отзывов",
                "description": "Визуализация наиболее частых тем в отзывах",
                "params": {}
            })
        
        return {"visualizations": visualizations}
    
    def generate_visualizations(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Генерирует визуализации на основе доступных метрик с помощью GPT для выбора
        оптимальных типов графиков.
        
        Args:
            metrics: Словарь доступных метрик из discover_metrics()
            
        Returns:
            Список путей к созданным файлам визуализаций
        """
        generated_files = []
        
        # Получаем рекомендации от GPT
        recommendations = self.get_visualization_recommendations(metrics)
        visualizations = recommendations.get("visualizations", [])
        
        if not visualizations:
            self.logger.warning("Не получено рекомендаций по визуализациям")
            return generated_files
        
        # Настраиваем стиль visualizations
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set(font_scale=1.2)
        
        for viz in visualizations:
            try:
                viz_type = viz.get("type")
                data_source = viz.get("data_source")
                title = viz.get("title", "")
                name = viz.get("name", "visualization")
                params = viz.get("params", {})
                
                # Извлекаем данные из метрик
                data = self._get_data_from_source(metrics, data_source)
                if data is None:
                    self.logger.warning(f"Не удалось получить данные для {data_source}")
                    continue
                
                # Генерируем соответствующую визуализацию
                file_path = self._generate_visualization(
                    viz_type, data, title, name, params
                )
                
                if file_path:
                    generated_files.append(file_path)
                    self.logger.info(f"Создана визуализация: {file_path}")
                
            except Exception as e:
                self.logger.error(f"Ошибка при создании визуализации {viz.get('name', '')}: {e}")
        
        return generated_files
    
    def _get_data_from_source(self, metrics: Dict[str, Any], data_source: str) -> Any:
        """
        Извлекает данные из указанного источника в метриках.
        
        Args:
            metrics: Словарь метрик
            data_source: Путь к данным (например, "ratings.distribution")
            
        Returns:
            Извлеченные данные или None при ошибке
        """
        try:
            if not data_source:
                return None
                
            parts = data_source.split(".")
            data = metrics
            for part in parts:
                data = data.get(part, {})
                
            return data
        except Exception as e:
            self.logger.error(f"Ошибка при извлечении данных из {data_source}: {e}")
            return None
    
    def _generate_visualization(self, viz_type: str, data: Any, title: str, name: str, 
                               params: Dict[str, Any]) -> Optional[str]:
        """
        Генерирует визуализацию указанного типа и сохраняет её в файл.
        
        Args:
            viz_type: Тип визуализации
            data: Данные для визуализации
            title: Заголовок графика
            name: Уникальное имя для файла
            params: Дополнительные параметры
            
        Returns:
            Путь к сохраненному файлу или None при ошибке
        """
        try:
            # Настраиваем базовые параметры
            plt.figure(figsize=(12, 8))
            file_name = f"{name.lower().replace(' ', '_')}.png"
            file_path = os.path.join(self.output_dir, file_name)
            
            # Устанавливаем метки осей из параметров
            x_label = params.get("x_label", "")
            y_label = params.get("y_label", "")
            
            if viz_type.lower() in ["vertical bar chart", "bar chart"]:
                if isinstance(data, dict):
                    keys = list(data.keys())
                    values = list(data.values())
                    plt.bar(keys, values, color=sns.color_palette("viridis", len(data)))
                    plt.xlabel(x_label or "Категория", fontsize=12)
                    plt.ylabel(y_label or "Значение", fontsize=12)
                    if len(keys) > 6:
                        plt.xticks(rotation=45, ha="right")
                elif isinstance(data, (list, tuple)):
                    plt.bar(range(len(data)), data, color=sns.color_palette("viridis", len(data)))
                    plt.xlabel(x_label or "Индекс", fontsize=12)
                    plt.ylabel(y_label or "Значение", fontsize=12)
            
            elif viz_type.lower() == "horizontal bar chart":
                if isinstance(data, dict):
                    items = sorted(data.items(), key=lambda x: x[1], reverse=True)
                    keys, values = zip(*items) if items else ([], [])
                    y_pos = range(len(keys))
                    plt.barh(y_pos, values, color=sns.color_palette("viridis", len(data)))
                    plt.yticks(y_pos, keys)
                    plt.xlabel(x_label or "Значение", fontsize=12)
                    plt.ylabel(y_label or "Категория", fontsize=12)
                    
                    # Если много элементов, ограничиваем до топ-15
                    if len(keys) > 15:
                        plt.figure(figsize=(12, 10))
                        top_items = items[:15]
                        keys, values = zip(*top_items)
                        y_pos = range(len(keys))
                        plt.barh(y_pos, values, color=sns.color_palette("viridis", len(top_items)))
                        plt.yticks(y_pos, keys)
                        plt.xlabel(x_label or "Значение", fontsize=12)
                        plt.ylabel(y_label or "Категория (топ-15)", fontsize=12)
            
            elif viz_type.lower() == "pie chart":
                if isinstance(data, dict):
                    # Ограничиваем количество секторов для лучшей читаемости
                    if len(data) > 7:
                        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
                        top_items = dict(sorted_items[:6])
                        other_sum = sum(dict(sorted_items[6:]).values())
                        if other_sum > 0:
                            top_items["Другое"] = other_sum
                        data = top_items
                        
                    plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', 
                          startangle=90, colors=sns.color_palette("viridis", len(data)))
                    plt.axis('equal')  # Круговая диаграмма выглядит лучше как круг
            
            elif viz_type.lower() == "donut chart":
                if isinstance(data, dict):
                    # Ограничиваем количество секторов для лучшей читаемости
                    if len(data) > 7:
                        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
                        top_items = dict(sorted_items[:6])
                        other_sum = sum(dict(sorted_items[6:]).values())
                        if other_sum > 0:
                            top_items["Другое"] = other_sum
                        data = top_items
                    
                    # Создаем кольцевую диаграмму
                    center_circle = plt.Circle((0, 0), 0.70, fc='white')
                    fig = plt.gcf()
                    fig.gca().add_artist(center_circle)
                    
                    plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', 
                          startangle=90, colors=sns.color_palette("viridis", len(data)))
                    plt.axis('equal')
            
            elif viz_type.lower() == "line chart":
                if isinstance(data, dict):
                    x = list(data.keys())
                    y = list(data.values())
                    plt.plot(x, y, marker='o', linestyle='-', color='blue')
                    plt.xlabel(x_label or "Категория", fontsize=12)
                    plt.ylabel(y_label or "Значение", fontsize=12)
                    if len(x) > 10:
                        plt.xticks(rotation=45, ha="right")
            
            elif viz_type.lower() == "area plot":
                if isinstance(data, dict):
                    x = list(data.keys())
                    y = list(data.values())
                    plt.fill_between(x, y, color='skyblue', alpha=0.4)
                    plt.plot(x, y, color='blue', alpha=0.6)
                    plt.xlabel(x_label or "Категория", fontsize=12)
                    plt.ylabel(y_label or "Значение", fontsize=12)
                    if len(x) > 10:
                        plt.xticks(rotation=45, ha="right")
            
            elif viz_type.lower() == "stacked bar chart":
                if "stacked_data" in params:
                    stacked_data = params["stacked_data"]
                    categories = list(stacked_data.keys())
                    series = {}
                    for cat in categories:
                        for series_name, value in stacked_data[cat].items():
                            if series_name not in series:
                                series[series_name] = []
                            series[series_name].append(value)
                    
                    bottom = np.zeros(len(categories))
                    for series_name, values in series.items():
                        plt.bar(categories, values, bottom=bottom, label=series_name)
                        bottom += np.array(values)
                    
                    plt.xlabel(x_label or "Категория", fontsize=12)
                    plt.ylabel(y_label or "Значение", fontsize=12)
                    plt.legend()
            
            elif viz_type.lower() == "dual axis plot":
                # Для dual axis нужны два набора данных
                if "secondary_data" in params and isinstance(data, dict):
                    x = list(data.keys())
                    y1 = list(data.values())
                    y2 = list(params["secondary_data"].values())
                    
                    fig, ax1 = plt.subplots()
                    
                    color1 = 'tab:blue'
                    ax1.set_xlabel(x_label or 'Категория')
                    ax1.set_ylabel(y_label or 'Значение 1', color=color1)
                    ax1.plot(x, y1, color=color1, marker='o')
                    ax1.tick_params(axis='y', labelcolor=color1)
                    
                    ax2 = ax1.twinx()
                    color2 = 'tab:red'
                    ax2.set_ylabel(params.get("secondary_y_label", 'Значение 2'), color=color2)
                    ax2.plot(x, y2, color=color2, marker='s')
                    ax2.tick_params(axis='y', labelcolor=color2)
                    
                    if len(x) > 10:
                        plt.xticks(rotation=45, ha="right")
                    
                    fig.tight_layout()
            
            elif viz_type.lower() == "wordcloud":
                if isinstance(data, dict):
                    plt.figure(figsize=(10, 10))
                    wordcloud = WordCloud(width=800, height=800, background_color='white', 
                                      min_font_size=10, colormap='viridis').generate_from_frequencies(data)
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis("off")
            
            elif viz_type.lower() == "scatter plot":
                if "x_data" in params and "y_data" in params:
                    x = params["x_data"]
                    y = params["y_data"]
                    plt.scatter(x, y)
                    plt.xlabel(x_label or "X", fontsize=12)
                    plt.ylabel(y_label or "Y", fontsize=12)
            
            elif viz_type.lower() == "box plot":
                if isinstance(data, dict):
                    plt.boxplot(list(data.values()), labels=list(data.keys()))
                    plt.xlabel(x_label or "Категория", fontsize=12)
                    plt.ylabel(y_label or "Распределение", fontsize=12)
            
            elif viz_type.lower() == "heatmap":
                if isinstance(data, list) and all(isinstance(row, list) for row in data):
                    sns.heatmap(data, annot=True, cmap="viridis")
                    plt.xlabel(x_label or "X", fontsize=12)
                    plt.ylabel(y_label or "Y", fontsize=12)
            
            else:
                self.logger.warning(f"Неизвестный тип визуализации: {viz_type}")
                return None
            
            # Добавляем заголовок и сохраняем файл
            plt.title(title, fontsize=15)
            plt.tight_layout()
            plt.savefig(file_path)
            plt.close()
            
            return file_path
        except Exception as e:
            self.logger.error(f"Ошибка при создании визуализации {name}: {e}")
            return None

    def generate_insights(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Автоматически генерирует инсайты на основе данных.
        
        Args:
            metrics: Словарь доступных метрик
            
        Returns:
            Список инсайтов с описанием и уровнем значимости
        """
        insights = []
        
        # Инсайт по общей удовлетворенности (рейтинги)
        if metrics.get("ratings", {}).get("available", False):
            mean_rating = metrics["ratings"]["mean"]
            rating_insight = {
                "title": "Общая удовлетворенность продуктом",
                "description": "",
                "significance": "high"
            }
            
            if mean_rating >= 4.5:
                rating_insight["description"] = f"Крайне высокая удовлетворенность продуктом (средняя оценка {mean_rating:.2f}/5). Покупатели очень довольны."
            elif mean_rating >= 4.0:
                rating_insight["description"] = f"Высокая удовлетворенность продуктом (средняя оценка {mean_rating:.2f}/5). Большинство отзывов положительные."
            elif mean_rating >= 3.0:
                rating_insight["description"] = f"Средняя удовлетворенность продуктом (средняя оценка {mean_rating:.2f}/5). Есть как положительные, так и отрицательные отзывы."
            else:
                rating_insight["description"] = f"Низкая удовлетворенность продуктом (средняя оценка {mean_rating:.2f}/5). Преобладают отрицательные отзывы."
                
            insights.append(rating_insight)
        
        # Инсайт по ключевым темам
        if metrics.get("topics", {}).get("available", False):
            top_topics = list(metrics["topics"]["top_topics"].items())
            if top_topics:
                top_3 = top_topics[:3]
                topics_text = ", ".join([f"{topic} ({count})" for topic, count in top_3])
                
                topics_insight = {
                    "title": "Ключевые темы в отзывах",
                    "description": f"Наиболее часто упоминаемые темы: {topics_text}. Эти аспекты продукта заслуживают особого внимания.",
                    "significance": "medium"
                }
                insights.append(topics_insight)
        
        # Инсайт по наиболее проблемным аспектам (низкие оценки)
        if self.df is not None:
            try:
                # Находим отзывы с низкими оценками (≤ 2)
                low_ratings = self.df[self.df["rating_normalized"] <= 2].copy()
                if not low_ratings.empty:
                    # Собираем темы из отзывов с низкими оценками
                    problem_topics = []
                    for topics_str in low_ratings["topics"].dropna():
                        topics = [t.strip() for t in topics_str.split(",")]
                        problem_topics.extend([t for t in topics if t])
                    
                    problem_counter = Counter(problem_topics)
                    if problem_counter:
                        top_problems = problem_counter.most_common(3)
                        problems_text = ", ".join([f"{topic} ({count})" for topic, count in top_problems])
                        
                        problems_insight = {
                            "title": "Проблемные аспекты продукта",
                            "description": f"В отзывах с низкими оценками чаще всего упоминаются: {problems_text}. Эти аспекты требуют улучшения.",
                            "significance": "high"
                        }
                        insights.append(problems_insight)
            except Exception as e:
                self.logger.warning(f"Не удалось проанализировать проблемные аспекты: {e}")
        
        # Динамически добавляем дополнительные инсайты на основе данных
        # Например, анализ изменения оценок со временем, если есть даты
        if metrics.get("dates", {}).get("available", False):
            try:
                date_column = f"{metrics['dates']['column']}_parsed"
                if date_column in self.df.columns:
                    # Группируем по дате и вычисляем среднюю оценку
                    date_groups = self.df.dropna(subset=[date_column, "rating_normalized"]).copy()
                    date_groups["month_year"] = date_groups[date_column].dt.strftime('%Y-%m')
                    rating_trend = date_groups.groupby("month_year")["rating_normalized"].mean()
                    
                    # Анализируем тренд
                    if len(rating_trend) > 1:
                        first_period = rating_trend.iloc[0]
                        last_period = rating_trend.iloc[-1]
                        diff = last_period - first_period
                        
                        trend_insight = {
                            "title": "Динамика удовлетворенности со временем",
                            "description": "",
                            "significance": "medium"
                        }
                        
                        if abs(diff) < 0.2:
                            trend_insight["description"] = "Удовлетворенность продуктом остается стабильной во времени."
                        elif diff > 0:
                            trend_insight["description"] = f"Удовлетворенность продуктом растет со временем (+{diff:.2f} баллов)."
                        else:
                            trend_insight["description"] = f"Удовлетворенность продуктом снижается со временем ({diff:.2f} баллов)."
                        
                        insights.append(trend_insight)
            except Exception as e:
                self.logger.warning(f"Не удалось проанализировать временную динамику: {e}")
        
        return insights
        
    def generate_report(self) -> Dict[str, Any]:
        """
        Генерирует полный аналитический отчет с метриками, инсайтами и визуализациями.
        
        Returns:
            Словарь с отчетом, включая пути к визуализациям
        """
        # Определяем метрики, доступные в данных
        metrics = self.discover_metrics()
        
        # Генерируем визуализации с использованием рекомендаций GPT
        visualization_files = self.generate_visualizations(metrics)
        
        # Генерируем инсайты
        insights = self.generate_insights(metrics)
        
        # Формируем отчет
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_file": self.data_file,
            "reviews_count": len(self.reviews),
            "metrics": metrics,
            "insights": insights,
            "visualizations": visualization_files
        }
        
        # Сохраняем отчет в JSON
        report_path = os.path.join(self.output_dir, "analytics_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Аналитический отчет сохранен: {report_path}")
        return report

    def generate_html_report(self, report: Dict[str, Any]) -> str:
        """
        Создает HTML-версию отчета для просмотра в браузере.
        
        Args:
            report: Результат функции generate_report()
            
        Returns:
            Путь к HTML-файлу отчета
        """
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Аналитический отчет по отзывам</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .report-header {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 30px;
                    border-left: 5px solid #3498db;
                }}
                .insight {{
                    margin-bottom: 20px;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .high {{
                    background-color: #ffe0e0;
                    border-left: 5px solid #e74c3c;
                }}
                .medium {{
                    background-color: #fff8e0;
                    border-left: 5px solid #f39c12;
                }}
                .low {{
                    background-color: #e0f8ff;
                    border-left: 5px solid #3498db;
                }}
                .visualization {{
                    margin: 30px 0;
                    text-align: center;
                }}
                .visualization img {{
                    max-width: 100%;
                    height: auto;
                    box-shadow: 0 3px 6px rgba(0,0,0,0.16);
                    border-radius: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                }}
                tr:hover {{
                    background-color: #f8f9fa;
                }}
            </style>
        </head>
        <body>
            <div class="report-header">
                <h1>Аналитический отчет по отзывам</h1>
                <p>Дата формирования: {report['report_date']}</p>
                <p>Файл данных: {report['data_file']}</p>
                <p>Количество отзывов: {report['reviews_count']}</p>
            </div>

            <h2>Ключевые инсайты</h2>
        """
        
        # Добавляем инсайты
        for insight in report["insights"]:
            significance = insight.get("significance", "low")
            html_content += f"""
            <div class="insight {significance}">
                <h3>{insight['title']}</h3>
                <p>{insight['description']}</p>
            </div>
            """
        
        # Добавляем визуализации
        if report.get("visualizations"):
            html_content += f"""
            <h2>Визуализации</h2>
            """
            
            for viz_path in report["visualizations"]:
                viz_filename = os.path.basename(viz_path)
                # Создаем относительный путь к изображению
                rel_path = os.path.join(".", viz_filename)
                title = " ".join(viz_filename.replace("_", " ").replace(".png", "").title().split())
                
                html_content += f"""
                <div class="visualization">
                    <h3>{title}</h3>
                    <img src="{rel_path}" alt="{title}">
                </div>
                """
        
        # Добавляем метрики
        if report.get("metrics"):
            html_content += f"""
            <h2>Доступные метрики</h2>
            """
            
            # Рейтинги
            if report["metrics"].get("ratings", {}).get("available", False):
                html_content += f"""
                <h3>Статистика рейтингов</h3>
                <table>
                    <tr>
                        <th>Метрика</th>
                        <th>Значение</th>
                    </tr>
                    <tr>
                        <td>Средний рейтинг</td>
                        <td>{report["metrics"]["ratings"]["mean"]:.2f}</td>
                    </tr>
                    <tr>
                        <td>Медианный рейтинг</td>
                        <td>{report["metrics"]["ratings"]["median"]}</td>
                    </tr>
                    <tr>
                        <td>Минимальный рейтинг</td>
                        <td>{report["metrics"]["ratings"]["min"]}</td>
                    </tr>
                    <tr>
                        <td>Максимальный рейтинг</td>
                        <td>{report["metrics"]["ratings"]["max"]}</td>
                    </tr>
                </table>
                
                <h4>Распределение рейтингов</h4>
                <table>
                    <tr>
                        <th>Рейтинг</th>
                        <th>Количество отзывов</th>
                    </tr>
                """
                
                for rating, count in report["metrics"]["ratings"]["distribution"].items():
                    html_content += f"""
                    <tr>
                        <td>{rating}</td>
                        <td>{count}</td>
                    </tr>
                    """
                
                html_content += """
                </table>
                """
            
            # Темы
            if report["metrics"].get("topics", {}).get("available", False):
                html_content += f"""
                <h3>Топ темы отзывов</h3>
                <table>
                    <tr>
                        <th>Тема</th>
                        <th>Количество упоминаний</th>
                    </tr>
                """
                
                for topic, count in report["metrics"]["topics"]["top_topics"].items():
                    html_content += f"""
                    <tr>
                        <td>{topic}</td>
                        <td>{count}</td>
                    </tr>
                    """
                
                html_content += """
                </table>
                """
        
        # Закрываем HTML-документ
        html_content += """
        </body>
        </html>
        """
        
        # Сохраняем HTML-отчет
        html_path = os.path.join(self.output_dir, "analytics_report.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        self.logger.info(f"HTML-отчет сохранен: {html_path}")
        return html_path

    def run_analysis(self) -> Tuple[Dict[str, Any], str]:
        """
        Запускает полный цикл анализа и создает отчеты.
        
        Returns:
            Кортеж (отчет JSON, путь к HTML-отчету)
        """
        report = self.generate_report()
        html_path = self.generate_html_report(report)
        return report, html_path