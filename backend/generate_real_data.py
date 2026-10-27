import os
import pandas as pd
import numpy as np

def generate_enterprise_datasets():
    os.makedirs("./data/samples", exist_ok=True)
    np.random.seed(42)

    # 1. Retail Transactions Dataset (1,200 rows with temporal span, customers, products, regions, prices)
    n_records = 1200
    dates = pd.date_range("2025-01-01", periods=180, freq="D")
    sample_dates = np.random.choice(dates, size=n_records)
    
    customers = [f"CUST_{i:04d}" for i in range(1, 151)]
    sample_custs = np.random.choice(customers, size=n_records)

    products = [
        ("SKU_TECH_01", "Enterprise Server Blade", "Hardware", 1250.0),
        ("SKU_TECH_02", "Cloud Backup License", "Software", 350.0),
        ("SKU_TECH_03", "AI Inference Accelerator", "Hardware", 2800.0),
        ("SKU_TECH_04", "Security Perimeter Gateway", "Security", 950.0),
        ("SKU_TECH_05", "DevOps Pipeline Annual Sub", "SaaS", 600.0),
        ("SKU_TECH_06", "Consulting & Deployment", "Services", 1500.0),
        ("SKU_TECH_07", "Database Migration Tool", "Software", 450.0),
        ("SKU_TECH_08", "Workstation Pro", "Hardware", 1850.0)
    ]
    prod_indices = np.random.choice(len(products), size=n_records)
    
    regions = ["North America", "Western Europe", "Asia Pacific", "Latin America"]
    sample_regions = np.random.choice(regions, size=n_records, p=[0.4, 0.3, 0.2, 0.1])

    quantities = np.random.choice([1, 2, 3, 4, 5, 10], size=n_records, p=[0.5, 0.25, 0.12, 0.08, 0.03, 0.02])

    data = []
    for i in range(n_records):
        sku, p_name, cat, unit_price = products[prod_indices[i]]
        qty = int(quantities[i])
        # Add slight discount/variation
        discount = np.random.choice([0.0, 0.05, 0.1, 0.15], p=[0.6, 0.2, 0.15, 0.05])
        revenue = round(unit_price * qty * (1 - discount), 2)
        
        data.append({
            "transaction_id": f"TX_{100000 + i}",
            "transaction_date": pd.to_datetime(sample_dates[i]).strftime("%Y-%m-%d"),
            "customer_id": sample_custs[i],
            "product_id": sku,
            "product_name": p_name,
            "category": cat,
            "region": sample_regions[i],
            "unit_price": unit_price,
            "quantity": qty,
            "discount_rate": discount,
            "revenue": revenue
        })

    retail_df = pd.DataFrame(data).sort_values(by="transaction_date")
    
    # Introduce 5 realistic duplicates & 10 missing values to verify profiling & data quality engines
    retail_df.loc[12, "discount_rate"] = np.nan
    retail_df.loc[34, "region"] = np.nan
    
    retail_csv_path = "./data/samples/enterprise_sales_transactions.csv"
    retail_df.to_csv(retail_csv_path, index=False)
    print(f"Generated {retail_csv_path} with {len(retail_df)} records.")

    # 2. Large Dataset for Stress & Performance Testing (25,000 rows)
    n_large = 25000
    large_dates = np.random.choice(pd.date_range("2024-01-01", "2025-12-31", freq="D"), size=n_large)
    large_custs = np.random.choice([f"C_{i:05d}" for i in range(1, 1500)], size=n_large)
    large_amounts = np.round(np.random.exponential(scale=120.0, size=n_large) + 15.0, 2)
    large_regions = np.random.choice(["EMEA", "APAC", "AMER"], size=n_large)

    large_df = pd.DataFrame({
        "order_id": [f"ORD_{i:07d}" for i in range(1, n_large + 1)],
        "order_date": [pd.to_datetime(d).strftime("%Y-%m-%d") for d in large_dates],
        "customer_id": large_custs,
        "region": large_regions,
        "revenue": large_amounts,
        "status": np.random.choice(["Completed", "Shipped", "Processing"], size=n_large, p=[0.8, 0.15, 0.05])
    })
    large_csv_path = "./data/samples/large_scale_orders_25k.csv"
    large_df.to_csv(large_csv_path, index=False)
    print(f"Generated {large_csv_path} with {len(large_df)} records.")

if __name__ == "__main__":
    generate_enterprise_datasets()
