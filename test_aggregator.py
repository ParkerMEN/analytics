from aggregator_agent import AggregatorAgent

def main():
    batches_dir = "session_8def6620-ef40-4d6f-b0c0-fc7578e3428f/batches"  # замените на вашу папку с партиями
    output_file = "all_reviews.json"
    agent = AggregatorAgent(batches_dir=batches_dir)
    all_reviews = agent.aggregate()
    agent.save_aggregated(output_file, all_reviews)
    print(f"Собрано отзывов: {len(all_reviews)}. Сохранено в {output_file}")

if __name__ == "__main__":
    main()