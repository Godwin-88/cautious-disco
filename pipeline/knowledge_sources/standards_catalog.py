"""
Curated authoritative standards catalog mapped to EA domain name patterns.
Each entry is deterministic (hand-authored from primary sources) — not LLM-generated.
The enrich_graph pipeline uses this as its primary source before LLM fallback.

Sources: TOGAF 10, COBIT 2019, ISO/IEC 42001, DAMA-DMBOK2, NIST AI RMF,
         ISO 27001:2022, NIST CSF 2.0, CIS Controls v8, ITIL 4, GDPR,
         Basel IV, DORA, PSD2, HL7 FHIR R4, HIPAA, ISO 22000, GS1,
         TMForum ODA, 3GPP, ISO 30414, SHRM, ISO 37001, GovStack
"""

from dataclasses import dataclass, field


@dataclass
class StandardData:
    name: str
    full_name: str
    publisher: str
    version: str
    year: int
    description: str
    key_principles: list = field(default_factory=list)
    compliance_requirements: list = field(default_factory=list)
    applicable_domains: list = field(default_factory=list)
    maturity_model: str = ""
    certification_body: str = ""
    source_url: str = ""
    industry_relevance: list = field(default_factory=list)
    tags: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Universal EA/DT Standards (applied to all domains)
# ---------------------------------------------------------------------------

TOGAF_10 = StandardData(
    name="TOGAF 10",
    full_name="The Open Group Architecture Framework, 10th Edition",
    publisher="The Open Group",
    version="10.0",
    year=2022,
    description=(
        "TOGAF 10 is the world's most widely used enterprise architecture framework, "
        "providing a comprehensive approach to designing, planning, implementing, and governing "
        "enterprise information architecture."
    ),
    key_principles=[
        "Architecture Vision must be defined before initiating transformation",
        "Architecture is governed by a dedicated Architecture Board",
        "All architecture work must align to a defined Architecture Principles set",
        "Reuse before buy before build — prioritise existing architecture assets",
        "Stakeholder concerns drive architecture decisions",
        "Architecture Repository maintains baseline, transition and target state",
    ],
    compliance_requirements=[
        "Establish an Architecture Board with defined governance charter",
        "Produce Architecture Vision document aligned to business strategy",
        "Maintain Architecture Repository with baseline and target state artifacts",
        "Define Architecture Principles and publish to all delivery teams",
        "Conduct Architecture Compliance Reviews for all significant projects",
        "Produce Architecture Roadmap covering transition states to target",
        "Document Architecture Decisions with rationale and tradeoff analysis",
    ],
    applicable_domains=["All"],
    maturity_model="CMMI Level 3 equivalent governance maturity",
    certification_body="The Open Group",
    source_url="https://www.opengroup.org/togaf",
    industry_relevance=["All sectors"],
    tags=["EA", "governance", "architecture", "framework", "transformation"],
)

COBIT_2019 = StandardData(
    name="COBIT 2019",
    full_name="Control Objectives for Information and Related Technologies, 2019",
    publisher="ISACA",
    version="2019",
    year=2019,
    description=(
        "COBIT 2019 is an IT governance framework providing a comprehensive set of "
        "governance and management objectives to help organisations meet their IT-related goals."
    ),
    key_principles=[
        "Provide stakeholder value through IT governance",
        "Holistic approach — governance system spans people, process and technology",
        "Dynamic governance — adapts to enterprise context and risk appetite",
        "Governance distinct from management",
        "Tailored to enterprise needs via design factors",
        "End-to-end governance system covering all technology functions",
    ],
    compliance_requirements=[
        "Define governance objectives aligned to enterprise goals",
        "Establish IT governance structures (board, committees, roles)",
        "Implement IT risk management and risk appetite framework",
        "Define and monitor IT performance metrics and KPIs",
        "Establish change management and configuration management processes",
        "Conduct regular IT compliance assessments against defined objectives",
        "Manage third-party and vendor governance for IT services",
    ],
    applicable_domains=["All"],
    maturity_model="CMMI-DEV Level 3 / ISO 33000 equivalent",
    certification_body="ISACA",
    source_url="https://www.isaca.org/resources/cobit",
    industry_relevance=["All sectors"],
    tags=["IT governance", "risk", "compliance", "controls", "management"],
)

