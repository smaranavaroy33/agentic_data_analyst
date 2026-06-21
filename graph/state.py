import operator
from typing import TypedDict, Annotated, Any

class AgentState(TypedDict, total=False):
    """State schema for the data analyst workflow."""
    chat_history: str
    user_question: str
    file_name: str
    session_id: str
    db_path: str
    schema_info: str
    sql_query: str
    sql_error: str
    raw_data: list[Any]
    needs_chart: bool
    plotly_code: str
    visualization_error: str
    final_summary: str
    sql_retry_count: int
    viz_retry_count: int
    reasoning_log: Annotated[list[dict], operator.add]  # Accumulates across nodes
