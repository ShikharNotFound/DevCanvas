import asyncio
from llm import get_llm


async def main():
    llm = get_llm("default")

    print("Testing default provider...")
    response = await llm.complete(
        system="You are a helpful assistant.",
        user="Say 'hello' in exactly one word.",
    )
    print("Response:", response)

    print("\nTesting JSON mode...")
    llm_json = get_llm("developer")
    response = await llm_json.complete(
        system="Return only a JSON object with keys 'ok' and 'message'.",
        user="Return ok=true and message='working'.",
        json_mode=True,
    )
    print("Response:", response)


if __name__ == "__main__":
    asyncio.run(main())