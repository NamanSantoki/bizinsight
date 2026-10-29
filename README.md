# BIZINSIGHT Enterprise Platform 2.0
## Mini Enterprise Data, MLOps & Decision Intelligence Platform

BIZINSIGHT 2.0 is an enterprise-grade data and decision intelligence platform engineered across four foundational architectural planes: **Data Plane**, **Intelligence Plane**, **Governance Plane**, and **Experience Plane**. 

Designed to reflect production architectures found in modern data companies, BIZINSIGHT transitions business analytics from ad-hoc queries into a governed, auditable, and resilient platform featuring **multi-source ingestion connectors, formal data contracts with quarantine gates, 6-dimension data quality scoring, centralized semantic metrics stores, governed text-to-SQL with AST validation, MLOps model registry & drift monitoring, digital twin scenario planning, and attribute-based access control (ABAC)**.

---

## 1. Enterprise 4-Plane Architecture

```
                         BIZINSIGHT ENTERPRISE PLATFORM
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXPERIENCE PLANE                              │
│                                                                         │
│ Dashboard │ Data Catalog │ Governed NLQ │ Lineage │ Scenarios │ Health  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                         API Gateway / BFF
                                │
              ┌─────────────────┴──────────────────┐
              │                                    │
       Identity & Access                     Job Orchestrator
       OIDC / JWT Bearer                     Async Workers
       RBAC + ABAC Policies                  Queue / Scheduler
              │                                    │
              └─────────────────┬──────────────────┘
                                │
                    ENTERPRISE DATA PLATFORM
                                │
       ┌────────────────────────┼────────────────────────┐
       │                        │                        │
   Data Sources            Data Contracts           Data Lineage
   Multi-Connectors        Schema & Rules           End-to-End DAG
   CDC / Batch Sync        Quarantine Routing       Lakehouse Trace
       │                        │                        │
       └────────────────────────┼────────────────────────┘
                                │
                         Lakehouse Layer
                  Bronze (Raw) → Silver (Clean) → Gold (Curated)
                                │
                    Semantic / Metrics Store
                                │
             ┌──────────────────┼───────────────────┐
             │                  │                   │
      Analytics Plane       MLOps Plane         GenAI / NLQ
             │                  │                   │
       KPI & Variance     Model Registry v1..v7   AST Validation
       Segmentation       Population Drift (PSI)  Semantic Layer
       Digital Twin       Retraining Pipeline     Zero Hallucination
       Causal Rigor       TreeSHAP Attribution    Evidence Citations
             │                  │                   │
             └──────────────────┼───────────────────┘
                                │
                    GOVERNANCE + OBSERVABILITY
                                │
        Cryptographic Audit │ Kubernetes Probes │ Telemetry
        Row/Column Masking │ 4-Tier PII Classification │ Cost Gov
```

---

## 2. Core Subsystem Breakdown

### 🗄️ A. Data Platform Layer
- **Multi-Source Connectors**: Direct connectors for PostgreSQL, MySQL, SQLite, REST APIs, CSV, Parquet, and S3 Object Stores with credential masking, connection health pings, and on-demand synchronizations.
- **Governed Data Contracts**: Strict declarative schemas defining required fields, data types, uniqueness constraints, numerical bounds, and enum domains.
- **Automated Quarantine Gate**: Datasets failing schema checks or containing duplicate/out-of-bounds records are automatically quarantined for investigation rather than corrupting curated lakehouse tables.
- **6-Dimension Quality Framework**: Evaluates datasets across Completeness, Validity, Uniqueness, Consistency, Freshness, and Distribution Stability. Enforces an automated gate ($\text{Score} \ge 95.0\%$) to promote records to the Gold Lakehouse layer.
- **Interactive Data Lineage DAG**: End-to-end directed acyclic graph mapping data transformation dependencies:
  $$\text{Source DB} \longrightarrow \text{Bronze (Raw)} \longrightarrow \text{Silver (Clean)} \longrightarrow \text{Gold (Curated)} \longrightarrow \text{KPIs / ML Models / Dashboards}$$

### 🧠 B. Semantic Layer & Centralized Metrics Store
- **Single Source of Truth**: Eliminates conflicting SQL calculations across teams by defining metrics centrally:
  - $\text{Net Revenue} = \sum(\text{completed\_orders.amount})$
  - $\text{AOV} = \text{Revenue} / \text{Order Count}$
  - $\text{Gross Margin} = (\text{Revenue} - \text{COGS}) / \text{Revenue}$
  - $\text{Retention Rate} = \text{Returning Customers} / \text{Base Customers}_{t-1}$
  - $\text{Churn Rate} = \text{Lost Accounts} / \text{Active Accounts}_t$
- **Governed Query Compiler**: Automatically compiles certified SQL queries sliced across verified dimensions (Region, Segment, Product Category) with a strict zero-metric-hallucination guarantee.

### 🤖 C. Governed AI Analyst & NLQ Engine
- **Governed Text-to-SQL Pipeline**:
  $$\text{User Prompt} \longrightarrow \text{Intent Detection} \longrightarrow \text{Semantic Lookup} \longrightarrow \text{SQL Generation} \longrightarrow \text{AST Security Check} \longrightarrow \text{Read-Only Exec} \longrightarrow \text{Evidence Citation}$$
