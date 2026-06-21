import re
import sqlite3
from typing import Any
from graph.state import AgentState

_VALID_IDENTIFIER = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

def schema_extractor(state: AgentState) -> dict[str, Any]:
    """
    Extracts the schema from the temporary SQLite database.

    This node connects to the database specified in 'state["db_path"]', 
    retrieves all table names, and then fetches the column names 
    and types for each table.

    Args:
        state (AgentState): The current state of the agent.

    Returns:
        dict: A dictionary containing the 'schema_info' string.
    """
    db_path = state["db_path"]
    schema_parts = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # Validate identifier to prevent SQL injection
            if not _VALID_IDENTIFIER.match(table_name):
                continue
                
            schema_parts.append(f"Table: {table_name}")
            
            # 2. Get columns for each table (identifier validated above)
            cursor.execute(f'PRAGMA table_info("{table_name}");')
            columns = cursor.fetchall()
            
            for col in columns:
                # col format: (id, name, type, notnull, default_value, pk)
                col_name = col[1]
                col_type = col[2]
                
                # Fetch up to 3 unique sample values to help the LLM with exact casing/formatting
                try:
                    if not _VALID_IDENTIFIER.match(col_name):
                        sample_str = ""
                    else:
                        cursor.execute(f'SELECT DISTINCT "{col_name}" FROM "{table_name}" WHERE "{col_name}" IS NOT NULL LIMIT 3;')
                        samples = [str(row[0]) for row in cursor.fetchall()]
                        sample_str = f" (Sample values: {', '.join(samples)})" if samples else ""
                except Exception:
                    sample_str = ""
                    
                schema_parts.append(f"  - {col_name} ({col_type}){sample_str}")
            schema_parts.append("") # Blank line between tables
            
        conn.close()
    except Exception as e:
        return {"schema_info": f"Error extracting schema: {str(e)}"}
    
    schema_info = "\n".join(schema_parts).strip()
    
    if not schema_info:
        schema_info = "No tables found in the database."
        
    return {"schema_info": schema_info}
