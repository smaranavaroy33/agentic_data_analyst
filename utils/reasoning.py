def extract_reasoning(response, agent_name: str) -> list[dict]:
    """
    Extracts the reasoning (thinking) block from an LLM response.
    
    Returns a list with a single entry if reasoning is found, or an empty list.
    The list is merged into state.reasoning_log via the operator.add reducer.
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

    if reasoning:
        return [{"agent": agent_name, "content": reasoning}]
    return []