import os
import shutil
import hashlib
import pandas as pd
from backend.app.core.database import SessionLocal
from backend.app.models.all_models import Dataset, AuditLog, DataSource
from backend.app.core.config import settings

def seed_enterprise_data():
    db = SessionLocal()
    try:
        existing_count = db.query(Dataset).count()
        if existing_count > 0:
            print(f"[SEED] Datasets already populated ({existing_count} datasets found). Skipping.")
            return

        print("[SEED] Starting automated enterprise dataset population...")

        samples_dir = settings.SAMPLES_DIR
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

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

        for display_name, filename in target_samples:
            source_path = os.path.join(samples_dir, filename)
            if not os.path.exists(source_path):
                continue

            dest_path = os.path.join(settings.UPLOAD_DIR, f"seeded_{filename}")
            shutil.copy2(source_path, dest_path)

            file_bytes = open(dest_path, "rb").read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

            df = pd.read_csv(dest_path)
            schema_info = [{"name": col, "type": str(dtype)} for col, dtype in zip(df.columns, df.dtypes)]

            dataset = Dataset(
                name=display_name,
                description=f"Automated enterprise seed dataset from {filename}",
                source_type="csv",
                raw_file_path=dest_path,
                processed_file_path=dest_path,
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
                details={"filename": filename, "rows": len(df), "columns": len(df.columns)},
                ip_address="127.0.0.1",
                prev_hash="0" * 64,
                record_hash=file_hash
            )
            db.add(audit)
            print(f"  + Seeded: {display_name} ({len(df)} rows, {len(df.columns)} columns)")

        db.commit()
        print("[SEED] Successfully populated 5 production datasets into PostgreSQL!")
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_enterprise_data()
