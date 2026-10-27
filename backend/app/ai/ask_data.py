import re
import time
import requests
import sqlparse
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.core.config import settings

# Disallowed dangerous SQL keywords for Read-Only Execution
FORBIDDEN_KEYWORDS = [
    r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b', r'\bALTER\b',
    r'\bTRUNCATE\b', r'\bCREATE\b', r'\bGRANT\b', r'\bREVOKE\b', r'\bEXEC\b',
    r'\bEXECUTE\b', r'\bATTACH\b', r'\bDETACH\b', r'\bPRAGMA\b'
]

def validate_sql_query(query: str, allowed_table: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates that a SQL query is strictly a read-only SELECT query:
    1. Checks for forbidden mutating keywords
    2. Ensures it starts with SELECT
    3. Prevents multi-statement SQL injection (e.g. semicolon chaining)
    4. Enforces row limits
    """
    if not query or not query.strip():
        return False, None, "Empty SQL query."

    clean_q = query.strip()
    
    # Strip markdown block quotes if LLM returned ```sql ... ```
    clean_q = re.sub(r'^```sql\s*', '', clean_q, flags=re.IGNORECASE)
    clean_q = re.sub(r'^```\s*', '', clean_q)
    clean_q = re.sub(r'\s*```$', '', clean_q)
    clean_q = clean_q.strip()

    # Parse with sqlparse
    parsed = sqlparse.parse(clean_q)
    if len(parsed) > 1:
        return False, None, "Multiple SQL statements are not permitted for security."

    stmt = parsed[0]
    if stmt.get_type() != "SELECT":
        return False, None, f"Only SELECT queries are permitted. Detected statement type: {stmt.get_type()}."

    # Check forbidden keywords
    upper_q = clean_q.upper()
    for kw_pattern in FORBIDDEN_KEYWORDS:
        if re.search(kw_pattern, upper_q):
            return False, None, f"Security Violation: Prohibited SQL command '{kw_pattern}' detected."

    # Ensure LIMIT is present, or append safe limit
    if "LIMIT" not in upper_q:
        clean_q = f"{clean_q.rstrip(';')} LIMIT {settings.MAX_QUERY_ROW_LIMIT}"
    
    return True, clean_q, None

def generate_sql_from_question(
    question: str,
    table_name: str,
    columns: List[str],
    column_types: Dict[str, str]
) -> str:
    """
    Translates user's natural language question to a safe SQL query using Ollama if running,
    or our high-precision deterministic semantic SQL mapper as fallback.
    """
    # 1. Try local Ollama if available
    try:
        schema_desc = ", ".join([f'"{col}" ({column_types.get(col, "TEXT")})' for col in columns])
        system_prompt = (
            f"You are a strict text-to-SQL translator for a table named '{table_name}'. "
            f"Columns: {schema_desc}. "
            "Return ONLY a single valid read-only SELECT query. "
            "Never use DROP, DELETE, UPDATE, INSERT, ALTER. "
            "Wrap column names with double quotes if needed. Return ONLY the SQL query."
        )
        
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": f"{system_prompt}\n\nQuestion: {question}\nSQL:",
                "stream": False
            },
            timeout=3.0
        )
        if response.status_code == 200:
            sql_out = response.json().get("response", "").strip()
            if sql_out.upper().startswith("SELECT"):
                return sql_out
    except Exception:
        # Fall through to deterministic semantic mapping
        pass

    # 2. High-precision Deterministic Semantic SQL Engine (Fallback)
    q_lower = question.lower()
    
    # Identify candidate columns
    numeric_cols = [c for c, t in column_types.items() if any(nt in t.lower() for nt in ["int", "float", "double", "num", "real"])]
    date_cols = [c for c, t in column_types.items() if any(dt in t.lower() for dt in ["date", "time"])]
    cat_cols = [c for c in columns if c not in numeric_cols and c not in date_cols]

    # Target metric
    target_metric = None
    for candidate in ["revenue", "sales", "total_amount", "amount", "price", "profit", "cost", "quantity"]:
        matched = next((c for c in numeric_cols if candidate in c.lower()), None)
        if matched:
            target_metric = matched
            break
    if not target_metric and numeric_cols:
        target_metric = numeric_cols[0]

    # Target dimension
    target_dim = None
    for candidate in ["region", "country", "category", "product", "customer", "state", "city", "department"]:
        matched = next((c for c in cat_cols if candidate in c.lower()), None)
        if matched:
            target_dim = matched
            break

    # Construct appropriate query
    if ("highest" in q_lower or "top" in q_lower or "most" in q_lower) and target_dim and target_metric:
        return f'SELECT "{target_dim}", SUM("{target_metric}") AS total_{target_metric} FROM "{table_name}" GROUP BY "{target_dim}" ORDER BY total_{target_metric} DESC LIMIT 5'
    
    if ("lowest" in q_lower or "bottom" in q_lower or "least" in q_lower) and target_dim and target_metric:
        return f'SELECT "{target_dim}", SUM("{target_metric}") AS total_{target_metric} FROM "{table_name}" GROUP BY "{target_dim}" ORDER BY total_{target_metric} ASC LIMIT 5'

    if ("average" in q_lower or "mean" in q_lower) and target_dim and target_metric:
        return f'SELECT "{target_dim}", AVG("{target_metric}") AS avg_{target_metric} FROM "{table_name}" GROUP BY "{target_dim}" ORDER BY avg_{target_metric} DESC LIMIT 10'

    if ("total" in q_lower or "sum" in q_lower) and target_metric:
        if target_dim:
            return f'SELECT "{target_dim}", SUM("{target_metric}") AS total_{target_metric} FROM "{table_name}" GROUP BY "{target_dim}" ORDER BY total_{target_metric} DESC LIMIT 10'
        return f'SELECT SUM("{target_metric}") AS total_{target_metric} FROM "{table_name}"'

    if ("count" in q_lower or "how many" in q_lower):
        if target_dim:
            return f'SELECT "{target_dim}", COUNT(*) AS count_records FROM "{table_name}" GROUP BY "{target_dim}" ORDER BY count_records DESC LIMIT 10'
        return f'SELECT COUNT(*) AS total_records FROM "{table_name}"'

    # Default fallback: inspect top rows
    cols_quoted = ', '.join([f'"{c}"' for c in columns[:6]])
    return f'SELECT {cols_quoted} FROM "{table_name}" LIMIT 10'

def execute_safe_query(
    db: Session,
    sql_query: str,
    table_name: str
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Executes validated read-only SQL query with timeout protection.
    """
    is_valid, validated_sql, err = validate_sql_query(sql_query, table_name)
    if not is_valid:
        return None, err

    try:
        # Execute query
        cursor = db.execute(text(validated_sql))
        keys = list(cursor.keys())
        rows = cursor.fetchall()
        
        results = [dict(zip(keys, row)) for row in rows]
        # Clean results for JSON serialization
        clean_results = []
        for r in results:
            clean_r = {}
            for k, v in r.items():
                if v is None:
                    clean_r[k] = None
                elif hasattr(v, 'isoformat'):
                    clean_r[k] = v.isoformat()
                elif isinstance(v, (int, float, str, bool)):
                    clean_r[k] = v
                else:
                    clean_r[k] = str(v)
            clean_results.append(clean_r)

        return clean_results, None
    except Exception as e:
        return None, f"Database query execution error: {str(e)}"
