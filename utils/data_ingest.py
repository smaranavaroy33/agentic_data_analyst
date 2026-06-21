import logging
import os
import re

import pandas as pd
import sqlite3

logger = logging.getLogger(__name__)

def ingest_to_sqlite(file_path: str, db_path: str = "sessions/temp.db", table_name: str = "uploaded_data") -> bool:
    """
    Reads a CSV or Excel file and ingests it into a temporary SQLite database.

    This utility handles the conversion of user-uploaded files into a 
    structured format that can be queried via SQL. It creates or overwrites 
    the specified SQLite database.

    Args:
        file_path (str): The absolute or relative path to the uploaded file.
        db_path (str): The path to the SQLite database file. 
            Defaults to 'sessions/temp.db'.
        table_name (str): The name of the table to create in SQLite. 
            Defaults to 'uploaded_data'.

    Returns:
        bool: True if ingestion was successful.
    
    Raises:
        ValueError: If the file format is unsupported.
        Exception: If any other error occurs during ingestion.
    """
    # 1. Ensure the directory for the database exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # 2. Read the file based on its extension
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

    # 3. Clean column names (remove spaces and special characters for SQL compatibility)
    def clean_col(c):
        c = str(c).strip()
        c = re.sub(r'\W+', '_', c)  # Replace non-alphanumeric with underscore
        c = c.strip('_')
        # Ensure it doesn't start with a number (SQLite columns shouldn't start with numbers ideally)
        if c and c[0].isdigit():
            c = f"col_{c}"
        return c if c else "unnamed_col"
        
    df.columns = [clean_col(c) for c in df.columns]

    # 4. Connect to SQLite and write the data using a context manager
    with sqlite3.connect(db_path) as conn:
        # We use 'replace' to ensure that if a user uploads a new file, 
        # the old 'uploaded_data' table is dropped.
        df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    logger.info("Successfully ingested '%s' into table '%s' at '%s'", file_path, table_name, db_path)
    return True
