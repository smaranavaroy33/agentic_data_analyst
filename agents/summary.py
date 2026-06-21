import pandas as pd
from typing import Any
from graph.state import AgentState
from prompt_library.summary_prompts import SUMMARY_PROMPT
from utils.config import get_chat_model
from utils.reasoning import extract_reasoning

def inference_agent(state: AgentState) -> dict[str, Any]:
    """
    Synthesizes the final analytical summary for the user.

    This node acts as the Lead Analyst, taking the raw data retrieved from 
    the database and the original question to formulate a comprehensive, 
    executive-style response.

    Args:
        state (AgentState): The current state containing the user question, 
            raw data results, and visualization status.

    Returns:
        dict: A dictionary updating 'final_summary' with the LLM's response.
    """
    llm = get_chat_model()
    user_q = state["user_question"]
    chat_history = state.get("chat_history", "")
    
    # Generate stats instead of just truncating
    df = pd.DataFrame(state.get("raw_data", []))
    if not df.empty:
        stats = df.describe(include='all').to_string()
        data_context = f"Data Summary Statistics:\n{stats}"
    else:
        data_context = "No data returned from query."
        
    visualization_status = "A chart was generated to visualize this data." if state.get("needs_chart", False) else "No chart was generated for this response."
    
    # Construct the context for the summary
    input_content = f"User Question: {user_q}\n\n{data_context}\n\nVisualization Status: {visualization_status}"
    if chat_history:
        input_content = f"Chat History:\n{chat_history}\n\n{input_content}"
    
    # Call LLM
    messages = [
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": input_content}
    ]
    response = llm.invoke(messages)
    final_summary = response.content.strip()

    # Capture Reasoning (Thinking)
    new_reasoning = extract_reasoning(response, "Lead Analyst")

    return {
        "final_summary": final_summary,
        "reasoning_log": new_reasoning
    }
