from langgraph.graph import END, StateGraph
from langgraph.types import Send

from server.agent.nodes.content_analyser import content_analyser
from server.agent.nodes.content_merger import content_merger
from server.agent.nodes.file_writer import file_writer
from server.agent.nodes.gfg_scraper import gfg_scraper
from server.agent.nodes.image_generator import image_generator
from server.agent.nodes.llm_knowledge import llm_knowledge
from server.agent.nodes.mdx_generator import mdx_generator
from server.agent.nodes.mdx_validator import mdx_validator
from server.agent.nodes.tpointtech_scraper import tpointtech_scraper
from server.agent.nodes.topic_router import topic_router
from server.agent.state import AgentState


def _fan_out_after_router(state: AgentState) -> list[Send]:
    return [
        Send("gfg_scraper", state),
        Send("tpointtech_scraper", state),
        Send("llm_knowledge", state),
    ]


def _route_after_merge(state: AgentState) -> str:
    if state.get("coverage_ok") or state.get("scrape_attempts", 0) >= 2:
        return "content_analyser"
    return "content_merger"


def _route_after_analyse(state: AgentState) -> str:
    return "image_generator" if state.get("needs_images") else "mdx_generator"


def _route_after_validate(state: AgentState) -> str:
    if state.get("validation_ok") or state.get("generation_attempts", 0) >= 3:
        return "file_writer"
    return "mdx_generator"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("topic_router", topic_router)
    graph.add_node("gfg_scraper", gfg_scraper)
    graph.add_node("tpointtech_scraper", tpointtech_scraper)
    graph.add_node("llm_knowledge", llm_knowledge)
    graph.add_node("content_merger", content_merger)
    graph.add_node("content_analyser", content_analyser)
    graph.add_node("image_generator", image_generator)
    graph.add_node("mdx_generator", mdx_generator)
    graph.add_node("mdx_validator", mdx_validator)
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
        {"content_analyser": "content_analyser", "content_merger": "content_merger"},
    )

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
        {"file_writer": "file_writer", "mdx_generator": "mdx_generator"},
    )

    graph.add_edge("file_writer", END)

    return graph.compile()


compiled_graph = build_graph()
