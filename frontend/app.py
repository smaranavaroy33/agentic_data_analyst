import streamlit as st
import os
import sys
import pandas as pd
import uuid
import json
import sqlite3

# --- Path Configuration ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.data_ingest import ingest_to_sqlite
from graph.workflow import app as graph_app
from graph.state import AgentState
from utils.config import get_chat_model
from prompt_library.column_descriptions import COLUMN_DESCRIPTION_PROMPT
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Self-Correcting Data Analyst",
    page_icon="📊",
    layout="wide"
)

# --- Session Folder Management ---
def get_next_session_number(base_dir="sessions"):
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        return 1
    existing_sessions = [d for d in os.listdir(base_dir) if d.startswith("session_")]
    numbers = []
    for s in existing_sessions:
        try: numbers.append(int(s.split("_")[1]))
        except: continue
    return max(numbers) + 1 if numbers else 1

# --- Session State Initialization ---
if "session_num" not in st.session_state:
    st.session_state.session_num = get_next_session_number()
    st.session_state.session_dir = os.path.join("sessions", f"session_{st.session_state.session_num}")
    os.makedirs(st.session_state.session_dir, exist_ok=True)

if "db_path" not in st.session_state:
    st.session_state.db_path = os.path.join(st.session_state.session_dir, "data.db")
if "final_state" not in st.session_state:
    st.session_state.final_state = None
if "last_question" not in st.session_state:
    st.session_state.last_question = None
if "column_descriptions" not in st.session_state:
    st.session_state.column_descriptions = {} # Key: table_name, Value: dict of descriptions
if "preview_dfs" not in st.session_state:
    st.session_state.preview_dfs = {} # Key: table_name, Value: DataFrame
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "uploaded_file_names" not in st.session_state:
    st.session_state.uploaded_file_names = []

