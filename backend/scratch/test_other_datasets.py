import requests

datasets = requests.get('http://127.0.0.1:8000/api/v1/datasets').json()

tests = [
    ("diamonds", "what is the most expensive diamond"),
    ("diamonds", "average diamond price by cut"),
    ("sales", "top 5 products by revenue"),
    ("titanic", "how many passengers survived"),
    ("titanic", "who paid the highest fare")
]

for kw, q in tests:
    ds = next((d for d in datasets if kw in d['name'].lower()), None)
    if not ds:
        print(f"Dataset for {kw} not found")
        continue
    res = requests.post('http://127.0.0.1:8000/api/v1/ask-data', json={
        "question": q,
        "dataset_id": ds['id']
    }).json()
    print("=" * 60)
    print(f"DATASET: {ds['name']} | QUESTION: {q}")
    print("SQL:", res.get("sql_query"))
    print("INTENT:", res.get("intent"))
    print("ANSWER:\n", res.get("answer"))

