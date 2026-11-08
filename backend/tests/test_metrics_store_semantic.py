# Tests for Semantic Metrics Store (semantic/metrics_store.py)
import pandas as pd
import pytest
from backend.app.semantic.metrics_store import MetricsStore

@pytest.fixture
def store():
    return MetricsStore()

def test_list_metrics_returns_defaults(store):
    metrics = store.list_metrics()
    assert isinstance(metrics, list)
    assert len(metrics) >= 4  # seeded metrics
    ids = {m['id'] for m in metrics}
    assert {'revenue', 'aov', 'gross_margin', 'retention_rate'} & ids

def test_generate_dataset_metrics_numeric_and_categorical():
    df = pd.DataFrame({
        'sales': [100, 200, 150],
        'region': ['EU', 'APAC', 'EU'],
        'category': ['A', 'B', 'A']
    })
    store = MetricsStore()
    generated = store.generate_dataset_metrics('custom_data', 'sales_table', df)
    # Should generate at least sum, avg, max for numeric column 'sales'
    ids = {m['id'] for m in generated}
    assert any('custom_data_sum_sales' in i for i in ids)
    assert any('custom_data_avg_sales' in i for i in ids)
    assert any('custom_data_max_sales' in i for i in ids)
    # Should generate distinct count for first categorical column 'region'
    assert any('custom_data_count_region' in i for i in ids)

