"""
Capability and SubDomain enrichment catalog.
Provides description, business_outcomes, technical_requirements, risk_factors, kpis.

Pattern-matched by capability name keywords. Used by GraphEnricher before LLM fallback.
Sources: BIZBOK, OMG Business Architecture, TOGAF ADM, industry best practices.
"""

from dataclasses import dataclass, field


@dataclass
class CapabilityEnrichment:
    description: str
    business_outcomes: list = field(default_factory=list)
    technical_requirements: list = field(default_factory=list)
    implementation_complexity: str = "medium"   # low | medium | high | very_high
    risk_factors: list = field(default_factory=list)
    typical_duration_weeks: int = 16
    common_frameworks: list = field(default_factory=list)
    solution_patterns: list = field(default_factory=list)
    kpis: list = field(default_factory=list)
    industry_applicability: list = field(default_factory=list)


@dataclass
class SubDomainEnrichment:
    description: str
    functional_scope: str
    business_driver: str
    grouping_rationale: str


# ---------------------------------------------------------------------------
# SubDomain enrichments (by name pattern)
# ---------------------------------------------------------------------------

SUBDOMAIN_ENRICHMENTS: dict[str, SubDomainEnrichment] = {
    "intelligence governance": SubDomainEnrichment(
        description="Manages policies, ownership, and accountability structures for enterprise data and AI assets to ensure trusted decision-making.",
        functional_scope="Data ownership definition, data stewardship programmes, AI governance policies, data cataloguing and lineage tracking",
        business_driver="Regulatory compliance mandates (GDPR, DORA) and the need for trusted data as a foundation for AI adoption",
        grouping_rationale="Capabilities share a governance lifecycle: policy → ownership → enforcement → audit",
    ),
    "manage finance": SubDomainEnrichment(
        description="Encompasses financial management capabilities covering revenue management, investment relations, accounting, and financial reporting.",
        functional_scope="Revenue recognition, investment portfolio management, financial accounting, regulatory financial reporting",
        business_driver="Regulatory compliance (IFRS, Basel), shareholder accountability, and optimisation of financial performance",
        grouping_rationale="Capabilities share a financial data model and reporting lifecycle",
    ),
    "manage human resources": SubDomainEnrichment(
        description="Covers workforce management capabilities from talent acquisition through payroll, learning and development, and workforce analytics.",
        functional_scope="Talent acquisition, workforce planning, payroll processing, learning and development, performance management",
        business_driver="Talent shortage and skills gaps in digital transformation require modern HR capabilities and workforce analytics",
        grouping_rationale="Capabilities share employee lifecycle data and HR system integration",
    ),
    "manage legal": SubDomainEnrichment(
        description="Manages intellectual property, contracts, regulatory compliance, and litigation risk across the organisation.",
        functional_scope="IP portfolio management, contract lifecycle management, regulatory compliance tracking, litigation management",
        business_driver="Increasing regulatory complexity and IP value in digital businesses require systematic legal capability",
        grouping_rationale="Capabilities share legal entity data and contract/compliance lifecycle",
    ),
    "manage property, facility and workspace": SubDomainEnrichment(
        description="Manages physical and digital workspace assets including property portfolio, facility operations, and flexible work environments.",
        functional_scope="Property portfolio management, facility maintenance, workspace allocation, smart building management",
        business_driver="Hybrid work models and sustainability goals are driving transformation of workspace management",
        grouping_rationale="Capabilities share asset register and facilities management data",
    ),
}


# ---------------------------------------------------------------------------
# Capability enrichments (by name pattern keywords)
# ---------------------------------------------------------------------------