ISO_42001 = StandardData(
    name="ISO/IEC 42001",
    full_name="ISO/IEC 42001:2023 — Artificial Intelligence Management System",
    publisher="ISO/IEC JTC 1/SC 42",
    version="2023",
    year=2023,
    description=(
        "ISO/IEC 42001 specifies requirements and provides guidance for establishing, "
        "implementing, maintaining and continually improving an AI management system within "
        "organisations deploying or providing AI-based products and services."
    ),
    key_principles=[
        "AI systems must be trustworthy, transparent and explainable",
        "Risk-based approach to AI deployment and operation",
        "Human oversight maintained for high-risk AI decisions",
        "Responsible AI development across the full lifecycle",
        "Continuous monitoring of AI system performance and bias",
        "Stakeholder engagement in AI governance",
    ],
    compliance_requirements=[
        "Establish AI governance policy and assign AI governance roles",
        "Conduct AI risk assessment for each AI application in scope",
        "Document AI system objectives, intended use and limitations",
        "Implement bias testing and fairness evaluation processes",
        "Maintain AI model registry with versioning and provenance",
        "Define human oversight checkpoints for automated AI decisions",
        "Conduct regular AI system audits and performance reviews",
        "Publish AI transparency documentation for external stakeholders",
    ],
    applicable_domains=["Digital Intelligence", "AI", "Data"],
    certification_body="ISO/IEC accredited bodies",
    source_url="https://www.iso.org/standard/81230.html",
    industry_relevance=["All sectors deploying AI"],
    tags=["AI", "governance", "management system", "trustworthy AI", "ISO"],
)

NIST_AI_RMF = StandardData(
    name="NIST AI RMF 1.0",
    full_name="NIST Artificial Intelligence Risk Management Framework 1.0",
    publisher="National Institute of Standards and Technology",
    version="1.0",
    year=2023,
    description=(
        "The NIST AI RMF provides guidance for organisations to manage risks to individuals, "
        "organisations, and society associated with artificial intelligence."
    ),
    key_principles=[
        "GOVERN — culture of risk management across the organisation",
        "MAP — AI risks identified, categorised and prioritised",
        "MEASURE — AI risks analysed and assessed with defined metrics",
        "MANAGE — AI risks prioritised and treated with defined responses",
        "Trustworthy AI requires: validity, reliability, safety, security, explainability, privacy, fairness",
    ],
    compliance_requirements=[
        "Establish AI risk governance structure and assign accountability",
        "Map AI systems to risk categories (high, medium, low)",
        "Define measurable AI risk metrics and tolerance thresholds",
        "Implement AI incident response and escalation procedures",
        "Document AI model cards for all production AI systems",
        "Test AI systems for bias, fairness and adversarial robustness",
        "Maintain AI risk register with treatment plans",
    ],
    applicable_domains=["Digital Intelligence", "AI", "Security"],
    certification_body="NIST",
    source_url="https://www.nist.gov/system/files/documents/2023/01/26/AI RMF 1.0.pdf",
    industry_relevance=["All sectors"],
    tags=["AI risk", "NIST", "governance", "trustworthy AI"],
)

# ---------------------------------------------------------------------------
# Data / Intelligence Standards
# ---------------------------------------------------------------------------

DAMA_DMBOK2 = StandardData(
    name="DAMA-DMBOK2",
    full_name="Data Management Body of Knowledge, 2nd Edition",
    publisher="DAMA International",
    version="2.0",
    year=2017,
    description=(
        "DAMA-DMBOK2 is the definitive guide for data management professionals, covering "
        "all aspects of enterprise data management including governance, quality, architecture, "
        "metadata, security, and analytics."
    ),
    key_principles=[
        "Data is a valuable organisational asset requiring active management",
        "Data quality is a shared organisational responsibility",
        "Data governance provides accountability for data management decisions",
        "Metadata management is foundational to all data management disciplines",
        "Data architecture aligns data assets to business strategy",
        "Master data provides the authoritative source of key business entities",
    ],
    compliance_requirements=[
        "Define data ownership and data stewardship roles for all critical data domains",
        "Implement data governance council with defined charter and authority",
        "Establish and enforce data quality rules with measurable thresholds",
        "Maintain enterprise data catalogue covering all production data assets",
        "Implement data lineage tracking from source to consumption",
        "Define master data management (MDM) strategy for key entities (Customer, Product, etc.)",
        "Establish data classification policy (Public, Internal, Confidential, Restricted)",
        "Conduct data quality assessments on a defined schedule",
    ],
    applicable_domains=["Digital Intelligence", "Data Management"],
    certification_body="DAMA International",
    source_url="https://www.dama.org/cpages/body-of-knowledge",
    industry_relevance=["All sectors with significant data assets"],
    tags=["data management", "data governance", "data quality", "MDM", "metadata"],
)

