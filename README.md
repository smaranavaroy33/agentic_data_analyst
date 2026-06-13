# 📊 Automated Data Analyst (Self-Correcting Multi-Agent System)

An advanced, end-to-end data analysis platform that leverages a multi-agent "Chain-of-Thought" architecture to transform raw data into actionable insights. Built with **LangGraph**, **Streamlit**, and **NVIDIA's Nemotron-3 Super 120B**, the system autonomously writes SQL, generates visualizations, and provides detailed natural language summaries.

---

## 🚀 Key Features

- **🧠 Persistent "Model Thinking" History**: A dedicated sidebar that streams the model's internal reasoning in real-time. Unlike standard chatbots, the "Thinking" logs are preserved for every question asked, allowing you to audit the model's decision-making process at any time.
- **🤖 Self-Correcting Multi-Agent Workflow**: If an agent makes an error (e.g., an invalid SQL query or a visualization bug), the system detects the failure and loops back to correct itself before presenting the final result.
- **📈 Dynamic Visualization Engine**: Autonomously decides which chart type (Bar, Line, Scatter, etc.) best represents the data and generates interactive Plotly visualizations.
- **📁 Multi-Format Data Ingestion**: Upload CSV or Excel files. The system automatically sanitizes, processes, and stores them in a local SQLite database for efficient querying.
- **📄 Automated PDF Reporting**: Compile your entire analysis history—including questions, SQL queries, summaries, and charts—into a professional PDF report with a single click.
- **🔍 Intelligent Metadata Discovery**: Uses LLMs to analyze data samples and automatically generate meaningful column descriptions, helping the agents understand the context of your dataset.

---

## 🕵️ Agent Descriptions

The system is powered by four specialized agents that collaborate within a LangGraph workflow:

1.  **Router Agent**: The "Brain" of the operation. It analyzes the user's question and the database schema to decide the best path forward. It identifies which tables are needed and determines if a simple query or a complex multi-step analysis is required.
2.  **SQL Agent**: Responsible for drafting precise SQL queries. It understands SQLite dialect nuances and uses the metadata provided by the system to ensure joins and filters are accurate.
3.  **Visualization Agent**: Determines if the data requires a visual representation. If so, it writes Python code using Plotly to generate interactive charts, ensuring the visual style is clean and informative.
4.  **Summary Agent**: Synthesizes the raw data results, the SQL logic used, and the visual insights into a clear, natural language explanation for the user.

---

## 📁 Project Structure

```text
agentic_data_analyst/
├── agents/                  # Specialized LLM agent logic
│   ├── router.py            # Logic for routing queries
│   ├── schema.py            # Schema extraction logic
│   ├── sql.py               # SQL generation logic
│   ├── summary.py           # Analysis summarization logic
│   └── visualization.py     # Plotly code generation logic
├── frontend/                # Streamlit UI implementation
│   └── app.py               # Main application entry point
├── graph/                   # LangGraph workflow orchestration
│   ├── state.py             # Agent state definitions
│   └── workflow.py          # Workflow graph construction
├── prompt_library/          # Centralized LLM prompts
├── sessions/                # Session-specific databases and file uploads
├── tools/                   # Executable tools (DB executor, Python REPL)
├── utils/                   # Shared utilities (Config, Ingestion, PDF Export)
├── pyproject.toml           # Project dependencies
└── README.md                # Project documentation
```

---

## 🛠️ Tech Stack

- **LLM**: NVIDIA Nemotron-3 Super 120B (nemotron-3-super-120b-a12b)
- **Orchestration**: LangGraph
- **Frontend**: Streamlit
- **Visualization**: Plotly
- **Database**: SQLite
- **Environment**: Python 3.10+
