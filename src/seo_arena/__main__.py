import argparse
from pathlib import Path

from seo_arena.agent import load_brief, run_agent, write_records
from seo_arena.digest import publish_digest
from seo_arena.render import render_site


def main() -> None:
    parser = argparse.ArgumentParser(description="用 SEO 步骤生成一个可抓取的站点")
    parser.add_argument("--brief", type=Path, default=Path("briefs/nanmen.json"))
    parser.add_argument("--out", type=Path, default=Path("docs"))
    args = parser.parse_args()
    root = Path.cwd()
    brief = load_brief(args.brief)
    plans, trace, template = run_agent(brief)
    render_site(brief, plans, root, args.out, template)
    report = publish_digest(brief, plans, template, args.out, root)
    write_records(brief, plans, trace, root)
    print(f"pages={len(plans)} steps={len(trace)} digest={report['fetched_at']} out={args.out}")


if __name__ == "__main__":
    main()
