import os
import shutil
import hashlib
import pandas as pd
from sqlalchemy import inspect as sa_inspect
from backend.app.core.database import SessionLocal, engine
from backend.app.models.all_models import Dataset, AuditLog, DataSource
from backend.app.core.config import settings
from backend.app.ingestion.service import sanitize_table_name

def seed_enterprise_data():
    db = SessionLocal()
    try:
        samples_dir = settings.SAMPLES_DIR
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

        # 1. First, verify existing datasets and ensure they have queryable SQL tables
        inspector = sa_inspect(engine)
        existing_datasets = db.query(Dataset).all()
        for d in existing_datasets:
            needs_table = not d.storage_table_name or not inspector.has_table(d.storage_table_name)
            if needs_table:
                file_path = d.processed_file_path or d.raw_file_path
                df = None
                if file_path and os.path.exists(file_path):
                    df = pd.read_csv(file_path, low_memory=False)
                elif samples_dir and os.path.exists(samples_dir):
                    for fname in os.listdir(samples_dir):
                        if fname.lower() in d.name.lower() or fname.replace(".csv", "").lower() in d.name.lower():
                            df = pd.read_csv(os.path.join(samples_dir, fname), low_memory=False)
                            break
                if df is not None:
                    table_name = sanitize_table_name(f"ds_{d.id}_{d.name}")
                    sql_df = df.copy()
                    sql_df.columns = [str(c).strip().replace(" ", "_").replace("-", "_") for c in sql_df.columns]
                    sql_df.to_sql(table_name, con=engine, if_exists="replace", index=False)
                    d.storage_table_name = table_name
                    print(f"  + Indexed existing dataset '{d.name}' into SQL table '{table_name}'")

        db.commit()

        if len(existing_datasets) > 0:
            print(f"[SEED] Datasets verified and indexed ({len(existing_datasets)} datasets active).")
            return

        print("[SEED] Starting automated enterprise dataset population...")

        if not os.path.exists(samples_dir):
            print(f"[SEED] Samples dir '{samples_dir}' not found.")
            return

        # Ensure a default data source
        ds = db.query(DataSource).first()
        if not ds:
            ds = DataSource(name="Enterprise Local Storage", source_type="csv", status="active")
            db.add(ds)
            db.flush()

        target_samples = [
            ("Enterprise Sales Transactions", "enterprise_sales_transactions.csv"),
            ("Supermarket Retail Transactions", "supermarket_sales_real.csv"),
            ("Global GDP Macroeconomic Indicators", "global_gdp_real.csv"),
            ("Commodities WTI Crude Daily", "wti_crude_oil_daily_prices.csv"),
            ("Global Passenger Manifest Census", "titanic_real_passengers.csv")
        ]

        for display_name, filename in target_samples:
            source_path = os.path.join(samples_dir, filename)
            if not os.path.exists(source_path):
                continue

            dest_path = os.path.join(settings.UPLOAD_DIR, f"seeded_{filename}")
            shutil.copy2(source_path, dest_path)

            file_bytes = open(dest_path, "rb").read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

            df = pd.read_csv(dest_path)
            table_name = sanitize_table_name(f"ds_{filename.replace('.csv', '')}")
            sql_df = df.copy()
            sql_df.columns = [str(c).strip().replace(" ", "_").replace("-", "_") for c in sql_df.columns]
            sql_df.to_sql(table_name, con=engine, if_exists="replace", index=False)

            schema_info = [{"name": col, "type": str(dtype)} for col, dtype in zip(df.columns, df.dtypes)]

            dataset = Dataset(
                name=display_name,
                description=f"Automated enterprise seed dataset from {filename}",
                source_type="csv",
                raw_file_path=dest_path,
                processed_file_path=dest_path,
                storage_table_name=table_name,
                file_hash=file_hash,
                row_count=len(df),
                column_count=len(df.columns),
                schema_metadata={"columns": schema_info},
                owner_id=1,
                data_source_id=ds.id
            )
            db.add(dataset)
            db.flush()

            audit = AuditLog(
                user_id=1,
                username="admin",
                action="DATASET_SEEDED",
                resource_type="dataset",
                resource_id=str(dataset.id),
                details={"filename": filename, "rows": len(df), "columns": len(df.columns), "table_name": table_name},
                ip_address="127.0.0.1",
                prev_hash="0" * 64,
                record_hash=file_hash
            )
            db.add(audit)
            print(f"  + Seeded: {display_name} ({len(df)} rows, {len(df.columns)} columns) -> Table: {table_name}")

        db.commit()
        print("[SEED] Successfully populated 5 production datasets into PostgreSQL!")
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_enterprise_data()
