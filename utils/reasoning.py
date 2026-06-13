def extract_reasoning(response, agent_name, state):
    """
    Extracts the reasoning (thinking) block from an LLM response and updates the state.
    """
    reasoning = ""
    if hasattr(response, "response_metadata"):
        ctk = response.response_metadata.get("chat_template_kwargs", {})
        if isinstance(ctk, dict):
            reasoning = ctk.get("thinking", "")
        elif isinstance(ctk, str):
            reasoning = ctk
            
    if not reasoning and hasattr(response, "additional_kwargs") and "chat_template_kwargs" in response.additional_kwargs:
        ctk = response.additional_kwargs.get("chat_template_kwargs", {})
        if isinstance(ctk, dict):
            reasoning = ctk.get("thinking", "")
        elif isinstance(ctk, str):
            reasoning = ctk

    if not reasoning and hasattr(response, "additional_kwargs"):
        reasoning = response.additional_kwargs.get("reasoning_content", "")

    new_reasoning = state.reasoning_log.copy() if hasattr(state, 'reasoning_log') else []
    if reasoning:
        new_reasoning.append({"agent": agent_name, "content": reasoning})
        
    return new_reasoning