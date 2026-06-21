# Technical Documentation: Automated Data Analyst

## 1. Overview
The **Automated Data Analyst** is a self-correcting, multi-agent system designed to automate end-to-end data analysis. It transforms raw structured data (CSV/Excel) into interactive visualizations and natural language insights using a "Chain-of-Thought" architecture orchestrated by **LangGraph**.

## 2. System Architecture
The application is built on a directed acyclic graph (with controlled cycles for correction) using LangGraph.

### 2.1 Workflow Nodes
- **Schema Extractor**: Analyzes the SQLite database to extract table structures and column types.
- **SQL Drafter**: Generates SQLite-compatible queries based on user intent and schema.
- **SQL Executor**: Executes the generated SQL query in a secure, read-only environment.
- **Router**: Analyzes retrieved data and the user question to decide if a visualization is necessary.
- **Visualization Drafter**: Writes Python code using the Plotly library to create interactive charts.
- **Visualization Tester**: Executes and validates the generated Python code in a sandboxed REPL.
- **Inference Agent (Summary)**: Synthesizes the SQL logic, raw data, and visual findings into a final response.

### 2.2 Control Flow & Self-Correction
The system features two primary self-correction loops:
1.  **SQL Correction Loop**: If `SQL Executor` encounters an error (syntax, missing columns, etc.), the graph routes back to `SQL Drafter` with the error message. It allows up to 3 retries.
2.  **Visualization Correction Loop**: If `Visualization Tester` fails to execute the Python code, the graph routes back to `Visualization Drafter` for a fix. It allows up to 3 retries.

## 3. State Management
The `AgentState` object persists across the entire workflow, ensuring context is shared between agents:
- `user_question`: Original user prompt.
- `schema_info`: Database metadata.
- `sql_query` / `sql_error`: Current SQL state.
- `raw_data`: Result set from the database.
- `needs_chart`: Boolean flag from the Router.
- `plotly_code` / `visualization_error`: Current visualization state.
- `reasoning_log`: Captured "Thinking" blocks from the LLM for transparency.

## 4. Agent Descriptions

### 4.1 Router Agent
Acts as the decision-maker. It evaluates if the data retrieved is suitable for visualization (e.g., trends over time, comparisons, distributions) and sets the `needs_chart` flag.

### 4.2 SQL Drafter
Specializes in translating natural language to SQLite. It is instructed to handle complex joins, aggregations, and filtering while adhering to the provided schema.

### 4.3 Visualization Agent
Expert in data storytelling using Plotly. It generates clean, interactive code and handles dynamic scaling and labeling based on the data provided in `raw_data`.

### 4.4 Summary Agent
The final touchpoint. It provides context to the numbers, explaining *why* the data looks the way it does and highlighting key takeaways.

## 5. Tools and Utilities

### 5.1 SQL Executor (`db_executor.py`)
- **Security**: Enforces `SELECT`-only queries and blocks destructive keywords (`DROP`, `DELETE`, etc.).
- **Data Handling**: Uses `sqlite3.Row` to return data as dictionaries, providing better context for the LLM.

### 5.2 Python REPL (`python_repl.py`)
- **Sandboxing**: Executes generated Python code for visualizations.
- **Validation**: Captures tracebacks to feed into the Visualization Correction Loop.

### 5.3 PDF Export (`pdf_export.py`)
Compiles the analysis history into a formatted report using `reportlab`, including tables, text, and embedded chart logic.

## 6. Data Ingestion & Metadata Discovery
1.  **Upload**: User provides CSV or Excel through the Streamlit interface.
2.  **Sanitization**: `data_ingest.py` cleans column names (removes spaces, special characters, and ensures they don't start with numbers).
3.  **Storage**: Data is loaded into a session-specific SQLite database (`sessions/session_{id}/data.db`).
4.  **Intelligent Metadata Discovery**: In the frontend (`app.py`), the system uses an LLM to analyze data statistics (unique counts, min/max, samples) and generates natural language descriptions for every column. These are displayed in the "Data Preview" tab.
5.  **Schema Extraction**: Within the graph, the `schema_extractor` node dynamically fetches table structures and includes sample values for each column to provide the LLM with precise context for query generation.

## 7. Reasoning & Transparency ("Thinking")
A core feature of the system is the persistence of the model's internal reasoning:
- **Extraction**: The `utils/reasoning.py` utility extracts "thinking" or "reasoning_content" blocks from the NVIDIA Nemotron-3 responses.
- **Logging**: Each agent's reasoning is appended to the `reasoning_log` in the `AgentState`.
- **UI Display**: The Streamlit sidebar features a "Thinking History" that shows the step-by-step logic for every question asked, as well as a "Live Thinking" view for real-time updates during analysis.
## 8. Tech Stack
- **Core Framework**: LangGraph
- **LLM**: NVIDIA Nemotron-3 Super 120B (via NVIDIA API)
- **Frontend**: Streamlit
- **Data Visualization**: Plotly
- **Database**: SQLite
- **Report Generation**: ReportLab
- **Language**: Python 3.10+

## 9. Security Considerations
- **Read-Only DB**: Databases are opened in `mode=ro` (read-only) at the URI level.
- **SQL Sanitization**: Keyword filtering prevents common injection attacks.
- **Local Isolation**: Each user session has a dedicated SQLite file and directory to prevent data leakage between sessions.
