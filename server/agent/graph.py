from langgraph.graph import END, StateGraph
from langgraph.types import Send

from server.agent.nodes.content_analyser import content_analyser
from server.agent.nodes.content_merger import content_merger
from server.agent.nodes.file_writer import file_writer
from server.agent.nodes.gap_filler import gap_filler
from server.agent.nodes.gfg_scraper import gfg_scraper
from server.agent.nodes.image_generator import image_generator
from server.agent.nodes.llm_knowledge import llm_knowledge
from server.agent.nodes.mdx_fixer import mdx_fixer
from server.agent.nodes.mdx_generator import mdx_generator
from server.agent.nodes.mdx_validator import mdx_validator
from server.agent.nodes.outline_planner import outline_planner
from server.agent.nodes.quality_judge import quality_judge
from server.agent.nodes.tpointtech_scraper import tpointtech_scraper
from server.agent.nodes.topic_router import topic_router
from server.agent.state import AgentState

MAX_MERGE_ATTEMPTS = 2
MAX_GENERATION_ATTEMPTS = 3


def _fan_out_after_router(state: AgentState) -> list[Send]:
    return [
        Send("gfg_scraper", state),
        Send("tpointtech_scraper", state),
        Send("llm_knowledge", state),
    ]


def _route_after_merge(state: AgentState) -> str:
    if state.get("coverage_ok") or state.get("scrape_attempts", 0) >= MAX_MERGE_ATTEMPTS:
        return "outline_planner"
    return "gap_filler"


def _route_after_analyse(state: AgentState) -> str:
    return "image_generator" if state.get("needs_images") else "mdx_generator"


def _route_after_validate(state: AgentState) -> str:
    if state.get("validation_ok"):
        return "quality_judge"
    if state.get("generation_attempts", 0) >= MAX_GENERATION_ATTEMPTS:
        return "file_writer"
    return "mdx_fixer"


def _route_after_judge(state: AgentState) -> str:
    return "mdx_fixer" if state.get("revision_notes") else "file_writer"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("topic_router", topic_router)
    graph.add_node("gfg_scraper", gfg_scraper)
    graph.add_node("tpointtech_scraper", tpointtech_scraper)
    graph.add_node("llm_knowledge", llm_knowledge)
    graph.add_node("content_merger", content_merger)
    graph.add_node("gap_filler", gap_filler)
    graph.add_node("outline_planner", outline_planner)
    graph.add_node("content_analyser", content_analyser)
    graph.add_node("image_generator", image_generator)
    graph.add_node("mdx_generator", mdx_generator)
    graph.add_node("mdx_validator", mdx_validator)
    graph.add_node("mdx_fixer", mdx_fixer)
    graph.add_node("quality_judge", quality_judge)
    graph.add_node("file_writer", file_writer)

    graph.set_entry_point("topic_router")

    graph.add_conditional_edges(
        "topic_router",
        _fan_out_after_router,
        ["gfg_scraper", "tpointtech_scraper", "llm_knowledge"],
    )

    graph.add_edge("gfg_scraper", "content_merger")
    graph.add_edge("tpointtech_scraper", "content_merger")
    graph.add_edge("llm_knowledge", "content_merger")

    graph.add_conditional_edges(
        "content_merger",
        _route_after_merge,
        {"outline_planner": "outline_planner", "gap_filler": "gap_filler"},
    )
    graph.add_edge("gap_filler", "content_merger")

    graph.add_edge("outline_planner", "content_analyser")

    graph.add_conditional_edges(
        "content_analyser",
        _route_after_analyse,
        {"image_generator": "image_generator", "mdx_generator": "mdx_generator"},
    )

    graph.add_edge("image_generator", "mdx_generator")
    graph.add_edge("mdx_generator", "mdx_validator")

    graph.add_conditional_edges(
        "mdx_validator",
        _route_after_validate,
        {
            "quality_judge": "quality_judge",
            "mdx_fixer": "mdx_fixer",
            "file_writer": "file_writer",
        },
    )
    graph.add_edge("mdx_fixer", "mdx_validator")

    graph.add_conditional_edges(
        "quality_judge",
        _route_after_judge,
        {"mdx_fixer": "mdx_fixer", "file_writer": "file_writer"},
    )

    graph.add_edge("file_writer", END)

    return graph.compile()


compiled_graph = build_graph()
