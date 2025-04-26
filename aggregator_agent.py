import os
import json
import logging
from typing import List, Dict, Any, Optional

class AggregatorAgent:
    """
    Агент для сбора, проверки полноты и агрегации данных по всем отзывам из batch-файлов SplitterAgent.
    Гарантирует отсутствие пропусков и дублей, формирует единую структуру для аналитики и визуализации.
    """

    def __init__(self, batches_dir: str, mapping_file: Optional[str] = None, log_file: Optional[str] = None):
        self.batches_dir = batches_dir
        self.mapping_file = mapping_file or os.path.join(os.path.dirname(batches_dir), "mapping.json")
        self.log_file = log_file or os.path.join(os.path.dirname(batches_dir), "aggregator.log")
        self._setup_logging()

    def _setup_logging(self):
        self.logger = logging.getLogger(f"AggregatorAgent_{self.batches_dir}")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(fh)

    def _load_batches(self) -> List[Dict[str, Any]]:
        """
        Загружает все batch_x.json из batches_dir.
        """
        batches = []
        for fname in sorted(os.listdir(self.batches_dir)):
            if fname.startswith("batch_") and fname.endswith(".json"):
                path = os.path.join(self.batches_dir, fname)
                with open(path, "r", encoding="utf-8") as f:
                    batch = json.load(f)
                    batches.append(batch)
        self.logger.info(f"Загружено партий: {len(batches)}")
        return batches

    def _load_mapping(self) -> Dict[str, str]:
        """
        Загружает карту соответствия review_idx -> batch_x.json.
        """
        if not os.path.exists(self.mapping_file):
            self.logger.warning("Файл mapping.json не найден.")
            return {}
        with open(self.mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        return mapping

    def aggregate(self) -> List[Dict[str, Any]]:
        """
        Собирает все отзывы из batch-файлов, проверяет уникальность и полноту.
        Возвращает список всех отзывов для дальнейшей аналитики.
        """
        batches = self._load_batches()
        all_reviews = []
        seen_idx = set()
        for batch in batches:
            for review in batch.get("reviews", []):
                idx = str(review.get("review_idx"))
                if idx in seen_idx:
                    self.logger.error(f"Дублирующий review_idx: {idx}")
                    continue
                seen_idx.add(idx)
                all_reviews.append(review)
        self.logger.info(f"Собрано отзывов: {len(all_reviews)} (уникальных review_idx: {len(seen_idx)})")
        # Проверка на пропуски (если mapping.json есть)
        mapping = self._load_mapping()
        if mapping:
            missing = set(mapping.keys()) - seen_idx
            if missing:
                self.logger.error(f"Пропущены review_idx: {sorted(missing)}")
            else:
                self.logger.info("Все отзывы из mapping.json учтены.")
        return all_reviews

    def save_aggregated(self, output_file: str, reviews: List[Dict[str, Any]]):
        """
        Сохраняет агрегированные отзывы в единый JSON-файл.
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Агрегированные отзывы сохранены в {output_file}")

if __name__ == "__main__":
    # Пример использования:
    batches_dir = "session_8def6620-ef40-4d6f-b0c0-fc7578e3428f/batches"  # Укажите путь к папке с batch-файлами
    output_file = "all_reviews.json"  # Укажите имя выходного файла

    agent = AggregatorAgent(batches_dir=batches_dir)
    all_reviews = agent.aggregate()
    agent.save_aggregated(output_file, all_reviews)
    print(f"Собрано отзывов: {len(all_reviews)}. Сохранено в {output_file}")