import re
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower())
    return slug.strip("-") or "untitled"


def get_project_dir(project_slug: str) -> Path:
    path = OUTPUT_DIR / project_slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_text(project_slug: str, filename: str, content: str) -> Path:
    project_dir = get_project_dir(project_slug)
    path = project_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def save_file_tree(project_slug: str, tree: dict) -> Path:
    code_dir = get_project_dir(project_slug) / "code"
    code_dir.mkdir(parents=True, exist_ok=True)

    for f in tree.get("files", []):
        path = code_dir / f["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f["content"], encoding="utf-8")

    return code_dir


def list_projects() -> list[str]:
    dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
    return [d.name for d in sorted(dirs, key=lambda d: d.stat().st_mtime, reverse=True)]


def find_latest_project() -> str | None:
    projects = list_projects()
    return projects[0] if projects else None


def read_project_file(project_slug: str, filename: str) -> str:
    path = OUTPUT_DIR / project_slug / filename
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    return path.read_text(encoding="utf-8")