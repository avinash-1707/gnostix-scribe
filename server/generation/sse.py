from server.schemas import NodeEvent


def format_event(event: NodeEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


def format_keepalive() -> str:
    return ": keepalive\n\n"
