import argparse
import json
from pathlib import Path

from seo_arena.digest import run_briefing
from seo_arena.render import write_site


def main() -> None:
    parser = argparse.ArgumentParser(description="拉取论文、大模型和 Skill，写成一期 AI 简报")
    parser.add_argument("--out", type=Path, default=Path("docs"))
    args = parser.parse_args()
    root = Path.cwd()
    issue, trace = run_briefing()
    write_site(issue, root, args.out)
    records = root / "records"
    records.mkdir(exist_ok=True)
    (records / "digest.json").write_text(json.dumps(issue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (records / "digest-trace.json").write_text(
        json.dumps({"fetched_at": issue["fetched_at"], "steps": trace}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    counts = ", ".join(f"{section['id']}={len(section['items'])}" for section in issue["sections"])
    print(f"issue={issue['h1']} {counts} out={args.out}")


if __name__ == "__main__":
    main()
