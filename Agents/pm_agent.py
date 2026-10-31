import asyncio
from dotenv import load_dotenv
from output_store import save_text
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

async def run_pm_agent(project_slug: str, project_description: str) -> str:
    """Generates the PRD, saves it, and returns the path."""
    print(f"[PM Agent] Received description for project: {project_slug}")
    
    prd = await call_llm(
        system_prompt=PM_SYSTEM_PROMPT,
        user_prompt=project_description,
    )

    saved_path = save_text(project_slug, "prd.md", prd)
    print(f"[PM Agent] PRD saved to: {saved_path}")
    
    return str(saved_path)