- **SQL AST Validation**: Enforces read-only `SELECT` queries, rejects multi-statement execution, blocks mutation keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`), and appends row limits.
- **Evidence-Backed Attribution**: Every answer is assigned a traceable Query ID (e.g., `QRY-8F291A`), lists primary contributors, states model confidence, and cites exact underlying curated datasets.

### 🔮 D. Decision Intelligence & Econometric Causal Inference
- **Digital Twin Scenario Simulator**: Simulates multi-variable macroeconomic interventions (Marketing Spend, Pricing, Sales Capacity) through empirical elasticity equations, generating projected revenue, operating margins, and expected customer counts with **80% prediction intervals** (accounting for residual standard error).
- **Prescriptive Goal-Seek Optimizer**: Solves inverse constrained optimization problems (e.g. *Achieve ₹25 Cr revenue while maintaining $\ge 20\%$ margin and $\le ₹4$ Cr marketing budget*) to recommend optimal tactical lever allocations.
- **Econometric Causal Engine**: Evaluates treatment effects using Inverse Probability Weighting (IPW) and Double Machine Learning (DML). Features Standardized Mean Difference (SMD) covariate balance checks, placebo refutation sensitivity tests, and explicit verification of identification assumptions:
  1. *Conditional Exchangeability* (Unconfoundedness)
  2. *Positivity* (Common Support)
  3. *Consistency & SUTVA*
  - **Epistemic Disclaimer**: Explicitly enforces that **Association $\ne$ Causation**.

### ⚙️ E. MLOps Model Registry & Drift Observability
- **Governed Model Registry**: Tracks model artifacts, hyperparameters, evaluation metrics (MAE, RMSE, Accuracy), and training dataset lineage across semantic versions ($v_1 \dots v_7$).
- **Lifecycle State Machine**: Enforces formal stage progression:
  $$\text{TRAINED} \longrightarrow \text{EVALUATION} \longrightarrow \text{VALIDATION} \longrightarrow \text{PENDING\_APPROVAL} \longrightarrow \text{APPROVED} \longrightarrow \text{STAGING} \longrightarrow \text{PRODUCTION}$$
- **Population Stability & Drift Telemetry**: Continuously tracks prediction volume, P95 inference latency, error rates, data drift, and feature drift, triggering automated retraining recommendations when feature drift exceeds nominal thresholds.

### 🔐 F. Enterprise Identity, ABAC & Governance
- **Attribute-Based Access Control (ABAC)**: Evaluates dynamic multi-attribute authorization matrices across Role (`admin`, `analyst`, `viewer`), Department (`Finance`, `Marketing`, `Engineering`, `Executive`), Region (`Global`, `Europe`, `NorthAmerica`, `APAC`), and Resource Sensitivity.
- **Row-Level & Column-Level Dynamic Masking**: Automatically filters rows according to the user's regional clearance and dynamically masks personal identifying information (`n***@enterprise.com`, `***-***-1234`).
- **4-Tier Data Classification**: Deep column scanner classifying data into:
  - 🔴 **Highly Sensitive** (SSN, Passport, Payment Cards)
  - 🟠 **Confidential** (Customer Email, Phone, Revenue, Margins)
  - 🟡 **Internal** (Order IDs, Statuses, Department Codes)
  - 🟢 **Public** (Country, Currency, Aggregate Dates)
- **Two-Person Dual Approvals**: Sensitive operations (production model promotions, high-risk PII data exports) require independent reviewer verification before execution.
- **Cryptographically Auditable Architecture**: Every administrative, ingest, and export action is logged with SHA-256 block chaining to provide tamper evidence and detect inconsistency with the expected chain (designed to support SOC 2-oriented security and audit controls).

### 📡 G. Observability & Operations Center
- **Kubernetes Health Probes**: Cloud-native endpoints (`/health/live`, `/health/ready`, `/health/database`, `/health/ml`, `/health/queue`) for orchestration liveness and readiness monitoring.
- **Operations Center**: Subsystem uptime monitoring and incident response tracking (impact analysis, root-cause diagnostics, and remediation logging).
- **Cloud Cost Observability**: Granular financial attribution tracking compute, SQL queries, ML inference, and curated storage across tenants and business units.

---

## 3. Quick Start & Execution

### Option A: Local Execution
1. **Backend**:
   ```bash
   pip install -r backend/requirements.txt
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```
2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev -- --host 127.0.0.1 --port 5173
   ```
   Open `http://localhost:5173` in your browser.

### Option B: Docker Compose
```bash
docker-compose up --build
```

---

## 4. Test Suite Execution

Run the complete 39-test enterprise test suite:
```bash
python -m pytest backend/tests -v
```

### Verified Test Categories:
- **Enterprise Data Platform**: Data source connectors, health pings, sync runs, contract validation rules, quarantine logic, 6-dimension quality gates, and lineage DAG graph traversals.
- **Semantic Layer**: Central metrics resolution, dimensional slicing, and SQL compilation with zero-hallucination validation.
- **Governance & Security**: ABAC policy evaluation, dynamic row filtering, column PII masking, 4-tier automated data classification, dual-person approvals, and expirable export tokens.
- **MLOps Platform**: Model registry version transitions ($v_1 \dots v_7$), population stability index drift detection, and automated retraining flags.
- **Decision Intelligence**: Digital twin scenario simulations with 80% prediction intervals, convex prescriptive goal-seek optimization, and econometric causal refutation tests.
- **Observability**: Standard Kubernetes probes (`/health/live`, `/health/ready`, `/health/database`, `/health/ml`), telemetry percentiles, cost attribution, and incident triage.
- **Core Security & Integrity**: Salted PBKDF2 hashing, zero-trust JWT authentication, SQL injection guards, system table overwrite protection, and SHA-256 cryptographic audit chain tamper detection.
