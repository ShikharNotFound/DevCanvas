import asyncio
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Functions from the files
from llm import get_llm
from output_store import get_project_dir, list_projects, read_project_file

load_dotenv()

# ── Configuration & Limits ──
MAX_SDD_CHARS = 20000
MAX_FILES = 50             
MAX_FILE_BYTES = 1_000_000  
DOC_EXTS = (".md", ".txt", ".rst", ".adoc")

# ── Security Patterns ──
SECRET_PATTERNS = (
    "sk_live_", "sk_test_", "AKIA", "ghp_", "gho_",
    "-----BEGIN PRIVATE KEY-----", "-----BEGIN RSA PRIVATE KEY-----"
)

DANGEROUS_CODE_PATTERNS = (
    r"\beval\s*\(", r"\bexec\s*\(", 
    r"os\.system\s*\(", r"subprocess\.(?:run|call|Popen)\s*\([^)]*shell\s*=\s*True",
    r"child_process\.exec\s*\("
)

SECRET_ASSIGN_REGEX = re.compile(
    r"(?i)(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*['\"]([^'\"]{8,})['\"]"
)

# ── Prompts ──
PLAN_PROMPT = """
You are a senior developer. Given a System Design Document (SDD), list the files needed to implement it.

Return ONLY a JSON object with this structure:
{
  "files": [{"path": "relative/path.ext", "purpose": "one-line purpose"}]
}

Rules:
- Use paths from the SDD's file structure.
- Include config files (.env.example).
- Never include a real ".env" file.
- **ASSETS RULE: If the project needs icons, logos, or simple graphics, plan for `.svg` files. NEVER plan for `.png`, `.jpg`, or other binary files because you are a text model.**
- Return only JSON. No markdown fences. No explanation.
"""
FILE_PROMPT = """
You are a senior developer. Write ONE file for a project.

You will receive:
- An excerpt of the SDD
- The full file manifest
- The specific file to write

Return ONLY the raw file contents. No markdown fences. No explanations.
No placeholders like "..." or "# TODO". Complete, runnable code.

CRITICAL FRAMEWORK RULES:
- If writing Express.js routes (Node.js), ALWAYS pass a function or an async function as the callback: `router.post('/path', (req, res) => { ... })` or `router.post('/path', controllerFunction)`. NEVER pass an object to a router method.
- If writing React components, ensure all imported components actually exist and are exported correctly.
- If writing FastAPI routes (Python), use `@app.get("/path")` decorators correctly.
- Ensure that all functions and variables you import actually exist in the other files listed in the manifest.
"""# ── Pure Utility Functions ──
def strip_fences(text: str) -> str:
    """Safely removes markdown fences if the LLM wrapped the whole file in them."""
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) > 2:
            return "\n".join(lines[1:-1])
    return text

def sanitize_for_xml(text: str) -> str:
    """Prevents Prompt Injection by neutralizing XML tags in the SDD."""
    return text.replace("<", "&lt;").replace(">", "&gt;")

