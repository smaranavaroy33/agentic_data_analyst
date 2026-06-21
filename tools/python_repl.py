from typing import Any
from graph.state import AgentState
from utils.safe_exec import safe_exec

def visualization_tester(state: AgentState) -> dict[str, Any]:
    """
    Tests the generated Python Plotly code for execution errors.

    This tool uses safe_exec() to run the generated visualization code in a 
    controlled, sandboxed environment. It ensures the code is syntactically 
    correct and produces a valid figure before the frontend attempts to render it.

    Args:
        state (AgentState): The current state containing 'plotly_code' 
            and 'raw_data'.

    Returns:
        dict: A dictionary updating 'visualization_error'.
    """
    code = state.get("plotly_code", "")
    data = state.get("raw_data", [])
    
    if not code:
        return {"visualization_error": "No visualization code provided to test."}
    
    try:
        exec_scope = safe_exec(code, data)
        
        # Check if 'fig' was successfully created
        if "fig" not in exec_scope:
            return {"visualization_error": "Code executed but no 'fig' object was created."}
            
        # Success: Clear any previous error
        return {"visualization_error": ""}
        
    except ValueError as e:
        # Safety check failure
        return {"visualization_error": str(e)}
    except Exception as e:
        # Execution failure
        return {"visualization_error": str(e)}
