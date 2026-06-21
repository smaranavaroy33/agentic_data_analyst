from functools import lru_cache
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import AgentState
from agents.schema import schema_extractor
from agents.sql import sql_drafter
from tools.db_executor import sql_executor
from agents.router import router
from agents.visualization import visualization_drafter
from tools.python_repl import visualization_tester
from agents.summary import inference_agent

@lru_cache(maxsize=1)
def create_workflow():
    """
    Constructs the LangGraph workflow for the self-correcting data analyst.

    This function defines the nodes, linear edges, and conditional routing 
    logic for the entire analysis pipeline. Uses lru_cache to compile once.

    Returns:
        CompiledGraph: The compiled LangGraph application ready for execution.
    """
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("schema_extractor", schema_extractor)
    workflow.add_node("sql_drafter", sql_drafter)
    workflow.add_node("sql_executor", sql_executor)
    workflow.add_node("router", router)
    workflow.add_node("visualization_drafter", visualization_drafter)
    workflow.add_node("visualization_tester", visualization_tester)
    workflow.add_node("inference_agent", inference_agent)

    # 2. Define Linear Edges
    workflow.add_edge(START, "schema_extractor")
    workflow.add_edge("schema_extractor", "sql_drafter")
    workflow.add_edge("sql_drafter", "sql_executor")
    workflow.add_edge("visualization_drafter", "visualization_tester")
    workflow.add_edge("inference_agent", END)

    # 3. Define Conditional Edges (Loops & Forks)

    # SQL Correction Loop: Check if execution failed
    def should_continue_sql(state: AgentState):
        if state.get("sql_error") and state.get("sql_retry_count", 0) < 3:
            return "retry"
        return "continue"

    workflow.add_conditional_edges(
        "sql_executor",
        should_continue_sql,
        {
            "retry": "sql_drafter",
            "continue": "router"
        }
    )

    # Visualization Fork: Decision from the Router
    def should_visualize(state: AgentState):
        if state.get("needs_chart", False):
            return "yes"
        return "no"

    workflow.add_conditional_edges(
        "router",
        should_visualize,
        {
            "yes": "visualization_drafter",
            "no": "inference_agent"
        }
    )

    # Visualization Correction Loop: Check if python code failed
    def should_continue_visualization(state: AgentState):
        if state.get("visualization_error") and state.get("viz_retry_count", 0) < 3:
            return "retry"
        return "continue"

    workflow.add_conditional_edges(
        "visualization_tester",
        should_continue_visualization,
        {
            "retry": "visualization_drafter",
            "continue": "inference_agent"
        }
    )

    # Initialize MemorySaver checkpointer
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
