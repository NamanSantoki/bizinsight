from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class CompanyProfileBase(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=255, description="Official enterprise organization name")
    industry_sector: str = Field(..., description="Primary industry sector from enterprise taxonomy")
    business_model: str = Field(..., description="Core business model (B2B, B2C, D2C, Marketplace, Enterprise)")
    annual_revenue_bracket: Optional[str] = Field(default="USD $10M - $50M", description="Estimated annual revenue tier")
    operating_currencies: List[str] = Field(default_factory=lambda: ["USD"], description="Currencies relevant to treasury and reporting")
    geographic_regions: List[str] = Field(default_factory=lambda: ["North America"], description="Operating and distribution geographies")
    key_macro_sensitivities: List[str] = Field(
        default_factory=lambda: ["crude_oil", "interest_rates", "freight_rates"],
        description="Macroeconomic external factors that materially impact COGS or revenue"
    )
    key_competitors: List[str] = Field(default_factory=list, description="Primary direct competitors in key markets")
    monitored_kpis: List[str] = Field(
        default_factory=lambda: ["gross_margin", "inventory_turnover", "customer_churn"],
        description="Critical business KPIs subject to external volatility"
    )
    risk_tolerance: str = Field(default="moderate", description="Corporate risk appetite: conservative, moderate, aggressive")

class CompanyProfileCreate(CompanyProfileBase):
    pass

class CompanyProfileUpdate(BaseModel):
    organization_name: Optional[str] = None
    industry_sector: Optional[str] = None
    business_model: Optional[str] = None
    annual_revenue_bracket: Optional[str] = None
    operating_currencies: Optional[List[str]] = None
    geographic_regions: Optional[List[str]] = None
    key_macro_sensitivities: Optional[List[str]] = None
    key_competitors: Optional[List[str]] = None
    monitored_kpis: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None

class CompanyProfileResponse(CompanyProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IndustryTaxonomyItem(BaseModel):
    id: str
    label: str
    description: str

class TaxonomyResponse(BaseModel):
    sectors: List[IndustryTaxonomyItem]
    business_models: List[str]
    macro_sensitivities: List[IndustryTaxonomyItem]
    standard_kpis: List[IndustryTaxonomyItem]
    supported_currencies: List[str]
    geographic_regions: List[str]
