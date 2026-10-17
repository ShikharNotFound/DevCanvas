"""
Developer Agent — plan → checkpoint → execute → validate → review.

Reads an SDD from a project folder.
Produces a file manifest for human approval.
Then generates code file-by-file.
Saves to output/<project>/code/.
"""
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from llm import get_llm
from output_store import (
    list_projects,
    read_project_file,
    get_project_dir,
)

load_dotenv()


# ─────────────────────────────────────────────────────────────
# PHASE 1 — PLAN  (short prompt, works on any model)
# ─────────────────────────────────────────────────────────────
PLAN_SYSTEM_PROMPT = """
You are a senior developer. Given a System Design Document (SDD), list the files needed to implement it.

Return ONLY a JSON object with this structure:

{
  "files": [
    {"path": "relative/path.ext", "purpose": "one-line purpose"}
  ],
  "assumptions": [],
  "warnings": []
}

Rules:
- Use paths from the SDD's file structure if it has one.
- Include config files (.env.example, requirements.txt, etc.).
- Never include a real ".env" file.
- Return only JSON. No markdown fences. No explanation.
- Keep the list focused. 5 to 15 files for a small project.

Example for a browser snake game:
{"files": [{"path": "index.html", "purpose": "main HTML page"}, {"path": "styles.css", "purpose": "CSS styles"}, {"path": "script.js", "purpose": "game logic"}], "assumptions": [], "warnings": []}
"""

async def plan_developer_agent(sdd: str) -> dict:
    print("[Developer] Phase 1 : Planning file manifest...")
    llm = get_llm("developer")

    # Truncate long SDDs — local models choke on huge prompts
    if len(sdd) > 20000:
        print(f"  [note] SDD is {len(sdd)} chars, truncating to 20000 for plan phase")
        sdd = sdd[:20000] + "\n\n[... SDD truncated for plan phase ...]"

    raw = await llm.complete(
        system=PLAN_SYSTEM_PROMPT,
        user=sdd,
        temperature=0.2,
    )

    print(f"  [debug] Response preview: {raw[:300]!r}")

    # Strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    parsed = json.loads(cleaned)
    if "files" not in parsed or not isinstance(parsed["files"], list):
        raise ValueError(
            f"Plan missing 'files' array. Got keys: {list(parsed.keys())}"
        )

    return parsed




# ─────────────────────────────────────────────────────────────
# HUMAN CHECKPOINT — approve/edit the plan
# ─────────────────────────────────────────────────────────────
def review_plan(plan: dict) -> dict | str | None:
    files = plan.get("files", [])
    assumptions = plan.get("assumptions", [])
    warnings = plan.get("warnings", [])

    while True:
        print("\n" + "=" * 60)
        print(f"PLAN — {len(files)} files")
        print("=" * 60)

        for i, f in enumerate(files, 1):
            print(f"  {i:>2}. {f['path']}")
            print(f"      {f.get('purpose', '')}")

        if assumptions:
            print("\n  Assumptions:")
            for a in assumptions:
                print(f"    • {a}")

        if warnings:
            print("\n  Warnings:")
            for w in warnings:
                print(f"    ⚠ {w}")

        print("\n  Commands:")
        print("    [enter] accept and proceed")
        print("    [r N]   remove file N")
        print("    [a]     add a file")
        print("    [n]     add a note (injected into generation)")
        print("    [p]     re-plan with notes")
        print("    [q]     cancel")
        print()

        cmd = input("> ").strip().lower()

        if cmd == "":
            return plan

        if cmd == "q":
            return None

        if cmd == "n":
            note = input("Note for the developer: ").strip()
            if note:
                plan.setdefault("notes", []).append(note)

        elif cmd.startswith("r "):
            try:
                idx = int(cmd[2:]) - 1
                if 0 <= idx < len(files):
                    removed = files.pop(idx)
                    print(f"  Removed: {removed['path']}")
                else:
                    print("  Invalid index.")
            except ValueError:
                print("  Usage: r N (e.g., r 3)")

        elif cmd == "a":
            path = input("Path: ").strip()
            purpose = input("Purpose: ").strip()
            if path:
                files.append({"path": path, "purpose": purpose})
                print(f"  Added: {path}")

        elif cmd == "p":
            return "__REPLAN__"

        else:
            print("  Unknown command.")





