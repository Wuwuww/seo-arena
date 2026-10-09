"""Site templates. One layout wraps every page; copy stays in the HTML."""

from __future__ import annotations


TEMPLATES = [
    {
        "id": "night-poster",
        "label": "深色海报",
        "source": "https://docs.astro.build/en/basics/layouts/",
        "does": "一套深色海报版式套全部页面：全站导航、大标题、配图和正文档位。正文留在首屏 HTML。",
        "tokens": {
            "ink": "#f7f3ea",
            "paper": "#12110f",
            "panel": "#1c1a16",
            "line": "#3f382f",
            "accent": "#e2ff4d",
            "muted": "#d7cec2",
            "scheme": "dark",
            "title": "clamp(2.5rem, 7vw, 4.8rem)",
            "step-1": "0.5rem",
            "step-2": "1rem",
            "step-3": "1.5rem",
            "step-4": "3rem",
        },
    },
    {
        "id": "day-sheet",
        "label": "浅色纸页",
        "source": "https://gohugo.io/templates/introduction/",
        "does": "一套浅色纸页版式套全部页面，导航和档位与深色模板相同，只换颜色。",
        "tokens": {
            "ink": "#1c1917",
            "paper": "#f4f0e6",
            "panel": "#fffdf8",
            "line": "#d9d1c3",
            "accent": "#9a3412",
            "muted": "#5c5346",
            "scheme": "light",
            "title": "clamp(2.5rem, 7vw, 4.8rem)",
            "step-1": "0.5rem",
            "step-2": "1rem",
            "step-3": "1.5rem",
            "step-4": "3rem",
        },
    },
]


def lookup_templates() -> list[dict]:
    return list(TEMPLATES)
