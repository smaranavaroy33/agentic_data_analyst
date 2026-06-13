from graph.state import AgentState
from prompt_library.router_prompts import ROUTER_PROMPT
from utils.config import get_chat_model
from utils.reasoning import extract_reasoning

llm = get_chat_model()

def router(state: AgentState):
    """
    Determines if the user's question requires a visual chart.

    This node acts as a decision-maker by analyzing the semantic intent 
     of the user's question.

    Args:
        state (AgentState): The current state containing the user question.

    Returns:
        dict: A dictionary updating 'needs_chart' (bool).
    """
    user_q = state.user_question
    
    # Call LLM
    messages = [
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": f"User Question: {user_q}"}
    ]
    response = llm.invoke(messages)
    decision = response.content.strip().upper()

    # Capture Reasoning (Thinking)
    new_reasoning = extract_reasoning(response, "Router", state)

    needs_chart = "YES" in decision

    return {
        "needs_chart": needs_chart,
        "reasoning_log": new_reasoning
    }
