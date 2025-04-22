import asyncio
from splitter_agent import SplitterAgent

async def main():
    agent = SplitterAgent(openai_api_key="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")
    batch_files = await agent.process("reviews_258375891_prepared_for_ai.txt")
    print("Созданы файлы партий:")
    for f in batch_files:
        print(f)

if __name__ == "__main__":
    asyncio.run(main())