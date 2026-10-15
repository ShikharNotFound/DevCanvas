import os
import asyncio
from dotenv import load_dotenv
from output_store import list_projects, read_project_file, save_text
from llm  import get_llm

load_dotenv()


ARCHITECT_SYSTEM_PROMPT = """
You are a senior software architect. Given a Product Requirements Document (PRD), produce a System Design Document (SDD) in Markdown.

Use this exact structure:

# System Design Document

## 1. Overview
2-4 sentences. What's being built, architectural style, main components.

## 2. Technology Stack
Table: Category | Technology | Why
Include only relevant categories (Frontend, Backend, Database, Auth, Hosting, etc.).

## 3. File & Folder Structure
Text tree showing the recommended project layout. Include real filenames.

## 4. Data Model
For each entity: name, purpose, fields with types, relationships.

## 5. API Endpoints
For each endpoint:
- Method + path (e.g., POST /api/v1/tasks)
- Purpose
- Request body
- Response body
- Status codes
- Auth required (yes/no)

## 6. Core User Flows
For the 2-3 most important flows, describe the sequence of operations (client → API → DB → response).

## 7. Authentication & Authorization
How users authenticate and how access is controlled. Justify the choice.

## 8. External Dependencies
Third-party services and why they're needed.

## 9. Architectural Decisions
3-5 key decisions with brief justifications.

## 10. Out of Scope
Technical concerns NOT addressed in this design.

Rules:
- Return only the SDD in Markdown. No preamble.
- Be specific. Use exact names for tables, routes, fields.
- Do not over-engineer. Prefer simple, mainstream choices.
- Do not include code, only design.
"""

SUMMARIZE_PROMPT = """
Compress the following PRD into a technical brief under 1500 tokens.
Keep: features, users, tech stack mentions, acceptance criteria, constraints.
Remove: prose, repetition, examples, marketing language.
Return only the compressed brief.
"""

async def compress_prd(prd: str) -> str:
    llm = get_llm("architect")
    return await llm.complete(
        system=SUMMARIZE_PROMPT,
        user=prd,
        temperature=0.1,
    )





async def call_llm(system_prompt: str, user_prompt: str) -> str:
    llm = get_llm("architect")
    return await llm.complete(
        system=system_prompt,
        user=user_prompt,
        temperature=0.2,
    )


async def run_architect_agent(prd: str) -> str:
    print("[Architect Agent] Received PRD (", len(prd), "chars )")
    print("[Architect Agent] Calling LLM...\n")
    if len(prd) > 20000:  
            print("[Architect Agent] PRD too large — compressing...")
            prd = await compress_prd(prd)


    sdd = await call_llm(
        system_prompt=ARCHITECT_SYSTEM_PROMPT,
        user_prompt=prd,
    )

    return sdd



def get_user_input() -> str:
    print("=" * 30)
    print("  DevCanvas — Architect Agent")
    print("=" * 30)
    print("Paste the PRD below.")
    print("When finished, type END on its own line and press Enter.")
    print()

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def pick_project() -> str | None:
    projects = list_projects()
    if not projects:
        print("[Architect Agent] No projects found in output/. Run the PM agent first.")
        return None

    print("Available projects:")
    for i, p in enumerate(projects):
        marker = " (latest)" if i == 0 else ""
        print(f"  {i + 1}. {p}{marker}")
    print()

    default = projects[0]
    print(f"Pick a project number [default: 1 = {default}]: ", end="")
    choice = input().strip()

    if not choice:
        return default

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            return projects[idx]
    except ValueError:
        pass

    print(f"[!] Invalid choice. Using default: {default}")
    return default


async def main():
    project_slug = pick_project()
    if not project_slug:
        return

    try:
        prd = read_project_file(project_slug, "prd.md")
    except FileNotFoundError:
        print(f"[!] No prd.md found for project '{project_slug}'. Run the PM agent first.")
        return

    print(f"\n[Architect Agent] Project: {project_slug}")
    print(f"[Architect Agent] Loaded PRD ({len(prd)} chars)\n")

    try:
        sdd = await run_architect_agent(prd)
    except Exception as e:
        print(f"\n[!] Architect agent failed: {e}\n")
        return

    saved_path = save_text(project_slug, "sdd.md", sdd)

    print("=" * 60)
    print(sdd)
    print("=" * 60)
    print(f"\n[Architect Agent] Saved SDD to: {saved_path}\n")


if __name__ == "__main__":
    asyncio.run(main())