def get_column_descriptions(df):
    """Fetch column descriptions using LLM by analyzing a summary of the data."""
    llm = get_chat_model()
    
    # 1. Prepare a meaningful summary of the dataset
    num_rows = len(df)
    sample_data = df.head(5).to_dict(orient="records")
    
    # Generate per-column stats (unique counts, examples, min/max for numbers)
    stats = {}
    for col in df.columns:
        col_data = df[col]
        stats[col] = {
            "dtype": str(col_data.dtype),
            "unique_values_count": int(col_data.nunique()),
            "sample_values": col_data.dropna().unique()[:3].tolist()
        }
        # Add range info for numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            stats[col]["min"] = float(col_data.min()) if not pd.isna(col_data.min()) else None
            stats[col]["max"] = float(col_data.max()) if not pd.isna(col_data.max()) else None

    prompt_context = f"""
    Dataset Overview:
    - Total Rows: {num_rows}
    - Total Columns: {len(df.columns)}
    
    Column Statistics and Samples:
    {json.dumps(stats, indent=2)}
    
    Data Sample (First 5 rows):
    {json.dumps(sample_data, indent=2)}
    """
    
    messages = [
        {"role": "system", "content": COLUMN_DESCRIPTION_PROMPT},
        {"role": "user", "content": prompt_context}
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Log response for debugging
        print(f"DEBUG: LLM Column Description Response:\n{content}")
        
        # Robust JSON Extraction: 
        # 1. Try to find content between ```json and ```
        # 2. Try to find content between { and }
        import re
        json_content = None
        
        code_block_match = re.search(r"```json\s*({.*?})\s*```", content, re.DOTALL)
        if code_block_match:
            json_content = code_block_match.group(1).strip()
        else:
            brace_match = re.search(r"({.*})", content, re.DOTALL)
            if brace_match:
                json_content = brace_match.group(1).strip()
        
        if not json_content:
            json_content = content # Try the raw content if regex fails

        descriptions = json.loads(json_content)
        
        # Case-insensitive mapping and ensuring all columns have a description
        final_descriptions = {}
        llm_keys_lower = {k.lower(): v for k, v in descriptions.items()}
        
        for col in df.columns:
            if col in descriptions:
                final_descriptions[col] = descriptions[col]
            elif col.lower() in llm_keys_lower:
                final_descriptions[col] = llm_keys_lower[col.lower()]
            else:
                final_descriptions[col] = f"Column containing {df[col].dtype} data."
        
        return final_descriptions
    except Exception as e:
        print(f"ERROR in get_column_descriptions: {e}")
        # Fallback to deterministic descriptions if LLM fails
        return {col: f"Column with {df[col].nunique()} unique {df[col].dtype} values." for col in df.columns}

def main():
    st.title("Automated Data Analyst")
    # st.caption(f"Project Workspace: {st.session_state.session_dir}")

    # --- Sidebar: Data Ingestion & Thinking History ---
    with st.sidebar:
        st.header("📁 Data Ingestion")
        uploaded_files = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"], accept_multiple_files=True)
        
        if uploaded_files:
            new_files = [f for f in uploaded_files if f.name not in st.session_state.uploaded_file_names]
            
            if new_files:
                for uploaded_file in new_files:
                    save_path = os.path.join(st.session_state.session_dir, uploaded_file.name)
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Sanitize filename for table name
                    table_name = os.path.splitext(uploaded_file.name)[0].lower()
                    table_name = "".join([c if c.isalnum() else "_" for c in table_name])
                    if table_name[0].isdigit():
                        table_name = f"t_{table_name}"
                    
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        try:
                            ingest_to_sqlite(save_path, db_path=st.session_state.db_path, table_name=table_name)
                            
                            # Load DF for preview and descriptions
                            with sqlite3.connect(st.session_state.db_path) as conn:
                                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                            
                            st.session_state.preview_dfs[table_name] = df
                            st.session_state.column_descriptions[table_name] = get_column_descriptions(df)
                            st.session_state.uploaded_file_names.append(uploaded_file.name)
                            st.success(f"Table '{table_name}' ready!")
                        except Exception as e:
                            st.error(f"Ingestion Error ({uploaded_file.name}): {e}")
                
                st.session_state.final_state = None
                st.rerun()

        st.divider()
        
        # --- Thinking History (Persistent) ---
        st.header("🧠 Thinking History")
        # if not st.session_state.analysis_history:
        #     st.info("No thinking logs yet. Ask a question to see the model's reasoning!")
        # else:
        for i, entry in enumerate(st.session_state.analysis_history):
            with st.expander(f"Q{i+1} Thinking: {entry['question'][:30]}...", expanded=False):
                for step in entry.get("reasoning_log", []):
                    st.markdown(f"**{step['agent']}**")
                    st.caption(step['content'])
                    st.divider()

        # Placeholder for LIVE thinking (will be populated during analysis)
        live_thinking_container = st.container()

    # --- Tabbed Interface ---
    tab_preview, tab_analysis = st.tabs(["🔍 Data Preview", "🧪 Data Analysis"])

    with tab_preview:
        if st.session_state.preview_dfs:
            st.subheader("Select Table to Preview")
            selected_table = st.selectbox("Tables:", options=list(st.session_state.preview_dfs.keys()))
            
            if selected_table:
                df = st.session_state.preview_dfs[selected_table]
                st.subheader(f"Raw Data: {selected_table}")
                st.dataframe(df, use_container_width=True)
                
                st.subheader(f"Column Metadata: {selected_table}")
                # Combine types and descriptions
                meta_df = df.dtypes.astype(str).to_frame(name="Data Type")
                table_descriptions = st.session_state.column_descriptions.get(selected_table, {})
                meta_df["Description"] = meta_df.index.map(lambda x: table_descriptions.get(x, "N/A"))
                st.table(meta_df)
        else:
            st.info("Please upload files to view the preview.")

    with tab_analysis:
        if st.session_state.uploaded_file_names:
            # 1. Render History
            if st.session_state.analysis_history:
                st.subheader("Analysis History")
                for i, entry in enumerate(st.session_state.analysis_history):
                    with st.container():
                        st.markdown(f"### Q{i+1}: {entry['question']}")
                        
                        # 1. SQL Query First
                        with st.expander(f"SQL (Q{i+1})", expanded=False):
                            st.code(entry['sql_query'], language="sql")
                        
                        # 2. Detailed Analysis
                        st.markdown(entry['summary'])
                        
                        # 3. Visualization Finally
                        if entry['needs_chart'] and entry['plotly_code']:
                            try:
                                scope = {"pd": pd, "px": px, "data": entry['raw_data']}
                                exec(entry['plotly_code'], {}, scope)
                                if "fig" in scope:
                                    st.plotly_chart(scope["fig"], use_container_width=True, key=f"chart_{i}")
                            except Exception as e:
                                st.error(f"Visualization Error in Q{i+1}: {e}")
                        
                        st.divider()

            # --- PDF Download Section ---
            if "pdf_bytes" not in st.session_state:
                st.session_state.pdf_bytes = None
            if "pdf_history_len" not in st.session_state:
                st.session_state.pdf_history_len = 0

            # Invalidate cached PDF if history changed
            if len(st.session_state.analysis_history) > 0:
                if st.session_state.pdf_history_len != len(st.session_state.analysis_history):
                    st.session_state.pdf_bytes = None

                if st.session_state.pdf_bytes is None:
                    if st.button("Generate PDF Report"):
                        with st.spinner("Compiling PDF with charts (this may take a few seconds)..."):
                            from utils.pdf_export import generate_insights_pdf
                            st.session_state.pdf_bytes = generate_insights_pdf(st.session_state.analysis_history)
                            st.session_state.pdf_history_len = len(st.session_state.analysis_history)
                            st.rerun()
                else:
                    st.download_button(
                        label="Download Insights PDF",
                        data=st.session_state.pdf_bytes,
                        file_name="data_analysis_insights.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                    if st.button("Regenerate PDF"):
                        st.session_state.pdf_bytes = None
                        st.rerun()
            
            st.divider()

            # 2. Dynamic Input Section (Always at the bottom)
            st.subheader("Ask a Question")
            user_question = st.text_input(
                "Enter your query", 
                placeholder="e.g., Join customers and orders to find top spenders",
                key=f"analysis_input_{len(st.session_state.analysis_history)}"
            )

            col1, col2 = st.columns([1, 5])
            with col1:
                analyze_clicked = st.button("Analyze")
            with col2:
                if st.button("Clear History"):
                    st.session_state.analysis_history = []
                    st.rerun()

            if analyze_clicked and user_question:
                initial_state = AgentState(
                    user_question=user_question,
                    file_name=", ".join(st.session_state.uploaded_file_names),
                    session_id=str(st.session_state.session_num),
                    db_path=st.session_state.db_path
                )

                # Thread ID for the checkpointer
                config = {"configurable": {"thread_id": st.session_state.session_num}}

                # Use the pre-defined live container in the sidebar
                with live_thinking_container:
                    st.divider()
                    st.header("🧠 Live Thinking...")
                    thinking_placeholder = st.empty()

                with st.spinner("Generating insights..."):
                    try:
                        final_state_dict = {}
                        # Use streaming to get updates as each node finishes
                        for update in graph_app.stream(initial_state, config=config, stream_mode="updates"):
                            # Update our local record of the state
                            for node_name, state_update in update.items():
                                final_state_dict.update(state_update)
                                
                                # Dynamically update the sidebar with the latest reasoning log
                                if "reasoning_log" in final_state_dict:
                                    with thinking_placeholder.container():
                                        for step in final_state_dict["reasoning_log"]:
                                            with st.expander(f"Step: {step['agent']}", expanded=True):
                                                st.info(step['content'])

                        # Store in history after completion
                        st.session_state.analysis_history.append({
                            "question": user_question,
                            "summary": final_state_dict.get("final_summary"),
                            "needs_chart": final_state_dict.get("needs_chart"),
                            "plotly_code": final_state_dict.get("plotly_code"),
                            "raw_data": final_state_dict.get("raw_data"),
                            "sql_query": final_state_dict.get("sql_query"),
                            "reasoning_log": final_state_dict.get("reasoning_log", [])
                        })
                        st.session_state.final_state = final_state_dict # Update current state for sidebar
                        st.rerun() # Refresh to show new entry and move input down
                    except Exception as e:
                        st.error(f"Execution Error: {e}")
        else:
            st.info("Upload a file first to enable analysis.")

if __name__ == "__main__":
    main()
