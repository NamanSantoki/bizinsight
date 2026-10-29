"""
Row-Level & Column-Level Dynamic Masking Security Engine
Enforces row isolation by user region/department and column-level dynamic masking of PII attributes.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import re

class DynamicDataMaskingEngine:
    @staticmethod
    def mask_email(email: str) -> str:
        if not isinstance(email, str) or "@" not in email:
            return email
        local, domain = email.split("@", 1)
        if len(local) <= 1:
            masked_local = "*"
        else:
            masked_local = f"{local[0]}***"
        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        if not isinstance(phone, str):
            return str(phone)
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 4:
            return f"***-***-{digits[-4:]}"
        return "***-***-****"

    @staticmethod
    def mask_ssn(val: str) -> str:
        return "***-**-****"

    @staticmethod
    def mask_numeric(val: Any) -> str:
        return "*****"

    def apply_security_policies(
        self,
        df: pd.DataFrame,
        user_role: str,
        user_region: str = "Global",
        user_department: str = "General",
        mask_pii: bool = True
    ) -> pd.DataFrame:
        """
        Applies Row-Level Security (RLS) and Column-Level Security (CLS) to a DataFrame.
        """
        filtered_df = df.copy()

        # 1. Row-Level Security (RLS)
        # If user is not admin and has a regional assignment, filter region or country
        if user_role.lower() != "admin" and user_region != "Global":
            region_cols = [c for c in filtered_df.columns if c.lower() in ["region", "country", "market", "territory"]]
            if region_cols:
                col = region_cols[0]
                # Filter matching user region (case-insensitive substring)
                mask = filtered_df[col].astype(str).str.lower().str.contains(user_region.lower())
                if mask.any():
                    filtered_df = filtered_df[mask]

        # 2. Column-Level Security (CLS) & Dynamic Masking
        # Mask PII columns unless user is admin
        if user_role.lower() != "admin" and mask_pii:
            for col in filtered_df.columns:
                col_lower = col.lower()
                if "email" in col_lower:
                    filtered_df[col] = filtered_df[col].astype(str).apply(self.mask_email)
                elif any(k in col_lower for k in ["phone", "mobile", "tel"]):
                    filtered_df[col] = filtered_df[col].astype(str).apply(self.mask_phone)
                elif any(k in col_lower for k in ["ssn", "passport", "tax_id"]):
                    filtered_df[col] = filtered_df[col].astype(str).apply(self.mask_ssn)

        return filtered_df

masking_engine = DynamicDataMaskingEngine()

