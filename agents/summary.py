import pandas as pd
from graph.state import AgentState
from prompt_library.summary_prompts import SUMMARY_PROMPT
from utils.config import get_chat_model
from utils.reasoning import extract_reasoning

llm = get_chat_model()

def inference_agent(state: AgentState):
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
    user_q = state.user_question
    
    # Generate stats instead of just truncating
    df = pd.DataFrame(state.raw_data)
    if not df.empty:
        stats = df.describe(include='all').to_string()
        data_context = f"Data Summary Statistics:\n{stats}"
    else:
        data_context = "No data returned from query."
        
    visualization_status = "A chart was generated to visualize this data." if state.needs_chart else "No chart was generated for this response."
    
    # Construct the context for the summary
    input_content = f"User Question: {user_q}\n\n{data_context}\n\nVisualization Status: {visualization_status}"
    
    # Call LLM
    messages = [
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": input_content}
    ]
    response = llm.invoke(messages)
    final_summary = response.content.strip()

    # Capture Reasoning (Thinking)
    new_reasoning = extract_reasoning(response, "Lead Analyst", state)

    return {
        "final_summary": final_summary,
        "reasoning_log": new_reasoning
    }
