import pandas as pd
import plotly.express as px
import ast
from graph.state import AgentState

def is_safe_code(code: str) -> bool:
    """Checks if the generated python code uses forbidden modules or functions."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False # Handled by exec try/except, but good to catch here
        
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            return False # LLM should not import anything, only use pd and px
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['eval', 'exec', 'open', '__import__']:
                    return False
        if isinstance(node, ast.Attribute):
            if node.attr.startswith('__'):
                return False
    return True

def visualization_tester(state: AgentState):
    """
    Tests the generated Python Plotly code for execution errors.

    This tool uses 'exec()' to run the generated visualization code in a 
    controlled environment. It ensures the code is syntactically correct 
    and produces a valid figure before the frontend attempts to render it.

    Args:
        state (AgentState): The current state containing 'plotly_code' 
            and 'raw_data'.

    Returns:
        dict: A dictionary updating 'visualization_error'.
    """
    code = state.plotly_code
    data = state.raw_data
    
    if not code:
        return {"visualization_error": "No visualization code provided to test."}
        
    if not is_safe_code(code):
        return {"visualization_error": "Security Error: The generated code contains forbidden functions or imports. Only use 'px' and 'pd'."}
        
    try:
        # Define the execution scope with required libraries and data
        exec_scope = {
            "pd": pd,
            "px": px,
            "data": data
        }
        
        # Attempt to execute the code
        exec(code, {}, exec_scope)
        
        # Check if 'fig' was successfully created
        if "fig" not in exec_scope:
            return {"visualization_error": "Code executed but no 'fig' object was created."}
            
        # Success: Clear any previous error
        return {"visualization_error": ""}
        
    except Exception as e:
        # Failure: Capture the error message for the correction loop
        return {"visualization_error": str(e)}
