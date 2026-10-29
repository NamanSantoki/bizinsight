import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.all_models import CompanyProfile, User
from backend.app.schemas.company_schemas import (
    CompanyProfileCreate, CompanyProfileResponse, TaxonomyResponse, IndustryTaxonomyItem
)
from backend.app.security.auth import get_current_active_user
from backend.app.audit.service import log_audit_event

logger = logging.getLogger("bizinsight.company")
router = APIRouter(prefix="/company", tags=["Company Profile & DNA"])

# Standard enterprise taxonomies
TAXONOMIES = TaxonomyResponse(
    sectors=[
        IndustryTaxonomyItem(id="retail_ecommerce", label="Retail & E-Commerce", description="Omnichannel retail, consumer goods, apparel, marketplaces"),
        IndustryTaxonomyItem(id="energy_commodities", label="Energy & Commodities", description="Oil & gas exploration, refining, power utilities, renewables"),
        IndustryTaxonomyItem(id="manufacturing_logistics", label="Manufacturing & Supply Chain", description="Automotive, aerospace, industrial hardware, freight shipping"),
        IndustryTaxonomyItem(id="saas_tech", label="Enterprise Software / SaaS", description="B2B software, cloud services, developer platforms, cybersecurity"),
        IndustryTaxonomyItem(id="financial_services", label="Financial Services & Banking", description="Commercial banking, wealth management, payments, insurance"),
        IndustryTaxonomyItem(id="healthcare_pharma", label="Healthcare & Pharmaceuticals", description="Medical devices, clinical diagnostics, therapeutics, health systems")
    ],
    business_models=[
        "B2B Enterprise Contracts",
        "B2C High-Volume Transactions",
        "D2C Omnichannel Retail",
        "Two-Sided Marketplace",
        "Subscription / ARR Recurring"
    ],
    macro_sensitivities=[
        IndustryTaxonomyItem(id="crude_oil", label="Crude Oil & Energy Tariffs", description="Direct fuel costs, petrochemical inputs, plastic packaging"),
        IndustryTaxonomyItem(id="freight_rates", label="Maritime & Air Cargo Rates", description="Container shipping rates (SCFI/FBX), port dwell times"),
        IndustryTaxonomyItem(id="interest_rates", label="Central Bank Interest Rates", description="Cost of working capital, customer debt financing, mortgage demand"),
        IndustryTaxonomyItem(id="inflation_cpi", label="Consumer Price Index (CPI)", description="Consumer purchasing power, wage growth, supplier margin compression"),
        IndustryTaxonomyItem(id="fx_volatility", label="Foreign Exchange Volatility (USD/EUR/JPY)", description="Cross-border revenue conversion, overseas procurement hedging"),
        IndustryTaxonomyItem(id="semiconductor_supply", label="Semiconductor & Electronic Components", description="Lead times for microcontrollers, sensors, industrial computing")
    ],
    standard_kpis=[
        IndustryTaxonomyItem(id="gross_margin", label="Gross Profit Margin (%)", description="Revenue minus direct cost of goods sold"),
        IndustryTaxonomyItem(id="inventory_turnover", label="Inventory Turnover Ratio", description="Speed of working capital conversion into sales"),
        IndustryTaxonomyItem(id="customer_churn", label="Annualized Customer Churn (%)", description="Rate of customer contract terminations"),
        IndustryTaxonomyItem(id="operating_cash_flow", label="Operating Cash Flow", description="Cash generated directly from regular business operations"),
        IndustryTaxonomyItem(id="logistics_unit_cost", label="Logistics Cost per Unit Shipped", description="Fulfillment, warehousing, and transportation burn")
    ],
    supported_currencies=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "SGD", "INR"],
    geographic_regions=["North America", "European Union", "United Kingdom", "Asia-Pacific", "Latin America", "Middle East & Africa"]
)

@router.get("/profile/taxonomies", response_model=TaxonomyResponse, summary="Get enterprise industry taxonomies")
def get_taxonomies():
    """Returns standardized enterprise options for company DNA setup."""
    return TAXONOMIES

@router.get("/profile", response_model=Optional[CompanyProfileResponse], summary="Get enterprise company DNA")
def get_company_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve the active enterprise company profile and macroeconomic risk DNA."""
    profile = db.query(CompanyProfile).first()
    return profile

@router.post("/profile", response_model=CompanyProfileResponse, summary="Upsert enterprise company DNA profile")
def upsert_company_profile(
    payload: CompanyProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create or update the organization's company profile.
    Automatically signs a tamper-proof SHA-256 block in the cryptographic audit ledger.
    """
    profile = db.query(CompanyProfile).first()
    action = "company_profile_update" if profile else "company_profile_create"

    if profile:
        profile.organization_name = payload.organization_name
        profile.industry_sector = payload.industry_sector
        profile.business_model = payload.business_model
        profile.annual_revenue_bracket = payload.annual_revenue_bracket
        profile.operating_currencies = payload.operating_currencies
        profile.geographic_regions = payload.geographic_regions
        profile.key_macro_sensitivities = payload.key_macro_sensitivities
        profile.key_competitors = payload.key_competitors
        profile.monitored_kpis = payload.monitored_kpis
        profile.risk_tolerance = payload.risk_tolerance
    else:
        profile = CompanyProfile(
            organization_name=payload.organization_name,
            industry_sector=payload.industry_sector,
            business_model=payload.business_model,
            annual_revenue_bracket=payload.annual_revenue_bracket,
            operating_currencies=payload.operating_currencies,
            geographic_regions=payload.geographic_regions,
            key_macro_sensitivities=payload.key_macro_sensitivities,
            key_competitors=payload.key_competitors,
            monitored_kpis=payload.monitored_kpis,
            risk_tolerance=payload.risk_tolerance
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)

    # Cryptographically seal this governance event
    log_audit_event(
        db=db,
        action=action,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="company_profile",
        resource_id=str(profile.id),
        details={
            "organization_name": profile.organization_name,
            "industry_sector": profile.industry_sector,
            "macro_sensitivities": profile.key_macro_sensitivities,
            "risk_tolerance": profile.risk_tolerance
        }
    )

    return profile