ISO_25012 = StandardData(
    name="ISO/IEC 25012",
    full_name="ISO/IEC 25012:2008 — Software and System Quality — Data Quality Model",
    publisher="ISO/IEC",
    version="2008",
    year=2008,
    description="ISO/IEC 25012 defines a general data quality model for data retained in a structured form within a computer system.",
    key_principles=[
        "Data quality has inherent properties (accuracy, completeness, consistency) and system-dependent properties",
        "Accessibility, compliance, confidentiality, efficiency, precision, traceability, understandability",
        "Quality is measured against defined metrics and thresholds",
    ],
    compliance_requirements=[
        "Define data quality dimensions relevant to each data domain",
        "Establish data quality measurement methodology and baselines",
        "Implement automated data quality checks in data pipelines",
        "Report data quality scores on defined KPIs monthly",
        "Remediate data quality issues within defined SLAs",
    ],
    applicable_domains=["Digital Intelligence", "Data"],
    source_url="https://www.iso.org/standard/35736.html",
    industry_relevance=["All sectors"],
    tags=["data quality", "ISO", "measurement"],
)

# ---------------------------------------------------------------------------
# Security Standards
# ---------------------------------------------------------------------------

ISO_27001 = StandardData(
    name="ISO/IEC 27001:2022",
    full_name="ISO/IEC 27001:2022 — Information Security Management Systems",
    publisher="ISO/IEC",
    version="2022",
    year=2022,
    description=(
        "ISO/IEC 27001:2022 specifies requirements for establishing, implementing, "
        "maintaining and continually improving an information security management system (ISMS)."
    ),
    key_principles=[
        "Risk-based approach to information security management",
        "Leadership and commitment from top management is mandatory",
        "Security controls selected based on risk assessment results",
        "Continual improvement through Plan-Do-Check-Act (PDCA) cycle",
        "People, process and technology must all be addressed",
    ],
    compliance_requirements=[
        "Conduct information security risk assessment covering all assets",
        "Define risk treatment plan with accepted risk thresholds",
        "Implement Annex A controls relevant to scope (93 controls in 2022 edition)",
        "Establish information security policies approved by top management",
        "Define roles and responsibilities for information security",
        "Conduct security awareness training for all staff annually",
        "Perform internal ISMS audit at defined intervals",
        "Conduct management review of ISMS performance annually",
        "Define and test incident response procedures",
        "Implement vulnerability management and patch management processes",
    ],
    applicable_domains=["Security", "All digital domains"],
    certification_body="ISO/IEC accredited certification bodies",
    source_url="https://www.iso.org/standard/27001",
    industry_relevance=["All sectors"],
    tags=["information security", "ISMS", "ISO", "risk management", "controls"],
)

NIST_CSF_2 = StandardData(
    name="NIST CSF 2.0",
    full_name="NIST Cybersecurity Framework 2.0",
    publisher="National Institute of Standards and Technology",
    version="2.0",
    year=2024,
    description=(
        "NIST CSF 2.0 provides a taxonomy of high-level cybersecurity outcomes that can be used "
        "by any organisation — regardless of its size, sector, or maturity — to better understand, "
        "assess, prioritise, and communicate its cybersecurity efforts."
    ),
    key_principles=[
        "GOVERN — establish, communicate and monitor cybersecurity risk management strategy",
        "IDENTIFY — understand cybersecurity risks to systems, people, assets, data",
        "PROTECT — safeguards to limit cybersecurity incident impact",
        "DETECT — identify cybersecurity incidents in timely manner",
        "RESPOND — actions taken regarding detected cybersecurity incidents",
        "RECOVER — restore capabilities impaired by cybersecurity incidents",
    ],
    compliance_requirements=[
        "Establish cybersecurity governance structure and risk management strategy",
        "Conduct asset inventory and classification for all IT/OT systems",
        "Implement identity and access management (IAM) controls",
        "Deploy continuous monitoring and SIEM for threat detection",
        "Define and test incident response plan (IRP)",
        "Conduct regular penetration testing and red team exercises",
        "Implement supply chain security risk management",
        "Develop and test business continuity and disaster recovery plans",
    ],
    applicable_domains=["Security", "Digital IT", "All"],
    source_url="https://www.nist.gov/cyberframework",
    industry_relevance=["All sectors"],
    tags=["cybersecurity", "NIST", "risk", "framework"],
)

GDPR = StandardData(
    name="GDPR",
    full_name="General Data Protection Regulation (EU) 2016/679",
    publisher="European Parliament and Council of the EU",
    version="2018",
    year=2018,
    description="GDPR is the EU regulation on data protection and privacy, setting requirements for processing personal data of EU residents.",
    key_principles=[
        "Lawfulness, fairness and transparency in data processing",
        "Purpose limitation — data collected for specified, explicit, legitimate purposes",
        "Data minimisation — only collect data adequate and relevant to purpose",
        "Accuracy — data must be kept accurate and up to date",
        "Storage limitation — retain data only as long as necessary",
        "Integrity and confidentiality — appropriate security measures",
        "Accountability — controller responsible for demonstrating compliance",
    ],
    compliance_requirements=[
        "Maintain Records of Processing Activities (RoPA) for all data processing",
        "Establish lawful basis for each category of personal data processing",
        "Implement data subject rights procedures (access, erasure, portability)",
        "Appoint Data Protection Officer (DPO) where required",
        "Conduct Data Protection Impact Assessments (DPIA) for high-risk processing",
        "Notify Data Protection Authority within 72 hours of data breach",
        "Implement data retention and deletion schedules",
        "Review and update third-party data processing agreements (DPA)",
    ],
    applicable_domains=["All domains processing personal data"],
    source_url="https://gdpr-info.eu",
    industry_relevance=["All sectors with EU operations or EU data subjects"],
    tags=["privacy", "data protection", "GDPR", "EU", "compliance"],
)

