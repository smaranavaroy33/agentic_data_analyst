from graph.state import AgentState
from prompt_library.sql_prompts import SQL_DRAFTER_PROMPT
from utils.config import get_chat_model
from utils.reasoning import extract_reasoning
import re

llm = get_chat_model()

def sql_drafter(state: AgentState):
    """
    Drafts a SQL query based on the user question and database schema.

    This agent uses the LLM to generate a SQLite-compatible query.
    If a previous error exists in the state, it attempts to fix it.

    Args:
        state (AgentState): The current state containing the user question, 
            schema info, and any previous SQL errors.

    Returns:
        dict: A dictionary containing the generated 'sql_query' and updated 'retry_count'.
    """
    user_q = state.user_question
    schema = state.schema_info
    error = state.sql_error
    sql_retry_count = state.sql_retry_count
    
    # Construct the user message with the current context
    user_message = f"User Question: {user_q}\n\nDatabase Schema:\n{schema}"
    
    if error:
        user_message += f"\n\nPrevious SQL Error: {error}\nPlease fix the query based on this error."
        sql_retry_count += 1

    # Call LLM
    messages = [
        {"role": "system", "content": SQL_DRAFTER_PROMPT},
        {"role": "user", "content": user_message}
    ]
    response = llm.invoke(messages)
    sql_query = response.content.strip()

    # Capture Reasoning (Thinking)
    new_reasoning = extract_reasoning(response, "SQL Drafter", state)

    # Robust Markdown Stripping
    # Matches ```sql ... ``` or ``` ... ```
    sql_match = re.search(r"```(?:sql)?(.*?)```", sql_query, re.DOTALL | re.IGNORECASE)
    if sql_match:
        sql_query = sql_match.group(1).strip()
    
    # Remove any prefixing text if markdown tags are missing but query is obviously SQL
    if "SELECT " in sql_query.upper() and not sql_query.upper().startswith("SELECT"):
        sql_query = sql_query[sql_query.upper().find("SELECT"):]
    
    # Return the update to the state
    return {
        "sql_query": sql_query,
        "sql_retry_count": sql_retry_count,
        "reasoning_log": new_reasoning
    }
