import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional

class DataProcessingAgent:
    """
    Агент для обработки данных отзывов.
    Отвечает за загрузку, объединение и предобработку данных.
    """
    def __init__(self, session_dir: str):
        """
        Инициализирует агент с указанием директории с партиями данных.

        Args:
            session_dir: Директория с файлами партий (например, "session_xxx/batches").
        """
        self.session_dir = session_dir
        self.batches_dir = os.path.join(self.session_dir, "batches")

    def load_batches(self) -> List[Dict[str, Any]]:
        """
        Загружает все batch_x.json файлы из директории batches.

        Returns:
            Список всех отзывов из всех партий.
        """
        all_reviews = []
        for file in os.listdir(self.batches_dir):
            if file.endswith(".json"):
                batch_path = os.path.join(self.batches_dir, file)
                with open(batch_path, "r", encoding="utf-8") as f:
                    batch = json.load(f)
                    all_reviews.extend(batch.get("reviews", []))
        return all_reviews

    def preprocess_reviews(self, reviews: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Выполняет предобработку отзывов и преобразует их в DataFrame.

        Args:
            reviews: Список отзывов.

        Returns:
            DataFrame с предобработанными данными.
        """
        processed_reviews = []
        for review in reviews:
            processed_review = {
                "review_idx": review.get("review_idx"),
                "original_text": review.get("original_text", ""),
                "topics": ", ".join(review.get("topics", [])) if review.get("topics") else "",
                "raw_analysis": review.get("raw_analysis", ""),
                "raw_response": review.get("raw_response", "")
            }

            # Обработка метаданных
            meta = review.get("meta", {})
            for key, value in meta.items():
                if isinstance(value, list):
                    processed_review[f"meta_{key}"] = ", ".join(map(str, value))
                else:
                    processed_review[f"meta_{key}"] = value

            # Нормализация рейтинга
            rating = None
            for key in ["рейтинг", "rating", "оценка"]:
                if f"meta_{key}" in processed_review:
                    try:
                        rating_str = str(processed_review[f"meta_{key}"])
                        if "/" in rating_str:
                            rating = float(rating_str.split("/")[0])
                        else:
                            rating = float(rating_str)
                        break
                    except (ValueError, TypeError):
                        pass
            processed_review["rating_normalized"] = rating

            processed_reviews.append(processed_review)

        return pd.DataFrame(processed_reviews)

    def extract_key_metadata(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлекает ключевые метаданные из отзывов, выполняя глубокую обработку текста
        и объединение полей для более полного анализа.

        Args:
            reviews: Список отзывов.

        Returns:
            Список отзывов с расширенными и нормализованными метаданными.
        """
        processed_reviews = []
        
        # Создаем счетчик для отслеживания прогресса
        total = len(reviews)
        print(f"Обработка {total} отзывов...")
        
        # Расширяем список ключевых полей
        content_fields = ["topics", "Достоинства", "Недостатки", "Текст отзыва", 
                         "pros", "cons", "text", "text_review"]
        
        # Поля, которые мы исключаем как неинформативные
        exclude_fields = ["review_idx", "Отзыв ID", "review_id", "номер_отзыва", 
                         "рейтинг", "rating", "дата", "date", "Медиа контент", 
                         "Видео", "фото", "Номер отзыва", "Отзыв номер", "Отзыв", 
                         "Отзыв №", "Цена"]
        
        for idx, review in enumerate(reviews):
            # Периодически показываем прогресс
            if idx % 50 == 0 and idx > 0:
                print(f"Обработано {idx}/{total} отзывов...")
            
            processed_item = {}
            meta = review.get("meta", {})
            
            # Извлекаем и объединяем весь текстовый контент
            text_content = []
            
            # Добавляем оригинальный текст
            original_text = review.get("original_text", "")
            if original_text:
                # Очищаем от технических метаданных
                clean_lines = []
                for line in original_text.split("\n"):
                    skip_line = False
                    for skip_prefix in ["Отзыв #", "Рейтинг:", "Дата:", "Есть фото", "Есть видео"]:
                        if line.startswith(skip_prefix):
                            skip_line = True
                            break
                    
                    if not skip_line:
                        clean_lines.append(line)
                
                cleaned_text = " ".join(clean_lines).strip()
                if cleaned_text:
                    text_content.append(cleaned_text)
            
            # Добавляем содержимое из метаданных
            for field in content_fields:
                if field in meta and meta[field]:
                    content = meta[field]
                    if isinstance(content, list):
                        content = ", ".join(content)
                    text_content.append(content)
            
            # Объединяем весь текстовый контент
            if text_content:
                # Ограничиваем длину объединенного текста для экономии памяти
                combined_text = " ".join(text_content)
                if len(combined_text) > 1000:  # Устанавливаем лимит
                    combined_text = combined_text[:1000] + "... (текст сокращен)"
                processed_item["combined_text"] = combined_text
            else:
                # Если не нашли текстовый контент, используем оригинальный текст как есть
                processed_item["combined_text"] = original_text
            
            # Добавляем все топики из разных полей
            all_topics = []
            
            # Добавляем топики из поля topics
            topics = review.get("topics", [])
            if topics:
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split(",")]
                all_topics.extend(topics)
            
            # Добавляем топики из метаданных
            for topic_field in ["topics", "темы", "categories", "категории"]:
                if topic_field in meta:
                    topic_value = meta[topic_field]
                    if isinstance(topic_value, list):
                        all_topics.extend(topic_value)
                    elif isinstance(topic_value, str):
                        all_topics.extend([t.strip() for t in topic_value.split(",")])
            
            if all_topics:
                # Удаление дубликатов при сохранении порядка (Python 3.7+)
                unique_topics = []
                seen = set()
                for topic in all_topics:
                    if topic and topic.lower() not in seen:
                        unique_topics.append(topic)
                        seen.add(topic.lower())
                processed_item["all_topics"] = unique_topics
            
            # Добавляем все достоинства и недостатки
            for field_type, field_names in [
                ("pros", ["Достоинства", "достоинства", "pros", "плюсы", "положительные_аспекты"]),
                ("cons", ["Недостатки", "недостатки", "cons", "минусы", "отрицательные_аспекты"])
            ]:
                content = []
                for field in field_names:
                    if field in meta and meta[field]:
                        value = meta[field]
                        if isinstance(value, list):
                            content.extend(value)
                        elif isinstance(value, str):
                            content.append(value)
                
                if content:
                    processed_item[field_type] = content
            
            # Добавляем рейтинг для анализа корреляций
            rating = self._normalize_rating(review)
            if rating is not None:
                processed_item["rating"] = rating
            
            processed_reviews.append(processed_item)
        
        print(f"Обработано всего {len(processed_reviews)} отзывов")
        return processed_reviews

    def _normalize_rating(self, review: Dict[str, Any]) -> Optional[float]:
        """
        Извлекает и нормализует рейтинг из отзыва.
        
        Args:
            review: Отзыв
            
        Returns:
            Нормализованный рейтинг или None
        """
        meta = review.get("meta", {})
        
        # Проверяем различные варианты полей с рейтингом
        for key in ["рейтинг", "rating", "оценка", "Рейтинг"]:
            value = None
            
            # Проверяем в основном объекте
            if key in review:
                value = review[key]
            # Проверяем в метаданных
            elif key in meta:
                value = meta[key]
                
            if value is not None:
                try:
                    # Обрабатываем формат "X/Y"
                    if isinstance(value, str) and "/" in value:
                        parts = value.split("/")
                        return float(parts[0]) / float(parts[1]) * 5
                    return float(value)
                except (ValueError, TypeError):
                    pass
                    
        # Если не нашли рейтинг в обычных полях, ищем в оригинальном тексте
        original_text = review.get("original_text", "")
        if "Рейтинг:" in original_text:
            lines = original_text.split("\n")
            for line in lines:
                if line.startswith("Рейтинг:"):
                    try:
                        rating_text = line.replace("Рейтинг:", "").strip()
                        if "/" in rating_text:
                            parts = rating_text.split("/")
                            return float(parts[0]) / float(parts[1]) * 5
                        return float(rating_text)
                    except (ValueError, TypeError):
                        pass
        
        return None

    def process(self) -> pd.DataFrame:
        """
        Основной метод: загружает и обрабатывает данные из всех партий.

        Returns:
            DataFrame с объединенными и предобработанными данными.
        """
        reviews = self.load_batches()
        return self.preprocess_reviews(reviews)