# ---------------------------------------------------------------------------
# Finance / Banking Standards
# ---------------------------------------------------------------------------

DORA = StandardData(
    name="DORA",
    full_name="Digital Operational Resilience Act (EU) 2022/2554",
    publisher="European Parliament and Council of the EU",
    version="2025 (effective)",
    year=2025,
    description=(
        "DORA establishes uniform requirements for the security of network and information "
        "systems supporting the business processes of financial entities in the EU."
    ),
    key_principles=[
        "ICT risk management is a core board-level responsibility",
        "Operational resilience across the full digital supply chain",
        "Incident classification, reporting and information sharing",
        "Digital operational resilience testing including TLPT",
        "ICT third-party risk management including critical providers",
    ],
    compliance_requirements=[
        "Establish ICT risk management framework with board-level sign-off",
        "Implement ICT incident classification and reporting procedures",
        "Conduct advanced digital operational resilience testing (TLPT) annually",
        "Maintain ICT third-party service provider register",
        "Define contractual requirements for critical ICT third parties",
        "Implement threat intelligence programme and information sharing",
        "Conduct operational resilience scenarios and recovery tests",
    ],
    applicable_domains=["Banking", "Finance", "Insurance", "Digital IT"],
    source_url="https://www.eba.europa.eu/regulation-and-policy/operational-resilience/digital-operational-resilience-act-dora",
    industry_relevance=["Financial Services", "Insurance", "Asset Management"],
    tags=["resilience", "DORA", "financial", "ICT risk", "EU regulation"],
)

BASEL_IV = StandardData(
    name="Basel IV",
    full_name="Basel IV / Basel III Finalisation — BIS Standards",
    publisher="Basel Committee on Banking Supervision (BCBS) / BIS",
    version="Basel IV (2028 implementation)",
    year=2017,
    description=(
        "Basel IV finalises the post-crisis regulatory reforms, revising risk-weighted "
        "asset calculation methodologies for credit, market, and operational risk."
    ),
    key_principles=[
        "Enhanced risk sensitivity in capital calculations",
        "Output floor limits RWA reduction from internal models",
        "Standardised approach as floor for advanced approaches",
        "Operational risk capital framework simplification",
        "Leverage ratio as supplementary backstop measure",
    ],
    compliance_requirements=[
        "Implement revised standardised credit risk approach (SA-CR)",
        "Adopt output floor — RWA not below 72.5% of standardised approach",
        "Implement Fundamental Review of the Trading Book (FRTB) market risk rules",
        "Adopt standardised measurement approach (SMA) for operational risk",
        "Report capital adequacy ratios under revised methodology quarterly",
        "Maintain capital conservation buffer above minimum requirements",
        "Implement revised CVA risk framework",
    ],
    applicable_domains=["Banking", "Finance"],
    source_url="https://www.bis.org/bcbs/publ/d424.htm",
    industry_relevance=["Banking"],
    tags=["banking", "capital", "risk", "Basel", "regulatory capital"],
)

PSD2 = StandardData(
    name="PSD2",
    full_name="Payment Services Directive 2 (EU) 2015/2366",
    publisher="European Parliament and Council of the EU",
    version="2018 (RTS in force)",
    year=2018,
    description="PSD2 regulates payment services in the EU, introducing Open Banking, Strong Customer Authentication (SCA) and third-party access to account data.",
    key_principles=[
        "Open Banking — third-party providers (TPP) access to payment accounts via APIs",
        "Strong Customer Authentication (SCA) for electronic payments",
        "Account Information Service Providers (AISP) and Payment Initiation Service Providers (PISP)",
        "Enhanced consumer protection and transparency",
    ],
    compliance_requirements=[
        "Implement Open Banking APIs compliant with PSD2 technical standards",
        "Deploy Strong Customer Authentication (SCA) for all relevant transactions",
        "Establish TPP onboarding and access management procedures",
        "Maintain API availability and performance SLAs for TPPs",
        "Implement transaction monitoring for fraud detection",
        "Provide real-time payment confirmation and status to customers",
    ],
    applicable_domains=["Banking", "Payments", "Finance"],
    source_url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32015L2366",
    industry_relevance=["Banking", "Payments", "FinTech"],
    tags=["open banking", "payments", "PSD2", "SCA", "APIs"],
)

