"""Site templates. One layout wraps every page; copy stays in the HTML."""

from __future__ import annotations


TEMPLATES = [
    {
        "id": "repair-stand",
        "label": "修理架",
        "source": "https://docs.astro.build/en/basics/layouts/",
        "does": "修理铺工单版式：首页一只带补丁的轮子，文章左对齐回答，全站导航和配图留在首屏 HTML。",
        "tokens": {
            "ink": "#1a2a22",
            "paper": "#e3ebe6",
            "panel": "#f7faf8",
            "line": "#9aaba3",
            "accent": "#9a3412",
            "muted": "#3d4f46",
            "scheme": "light",
            "title": "clamp(2.6rem, 6vw, 4.4rem)",
            "step-1": "0.5rem",
            "step-2": "1rem",
            "step-3": "1.5rem",
            "step-4": "3.5rem",
        },
    },
    {
        "id": "day-sheet",
        "label": "浅色纸页",
        "source": "https://gohugo.io/templates/introduction/",
        "does": "同一套修理架结构，只把地面色换成更亮的纸色。",
        "tokens": {
            "ink": "#1a2a22",
            "paper": "#eef3ef",
            "panel": "#ffffff",
            "line": "#b7c4bc",
            "accent": "#9a3412",
            "muted": "#3d4f46",
            "scheme": "light",
            "title": "clamp(2.6rem, 6vw, 4.4rem)",
            "step-1": "0.5rem",
            "step-2": "1rem",
            "step-3": "1.5rem",
            "step-4": "3.5rem",
        },
    },
]


def lookup_templates() -> list[dict]:
    return list(TEMPLATES)
