import argparse
from pathlib import Path

from seo_arena.agent import load_brief
from seo_arena.digest import publish_digest
from seo_arena.templates import TEMPLATES


def main() -> None:
    parser = argparse.ArgumentParser(description="拉取论文、大模型和 Skill，写成今日简报")
    parser.add_argument("--brief", type=Path, default=Path("briefs/nanmen.json"))
    parser.add_argument("--out", type=Path, default=Path("docs"))
    args = parser.parse_args()
    root = Path.cwd()
    brief = load_brief(args.brief)
    plans = [{"path": f"/{page['slug']}/", "h1": page["query"]} for page in brief["pages"]]
    report = publish_digest(brief, plans, TEMPLATES[0], args.out, root)
    counts = ", ".join(f"{module['id']}={len(module['items'])}" for module in report["modules"])
    print(f"fetched_at={report['fetched_at']} {counts} out={args.out / 'ai'}")


if __name__ == "__main__":
    main()
