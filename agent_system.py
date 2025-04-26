import os
import uuid
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

class SplitterAgent:
    """
    Асинхронный агент для разбиения отзывов на партии, семантического анализа тем и сохранения результатов.
    """

    def __init__(
        self,
        openai_api_key: str,
        max_workers: Optional[int] = None,
        session_dir: Optional[str] = None,
        separator: str = "------------------------------"
    ):
        self.openai_api_key = openai_api_key
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
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    async def analyze_review(self, review: str, review_idx: int) -> Dict[str, Any]:
        """
        Анализирует отзыв с помощью OpenAI GPT-4 mini для извлечения тем и метаданных.
        """
        prompt = (
            "Проанализируй следующий отзыв. "
            "Верни JSON с полями: topics (список тем), meta (словарь с любыми найденными метаданными), "
            "raw_analysis (твой полный анализ в свободной форме), "
            "raw_response (весь твой ответ, включая JSON и текст). "
            "Если есть поля 'Рейтинг', 'Дата', 'Текст отзыва' — выдели их явно в meta.\n\n"
            f"Отзыв:\n{review}"
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
                "review_idx": review_idx,
                "original_text": review,
                "topics": analysis.get("topics", []),
                "meta": analysis.get("meta", {}),
                "raw_analysis": analysis.get("raw_analysis", ""),
                "raw_response": analysis.get("raw_response", content)
            }
            self._log_json(result)
            return result
        except Exception as e:
            self.logger.error(f"Ошибка анализа отзыва #{review_idx}: {e}")
            return {
                "review_idx": review_idx,
                "original_text": review,
                "topics": [],
                "meta": {},
                "raw_analysis": "",
                "raw_response": "",
                "error": str(e)
            }

    def _log_json(self, obj: Dict[str, Any]):
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    async def process(self, reviews_file: str) -> List[str]:
        """
        Основной метод: разбивает отзывы на партии, анализирует каждый отзыв, сохраняет результаты.
        Возвращает список файлов партий.
        """
        self.logger.info(f"Старт обработки файла: {reviews_file}")
        # 1. Загрузка отзывов
        with open(reviews_file, "r", encoding="utf-8") as f:
            content = f.read()
        raw_reviews = content.split(self.separator)
        reviews = [r.strip() for r in raw_reviews if r.strip()]
        self.logger.info(f"Загружено {len(reviews)} отзывов")

        # 2. Анализ каждого отзыва параллельно
        tasks = [
            self.analyze_review(review, idx)
            for idx, review in enumerate(reviews, 1)
        ]
        results = await asyncio.gather(*tasks)

        # 3. Формирование партий (по 3000 токенов, грубо: 1 токен ~ 4 символа)
        batches = []
        current_batch = []
        current_tokens = 0
        batch_files = []
        batch_map = []
        safe_batch_limit = 3000

        for res in results:
            review_text = res["original_text"]
            review_tokens = len(review_text) // 4
            if current_tokens + review_tokens > safe_batch_limit and current_batch:
                batches.append(current_batch)
                batch_map.append([r["review_idx"] for r in current_batch])
                current_batch = []
                current_tokens = 0
            current_batch.append(res)
            current_tokens += review_tokens
        if current_batch:
            batches.append(current_batch)
            batch_map.append([r["review_idx"] for r in current_batch])

        self.logger.info(f"Сформировано {len(batches)} партий")

        # 4. Сохранение партий и карты соответствия
        for i, batch in enumerate(batches, 1):
            batch_data = {
                "batch_idx": i,
                "reviews": batch,
                "mapping": {str(r["review_idx"]): i for r in batch}
            }
            batch_file = os.path.join(self.batches_dir, f"batch_{i}.json")
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(batch_data, f, ensure_ascii=False, indent=2)
            batch_files.append(batch_file)
            self.logger.info(f"Партия {i}: {len(batch)} отзывов, файл: {batch_file}")

        self.logger.info("Обработка завершена")
        return batch_files

# Пример использования:
async def main():
    # Укажите ваш API-ключ
    api_key = "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"  # Замените на ваш реальный ключ
    # Укажите путь к файлу с отзывами
    reviews_file = "reviews_258375891_prepared_for_ai.txt"  # Замените на ваш файл
    # Создайте экземпляр SplitterAgent
    agent = SplitterAgent(openai_api_key=api_key)
    # Запустите обработку
    await agent.process(reviews_file)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())