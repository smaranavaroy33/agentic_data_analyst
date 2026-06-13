from pydantic import BaseModel, Field
from typing import List, Any

class AgentState(BaseModel):
    user_question: str = Field(description="What the user asked initially")
    file_name: str = Field(description="Context and name of the uploaded file")
    session_id: str = Field(default="default", description="Unique ID for user session")
    db_path: str = Field(default="sessions/temp.db", description="Path to the session SQLite database")
    
    # Defaults provided so the graph can initialize before these are populated
    schema_info: str = Field(default="", description="The dynamically extracted database schema")
    sql_query: str = Field(default="", description="The generated SQL code drafted by the LLM")
    sql_error: str = Field(default="", description="Captures execution errors for the correction loop")
    raw_data: List[Any] = Field(default_factory=list, description="The successfully retrieved database rows")
    
    needs_chart: bool = Field(default=False, description="Router decision flag (True if visualization is needed)")
    plotly_code: str = Field(default="", description="The generated Python visualization code")
    visualization_error: str = Field(default="", description="Captures Python execution errors for the visualization loop")
    
    final_summary: str = Field(default="", description="The final analytical output generated for the user")
    sql_retry_count: int = Field(default=0, description="Current number of retries in the SQL loop")
    viz_retry_count: int = Field(default=0, description="Current number of retries in the Visualization loop")
    reasoning_log: List[dict] = Field(default_factory=list, description="Captures the internal reasoning (thinking) of the model at each step")