# ─────────────────────────────────────────────────────────────
# PHASE 2 — EXECUTE  (short prompt, one file at a time)
# ─────────────────────────────────────────────────────────────
FILE_SYSTEM_PROMPT = """
You are a senior developer. Write ONE file for a project.

You will receive:
- An excerpt of the System Design Document (SDD)
- The full file manifest
- The specific file to write (path + purpose)
- Any user notes

Return ONLY the raw file contents. No markdown fences. No explanations.
No placeholders like "..." or "# TODO". Complete, runnable code.

Rules:
- Read secrets from environment variables, never hardcode them.
- Follow the SDD's tech stack and API contracts.
- Use imports that exist in the file manifest.
- Match naming and conventions used elsewhere in the project.
"""

async def generate_file(sdd: str, manifest: dict, target: dict, notes: list) -> str:
    llm = get_llm("developer")

    # Keep SDD excerpt small so local models stay coherent
    sdd_excerpt = sdd[:12000] if len(sdd) > 12000 else sdd

    manifest_summary = "\n".join(
        f"  - {f['path']} : {f.get('purpose', '')}"
        for f in manifest.get("files", [])
    )

    notes_text = "\n".join(f"  - {n}" for n in notes) if notes else "  (none)"

    user = f"""SDD (excerpt):
{sdd_excerpt}

FILE MANIFEST:
{manifest_summary}

YOUR TASK — write this file:
  Path: {target['path']}
  Purpose: {target.get('purpose', '')}

USER NOTES:
{notes_text}

Return only the raw file contents.
"""

    raw = await llm.complete(
    system=FILE_SYSTEM_PROMPT,
    user=user,
    temperature=0.2,
    )

    # Strip markdown fences if the model wrapped the file in them
    content = raw.strip()
    if content.startswith("```"):
        # remove opening fence (```lang or just ```)
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1:]
        # remove closing fence
        if content.rstrip().endswith("```"):
            content = content.rstrip()[:-3].rstrip()
    
    return content





# ─────────────────────────────────────────────────────────────
# PHASE 3 — VALIDATE
# ─────────────────────────────────────────────────────────────
SECRET_PATTERNS = [
    "sk_live_", "sk_test_", "AKIA", "ghp_", "gho_",
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
]

def validate_file(path: str, content: str) -> list[str]:
    issues = []

    if not content.strip():
        issues.append("empty file")

    for pattern in SECRET_PATTERNS:
        if pattern in content:
            issues.append(f"contains a likely secret: {pattern}")

    placeholders = ["# TODO", "# implement", "pass  # stub", "... rest of code"]
    for p in placeholders:
        if p in content:
            issues.append(f"contains a placeholder: {p!r}")

    if Path(path).name == ".env":
        issues.append("real .env files are not allowed — use .env.example")

    if path.endswith(".py"):
        try:
            compile(content, path, "exec")
        except SyntaxError as e:
            issues.append(f"python syntax error: {e.msg} (line {e.lineno})")

    return issues