IFRS_17 = StandardData(
    name="IFRS 17",
    full_name="IFRS 17 Insurance Contracts",
    publisher="International Accounting Standards Board (IASB)",
    version="2017 (effective 2023)",
    year=2017,
    description="IFRS 17 establishes principles for the recognition, measurement, presentation and disclosure of insurance contracts.",
    key_principles=[
        "Contractual Service Margin (CSM) measures unearned profit",
        "Consistent measurement of insurance liabilities",
        "Transparency in financial reporting for insurance",
    ],
    compliance_requirements=[
        "Implement IFRS 17 measurement models (GMM, PAA, VFA)",
        "Produce insurance contract liability calculations per IFRS 17",
        "Report CSM roll-forward and release in financial statements",
        "Implement transition approaches (full retrospective, modified retrospective, fair value)",
        "Align actuarial and accounting data pipelines for IFRS 17 reporting",
    ],
    applicable_domains=["Insurance", "Finance"],
    source_url="https://www.ifrs.org/issued-standards/list-of-standards/ifrs-17-insurance-contracts/",
    industry_relevance=["Insurance"],
    tags=["insurance", "IFRS", "accounting", "financial reporting"],
)

# ---------------------------------------------------------------------------
# Healthcare Standards
# ---------------------------------------------------------------------------

HL7_FHIR = StandardData(
    name="HL7 FHIR R4",
    full_name="Health Level 7 Fast Healthcare Interoperability Resources, Release 4",
    publisher="Health Level Seven International (HL7)",
    version="R4 (4.0.1)",
    year=2019,
    description=(
        "FHIR is a standard for healthcare data exchange, based on modern web technologies. "
        "It enables interoperability between healthcare systems through RESTful APIs and standard resources."
    ),
    key_principles=[
        "Resources as the fundamental building blocks of healthcare data exchange",
        "RESTful API design for system interoperability",
        "Extensibility through profiles and implementation guides",
        "Human and machine readability of healthcare data",
        "Open standards enabling innovation and competition",
    ],
    compliance_requirements=[
        "Implement FHIR R4 compliant APIs for clinical data exchange",
        "Adopt FHIR resource profiles for Patient, Practitioner, Observation, Condition",
        "Implement SMART on FHIR for application authorisation",
        "Validate FHIR resources against published profiles and implementation guides",
        "Achieve ONC certification for FHIR-based data access requirements",
        "Implement FHIR Bulk Data Access for population health use cases",
        "Establish FHIR capability statement documenting supported operations",
    ],
    applicable_domains=["Healthcare", "Clinical", "Digital Health"],
    source_url="https://hl7.org/fhir/R4/",
    industry_relevance=["Healthcare", "Hospitals", "Payers", "Pharma"],
    tags=["healthcare", "interoperability", "FHIR", "HL7", "clinical data"],
)

HIPAA = StandardData(
    name="HIPAA",
    full_name="Health Insurance Portability and Accountability Act of 1996",
    publisher="U.S. Department of Health and Human Services",
    version="HITECH amended",
    year=1996,
    description="HIPAA sets the standard for protecting sensitive patient health information (PHI) and establishes rules for covered entities and business associates.",
    key_principles=[
        "Privacy Rule — rights over and use of PHI",
        "Security Rule — safeguards for electronic PHI (ePHI)",
        "Breach Notification Rule — notification requirements after breach",
        "Minimum necessary use of PHI",
        "Patient right of access to health information",
    ],
    compliance_requirements=[
        "Implement access controls limiting PHI access to authorised workforce",
        "Encrypt ePHI at rest and in transit",
        "Conduct annual HIPAA risk assessment",
        "Execute Business Associate Agreements with all PHI-handling vendors",
        "Implement audit logging for all PHI access",
        "Train all workforce members on HIPAA requirements annually",
        "Develop and test breach notification procedures",
        "Implement minimum necessary policies for PHI use and disclosure",
    ],
    applicable_domains=["Healthcare", "Clinical"],
    source_url="https://www.hhs.gov/hipaa/index.html",
    industry_relevance=["Healthcare", "Payers", "Health IT vendors"],
    tags=["healthcare", "privacy", "PHI", "HIPAA", "compliance"],
)

# ---------------------------------------------------------------------------
# Cloud / IT Service Standards
# ---------------------------------------------------------------------------

