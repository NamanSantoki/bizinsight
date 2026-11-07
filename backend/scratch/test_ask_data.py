import requests
import json

datasets = requests.get('http://127.0.0.1:8000/api/v1/datasets').json()
cal_id = next(d['id'] for d in datasets if 'california' in d['name'])
print("California dataset id:", cal_id)

queries = [
    "what is the most expensive house",
    "what is the average house value",
    "average house value by ocean proximity",
    "houses near the bay"
]

for q in queries:
    res = requests.post('http://127.0.0.1:8000/api/v1/ask-data', json={
        "question": q,
        "dataset_id": cal_id
    }).json()
    print("=" * 60)
    print("QUESTION:", q)
    print("SQL:", res.get("sql_query"))
    print("INTENT:", res.get("intent"))
    print("ANSWER:\n", res.get("answer"))
    print("INSIGHTS:", res.get("key_insights"))
    print("FOLLOWUPS:", res.get("suggested_followups"))
    print("ROWS RETRIEVED:", res.get("row_count"))