# ─────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────
def save_generated_files(project_slug: str, files: list[dict]) -> Path:
    code_dir = get_project_dir(project_slug) / "code"
    code_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        p = code_dir / f["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f["content"], encoding="utf-8")
    return code_dir





# ─────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────
def pick_project() -> str | None:
    projects = list_projects()
    if not projects:
        print("[Developer] No projects found. Run PM and Architect first.")
        return None

    print("Available Projects: ")
    for i, p in enumerate(projects, 1):
        print(f"  {i}. {p}{' (latest)' if i == 1 else ''}")
    default = projects[0]
    choice = input(f"Pick [default: 1 = {default}]: ").strip()
    if not choice:
        return default
    try:
        idx = int(choice) - 1
        return projects[idx] if 0 <= idx < len(projects) else default
    except ValueError:
        return default

async def review_files(
    project_slug: str,
    sdd: str,
    plan: dict,
    notes: list,
    files_out: list[dict],
) -> list[dict] | None:
    """
    Interactive per-file review.
    Returns the final list of files to save, or None to cancel.
    """
    purpose_by_path = {f["path"]: f.get("purpose", "") for f in plan.get("files", [])}

    while True:
        print("\n" + "=" * 60)
        print("REVIEW")
        print("=" * 60)
        for i, f in enumerate(files_out, 1):
            status = "✓" if not f["issues"] else "⚠"
            lines = f["content"].count("\n") + 1
            flag = ""
            if f["issues"]:
                flag = f"  ({f['issues'][0]})"
            print(f"  {status} {i:>2}. {f['path']:<40} {lines:>4} lines{flag}")

        print("\nCommands:")
        print("  [enter] save all and finish")
        print("  [v N]   view file N")
        print("  [r N]   regenerate file N (with a note)")
        print("  [d N]   drop file N from output")
        print("  [q]     cancel — nothing saved")

        cmd = input("\n> ").strip().lower()

        if cmd == "":
            return files_out

        if cmd == "q":
            return None

        if cmd.startswith("v "):
            try:
                idx = int(cmd[2:]) - 1
                if 0 <= idx < len(files_out):
                    print("\n" + "─" * 60)
                    print(files_out[idx]["content"])
                    print("─" * 60)
                    input("Press Enter to return to review...")
                else:
                    print("  Invalid index.")
            except ValueError:
                print("  Usage: v N")

        elif cmd.startswith("r "):
            try:
                idx = int(cmd[2:]) - 1
                if not (0 <= idx < len(files_out)):
                    print("  Invalid index.")
                    continue

                target = files_out[idx]
                note = input("  Regeneration note (why/what to change): ").strip()
                print(f"  Regenerating {target['path']}...")

                new_content = await generate_file(
                    sdd=sdd,
                    manifest=plan,
                    target={
                        "path": target["path"],
                        "purpose": purpose_by_path.get(target["path"], ""),
                    },
                    notes=notes + ([note] if note else []),
                )
                new_issues = validate_file(target["path"], new_content)

                target["content"] = new_content
                target["issues"] = new_issues

                if new_issues:
                    print("  ⚠ Still has issues:")
                    for issue in new_issues:
                        print(f"      - {issue}")
                else:
                    print(f"  ✓ Regenerated cleanly ({len(new_content)} chars)")
            except ValueError:
                print("  Usage: r N")

        elif cmd.startswith("d "):
            try:
                idx = int(cmd[2:]) - 1
                if 0 <= idx < len(files_out):
                    removed = files_out.pop(idx)
                    print(f"  Dropped: {removed['path']}")
                else:
                    print("  Invalid index.")
            except ValueError:
                print("  Usage: d N")

        else:
            print("  Unknown command.")

async def main():
    project_slug = pick_project()
    if not project_slug:
        return

    try:
        sdd = read_project_file(project_slug, "sdd.md")
    except FileNotFoundError:
        print(f"[!] No sdd.md for '{project_slug}'. Run the Architect first.")
        return

    print(f"\n[Developer] Project: {project_slug} ({len(sdd)} chars)\n")

    # ── Phase 1: Plan ──
    try:
        plan = await plan_developer_agent(sdd)
    except Exception as e:
        print(f"[!] Planning failed: {e}")
        return

    # ── Checkpoint: review plan ──
    while True:
        result = review_plan(plan)
        if result is None:
            print("Cancelled.")
            return
        if result == "__REPLAN__":
            notes = plan.get("notes", [])
            augmented = sdd + "\n\nUSER NOTES:\n" + "\n".join(notes)
            plan = await plan_developer_agent(augmented)
            continue
        plan = result
        break

    # Save the approved plan
    project_dir = get_project_dir(project_slug)
    (project_dir / "plan.json").write_text(
        json.dumps(plan, indent=2), encoding="utf-8"
    )

    # ── Phase 2 & 3: Execute + validate ──
    notes = plan.get("notes", [])
    files_out = []

    plan_files = plan.get("files", [])
    if not plan_files:
        print("[!] Plan contains 0 files. Nothing to generate.")
        print(f"    Saved plan for inspection: {project_dir / 'plan.json'}")
        return

    for i, f in enumerate(plan_files, 1):
        print(f"\n[Developer] ({i}/{len(plan_files)}) Generating {f['path']}...")
        try:
            content = await generate_file(sdd, plan, f, notes)
        except Exception as e:
            print(f"  ✗ Generation failed: {e}")
            continue

        issues = validate_file(f["path"], content)
        if issues:
            print("  ⚠ Issues found:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print(f"  ✓ {len(content)} chars, clean")

        files_out.append({
            "path": f["path"],
            "content": content,
            "issues": issues,
        })

    # ── Human review loop ──
    files_out = await review_files(
        project_slug=project_slug,
        sdd=sdd,
        plan=plan,
        notes=notes,
        files_out=files_out,
    )

    if files_out is None:
        print("Cancelled — no files saved.")
        return

    code_dir = save_generated_files(project_slug, files_out)
    print(f"\n[Developer] Saved {len(files_out)} files to: {code_dir}\n")



if __name__ == "__main__":
    asyncio.run(main())