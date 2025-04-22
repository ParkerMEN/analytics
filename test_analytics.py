from analytics_agent import AnalyticsAgent

def main():
    """Запускает анализ отзывов и генерирует отчет"""
    agent = AnalyticsAgent("all_reviews.json", output_dir="analytics_output")
    report, html_path = agent.run_analysis()
    
    print(f"Анализ завершен. Отчет доступен по пути: {html_path}")
    print(f"Обнаружено метрик: {len(report['metrics'])}")
    print(f"Выявлено инсайтов: {len(report['insights'])}")
    print(f"Создано визуализаций: {len(report['visualizations'])}")
    
    # Выводим ключевые инсайты
    print("\nКлючевые выводы:")
    for insight in report["insights"]:
        print(f"- {insight['title']}: {insight['description']}")

if __name__ == "__main__":
    main()