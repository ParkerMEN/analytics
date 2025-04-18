"""
Модуль для полной автоматизации процесса анализа отзывов:
1. Сбор отзывов с Wildberries
2. Подготовка данных для анализа
3. Анализ данных с помощью AI
4. Визуализация результатов
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_command(command, description):
    """Запускает команду и выводит результат выполнения"""
    print(f"\n=== {description} ===")
    process = subprocess.run(command, text=True)
    if process.returncode != 0:
        print(f"Ошибка при выполнении этапа: {description}")
        return False
    return True

def main():
    """Основная функция для запуска полного процесса анализа"""
    parser = argparse.ArgumentParser(description="Полный процесс анализа отзывов")
    parser.add_argument("article", help="Артикул товара на Wildberries")
    parser.add_argument("--skip-parser", action="store_true", help="Пропустить этап сбора отзывов")
    parser.add_argument("--skip-analyzer", action="store_true", help="Пропустить этап подготовки данных")
    parser.add_argument("--skip-ai", action="store_true", help="Пропустить этап AI-анализа")
    parser.add_argument("--skip-viz", action="store_true", help="Пропустить этап визуализации")
    args = parser.parse_args()

    article = args.article
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Создаем лог-директорию для данного запуска
    log_dir = f"logs/run_{timestamp}"
    os.makedirs(log_dir, exist_ok=True)
    
    # Создаем необходимые директории для PDF и диаграмм
    # Это важно для правильного выполнения chat_gpt.py
    pdf_dir = "pdf_reports"
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Создаём каталог для анализа заранее, чтобы использовать его имя в отчете
    session_dir = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    charts_dir = os.path.join(session_dir, "charts")
    scripts_dir = os.path.join(session_dir, "scripts") 
    responses_dir = os.path.join(session_dir, "responses")
    analysis_pdf_dir = os.path.join(session_dir, "pdf_reports")
    
    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(responses_dir, exist_ok=True)
    os.makedirs(analysis_pdf_dir, exist_ok=True)
    
    # Этап 1: Парсинг отзывов с Wildberries
    if not args.skip_parser:
        if not run_command(["python", "parserWB.py", article], "Сбор отзывов с Wildberries"):
            return
    
    # Проверяем, что файл с отзывами существует
    json_file = f"reviews_{article}.json"
    if not os.path.exists(json_file) and not args.skip_analyzer:
        print(f"Ошибка: Файл с отзывами не найден: {json_file}")
        print("Пожалуйста, сначала запустите parserWB.py для сбора отзывов.")
        return
    
    # Этап 2: Подготовка данных для анализа
    if not args.skip_analyzer:
        if not run_command(["python", "analyzer.py", json_file], "Подготовка данных для анализа"):
            return
    
    # Проверяем, что файл с подготовленными отзывами существует
    prepared_file = f"reviews_{article}_prepared_for_ai.txt"
    if not os.path.exists(prepared_file) and not args.skip_ai:
        print(f"Ошибка: Файл с подготовленными отзывами не найден: {prepared_file}")
        return
    
    # Этап 3: Анализ данных с помощью AI
    if not args.skip_ai:
        if not run_command(["python", "reviews_analyzer.py", prepared_file], "Анализ данных с помощью AI"):
            return
    
    # Проверяем, что файл с аналитикой существует
    analytics_file = f"reviews_{article}_prepared_for_ai_analytics.txt"
    if not os.path.exists(analytics_file) and not args.skip_viz:
        print(f"Ошибка: Файл с аналитикой не найден: {analytics_file}")
        return
    
    # Этап 4: Визуализация результатов
    if not args.skip_viz:
        # Запуск chat_gpt.py с путём к анализу и указанием созданной директории
        if not run_command(["python", "chat_gpt.py", analytics_file, "--session-dir", session_dir], "Визуализация результатов"):
            return
    
    # Создаем отчет о выполнении
    print("\n=== Процесс анализа завершен ===")
    print(f"Артикул: {article}")
    print(f"Время запуска: {timestamp}")
    print("Созданные файлы:")
    if not args.skip_parser:
        print(f"- JSON с отзывами: {json_file}")
    if not args.skip_analyzer:
        print(f"- Подготовленные отзывы: {prepared_file}")
    if not args.skip_ai:
        print(f"- Аналитический отчет: {analytics_file}")
    if not args.skip_viz:
        print(f"- Визуализация: см. директорию {session_dir}")
        
        # Если был создан итоговый PDF-отчет, показываем его путь
        final_pdf = os.path.join(session_dir, f"report_{article}.pdf")
        if os.path.exists(final_pdf):
            print(f"- Итоговый PDF-отчет: {final_pdf}")

if __name__ == "__main__":
    main()