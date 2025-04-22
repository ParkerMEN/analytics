import os
import uuid
import json
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI

class SplitterAgent:
    """
    Асинхронный агент для разбиения отзывов на партии, семантического анализа тем и сохранения результатов.
    Независимый модуль, поддерживающий лимиты по токенам и количеству отзывов, расширяемые метаданные, логирование и карту соответствия.
    """

    def __init__(
        self,
        openai_api_key: str,
        max_tokens_per_batch: int = 3000,
        max_reviews_per_batch: int = 30,
        max_workers: Optional[int] = None,
        session_dir: Optional[str] = None,
        separator: str = "------------------------------"
    ):
        self.openai_api_key = openai_api_key
        self.max_tokens_per_batch = max_tokens_per_batch
        self.max_reviews_per_batch = max_reviews_per_batch
        self.max_workers = max_workers
        self.separator = separator
        self.session_id = str(uuid.uuid4())
        self.session_dir = session_dir or f"session_{self.session_id}"
        self.batches_dir = os.path.join(self.session_dir, "batches")
        self.log_file = os.path.join(self.session_dir, "splitter.log")
        self.json_log_file = os.path.join(self.session_dir, "splitter.jsonl")
        os.makedirs(self.batches_dir, exist_ok=True)
        self._setup_logging()
        self.client = OpenAI(api_key=self.openai_api_key)

    def _setup_logging(self):
        self.logger = logging.getLogger(f"SplitterAgent_{self.session_id}")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(fh)

    def _estimate_tokens(self, text: str) -> int:
        # Грубая оценка: 1 токен ~ 4 символа
        return max(1, len(text) // 4)

    def _parse_reviews(self, text: str) -> List[Dict[str, Any]]:
        """
        Парсит отзывы по разделителю, извлекает стандартные и любые новые поля.
        """
        reviews = []
        review_blocks = text.split(self.separator)
        for idx, block in enumerate(review_blocks, 1):
            block = block.strip()
            if not block:
                continue
            # Извлекаем стандартные поля
            rating = re.search(r'Рейтинг:\s*([^\n]+)', block)
            date = re.search(r'Дата:\s*([^\n]+)', block)
            text_review = re.search(r'Текст отзыва:\s*([\s\S]+)', block)
            # Дополнительные поля
            has_photo = bool(re.search(r'Есть фото', block, re.IGNORECASE))
            has_video = bool(re.search(r'Есть видео', block, re.IGNORECASE))
            pros = re.findall(r'Достоинства:\s*([^\n]+)', block)
            cons = re.findall(r'Недостатки:\s*([^\n]+)', block)
            # Поиск других новых полей (всё, что "Ключ: Значение" кроме известных)
            meta = {}
            if rating: meta["rating"] = rating.group(1).strip()
            if date: meta["date"] = date.group(1).strip()
            if has_photo: meta["has_photo"] = True
            if has_video: meta["has_video"] = True
            if pros: meta["pros"] = pros
            if cons: meta["cons"] = cons
            for m in re.finditer(r'^([А-Яа-яA-Za-z\s]+):\s*([^\n]+)', block, re.MULTILINE):
                key, value = m.group(1).strip(), m.group(2).strip()
                if key not in ["Рейтинг", "Дата", "Текст отзыва", "Достоинства", "Недостатки"]:
                    meta[key] = value
            reviews.append({
                "review_idx": idx,
                "original_text": block,
                "meta": meta,
                "text": text_review.group(1).strip() if text_review else "",
            })
        return reviews

    async def _analyze_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует отзыв с помощью OpenAI GPT-4 mini для извлечения тем и метаданных.
        """
        prompt = (
            "Проанализируй следующий отзыв. "
            "Верни JSON с полями: topics (список тем), meta (словарь с любыми найденными метаданными), "
            "raw_analysis (твой полный анализ в свободной форме), "
            "raw_response (весь твой ответ, включая JSON и текст). "
            "Если есть новые поля, добавь их в meta.\n\n"
            f"Отзыв:\n{review['original_text']}"
        )
        messages = [
            {"role": "system", "content": "Ты — эксперт по анализу отзывов. Всегда возвращай корректный JSON."},
            {"role": "user", "content": prompt}
        ]
        try:
            response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.2,
                )
            )
            content = response.choices[0].message.content
            # Попытка извлечь JSON из ответа
            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]
                analysis = json.loads(json_str)
            except Exception:
                analysis = {"topics": [], "meta": {}, "raw_analysis": "", "raw_response": content}
            result = {
                "review_idx": review["review_idx"],
                "original_text": review["original_text"],
                "topics": analysis.get("topics", []),
                "meta": analysis.get("meta", {}),
                "raw_analysis": analysis.get("raw_analysis", ""),
                "raw_response": analysis.get("raw_response", content)
            }
            self._log_json(result)
            return result
        except Exception as e:
            self.logger.error(f"Ошибка анализа отзыва #{review['review_idx']}: {e}")
            return {
                "review_idx": review["review_idx"],
                "original_text": review["original_text"],
                "topics": [],
                "meta": {},
                "raw_analysis": "",
                "raw_response": "",
                "error": str(e)
            }

    def _log_json(self, obj: Dict[str, Any]):
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _split_batches(self, reviews: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Формирует партии по лимитам токенов и количеству отзывов.
        Если отзыв превышает лимит токенов — отдельная партия.
        """
        batches = []
        current_batch = []
        current_tokens = 0
        for review in reviews:
            review_tokens = self._estimate_tokens(review["original_text"])
            # Если отзыв сам по себе превышает лимит — отдельная партия
            if review_tokens > self.max_tokens_per_batch:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
                batches.append([review])
                continue
            # Если добавление приведет к превышению лимита — новая партия
            if (current_tokens + review_tokens > self.max_tokens_per_batch) or (len(current_batch) >= self.max_reviews_per_batch):
                if current_batch:
                    batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            current_batch.append(review)
            current_tokens += review_tokens
        if current_batch:
            batches.append(current_batch)
        return batches

    async def process(self, reviews_file: str) -> List[str]:
        """
        Основной метод: разбивает отзывы на партии, анализирует каждый отзыв, сохраняет результаты.
        Возвращает список файлов партий.
        """
        self.logger.info(f"Старт обработки файла: {reviews_file}")
        # 1. Загрузка отзывов
        with open(reviews_file, "r", encoding="utf-8") as f:
            content = f.read()
        reviews = self._parse_reviews(content)
        self.logger.info(f"Загружено {len(reviews)} отзывов")

        # 2. Анализ каждого отзыва параллельно
        tasks = [
            self._analyze_review(review)
            for review in reviews
        ]
        results = await asyncio.gather(*tasks)

        # 3. Формирование партий
        batches = self._split_batches(results)
        self.logger.info(f"Сформировано {len(batches)} партий")

        # 4. Сохранение партий и карты соответствия
        batch_files = []
        mapping = {}
        for i, batch in enumerate(batches, 1):
            batch_data = {
                "batch_idx": i,
                "reviews": batch,
                "mapping": {str(r["review_idx"]): f"batch_{i}.json" for r in batch}
            }
            batch_file = os.path.join(self.batches_dir, f"batch_{i}.json")
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(batch_data, f, ensure_ascii=False, indent=2)
            batch_files.append(batch_file)
            for r in batch:
                mapping[str(r["review_idx"])] = f"batch_{i}.json"
            self.logger.info(f"Партия {i}: {len(batch)} отзывов, файл: {batch_file}")

        # 5. Сохранение карты соответствия
        mapping_file = os.path.join(self.session_dir, "mapping.json")
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        self.logger.info("Обработка завершена")
        return batch_files

# Пример использования:
# async def main():
#     agent = SplitterAgent(openai_api_key="YOUR_API_KEY")
#     await agent.process("reviews_258375891_prepared_for_ai.txt")
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())