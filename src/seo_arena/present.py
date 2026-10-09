"""Visible page structure for rendered crawling: landmarks, figure, and caption."""

from __future__ import annotations


def _frame(body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 280" role="img">'
        '<rect width="640" height="280" fill="#f3efe6"/>'
        '<rect x="24" y="24" width="592" height="232" fill="#fffdf8" stroke="#e4ddd2"/>'
        f"{body}"
        "</svg>"
    )


def _gauge() -> str:
    return _frame(
        '<path d="M120 190 A90 90 0 0 1 300 190" fill="none" stroke="#1c1917" stroke-width="8"/>'
        '<path d="M168 190 A42 42 0 0 1 252 190" fill="none" stroke="#9a3412" stroke-width="8"/>'
        '<line x1="210" y1="190" x2="250" y2="150" stroke="#1c1917" stroke-width="4"/>'
        '<text x="340" y="120" fill="#1c1917" font-size="28">建议区间</text>'
        '<text x="340" y="168" fill="#57534e" font-size="20">中段，不打满</text>'
    )


def _patch() -> str:
    return _frame(
        '<circle cx="220" cy="140" r="70" fill="none" stroke="#1c1917" stroke-width="8"/>'
        '<circle cx="220" cy="140" r="36" fill="#9a3412"/>'
        '<text x="330" y="130" fill="#1c1917" font-size="28">冷补丁</text>'
        '<text x="330" y="174" fill="#57534e" font-size="20">边缘要压实</text>'
    )


def _valves() -> str:
    return _frame(
        '<rect x="120" y="70" width="36" height="140" fill="#1c1917"/>'
        '<rect x="210" y="90" width="18" height="120" fill="#9a3412"/>'
        '<text x="300" y="120" fill="#1c1917" font-size="28">美嘴更粗</text>'
        '<text x="300" y="168" fill="#57534e" font-size="20">法嘴更细</text>'
    )


def _bites() -> str:
    return _frame(
        '<circle cx="180" cy="140" r="16" fill="#1c1917"/>'
        '<circle cx="230" cy="140" r="16" fill="#1c1917"/>'
        '<text x="300" y="130" fill="#1c1917" font-size="28">并排两孔</text>'
        '<text x="300" y="174" fill="#57534e" font-size="20">轮圈夹到内胎</text>'
    )


_MOTIFS = {
    "tire-pressure": ("气压表停在建议区间中段", _gauge),
    "patch-life": ("内胎上的一块压实补丁", _patch),
    "valve-type": ("较粗的美嘴和较细的法嘴", _valves),
    "snake-bite": ("内胎上并排的两个小孔", _bites),
}


def present_plans(plans: list[dict]) -> list[dict]:
    for plan in plans:
        alt, draw = _MOTIFS.get(plan["slug"], ("与本页问题对应的示意图", _gauge))
        plan["figure"] = {
            "alt": alt,
            "caption": f"{alt}。{plan['offer']}。",
            "svg": draw(),
        }
    return plans
