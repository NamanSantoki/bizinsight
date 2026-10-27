# BIZINSIGHT
## Production-Grade Business Intelligence, Predictive Analytics & Natural-Language Platform

BIZINSIGHT is an end-to-end business analytics, ML evaluation, and natural-language data querying system engineered with strict data integrity, zero fabricated metrics, chronological validation, and robust SQL injection defenses.

---

## 1. System Architecture

```
BIZINSIGHT Architecture:
┌───────────────────────────┐      HTTP REST      ┌─────────────────────────────────┐
│     React 19 + TS +       │ ◄─────────────────► │        FastAPI Backend          │
│   Tailwind CSS Dashboard  │                     │   (Pydantic, SQLAlchemy 2.0)    │
└───────────────────────────┘                     └────────────────┬────────────────┘
                                                                   │
                                           ┌───────────────────────┴───────────────────────┐
                                           ▼                                               ▼
                         ┌───────────────────────────────────┐           ┌───────────────────────────────────┐
                         │      Analytics & ML Engines       │           │        PostgreSQL / SQLite        │
                         │ - Chronological Forecasting       │           │ - Dynamic Sanitized Tables        │
                         │ - Isolation Forest Anomalies      │           │ - Read-Only Safe SQL Validator    │
                         │ - K-Means RFM Segmentation        │           │ - Audit Trail & Model Run Store   │
                         │ - Profiling & Quality Scoring     │           └───────────────────────────────────┘
                         └───────────────────────────────────┘
```

---

## 2. Core Modules & Engineering Principles

### A. Data Ingestion & Profiling
- Multi-format ingestion supporting CSV, TXT, Excel (`.xlsx`, `.xls`).
- Automatic encoding detection (`chardet`) and delimiter sniffing (`,`, `;`, `\t`, `|`).
- Never mutates raw ingested files; strict separation of `raw` and `processed` layers.
- Full statistical profiling: IQR outlier counts, percentiles, null ratios, cardinality, and memory footprints.

### B. Transparent Data Quality Engine
- Documented quality formula:
  $$\text{Quality Score} = 100.0 - (\text{Null Penalty} + \text{Duplicate Penalty} + \text{Outlier Penalty} + \text{Domain Penalty})$$
- Detects prohibited negative pricing, 100% null columns, zero-variance columns, and date inconsistencies.
- Auditable cleaning operations (duplicate removal, snake_casing, median/mode imputation, IQR clipping).

### C. Leakage-Free Chronological Forecasting
- **Zero Random Splitting**: Prevents future data leakage by strictly partitioning time series into past train sets (80%) and holdout test sets (20%).
- **Multi-Model Benchmark**: Evaluates Naive Last-Value Baseline, Moving Average, Linear Regression, Random Forest, and XGBoost against actual test metrics (MAE, RMSE, MAPE, R²).
- **Uncertainty Bounds**: Generates 95% confidence intervals ($\pm 1.96 \times \sigma_{\text{residuals}}$) that widen as forecast steps project further ahead.
- **Honest Limitations**: If historical observations are fewer than 20 periods, the system rejects the execution with an explicit explanation rather than inventing predictions.

### D. Multivariate Anomaly Detection
- Unsupervised Isolation Forest isolating anomalous combinations across numeric dimensions.
- Explains deviations objectively using dataset medians and IQR factors without falsely labeling records as fraud.

### E. Customer Segmentation
- Data-driven RFM (Recency, Frequency, Monetary) clustering with K-Means.
- Log-transformation and standard scaling to handle skewed transaction distributions.

### F. Ask Your Data (NLP to SQL) with Injection Defense
- Natural language to SQL translation grounded directly on indexed table schemas.
- Strict security validator blocking mutating commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, etc.).
- Enforces read-only `SELECT` queries with mandatory row limits.
- Generates answers strictly from executed database results; refuses to fabricate answers.

---

## 3. Quick Start & Execution

### Option A: Local Native Execution (Offline-Ready)
1. **Backend**:
   ```bash
   cd N:/PathtoGermany
   pip install -r backend/requirements.txt
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```
2. **Frontend**:
   ```bash
   cd N:/PathtoGermany/frontend
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

### Option B: Docker Compose
```bash
docker-compose up --build
```
Services spun up:
- `postgresql`: Port 5432
- `backend`: Port 8000
- `frontend`: Port 3000
- `ollama`: Port 11434

---

## 4. Automated Testing
Run the complete backend test suite:
```bash
pytest backend/tests/test_core_engines.py -v
```
All 11 unit & integration tests verify:
- Delimiter detection & ingestion
- Profiler accuracy
- Quality score formula
- Auditable cleaning
- KPI calculations
- Chronological forecasting validation
- Insufficient data guards
- Isolation Forest anomaly detection
- RFM K-Means clustering
- SQL security filter & mutation blocking
- Salted PBKDF2 password hashing