ITIL_4 = StandardData(
    name="ITIL 4",
    full_name="Information Technology Infrastructure Library, 4th Edition",
    publisher="AXELOS / PeopleCert",
    version="4.0",
    year=2019,
    description=(
        "ITIL 4 is a comprehensive framework for IT service management (ITSM), "
        "providing practical guidance for organisations to define and embed a service management "
        "system and best practices for delivering value through services."
    ),
    key_principles=[
        "Focus on value — all activities should create value for stakeholders",
        "Start where you are — build on existing capabilities",
        "Progress iteratively with feedback",
        "Collaborate and promote visibility",
        "Think and work holistically",
        "Keep it simple and practical",
        "Optimise and automate",
    ],
    compliance_requirements=[
        "Define service catalogue covering all IT services with SLAs",
        "Implement incident management process with defined response/resolution SLAs",
        "Establish change management process with risk-based change advisory board",
        "Implement problem management with root cause analysis capability",
        "Define service level management and conduct SLA review meetings",
        "Implement configuration management database (CMDB) for all CIs",
        "Establish release and deployment management procedures",
        "Implement capacity and availability management reporting",
    ],
    applicable_domains=["Digital IT", "IT Service Management"],
    certification_body="PeopleCert",
    source_url="https://www.axelos.com/certifications/itil-service-management/",
    industry_relevance=["All sectors with IT operations"],
    tags=["ITSM", "ITIL", "service management", "IT operations"],
)

FINOPS = StandardData(
    name="FinOps Framework",
    full_name="Cloud Financial Management Framework — FinOps Foundation",
    publisher="FinOps Foundation",
    version="2024",
    year=2024,
    description="The FinOps Framework provides practices for managing cloud costs through collaboration between finance, engineering, and business teams.",
    key_principles=[
        "Teams need to collaborate — finance, engineering and business",
        "Decisions are driven by the business value of cloud",
        "Everyone takes ownership of their cloud usage",
        "FinOps reports should be accessible and timely",
        "A centralised team drives FinOps practice",
        "Take advantage of the variable cost model of the cloud",
    ],
    compliance_requirements=[
        "Implement cloud cost tagging strategy for 100% of cloud resources",
        "Establish unit economics metrics (cost per transaction, per user, per workload)",
        "Define cloud budget targets and alert thresholds per business unit",
        "Implement automated rightsizing recommendations review process",
        "Conduct monthly cloud cost review meetings across engineering and finance",
        "Define cloud waste elimination targets and track monthly",
    ],
    applicable_domains=["Cloud", "Digital IT", "Finance"],
    source_url="https://www.finops.org/framework/",
    industry_relevance=["All sectors using cloud"],
    tags=["cloud", "FinOps", "cost management", "cloud economics"],
)

# ---------------------------------------------------------------------------
# Telecom Standards
# ---------------------------------------------------------------------------

TMFORUM_ODA = StandardData(
    name="TM Forum ODA",
    full_name="TM Forum Open Digital Architecture",
    publisher="TM Forum",
    version="ODA Canvas R23.5",
    year=2023,
    description=(
        "TM Forum ODA defines a blueprint for cloud-native telco architecture, "
        "enabling communication service providers to modernise through standardised, "
        "component-based microservices using Open APIs."
    ),
    key_principles=[
        "Component-based architecture replacing monolithic BSS/OSS",
        "TM Forum Open APIs for interoperability",
        "Cloud-native deployment on Kubernetes (ODA Canvas)",
        "AI-native design for autonomous network operations",
        "Business Agility through loose coupling of ODA Components",
    ],
    compliance_requirements=[
        "Adopt TM Forum Open API standards for integration interfaces",
        "Design BSS/OSS capabilities as ODA Components with defined Open APIs",
        "Deploy on ODA Canvas (Kubernetes-based) for lifecycle management",
        "Map all business capabilities to eTOM (enhanced Telecom Operations Map)",
        "Implement SID (Shared Information Data model) for data consistency",
        "Achieve TM Forum conformance certification for Open API implementations",
    ],
    applicable_domains=["Telecom", "Communications", "Digital Channels"],
    source_url="https://www.tmforum.org/oda/",
    industry_relevance=["Telecommunications", "Communications Service Providers"],
    tags=["telecom", "ODA", "TM Forum", "BSS", "OSS", "Open API"],
)

# ---------------------------------------------------------------------------
# Supply Chain / Food Standards
# ---------------------------------------------------------------------------

