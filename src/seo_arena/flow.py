"""LangGraph flow: inspect the next gap, look up a step, apply it, repeat."""

from __future__ import annotations

import copy
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from seo_arena.agent import ScriptedAgent, _empty_plan, _link_pages, _missing, apply_method
from seo_arena.audit import FIXABLE, audit_plans, revise_plans
from seo_arena.catalog import lookup_methods
from seo_arena.present import present_plans


class FlowState(TypedDict, total=False):
    brief: dict
    site_url: str
    plans: list[dict]
    page_index: int
    gap: str | None
    candidates: list[dict]
    chosen: dict
    trace: list[dict]
    issues: list[dict]
    revised: bool


def build_graph(chooser=None):
    chooser = chooser or ScriptedAgent()

    def inspect(state: FlowState) -> dict:
        brief = state["brief"]
        plans = state.get("plans")
        if not plans:
            created = [_empty_plan(page, brief["brand"]) for page in brief["pages"]]
            return {
                "plans": created,
                "page_index": 0,
                "gap": _missing(created[0]),
                "trace": [],
                "site_url": brief["site_url"],
                "candidates": [],
            }
        index = state["page_index"]
        if index >= len(plans):
            return {"gap": None}
        return {"gap": _missing(plans[index])}

    def route(state: FlowState) -> str:
        if state["page_index"] >= len(state["plans"]):
            return "cross_link"
        if state.get("gap"):
            return "lookup"
        return "next_page"

    def lookup(state: FlowState) -> dict:
        found = lookup_methods(state["gap"])
        trace = list(state.get("trace") or [])
        trace.append({"tool": "lookup_methods", "gap": state["gap"], "hits": [item["id"] for item in found]})
        return {"candidates": found, "trace": trace}

    def choose(state: FlowState) -> dict:
        method = chooser.choose(state["gap"], state["candidates"])
        if method["gap"] != state["gap"]:
            raise RuntimeError(f"步骤 {method['id']} 不能补上 {state['gap']}")
        return {"chosen": method}

    def apply(state: FlowState) -> dict:
        plans = copy.deepcopy(state["plans"])
        index = state["page_index"]
        apply_method(state["chosen"], plans[index], state["site_url"])
        trace = list(state["trace"])
        trace.append(
            {
                "tool": "apply",
                "method": state["chosen"]["id"],
                "source": state["chosen"]["source"],
                "page": plans[index]["path"],
            }
        )
        return {"plans": plans, "trace": trace}

    def next_page(state: FlowState) -> dict:
        return {"page_index": state["page_index"] + 1}

    def cross_link(state: FlowState) -> dict:
        plans = copy.deepcopy(state["plans"])
        _link_pages(plans)
        return {"plans": plans, "revised": False}

    def audit(state: FlowState) -> dict:
        issues = audit_plans(state["plans"], state["site_url"])
        trace = list(state["trace"])
        trace.append({"tool": "audit", "issues": [issue["code"] for issue in issues]})
        return {"issues": issues, "trace": trace}

    def route_audit(state: FlowState) -> str:
        fixable = [issue for issue in state.get("issues") or [] if issue["code"] in FIXABLE]
        if fixable and not state.get("revised"):
            return "revise"
        return "present"

    def revise(state: FlowState) -> dict:
        plans = revise_plans(copy.deepcopy(state["plans"]), state["issues"])
        trace = list(state["trace"])
        trace.append({"tool": "revise", "codes": sorted({issue["code"] for issue in state["issues"] if issue["code"] in FIXABLE})})
        return {"plans": plans, "revised": True, "trace": trace}

    def present(state: FlowState) -> dict:
        plans = present_plans(copy.deepcopy(state["plans"]))
        trace = list(state["trace"])
        trace.append({"tool": "present", "pages": [plan["path"] for plan in plans]})
        return {"plans": plans, "trace": trace}

    def sitemap(state: FlowState) -> dict:
        trace = list(state["trace"])
        trace.append(
            {
                "tool": "apply",
                "method": "sitemap_and_robots",
                "source": lookup_methods("sitemap")[0]["source"],
                "page": "/sitemap.xml",
            }
        )
        return {"trace": trace}

    graph = StateGraph(FlowState)
    graph.add_node("inspect", inspect)
    graph.add_node("lookup", lookup)
    graph.add_node("choose", choose)
    graph.add_node("apply", apply)
    graph.add_node("next_page", next_page)
    graph.add_node("cross_link", cross_link)
    graph.add_node("audit", audit)
    graph.add_node("revise", revise)
    graph.add_node("present", present)
    graph.add_node("sitemap", sitemap)
    graph.add_edge(START, "inspect")
    graph.add_conditional_edges(
        "inspect",
        route,
        {"lookup": "lookup", "next_page": "next_page", "cross_link": "cross_link"},
    )
    graph.add_edge("lookup", "choose")
    graph.add_edge("choose", "apply")
    graph.add_edge("apply", "inspect")
    graph.add_edge("next_page", "inspect")
    graph.add_edge("cross_link", "audit")
    graph.add_conditional_edges("audit", route_audit, {"revise": "revise", "present": "present"})
    graph.add_edge("revise", "audit")
    graph.add_edge("present", "sitemap")
    graph.add_edge("sitemap", END)
    return graph.compile()


def run_flow(brief: dict, chooser=None) -> tuple[list[dict], list[dict]]:
    graph = build_graph(chooser)
    final = graph.invoke({"brief": brief}, config={"recursion_limit": 250})
    return final["plans"], final["trace"]
