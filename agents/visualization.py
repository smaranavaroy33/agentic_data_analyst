import re
import pandas as pd
from typing import Any
from graph.state import AgentState
from prompt_library.visualization_prompts import VISUALIZATION_PROMPT
from utils.config import get_chat_model
from utils.reasoning import extract_reasoning

def visualization_drafter(state: AgentState) -> dict[str, Any]:
    """
    Generates Python Plotly code to visualize the retrieved data.

    This node uses the LLM to write executable Python code that 
    creates a Plotly figure based on the data in 'raw_data' and the 
    user's analytical needs.

    Args:
        state (AgentState): The current state containing user question, 
            retrieved data, and any previous visualization errors.

    Returns:
        dict: A dictionary updating 'plotly_code' and 'retry_count'.
    """
    llm = get_chat_model()
    user_q = state["user_question"]
    chat_history = state.get("chat_history", "")
    raw_data = state.get("raw_data", [])
    
    # Generate stats instead of just truncating
    df = pd.DataFrame(raw_data)
    if not df.empty:
        stats = df.describe(include='all').to_string()
        preview = df.head(5).to_string()
        data_context = f"Data Summary Statistics:\n{stats}\n\nData Preview (first 5 rows):\n{preview}"
    else:
        data_context = "No data returned from query."
    
    error = state.get("visualization_error", "")
    viz_retry_count = state.get("viz_retry_count", 0)
    
    # Construct the context for the visualization drafting
    input_content = f"User Question: {user_q}\n\n{data_context}"
    if chat_history:
        input_content = f"Chat History:\n{chat_history}\n\n{input_content}"
    
    if error:
        input_content += f"\n\nPrevious Python Error:\n{error}\nPlease fix the code based on this error."
        viz_retry_count += 1
        
    # Call LLM
    messages = [
        {"role": "system", "content": VISUALIZATION_PROMPT},
        {"role": "user", "content": input_content}
    ]
    response = llm.invoke(messages)
    plotly_code = response.content.strip()

    # Capture Reasoning (Thinking)
    new_reasoning = extract_reasoning(response, "Visualization Drafter")

    # Robust Python Markdown Stripping
    python_match = re.search(r"```(?:python)?(.*?)```", plotly_code, re.DOTALL | re.IGNORECASE)
    if python_match:
        plotly_code = python_match.group(1).strip()
    elif plotly_code.startswith("```"):
        plotly_code = plotly_code.strip("`").strip()

    return {
        "plotly_code": plotly_code,
        "viz_retry_count": viz_retry_count,
        "reasoning_log": new_reasoning
    }