ISO_22000 = StandardData(
    name="ISO 22000:2018",
    full_name="ISO 22000:2018 — Food Safety Management Systems",
    publisher="ISO/TC 34",
    version="2018",
    year=2018,
    description="ISO 22000 specifies requirements for a food safety management system to ensure food is safe at the point of human consumption.",
    key_principles=[
        "Interactive communication across the food chain",
        "System management integrating PDCA and HACCP",
        "Prerequisite programmes (PRPs) controlling hazards",
        "Hazard Analysis and Critical Control Points (HACCP)",
        "Continual improvement of food safety management",
    ],
    compliance_requirements=[
        "Establish food safety policy and objectives",
        "Conduct hazard analysis for all food safety hazards",
        "Define Critical Control Points (CCPs) and critical limits",
        "Implement monitoring procedures for each CCP",
        "Establish corrective action procedures for CCP deviations",
        "Conduct internal food safety audits annually",
        "Maintain traceability system for all food products one step back/one step forward",
        "Manage food safety incidents and product recalls",
    ],
    applicable_domains=["Food Supply", "Supply Chain"],
    certification_body="ISO/IEC accredited bodies",
    source_url="https://www.iso.org/standard/65464.html",
    industry_relevance=["Food & Beverage", "Agriculture", "Food Retail"],
    tags=["food safety", "ISO", "HACCP", "supply chain"],
)

SCOR = StandardData(
    name="SCOR Model",
    full_name="Supply Chain Operations Reference Model",
    publisher="Association for Supply Chain Management (ASCM)",
    version="SCOR DS 2022",
    year=2022,
    description="SCOR is the world's leading supply chain framework, linking business processes, performance metrics, practices and people skills into a unified structure.",
    key_principles=[
        "Plan → Source → Make → Deliver → Return → Enable process framework",
        "Standardised performance metrics across supply chain tiers",
        "Best practice library for supply chain improvement",
        "Technology enablement of supply chain processes",
    ],
    compliance_requirements=[
        "Map all supply chain processes to SCOR Plan/Source/Make/Deliver/Return/Enable",
        "Establish supply chain performance metrics (Perfect Order, Cash-to-Cash, etc.)",
        "Implement supply chain risk assessment and mitigation framework",
        "Define supplier performance management programme with scorecards",
        "Implement supply chain visibility platform for end-to-end tracking",
    ],
    applicable_domains=["Supply Chain", "Food Supply", "Manufacturing"],
    source_url="https://www.ascm.org/supply-chain-management/scor-model/",
    industry_relevance=["Manufacturing", "Retail", "Distribution", "Food"],
    tags=["supply chain", "SCOR", "operations", "logistics"],
)

# ---------------------------------------------------------------------------
# Government / Regulatory Standards
# ---------------------------------------------------------------------------

NIST_SP_800_53 = StandardData(
    name="NIST SP 800-53 Rev.5",
    full_name="Security and Privacy Controls for Information Systems and Organizations",
    publisher="NIST",
    version="Rev.5",
    year=2020,
    description="NIST SP 800-53 provides a catalogue of security and privacy controls for protecting organisational operations and assets, individuals, and the nation.",
    key_principles=[
        "Security and privacy controls organised into 20 families",
        "Baseline control selections (Low, Moderate, High) based on impact level",
        "Privacy integrated with security controls throughout",
        "Supply chain risk management controls",
        "Zero Trust Architecture controls included",
    ],
    compliance_requirements=[
        "Select and implement security controls based on impact level (Low/Moderate/High)",
        "Conduct security and privacy control assessments",
        "Authorise information systems for operation (ATO process)",
        "Implement continuous monitoring programme for security controls",
        "Conduct supply chain risk management assessments",
        "Implement identity, credential and access management (ICAM) controls",
    ],
    applicable_domains=["Government", "Federal IT", "Security"],
    source_url="https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
    industry_relevance=["Government", "Defense", "Critical Infrastructure"],
    tags=["government", "security controls", "NIST", "federal", "compliance"],
)

GOVSTACK = StandardData(
    name="GovStack",
    full_name="GovStack — Digital Government Building Blocks Specification",
    publisher="ITU / GovStack Initiative",
    version="1.0",
    year=2023,
    description="GovStack provides reusable, open-source software building blocks for digital government, enabling countries to deliver citizen-centric digital public services.",
    key_principles=[
        "Building blocks as reusable, interoperable components",
        "Open standards and open source for vendor independence",
        "Citizen-centric design of public services",
        "Federated identity and consent management",
        "Interoperability through defined APIs",
    ],
    compliance_requirements=[
        "Implement Identity and Verification building block for citizen authentication",
        "Deploy Consent Management building block for personal data control",
        "Implement Digital Registries building block for civil registry systems",
        "Adopt Information Mediator (X-Road) for secure API exchange",
        "Design services following GovStack Service Design Principles",
        "Publish all building block APIs using OpenAPI specification",
    ],
    applicable_domains=["Government", "Regulatory", "Digital Services"],
    source_url="https://www.govstack.global/",
    industry_relevance=["Government", "Public Sector"],
    tags=["government", "digital public services", "building blocks", "GovStack"],
)

# ---------------------------------------------------------------------------
# HR / Workforce Standards
# ---------------------------------------------------------------------------

