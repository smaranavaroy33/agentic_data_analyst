import ast
import pandas as pd
import plotly.express as px


def is_safe_code(code: str) -> bool:
    """Checks if the generated python code uses forbidden modules or functions."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
        
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            return False  # LLM should not import anything, only use pd and px
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['eval', 'exec', 'open', '__import__', 'compile',
                                    'globals', 'locals', 'getattr', 'setattr', 'delattr']:
                    return False
        if isinstance(node, ast.Attribute):
            if node.attr.startswith('__'):
                return False
    return True


def safe_exec(code: str, data: list) -> dict:
    """
    Executes LLM-generated visualization code in a sandboxed environment.
    
    Performs AST safety checks and runs with builtins disabled.
    
    Args:
        code: The Python code string to execute.
        data: The raw data (list of dicts) to make available as 'data'.
    
    Returns:
        dict: The execution scope after running the code.
    
    Raises:
        ValueError: If the code fails safety checks.
        Exception: If code execution fails.
    """
    if not code:
        raise ValueError("No code provided to execute.")
    
    if not is_safe_code(code):
        raise ValueError(
            "Security Error: The generated code contains forbidden functions or imports. "
            "Only use 'px' and 'pd'."
        )
    
    # Define the execution scope with required libraries and data
    # Explicitly disable builtins to prevent access to dangerous functions
    exec_scope = {
        "pd": pd,
        "px": px,
        "data": data
    }
    
    # Use restricted globals with builtins disabled
    restricted_globals = {"__builtins__": {}}
    
    exec(code, restricted_globals, exec_scope)
    
    return exec_scope
