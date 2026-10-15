import asyncio
from dotenv import load_dotenv
from output_store import slugify, save_text
from llm import get_llm

load_dotenv()

PM_SYSTEM_PROMPT = """
You are a senior product manager. Given a short project description, write a Product Requirements Document (PRD) in Markdown.

Use this exact structure:

# Product Requirements Document

## 1. Overview
2-4 sentences on what the product is, who it's for, and the core problem it solves.

## 2. Goals
3-6 measurable product goals.

## 3. Target Users
Bulleted list. For each: who they are, their goal, their main pain point.

## 4. Key Features
4-8 features. For each:
- **Feature Name** — one-line purpose
- Priority: P0 (must have), P1 (should have), P2 (later)
- Brief description of behavior

## 5. User Flow
Numbered steps for the main user journey.

## 6. Functional Requirements
Bulleted list using IDs like FR-01, FR-02, etc. Each must be specific and testable.

## 7. Non-Functional Requirements
Performance, security, reliability, etc. Use measurable targets where possible.

## 8. MVP Scope
- Must Have: core features
- Should Have: important but deferrable
- Later: out of scope for MVP

## 9. Success Metrics
3-5 metrics that show the product is working.

## 10. Assumptions
Any assumptions you made because the description was incomplete.

Rules:
- Return only the PRD in Markdown. No preamble.
- Be specific, not vague. No marketing language.
- Keep it focused. Do not invent features not implied by the description.
"""

async def call_llm(system_prompt: str, user_prompt: str) -> str:
    llm = get_llm("pm")
    return await llm.complete(
        system=system_prompt,
        user=user_prompt,
        temperature=0.3,
    )


async def run_pm_agent(project_description: str) -> str:
    """The PM agent: description in, PRD out."""
    print("[PM Agent] Received:", project_description[:60], "...")
    print("[PM Agent] Calling LLM...")

    prd = await call_llm(
        system_prompt=PM_SYSTEM_PROMPT,
        user_prompt=project_description,
    )

    print("[PM Agent] PRD generated.\n")
    return prd




def get_user_input() -> str:
    """Ask the user for a project description."""
    print("=" * 30)
    print("  DevCanvas — PM Agent")
    print("=" * 30)
    print("Describe the software you want to build.")
    print("(Type your description and press Enter. Type 'quit' to exit.)")
    print()
    description = input("> ").strip()
    return description


def ask_project_name() -> str:
    print("Project name (e.g. 'Foodie App'): ", end="")
    name = input().strip()
    if not name:
        name = "untitled"
    return slugify(name)


async def main():
    project_slug = ask_project_name()
    print(f"[PM Agent] Project: {project_slug}\n")

    description = get_user_input()

    if not description:
        print("\n[!] Empty description. Exiting.\n")
        return

    try:
        prd = await run_pm_agent(description)
    except Exception as e:
        print(f"\n[!] PM agent failed: {e}\n")
        return

    saved_path = save_text(project_slug, "prd.md", prd)

    print("=" * 60)
    print(prd)
    print("=" * 60)
    print(f"\n[PM Agent] Saved PRD to: {saved_path}\n")


if __name__ == "__main__":
    asyncio.run(main())