ISO_30414 = StandardData(
    name="ISO 30414:2018",
    full_name="ISO 30414:2018 — Human Resource Management — Guidelines for Internal and External Human Capital Reporting",
    publisher="ISO/TC 260",
    version="2018",
    year=2018,
    description="ISO 30414 provides guidelines for human capital reporting, enabling organisations to report on workforce metrics internally and to external stakeholders.",
    key_principles=[
        "Transparency in human capital reporting",
        "Standardised workforce metrics across 9 reporting areas",
        "Enables benchmarking of workforce performance",
        "Supports board-level decisions on workforce investment",
    ],
    compliance_requirements=[
        "Report on workforce composition (headcount, diversity, part-time/full-time)",
        "Measure and report on leadership effectiveness and succession planning",
        "Report on learning and development investment and outcomes",
        "Measure employee well-being and safety metrics",
        "Report on workforce productivity metrics",
        "Conduct workforce risk assessment and report findings",
    ],
    applicable_domains=["Human Resources", "Workforce", "Backoffice"],
    source_url="https://www.iso.org/standard/69725.html",
    industry_relevance=["All sectors"],
    tags=["HR", "workforce", "human capital", "reporting", "ISO"],
)

# ---------------------------------------------------------------------------
# Domain → Standards mapping
# Pattern matching: domain name keywords → list of applicable StandardData
# ---------------------------------------------------------------------------

STANDARDS_BY_DOMAIN_PATTERN: dict[str, list[StandardData]] = {
    # Universal (matched to all domains)
    "_universal": [TOGAF_10, COBIT_2019],

    # Digital Intelligence / Data / AI
    "intelligence": [DAMA_DMBOK2, NIST_AI_RMF, ISO_42001, ISO_25012],
    "data": [DAMA_DMBOK2, ISO_25012, GDPR],
    "analytics": [DAMA_DMBOK2, NIST_AI_RMF, ISO_42001],

    # Security
    "security": [ISO_27001, NIST_CSF_2, GDPR],
    "cyber": [NIST_CSF_2, ISO_27001],
    "privacy": [GDPR, ISO_27001],

    # Finance / Banking
    "banking": [DORA, BASEL_IV, PSD2, ISO_27001, COBIT_2019],
    "finance": [DORA, IFRS_17, ISO_27001, COBIT_2019],
    "payment": [PSD2, ISO_27001, NIST_CSF_2],
    "insurance": [IFRS_17, ISO_27001, COBIT_2019],

    # Healthcare
    "health": [HL7_FHIR, HIPAA, ISO_27001],
    "clinical": [HL7_FHIR, HIPAA],
    "pharmaceutical": [ISO_27001, ITIL_4],

    # Cloud / IT
    "digital it": [ITIL_4, NIST_CSF_2, ISO_27001, FINOPS],
    "cloud": [ITIL_4, FINOPS, NIST_CSF_2],
    "devops": [ITIL_4, NIST_CSF_2],

    # Telecom / Communications
    "telecom": [TMFORUM_ODA, ISO_27001, ITIL_4],
    "communications": [TMFORUM_ODA, ITIL_4],
    "regulatory (communications)": [TMFORUM_ODA, COBIT_2019],

    # Supply Chain / Food
    "food supply": [ISO_22000, SCOR, ISO_27001],
    "supply": [SCOR, ISO_27001],
    "pharmaceutical": [ISO_22000, ISO_27001],

    # Government / Regulatory
    "government": [GOVSTACK, NIST_SP_800_53, ISO_27001, COBIT_2019],
    "regulatory": [COBIT_2019, ISO_27001, NIST_SP_800_53],

    # HR / Workforce
    "human resources": [ISO_30414, COBIT_2019],
    "workforce": [ISO_30414],
    "hr": [ISO_30414],

    # Legal
    "legal": [ISO_27001, GDPR, COBIT_2019],

    # Property / Facilities
    "property": [ISO_27001, COBIT_2019, ITIL_4],

    # Channels / CX
    "channel": [COBIT_2019, ISO_27001, GDPR],
    "experience": [COBIT_2019, ISO_27001, GDPR],

    # Backoffice
    "backoffice": [COBIT_2019, ISO_27001, GDPR],
}


def get_standards_for_domain(domain_name: str) -> list[StandardData]:
    """Return deduplicated standards list for a given domain name."""
    name_lower = domain_name.lower()
    seen_names: set[str] = set()
    result: list[StandardData] = []

    def add(std: StandardData):
        if std.name not in seen_names:
            seen_names.add(std.name)
            result.append(std)

    for std in STANDARDS_BY_DOMAIN_PATTERN["_universal"]:
        add(std)

    for pattern, stds in STANDARDS_BY_DOMAIN_PATTERN.items():
        if pattern == "_universal":
            continue
        if pattern in name_lower:
            for std in stds:
                add(std)

    return result
