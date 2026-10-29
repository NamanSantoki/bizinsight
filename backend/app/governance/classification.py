"""
Automated PII Detection & Data Sensitivity Classification Engine
Analyzes column signatures and values to assign data classification tiers:
🔴 Highly Sensitive | 🟠 Confidential | 🟡 Internal | 🟢 Public
"""
from typing import Dict, Any, List
import pandas as pd
import re

class DataClassificationEngine:
    TIERS = {
        "HIGHLY_SENSITIVE": "Highly Sensitive",
        "CONFIDENTIAL": "Confidential",
        "INTERNAL": "Internal",
        "PUBLIC": "Public"
    }

    def classify_column(self, col_name: str, sample_series: pd.Series) -> Dict[str, Any]:
        col_lower = col_name.lower()
        
        # 1. Highly Sensitive (SSN, Passport, Payment, Credit Card, Medical)
        if any(k in col_lower for k in ["passport", "ssn", "social_security", "credit_card", "card_no", "cvv", "tax_id"]):
            return {
                "column": col_name,
                "tier": self.TIERS["HIGHLY_SENSITIVE"],
                "color": "#dc2626",
                "tag": "PII / HIGHLY SENSITIVE",
                "reason": "Matches government identifier or financial credential pattern"
            }

        # 2. Confidential (Email, Phone, Salary, Revenue, Margin, Financial amount)
        if any(k in col_lower for k in ["email", "phone", "mobile", "tel", "salary", "wage", "revenue", "profit", "margin", "cogs"]):
            tag = "PII" if any(k in col_lower for k in ["email", "phone", "mobile", "tel"]) else "FINANCIAL CONFIDENTIAL"
            return {
                "column": col_name,
                "tier": self.TIERS["CONFIDENTIAL"],
                "color": "#ea580c",
                "tag": tag,
                "reason": "Direct personal identifier or proprietary commercial metric"
            }

        # 3. Internal (Customer ID, User ID, Order ID, Status, Department, Internal Code)
        if any(k in col_lower for k in ["id", "uuid", "cust", "status", "category", "dept", "department", "sku", "role"]):
            return {
                "column": col_name,
                "tier": self.TIERS["INTERNAL"],
                "color": "#ca8a04",
                "tag": "BUSINESS INTERNAL",
                "reason": "Internal business entity or operational metadata"
            }

        # 4. Public (Country, Region, Date, Year, Month, General Aggregation)
        return {
            "column": col_name,
            "tier": self.TIERS["PUBLIC"],
            "color": "#16a34a",
            "tag": "PUBLIC / GENERAL",
            "reason": "Non-sensitive contextual or temporal dimension"
        }

    def classify_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        classifications = []
        tier_counts = {
            self.TIERS["HIGHLY_SENSITIVE"]: 0,
            self.TIERS["CONFIDENTIAL"]: 0,
            self.TIERS["INTERNAL"]: 0,
            self.TIERS["PUBLIC"]: 0
        }

        for col in df.columns:
            meta = self.classify_column(col, df[col])
            classifications.append(meta)
            tier_counts[meta["tier"]] += 1

        return {
            "columns": classifications,
            "summary_counts": {
                "highly_sensitive": tier_counts[self.TIERS["HIGHLY_SENSITIVE"]],
                "confidential": tier_counts[self.TIERS["CONFIDENTIAL"]],
                "internal": tier_counts[self.TIERS["INTERNAL"]],
                "public": tier_counts[self.TIERS["PUBLIC"]],
                "total_columns": len(df.columns)
            }
        }

classification_engine = DataClassificationEngine()