CAPABILITY_ENRICHMENTS: dict[str, CapabilityEnrichment] = {

    "data ownership": CapabilityEnrichment(
        description="Establishes clear accountability for data assets by assigning data owners responsible for quality, access governance, and lifecycle management of specific data domains.",
        business_outcomes=[
            "Clear accountability reduces data quality incidents by 40%",
            "Faster regulatory data requests through known ownership",
            "Improved AI model accuracy from governed training data",
        ],
        technical_requirements=[
            "Data catalogue platform with ownership assignment (Collibra, Atlan, or Alation)",
            "Integration with Active Directory for stewardship role provisioning",
            "Automated data quality monitoring with ownership alerting",
        ],
        implementation_complexity="medium",
        risk_factors=[
            "Organisational resistance to data ownership accountability",
            "Shadow data stores not captured in catalogue",
        ],
        typical_duration_weeks=16,
        common_frameworks=["DAMA-DMBOK2", "TOGAF 10", "COBIT 2019"],
        solution_patterns=["Data Mesh domain ownership", "Federated data governance"],
        kpis=["100% of critical data domains have assigned data owners", "Data quality score > 95% on owned domains"],
        industry_applicability=["All sectors"],
    ),

    "data governance": CapabilityEnrichment(
        description="Implements the organisational framework, policies, processes, and standards to ensure enterprise data is managed as a strategic asset throughout its lifecycle.",
        business_outcomes=[
            "Regulatory compliance with GDPR, DORA, HIPAA data requirements",
            "Trusted data enabling AI/ML model deployment",
            "Reduced risk of data breaches through access governance",
        ],
        technical_requirements=[
            "Enterprise data governance platform (Collibra, Microsoft Purview)",
            "Data lineage tooling integrated with ETL/ELT pipelines",
            "Policy engine for automated data access control",
        ],
        implementation_complexity="high",
        risk_factors=[
            "Cultural resistance — governance seen as bureaucratic overhead",
            "Complex legacy system integration for lineage tracking",
        ],
        typical_duration_weeks=32,
        common_frameworks=["DAMA-DMBOK2", "TOGAF 10", "ISO 8000"],
        solution_patterns=["Data Governance Operating Model", "Federated Governance"],
        kpis=["Data governance maturity score ≥ 3/5", "100% of regulated data has documented lineage"],
        industry_applicability=["Financial Services", "Healthcare", "Government"],
    ),

    "manage revenue": CapabilityEnrichment(
        description="Manages the end-to-end revenue lifecycle from revenue recognition, billing accuracy, and collections through to revenue forecasting and optimisation.",
        business_outcomes=[
            "Reduction in revenue leakage through automated billing controls",
            "Improved revenue forecast accuracy to ±5%",
            "Faster revenue recognition cycle reducing DSO",
        ],
        technical_requirements=[
            "Revenue management platform (Salesforce Revenue Cloud, SAP BRIM)",
            "Integration with CRM, ERP, and billing systems",
            "Automated revenue recognition engine (ASC 606/IFRS 15 compliant)",
        ],
        implementation_complexity="high",
        risk_factors=[
            "Complex multi-element arrangement accounting (IFRS 15/ASC 606)",
            "Legacy billing system integration complexity",
        ],
        typical_duration_weeks=24,
        common_frameworks=["IFRS 15", "ASC 606", "TOGAF 10"],
        solution_patterns=["Quote-to-Cash automation", "Revenue Operations (RevOps)"],
        kpis=["Revenue leakage < 0.5% of total revenue", "Billing accuracy > 99.5%", "DSO reduction ≥ 10%"],
        industry_applicability=["All sectors"],
    ),

    "manage investment relations": CapabilityEnrichment(
        description="Manages relationships and communications with investors, analysts, and the capital markets community, ensuring timely, accurate, and compliant financial disclosures.",
        business_outcomes=[
            "Improved investor confidence through transparent reporting",
            "Lower cost of capital through strong IR programme",
            "Regulatory compliance with disclosure obligations",
        ],
        technical_requirements=[
            "Investor Relations management platform (Q4, Irwin)",
            "Regulatory filing system (EDGAR, SEDAR integration)",
            "Stakeholder engagement analytics and sentiment monitoring",
        ],
        implementation_complexity="medium",
        risk_factors=[
            "Selective disclosure risk under Regulation FD",
            "Inaccurate financial data in investor communications",
        ],
        typical_duration_weeks=12,
        common_frameworks=["IFRS", "SEC Regulation FD", "NIRI Best Practices"],
        solution_patterns=["Digital IR hub", "ESG reporting integration"],
        kpis=["Analyst coverage ≥ target", "ESG disclosure score ≥ industry benchmark"],
        industry_applicability=["Listed companies", "Financial Services"],
    ),

    "manage finance accounting": CapabilityEnrichment(
        description="Provides the core financial accounting function including general ledger management, period-end close, financial statement preparation, and audit support.",
        business_outcomes=[
            "Accurate and timely financial statements enabling investor trust",
            "Reduced period-end close cycle (target < 5 days)",
            "Audit-ready financial records reducing external audit cost",
        ],
        technical_requirements=[
            "ERP general ledger (SAP S/4HANA, Oracle Fusion Financials)",
            "Automated reconciliation platform (BlackLine, SAP FCC)",
            "XBRL reporting engine for regulatory filings",
        ],
        implementation_complexity="high",
        risk_factors=[
            "Complex multi-entity consolidation and intercompany eliminations",
            "Chart of accounts redesign for IFRS/US GAAP alignment",
        ],
        typical_duration_weeks=40,
        common_frameworks=["IFRS", "US GAAP", "COBIT 2019", "TOGAF 10"],
        solution_patterns=["Continuous close automation", "Account reconciliation automation"],
        kpis=["Period-end close < 5 business days", "Reconciliation coverage > 99%", "Zero material audit findings"],
        industry_applicability=["All sectors"],
    ),

    "manage workforce payroll": CapabilityEnrichment(
        description="Manages the accurate and compliant processing of employee payroll including gross-to-net calculation, statutory deductions, benefits administration, and payroll reporting.",
        business_outcomes=[
            "Zero payroll errors building employee trust",
            "Regulatory compliance across all payroll jurisdictions",
            "Reduced payroll processing cost through automation",
        ],
        technical_requirements=[
            "Payroll processing platform (ADP, Workday Payroll, SAP SuccessFactors EC Payroll)",
            "Tax engine with multi-jurisdiction support",
            "Integration with HR system for employee data synchronisation",
        ],
        implementation_complexity="high",
        risk_factors=[
            "Multi-country payroll complexity and regulatory variance",
            "HR-Payroll system integration data quality",
        ],
        typical_duration_weeks=32,
        common_frameworks=["ISO 30414", "IFRS", "Local payroll regulations"],
        solution_patterns=["Managed payroll service", "Cloud-native payroll platform"],
        kpis=["Payroll accuracy > 99.9%", "On-time payroll delivery 100%", "Payroll compliance score 100%"],
        industry_applicability=["All sectors"],
    ),

    "manage intellectual property": CapabilityEnrichment(
        description="Manages the organisation's intellectual property portfolio including patents, trademarks, copyrights, and trade secrets throughout their lifecycle.",
        business_outcomes=[
            "Maximised IP value through proactive portfolio management",
            "Reduced IP infringement risk through monitoring",
            "Competitive advantage protection through strategic patent filing",
        ],
        technical_requirements=[
            "IP management platform (Anaqua, CPA Global, Dennemeyer)",
            "Prior art search and patent analytics tools",
            "Trademark monitoring and watching services",
        ],
        implementation_complexity="medium",
        risk_factors=[
            "IP ownership ambiguity in collaborative R&D",
            "Open source licence compliance in proprietary software",
        ],
        typical_duration_weeks=20,
        common_frameworks=["WIPO IP Strategy Guide", "TOGAF 10"],
        solution_patterns=["IP portfolio analytics", "AI-assisted prior art search"],
        kpis=["IP portfolio ROI > 3:1", "Zero IP infringement incidents", "Patent grant rate > 60%"],
        industry_applicability=["Technology", "Pharma", "Manufacturing", "Media"],
    ),

    "manage property operation": CapabilityEnrichment(
        description="Manages the operational aspects of physical property assets including maintenance management, facilities services, space utilisation, and smart building operations.",
        business_outcomes=[
            "Reduced facility operational costs through predictive maintenance",
            "Improved space utilisation in hybrid work environment",
            "Energy cost reduction through smart building automation",
        ],
        technical_requirements=[
            "Integrated Workplace Management System (IWMS) (IBM TRIRIGA, Planon)",
            "IoT sensor network for occupancy and environmental monitoring",
            "Building Management System (BMS) integration",
        ],
        implementation_complexity="medium",
        risk_factors=[
            "IoT device security vulnerabilities in building systems",
            "Legacy BMS integration complexity",
        ],
        typical_duration_weeks=24,
        common_frameworks=["ISO 55000 (Asset Management)", "RICS Facilities Management"],
        solution_patterns=["Smart building automation", "Predictive maintenance IoT"],
        kpis=["Space utilisation > 80%", "Facility energy cost reduction ≥ 20%", "Planned maintenance % > 80%"],
        industry_applicability=["All sectors with significant property portfolios"],
    ),

    "manage trademark": CapabilityEnrichment(
        description="Manages the registration, maintenance, enforcement, and strategic development of the organisation's trademark portfolio across relevant jurisdictions.",
        business_outcomes=[
            "Brand protection across key markets",
            "Reduced trademark opposition and infringement incidents",
            "Maximised trademark portfolio value",
        ],
        technical_requirements=[
            "Trademark management platform with renewal alerts",
            "Online trademark monitoring and watching services",
            "Jurisdictional trademark search integration (TMview, EUIPO)",
        ],
        implementation_complexity="low",
        risk_factors=[
            "Lapsed trademark renewals due to poor portfolio visibility",
            "Domain name and social media handle conflicts",
        ],
        typical_duration_weeks=8,
        common_frameworks=["Madrid Protocol", "Nice Classification"],
        solution_patterns=["Centralised trademark portfolio management"],
        kpis=["100% trademark renewal on time", "Zero lapsed trademarks in core jurisdictions"],
        industry_applicability=["All sectors with brand assets"],
    ),

    "manage investor transactions": CapabilityEnrichment(
        description="Manages the end-to-end processing of investor transactions including share issuance, transfers, dividend payments, and shareholder register maintenance.",
        business_outcomes=[
            "Accurate and timely shareholder register maintenance",
            "Compliant dividend payment processing",
            "Efficient capital market transaction execution",
        ],
        technical_requirements=[
            "Transfer agent platform or share registry system",
            "Integration with stock exchange settlement systems (CREST, DTC)",
            "Shareholder communications platform",
        ],
        implementation_complexity="high",
        risk_factors=[
            "Settlement failure risk in capital market transactions",
            "Regulatory compliance with shareholder rights directives",
        ],
        typical_duration_weeks=24,
        common_frameworks=["IFRS", "Companies Act requirements", "SHAREHOLDER RIGHTS DIRECTIVE II"],
        solution_patterns=["Digital share registry", "Blockchain-based cap table management"],
        kpis=["Settlement failure rate < 0.01%", "Dividend payment accuracy 100%"],
        industry_applicability=["Listed companies", "Private equity", "Financial Services"],
    ),

    "architecture intelligence": CapabilityEnrichment(
        description="Provides the enterprise with AI-augmented capability to model, analyse, and optimise the digital and business architecture through knowledge graph intelligence and pattern recognition.",
        business_outcomes=[
            "60% reduction in architecture documentation effort",
            "Real-time architecture compliance checking",
            "Data-driven architecture roadmap prioritisation",
        ],
        technical_requirements=[
            "Enterprise architecture tool with knowledge graph (LeanIX, Ardoq)",
            "AI-powered architecture analysis engine",
            "Integration with CMDB and application portfolio management",
        ],
        implementation_complexity="very_high",
        risk_factors=[
            "Architecture data quality — CMDB accuracy",
            "Organisational adoption of architecture-as-code practices",
        ],
        typical_duration_weeks=40,
        common_frameworks=["TOGAF 10", "C4 Model", "Zachman Framework"],
        solution_patterns=["Architecture-as-Code", "AI-augmented EA", "Graph-RAG for EA"],
        kpis=["Architecture model coverage > 90% of critical applications", "Compliance score > 85%"],
        industry_applicability=["All sectors"],
    ),
}


def get_capability_enrichment(capability_name: str) -> CapabilityEnrichment | None:
    """Return enrichment data for a capability by name keyword matching."""
    name_lower = capability_name.lower()
    for pattern, enrichment in CAPABILITY_ENRICHMENTS.items():
        if pattern in name_lower:
            return enrichment
    return None


def get_subdomain_enrichment(subdomain_name: str) -> SubDomainEnrichment | None:
    """Return enrichment data for a subdomain by name keyword matching."""
    name_lower = subdomain_name.lower()
    for pattern, enrichment in SUBDOMAIN_ENRICHMENTS.items():
        if pattern in name_lower:
            return enrichment
    return None
