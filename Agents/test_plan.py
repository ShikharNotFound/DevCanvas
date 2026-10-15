import asyncio
from dotenv import load_dotenv
from llm import get_llm

load_dotenv()

SIMPLE_SYSTEM = """You are a developer. Given a project description, return ONLY a JSON object with this shape:
{"files": [{"path": "main.py", "purpose": "entry point"}], "assumptions": [], "warnings": []}
No markdown. No prose. Just JSON."""

SIMPLE_USER = "A snake game in a browser. HTML, CSS, JavaScript."


async def main():
    llm = get_llm("developer")

    print("=" * 60)
    print("TEST 1: Can the model respond at all?")
    print("=" * 60)
    try:
        raw = await llm.complete(
            system="Reply with exactly the word: hello",
            user="Say hello",
            temperature=0.2,
        )
        print(f"Response: {raw[:200]!r}")
    except Exception as e:
        print(f"FAILED: {e}")
        return

    print()
    print("=" * 60)
    print("TEST 2: Can the model produce JSON?")
    print("=" * 60)
    try:
        raw = await llm.complete(
            system=SIMPLE_SYSTEM,
            user=SIMPLE_USER,
            temperature=0.2,
            json_mode=True,
        )
        print(f"Response: {raw[:500]!r}")
    except Exception as e:
        print(f"FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())