# ── The Fortified Agent ──
class DeveloperAgent:
    def __init__(self, project_slug: str):
        self.project_slug = project_slug
        self.project_dir = get_project_dir(project_slug)
        self.code_dir = self.project_dir / "code"
        self.llm = get_llm("developer")
        
        self.sdd = ""
        self.plan = {}
        self.files_out = []
        
        self.lock_path = self.project_dir / ".agent.lock"
        self._lock_fd = None

    # ── HOST SECURITY: THE LOCK ──
    def _acquire_lock(self) -> bool:
        try:
            fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            self._lock_fd = fd
            os.write(fd, str(os.getpid()).encode())
            return True
        except FileExistsError:
            print(f"[!] Lock file exists. Another agent might be running.")
            print(f"[!] If you are sure no other process is running, delete: {self.lock_path}")
            return False

    def _release_lock(self):
        if self._lock_fd is not None:
            os.close(self._lock_fd)
        if self.lock_path.exists():
            try:
                self.lock_path.unlink()
            except OSError:
                pass

    # ── THE LLM CONNECTION ──
    async def _ask_llm(self, system: str, user: str) -> str:
        for attempt in range(3):
            try:
                return await self.llm.complete(system=system, user=user, temperature=0.2)
            except Exception as e:
                if attempt == 2:
                    raise e
                print(f"  [retry] LLM Error. Retrying in 3s... ({e})")
                await asyncio.sleep(3)
        return ""

    # ── APP SECURITY: THE SENTINEL ──
    def _validate_file(self, path: str, content: str) -> list[str]:
        issues = []
        if not content.strip():
            return ["empty file"]

        if len(content.encode('utf-8')) > MAX_FILE_BYTES:
            return [f"file exceeds max size ({MAX_FILE_BYTES} bytes)"]

        if not path.lower().endswith(DOC_EXTS) and content.lstrip().startswith("```"):
            issues.append("stray markdown fence at top of file")

        for pattern in SECRET_PATTERNS:
            if pattern in content:
                issues.append(f"contains likely secret: {pattern}")
                
        if SECRET_ASSIGN_REGEX.search(content):
            issues.append("possible hardcoded credential assignment")

        for pattern in DANGEROUS_CODE_PATTERNS:
            if re.search(pattern, content):
                issues.append(f"dangerous code execution: {pattern}")

        for p in ("# TODO", "# implement", "pass  # stub"):
            if p in content:
                issues.append(f"contains placeholder: {p!r}")

        if path.endswith(".py"):
            try:
                compile(content, path, "exec")
            except SyntaxError as e:
                issues.append(f"syntax error: {e.msg} (line {e.lineno})")

        return issues

    # ── HOST SECURITY: THE SAFE WRITER ──
    def _safe_write(self, rel_path: str, content: str):
        try:
            target = (self.code_dir / rel_path).resolve()
            target.relative_to(self.code_dir.resolve())
        except ValueError:
            print(f"  [SECURITY BLOCK] Path traversal detected: {rel_path}")
            return

        target.parent.mkdir(parents=True, exist_ok=True)

        try:
            fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), prefix=".tmp_")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, target)
        except Exception as e:
            print(f"  [ERROR] Failed to write {rel_path}: {e}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)        

    # ── PHASE 1: PLAN ──
    async def _phase_plan(self) -> bool:
        print("[Developer] Phase 1: Planning file manifest...")
        try:
            self.sdd = read_project_file(self.project_slug, "sdd.md")
        except FileNotFoundError:
            print(f"[!] Missing sdd.md. Run the Architect first.")
            return False
            
        if len(self.sdd) > MAX_SDD_CHARS:
            print(f"  [note] SDD truncated to {MAX_SDD_CHARS} chars for LLM limits.")
            self.sdd = self.sdd[:MAX_SDD_CHARS]
            
        safe_sdd = sanitize_for_xml(self.sdd)
        user_prompt = f"<SDD>\n{safe_sdd}\n</SDD>\n\nPlan the files for this project."
        
        raw = await self._ask_llm(PLAN_PROMPT, user_prompt)
        raw = strip_fences(raw)
        
        try:
            self.plan = json.loads(raw)
            if "files" not in self.plan:
                self.plan["files"] = []
            
            if len(self.plan["files"]) > MAX_FILES:
                print(f"[!] LLM planned too many files. Capping at {MAX_FILES}.")
                self.plan["files"] = self.plan["files"][:MAX_FILES]
                
            return True
        except Exception as e:
            print(f"[!] Failed to parse plan JSON: {e}")
            return False

    def _phase_review_plan(self) -> bool:
        files = self.plan.get("files", [])
        if not files:
            print("[!] Plan is empty. Nothing to generate.")
            return False
            
        while True:
            print(f"\n{'='*60}\nPLAN — {len(files)} files\n{'='*60}")
            for i, f in enumerate(files, 1):
                print(f"  {i:>2}. {f['path']}")
                
            print("\nCommands: [enter] accept | [r N] remove | [q] cancel")
            cmd = input("> ").strip().lower()
            
            if cmd == "": return True
            if cmd == "q": return False
            if cmd.startswith("r "):
                try:
                    idx = int(cmd[2:]) - 1
                    print(f"  Removed: {files.pop(idx)['path']}")
                except (ValueError, IndexError): 
                    print("  Invalid index.")

    # ── PHASE 2: EXECUTE ──
    async def _phase_execute(self):
        print(f"\n[Developer] Phase 2: Generating {len(self.plan['files'])} files...")
        manifest_str = "\n".join(f"- {f['path']}" for f in self.plan["files"])
        safe_sdd = sanitize_for_xml(self.sdd)
        
        for i, target in enumerate(self.plan["files"], 1):
            print(f"\n({i}/{len(self.plan['files'])}) Generating {target['path']}...")
            
            user_prompt = f"""
<SDD>
{safe_sdd}
</SDD>
<MANIFEST>
{manifest_str}
</MANIFEST>
<TASK>
Write the code for: {target['path']}
Purpose: {target.get('purpose', '')}
</TASK>
"""
            try:
                content = await self._ask_llm(FILE_PROMPT, user_prompt)
                content = strip_fences(content)
                issues = self._validate_file(target["path"], content)
            except Exception as e:
                content, issues = "", [f"generation failed: {e}"]

            if issues:
                print(f"  ⚠ Issues: {', '.join(issues)}")
            else:
                print(f"  ✓ Clean ({len(content)} chars)")

            self.files_out.append({"path": target["path"], "content": content, "issues": issues})

    # ── CHECKPOINT 2 & SAVE ──
    async def _phase_review_files(self) -> bool:
        while True:
            print(f"\n{'='*60}\nREVIEW\n{'='*60}")
            for i, f in enumerate(self.files_out, 1):
                status = "✓" if not f["issues"] else "⚠"
                print(f"  {status} {i:>2}. {f['path']:<40} ({len(f['content'].splitlines())} lines)")

            print("\nCommands: [enter] save | [v N] view | [r N] regenerate | [d N] drop | [q] cancel")
            cmd = input("> ").strip().lower()

            if cmd == "": return True
            if cmd == "q": return False

            if cmd.startswith("v "):
                try:
                    idx = int(cmd[2:]) - 1
                    print(f"\n--- {self.files_out[idx]['path']} ---")
                    print(self.files_out[idx]["content"])
                    input("\nPress Enter to continue...")
                except (ValueError, IndexError): print("  Invalid index.")
            
            elif cmd.startswith("r "):
                try:
                    idx = int(cmd[2:]) - 1
                    target = self.files_out[idx]
                    note = input("Regeneration note (why it failed): ").strip()
                    
                    safe_sdd = sanitize_for_xml(self.sdd)
                    user_prompt = f"<SDD>\n{safe_sdd}\n</SDD>\n<TASK>\nWrite the code for: {target['path']}\n</TASK>\nNOTE: {note}"
                    
                    print(f"  Regenerating {target['path']}...")
                    content = await self._ask_llm(FILE_PROMPT, user_prompt)
                    content = strip_fences(content)
                    issues = self._validate_file(target["path"], content)
                    
                    target["content"] = content
                    target["issues"] = issues
                    print(f"  {'✓ Fixed.' if not issues else '⚠ Still has issues.'}")
                except (ValueError, IndexError): print("  Invalid index.")
                
            elif cmd.startswith("d "):
                try:
                    idx = int(cmd[2:]) - 1
                    print(f"  Dropped: {self.files_out.pop(idx)['path']}")
                except (ValueError, IndexError): print("  Invalid index.")

    def _phase_save(self):
        print(f"\n[Developer] Phase 3: Saving files...")
        for f in self.files_out:
            if f["content"].strip():
                self._safe_write(f["path"], f["content"])
        
        # Save the plan for the record
        self._safe_write("../plan.json", json.dumps(self.plan, indent=2))
        print("[Developer] Done.\n")

    # ── THE ORCHESTRATOR ──
    async def run(self):
        if not self._acquire_lock():
            return
            
        try:
            if await self._phase_plan():
                if self._phase_review_plan():
                    await self._phase_execute()
                    if await self._phase_review_files():
                        self._phase_save()
        except Exception as e:
            print(f"\n[!] Agent Error: {e}\n")
        finally:
            self._release_lock()

# ── Entry Point ──
if __name__ == "__main__":
    projects = list_projects()
    if not projects:
        print("No projects found. Run PM and Architect first.")
        sys.exit(1)

    print("Available Projects:")
    for i, p in enumerate(projects, 1):
        print(f"  {i}. {p}")
    
    try:
        choice = input(f"Pick [default: 1 = {projects[0]}]: ").strip()
        idx = int(choice) - 1 if choice else 0
        slug = projects[idx]
    except (ValueError, IndexError):
        slug = projects[0]

    asyncio.run(DeveloperAgent(slug).run())