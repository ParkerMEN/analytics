# Импорт необходимых библиотек
from gpt_agent import GPTAgent
from data_processing_agent import DataProcessingAgent
from visualization_agent import VisualizationAgent
import time
import sys
import os
import json
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis.log", encoding="utf-8"),  # Указываем кодировку UTF-8
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_gpt_agent")

def main():
    # Выводим информацию о начале процесса
    logger.info("Запуск процесса анализа отзывов...")
    
    # Инициализация агентов
    data_agent = DataProcessingAgent(session_dir="session_5b629caa-c39f-440a-82ad-a37598306f2f")
    api_key = "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"
    gpt_agent = GPTAgent(api_key=api_key)
    viz_agent = VisualizationAgent(api_key=api_key)

    # Создаем директории для результатов анализа
    os.makedirs("analysis_results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("analytics_output/visualizations", exist_ok=True)

    # Загрузка и обработка данных
    logger.info("Загрузка отзывов из batches...")
    start_time = time.time()
    reviews = data_agent.load_batches()
    load_time = time.time() - start_time
    logger.info(f"Загружено {len(reviews)} отзывов за {load_time:.2f} секунд")

    # Извлечение ключевых метаданных
    logger.info("Извлечение и обработка ключевых метаданных...")
    start_time = time.time()
    key_metadata = data_agent.extract_key_metadata(reviews)
    extract_time = time.time() - start_time
    logger.info(f"Обработано {len(key_metadata)} отзывов за {extract_time:.2f} секунд")

    # Сохраняем промежуточные данные
    logger.info("Сохранение промежуточных данных...")
    with open("analysis_results/processed_metadata_sample.json", "w", encoding="utf-8") as f:
        json.dump(key_metadata[:10], f, ensure_ascii=False, indent=2)  # Сохраняем только 10 примеров для проверки

    # Также сохраним статистику о полных метаданных
    stats = {
        "total_reviews": len(key_metadata),
        "reviews_with_rating": sum(1 for r in key_metadata if "rating" in r),
        "reviews_with_topics": sum(1 for r in key_metadata if "all_topics" in r),
        "reviews_with_text": sum(1 for r in key_metadata if "combined_text" in r),
        "reviews_with_pros": sum(1 for r in key_metadata if "pros" in r),
        "reviews_with_cons": sum(1 for r in key_metadata if "cons" in r),
        "total_topics": sum(len(r.get("all_topics", [])) for r in key_metadata),
    }
    with open("analysis_results/metadata_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Статистика метаданных: {stats}")

    # Анализ данных с помощью GPT
    logger.info("Запуск глубокого анализа данных с помощью GPT...")
    start_time = time.time()
    try:
        hidden_patterns = gpt_agent.analyze_hidden_patterns(key_metadata)
        analysis_time = time.time() - start_time
        logger.info(f"Анализ завершен за {analysis_time:.2f} секунд")

        # Вывод результатов анализа
        print("\n== Результаты анализа ==")
        preview = hidden_patterns[:500] + "..." if len(hidden_patterns) > 500 else hidden_patterns
        print(f"{preview}\n(показаны первые 500 символов)")

        # Сохранение результатов в файл
        result_file = "analysis_results/hidden_patterns_analysis.txt"
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(hidden_patterns)
        logger.info(f"Полные результаты сохранены в файл: {result_file}")
    
    except Exception as e:
        logger.error(f"Произошла ошибка при анализе данных: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

    # Генерация визуализаций на основе анализа
    logger.info("Генерация визуализаций на основе анализа...")
    viz_agent = VisualizationAgent(api_key=api_key)
    try:
        generated_files = viz_agent.generate_visualizations(key_metadata, hidden_patterns)
        logger.info(f"Создано {len(generated_files)} файлов с кодом визуализаций")
        
        # Log created files
        for file_path in generated_files:
            logger.info(f"Создан файл визуализации: {file_path}")
        
        logger.info(f"Все результаты визуализации сохранены в директории: {viz_agent.output_dir}")
    except Exception as e:
        logger.error(f"Произошла ошибка при генерации визуализаций: {str(e)}")

    # Генерация визуализаций
    logger.info("Запуск генерации визуализаций...")
    try:
        recommendations = None
        if os.path.exists("visualization_recommendations.txt"):
            with open("visualization_recommendations.txt", "r", encoding="utf-8") as f:
                recommendations = f.read()
                logger.info("Загружены рекомендации по визуализации")
        
        generated_files = viz_agent.generate_visualizations(key_metadata, recommendations)
        logger.info(f"Создано {len(generated_files)} файлов с кодом визуализаций")
        
        # Выводим список созданных файлов
        for file_path in generated_files:
            logger.info(f"Создан файл: {file_path}")
    
    except Exception as e:
        logger.error(f"Произошла ошибка при генерации визуализаций: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()