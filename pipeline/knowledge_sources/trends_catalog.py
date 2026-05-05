"""
Curated authoritative digital transformation trends catalog mapped to EA domain patterns.

Sources: Gartner Hype Cycle 2024-2025, Forrester Wave Q4 2024, McKinsey Technology Trends 2024,
         MIT Sloan Management Review 2025, Harvard Business Review Digital, WEF Future of Jobs 2025,
         IEEE Spectrum Emerging Tech, Deloitte Tech Trends 2025, Accenture Technology Vision 2025,
         TOGAF Series Guides: Cloud, Agile, DevSecOps
"""

from dataclasses import dataclass, field


@dataclass
class TrendData:
    name: str
    description: str
    source: str
    source_type: str   # industry_analyst | academic | regulatory | practitioner | government
    publication_year: int
    impact_level: str  # transformational | high | moderate | low
    maturity: str      # emerging | growing | mainstream | declining
    time_horizon: str  # <1yr | 1-2yr | 2-5yr | 5+yr
    business_impact: str
    technology_enablers: list = field(default_factory=list)
    related_standards: list = field(default_factory=list)
    adoption_rate: str = ""
    industry_applicability: list = field(default_factory=list)
    citations: list = field(default_factory=list)
    tags: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Universal Digital Transformation Trends
# ---------------------------------------------------------------------------

AGENTIC_AI = TrendData(
    name="Agentic AI in Enterprise Operations",
    description=(
        "AI agents that autonomously plan, execute, and adapt multi-step workflows with "
        "minimal human intervention are transforming enterprise operations. Systems like "
        "LangGraph, AutoGen and CrewAI enable multi-agent pipelines for complex reasoning tasks."
    ),
    source="Gartner Hype Cycle for Artificial Intelligence, 2025",
    source_type="industry_analyst",
    publication_year=2025,
    impact_level="transformational",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "Reduces operational overhead by 30-40% in knowledge-work processes; "
        "accelerates decision cycles from days to hours for complex analytical tasks"
    ),
    technology_enablers=["Large Language Models", "Vector databases", "LangGraph/AutoGen", "AMD MI300X GPUs", "ROCm", "vLLM"],
    related_standards=["ISO 42001", "NIST AI RMF"],
    adoption_rate="18% of large enterprises in 2025, projected 65% by 2027 (Gartner)",
    industry_applicability=["Financial Services", "Healthcare", "Government", "Manufacturing", "All"],
    citations=["Gartner Top Strategic Technology Trends 2025", "MIT Sloan Review Q1 2025"],
    tags=["agentic AI", "LLM", "automation", "AI agents", "multi-agent"],
)

GENERATIVE_AI_ENTERPRISE = TrendData(
    name="Generative AI for Enterprise Productivity",
    description=(
        "Foundation models fine-tuned on enterprise data are delivering measurable productivity "
        "gains across document processing, code generation, customer service, and knowledge management."
    ),
    source="McKinsey Global Institute — The Economic Potential of Generative AI, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="transformational",
    maturity="growing",
    time_horizon="1-2yr",
    business_impact=(
        "Estimated $2.6–4.4 trillion annual value across industries; "
        "knowledge worker productivity improvement of 20-40% in early adopters"
    ),
    technology_enablers=["LLMs", "RAG pipelines", "Fine-tuning", "AMD Instinct MI300X", "vLLM inference"],
    related_standards=["ISO 42001", "NIST AI RMF", "GDPR"],
    adoption_rate="79% of organisations have started GenAI pilots in 2024 (McKinsey)",
    industry_applicability=["All sectors"],
    citations=["McKinsey 2024", "Gartner 2024", "Accenture Technology Vision 2025"],
    tags=["GenAI", "LLM", "productivity", "enterprise AI", "fine-tuning"],
)

COMPOSABLE_ARCHITECTURE = TrendData(
    name="Composable Enterprise Architecture",
    description=(
        "Organisations are moving from monolithic systems to composable, API-first "
        "architectures using modular packaged business capabilities (PBCs) to achieve "
        "business agility and faster time-to-market."
    ),
    source="Gartner — Magic Quadrant for Enterprise Architecture Tools, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="growing",
    time_horizon="2-5yr",
    business_impact=(
        "Reduces time-to-market for new digital products by 50-70%; "
        "enables rapid response to market changes through capability recombination"
    ),
    technology_enablers=["API Management", "Microservices", "Event-driven architecture", "Low-code platforms"],
    related_standards=["TOGAF 10", "COBIT 2019", "TM Forum ODA"],
    adoption_rate="40% of enterprises pursuing composability strategies in 2024 (Gartner)",
    industry_applicability=["All sectors"],
    citations=["Gartner 2024", "Forrester Research 2024"],
    tags=["composable", "API-first", "architecture", "modularity", "agility"],
)

PLATFORM_ENGINEERING = TrendData(
    name="Platform Engineering and Internal Developer Platforms",
    description=(
        "Internal Developer Platforms (IDPs) are becoming standard practice, providing "
        "self-service infrastructure and tooling that reduce cognitive load on engineering teams "
        "and accelerate software delivery velocity."
    ),
    source="Gartner Hype Cycle for Software Engineering, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="growing",
    time_horizon="1-2yr",
    business_impact=(
        "Developer productivity improvement of 30-50%; "
        "reduces environment provisioning from days to minutes"
    ),
    technology_enablers=["Kubernetes", "GitOps", "Terraform/Pulumi", "Backstage", "CI/CD pipelines"],
    related_standards=["ITIL 4", "NIST CSF 2.0"],
    adoption_rate="60% of large enterprises building IDPs by 2026 (Gartner)",
    industry_applicability=["Technology", "Financial Services", "Retail", "Manufacturing"],
    citations=["Gartner 2024", "DORA State of DevOps 2024"],
    tags=["platform engineering", "developer experience", "DevOps", "IDP", "Kubernetes"],
)

ZERO_TRUST_SECURITY = TrendData(
    name="Zero Trust Architecture",
    description=(
        "Zero Trust replaces perimeter-based security with continuous verification: "
        "'never trust, always verify'. Every access request is authenticated, authorised, "
        "and encrypted regardless of network location."
    ),
    source="NIST SP 800-207 Zero Trust Architecture + Gartner Security & Risk Summit 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="transformational",
    maturity="growing",
    time_horizon="1-2yr",
    business_impact=(
        "Reduces breach impact by 50-70% through lateral movement prevention; "
        "enables secure hybrid work and cloud-first architectures"
    ),
    technology_enablers=["Identity providers (Azure AD, Okta)", "SASE", "Micro-segmentation", "PAM solutions"],
    related_standards=["NIST CSF 2.0", "ISO 27001:2022", "NIST SP 800-53"],
    adoption_rate="60% of enterprises will have Zero Trust as primary framework by 2026 (Gartner)",
    industry_applicability=["All sectors"],
    citations=["NIST SP 800-207", "Gartner 2024", "Forrester Zero Trust Wave 2023"],
    tags=["zero trust", "security", "identity", "SASE", "cybersecurity"],
)

DATA_MESH = TrendData(
    name="Data Mesh and Decentralised Data Ownership",
    description=(
        "Data Mesh moves from centralised data lakes to domain-owned data products, "
        "with self-serve data infrastructure and federated governance enabling scalable, "
        "business-aligned data management."
    ),
    source="Forrester Wave: Data Management, Q3 2024 + MIT Sloan Management Review 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "Reduces time-to-insight from weeks to days; "
        "improves data quality through ownership accountability; "
        "scales data capability with organisational growth"
    ),
    technology_enablers=["Data catalogues", "Data contracts", "Event streaming (Kafka)", "Data Fabric platforms"],
    related_standards=["DAMA-DMBOK2", "ISO 25012", "TOGAF 10"],
    adoption_rate="25% of large enterprises piloting data mesh in 2024 (Forrester)",
    industry_applicability=["Financial Services", "Retail", "Technology", "Healthcare"],
    citations=["Forrester 2024", "MIT Sloan Review 2024", "ThoughtWorks Technology Radar 2024"],
    tags=["data mesh", "data products", "decentralised", "data governance", "data fabric"],
)

SUSTAINABLE_IT = TrendData(
    name="Sustainable IT and Green Digital Transformation",
    description=(
        "Organisations are embedding sustainability into digital strategy — measuring and "
        "reducing the carbon footprint of IT operations, using AI to optimise energy consumption, "
        "and aligning digital transformation with ESG targets."
    ),
    source="WEF Digital Economy and Society — Green Digital Transformation, 2024",
    source_type="government",
    publication_year=2024,
    impact_level="high",
    maturity="growing",
    time_horizon="2-5yr",
    business_impact=(
        "IT accounts for 2-3% of global carbon emissions; "
        "AI-optimised data centre cooling reduces energy usage by 30-40%; "
        "ESG reporting requirements driving board-level accountability"
    ),
    technology_enablers=["AI-optimised infrastructure", "Green cloud regions", "Carbon measurement tools", "AMD MI300X energy efficiency"],
    related_standards=["ISO 14001", "GRI Standards", "TCFD"],
    adoption_rate="70% of CIOs include sustainability in digital strategy in 2024 (Gartner)",
    industry_applicability=["All sectors"],
    citations=["WEF 2024", "Gartner 2024", "McKinsey Sustainability Report 2024"],
    tags=["sustainability", "ESG", "green IT", "carbon", "energy efficiency"],
)

# ---------------------------------------------------------------------------
# Domain-specific trends
# ---------------------------------------------------------------------------

# Intelligence / Data / AI
AI_AUGMENTED_EA = TrendData(
    name="AI-Augmented Enterprise Architecture",
    description=(
        "AI tools are transforming EA practice — from automated capability gap analysis "
        "and architecture pattern recommendations to AI-generated architecture documentation "
        "and compliance checking."
    ),
    source="Forrester Wave: Enterprise Architecture Management Suites Q4 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "Reduces architecture documentation effort by 60%; "
        "enables real-time architecture governance at scale"
    ),
    technology_enablers=["LLMs", "Knowledge graphs", "Neo4j", "Graph-RAG", "AMD ROCm"],
    related_standards=["TOGAF 10", "COBIT 2019", "ISO 42001"],
    industry_applicability=["All sectors"],
    citations=["Forrester 2024", "Gartner Magic Quadrant EA Tools 2024"],
    tags=["enterprise architecture", "AI", "knowledge graph", "automation"],
)

KNOWLEDGE_GRAPH_AI = TrendData(
    name="Knowledge Graph-driven AI Decision Making",
    description=(
        "Knowledge graphs combined with LLMs (GraphRAG) are enabling AI systems that "
        "reason over structured business knowledge, providing explainable and grounded "
        "AI outputs in enterprise contexts."
    ),
    source="MIT Sloan Management Review — AI and Knowledge Management, 2025",
    source_type="academic",
    publication_year=2025,
    impact_level="high",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "Reduces AI hallucinations in enterprise applications by 70-80%; "
        "enables explainable AI for regulated industries"
    ),
    technology_enablers=["Neo4j", "Graph embeddings", "LLMs", "Cypher", "Vector search"],
    related_standards=["ISO 42001", "NIST AI RMF", "TOGAF 10"],
    industry_applicability=["Financial Services", "Healthcare", "Government"],
    citations=["MIT Sloan 2025", "Microsoft Research GraphRAG 2024"],
    tags=["knowledge graph", "GraphRAG", "explainable AI", "Neo4j", "LLM"],
)

REAL_TIME_DATA = TrendData(
    name="Real-time Data Streaming and Event-driven Architecture",
    description=(
        "Organisations are replacing batch data pipelines with real-time event streaming "
        "architectures, enabling instant analytics, fraud detection, personalisation, "
        "and operational decision-making at millisecond latency."
    ),
    source="Gartner Magic Quadrant for Data Integration Tools, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="mainstream",
    time_horizon="<1yr",
    business_impact=(
        "Reduces fraud detection time from minutes to milliseconds; "
        "enables personalisation at the moment of customer interaction"
    ),
    technology_enablers=["Apache Kafka", "Apache Flink", "Confluent Platform", "Event-driven APIs"],
    related_standards=["DAMA-DMBOK2", "TMForum ODA"],
    adoption_rate="55% of large enterprises have deployed streaming platforms (Gartner 2024)",
    industry_applicability=["Banking", "Retail", "Telecom", "Healthcare"],
    citations=["Gartner 2024", "Confluent State of Data Streaming 2024"],
    tags=["streaming", "event-driven", "Kafka", "real-time", "data"],
)

# Banking / Finance trends
OPEN_BANKING = TrendData(
    name="Open Banking and Embedded Finance",
    description=(
        "Open Banking APIs are enabling financial services to be embedded into non-financial "
        "digital experiences (retail, healthcare, travel), creating new revenue streams and "
        "fundamentally reshaping financial services distribution."
    ),
    source="McKinsey Global Institute — The Next Frontier in Open Banking, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="transformational",
    maturity="growing",
    time_horizon="1-2yr",
    business_impact=(
        "Embedded finance market projected to reach $7.2 trillion by 2030; "
        "Open Banking reduces customer acquisition cost by 40% for digital-first banks"
    ),
    technology_enablers=["Open APIs", "PSD2 compliance", "API management platforms", "Microservices"],
    related_standards=["PSD2", "DORA", "ISO 27001"],
    adoption_rate="72% of banks have launched Open Banking APIs in Europe (McKinsey 2024)",
    industry_applicability=["Banking", "FinTech", "Insurance", "Retail"],
    citations=["McKinsey 2024", "EBA Open Banking Report 2024"],
    tags=["open banking", "embedded finance", "API", "PSD2", "BaaS"],
)

CBDC = TrendData(
    name="Central Bank Digital Currencies (CBDC) and Digital Assets",
    description=(
        "Over 130 central banks are exploring CBDCs, with wholesale and retail CBDC pilots "
        "accelerating. This requires banks to modernise core ledger systems and build "
        "programmable money capabilities."
    ),
    source="BIS — Central Bank Digital Currency Survey, 2024",
    source_type="regulatory",
    publication_year=2024,
    impact_level="transformational",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "Could reduce cross-border payment costs by 50%; "
        "requires significant core banking system modernisation investment"
    ),
    technology_enablers=["Distributed ledger technology", "Smart contracts", "Digital identity", "API-based ledgers"],
    related_standards=["Basel IV", "DORA", "ISO 20022"],
    industry_applicability=["Banking", "Payments", "Central Banks"],
    citations=["BIS 2024", "IMF Digital Money 2024", "ECB Digital Euro Progress 2024"],
    tags=["CBDC", "digital currency", "blockchain", "programmable money", "payments"],
)

# Healthcare trends
AI_CLINICAL_DECISION = TrendData(
    name="AI-Powered Clinical Decision Support",
    description=(
        "Machine learning models integrated into clinical workflows are providing real-time "
        "diagnostic support, treatment recommendations, and early warning systems, "
        "reducing diagnostic errors and improving patient outcomes."
    ),
    source="Gartner Hype Cycle for Healthcare, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="transformational",
    maturity="growing",
    time_horizon="1-2yr",
    business_impact=(
        "AI diagnostic tools reduce error rates by 30-40% in radiology and pathology; "
        "predictive readmission models cut 30-day readmissions by 25%"
    ),
    technology_enablers=["Computer vision", "NLP", "EHR integration", "FHIR APIs", "AMD GPU inference"],
    related_standards=["HL7 FHIR R4", "HIPAA", "ISO 42001", "FDA AI/ML Software guidance"],
    industry_applicability=["Healthcare", "Hospitals", "Clinical Labs"],
    citations=["Gartner 2024", "NEJM AI 2024", "FDA AI in Medical Devices 2024"],
    tags=["AI", "clinical", "diagnostics", "healthcare", "decision support"],
)

DIGITAL_TWIN_HEALTH = TrendData(
    name="Digital Twins for Healthcare Operations",
    description=(
        "Healthcare organisations are deploying digital twins of hospital operations, "
        "patient pathways, and supply chains to optimise resource allocation, "
        "predict demand, and simulate service redesign."
    ),
    source="Deloitte — Digital Twins in Healthcare, 2024",
    source_type="practitioner",
    publication_year=2024,
    impact_level="high",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "Hospital digital twins reduce bed waiting times by 15-25%; "
        "surgical scheduling optimisation improves theatre utilisation by 20%"
    ),
    technology_enablers=["IoT sensors", "Digital twin platforms", "AI simulation", "Real-time data feeds"],
    related_standards=["HL7 FHIR R4", "ISO 42001"],
    industry_applicability=["Healthcare", "Hospitals"],
    citations=["Deloitte 2024", "McKinsey Healthcare 2024"],
    tags=["digital twin", "healthcare", "operations", "simulation", "IoT"],
)

# Telecom trends
NETWORK_AS_A_SERVICE = TrendData(
    name="Network-as-a-Service and 5G Monetisation",
    description=(
        "Telcos are evolving from infrastructure providers to platform businesses, "
        "exposing 5G network capabilities as APIs for enterprise use cases including "
        "private networks, network slicing, and edge compute."
    ),
    source="TM Forum — Digital Transformation Survey, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="growing",
    time_horizon="2-5yr",
    business_impact=(
        "5G enterprise services projected to add $700B in telco revenue by 2030; "
        "NaaS reduces enterprise network TCO by 30-40%"
    ),
    technology_enablers=["5G standalone", "Network slicing", "Open APIs", "CAMARA", "TM Forum ODA"],
    related_standards=["TMForum ODA", "3GPP 5G SA", "ITIL 4"],
    industry_applicability=["Telecommunications", "Enterprise"],
    citations=["TM Forum 2024", "GSMA Intelligence 2024", "Analysys Mason 2024"],
    tags=["5G", "NaaS", "network slicing", "edge", "telco"],
)

AUTONOMOUS_NETWORK = TrendData(
    name="Autonomous Networks and AI-Ops for Telco",
    description=(
        "Telco operators are deploying AI-driven network operations that self-heal, "
        "self-optimise, and self-configure, reducing OPEX and improving network quality "
        "through ML-driven closed-loop automation."
    ),
    source="GSMA — Autonomous Network Maturity Index, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "AI-Ops reduces NOC operational costs by 30%; "
        "predictive maintenance reduces network outages by 40%"
    ),
    technology_enablers=["AIOps platforms", "5G RAN AI", "Digital twins", "Closed-loop automation"],
    related_standards=["TMForum ODA", "ETSI ZSM", "ITU-T Y.3172"],
    industry_applicability=["Telecommunications"],
    citations=["GSMA 2024", "TM Forum Autonomous Networks Report 2024"],
    tags=["autonomous networks", "AIOps", "telco", "automation", "5G"],
)

# Government / Public Sector trends
DIGITAL_PUBLIC_SERVICES = TrendData(
    name="Government Digital Service Transformation",
    description=(
        "Governments are accelerating digital public service delivery using citizen-centric "
        "design, digital identity, and data-sharing across agencies to reduce friction "
        "and increase inclusion in public services."
    ),
    source="WEF — Accelerating Digital Inclusion in the New Normal, 2024",
    source_type="government",
    publication_year=2024,
    impact_level="transformational",
    maturity="growing",
    time_horizon="2-5yr",
    business_impact=(
        "Digital government services reduce cost per transaction by 80-90% vs paper; "
        "citizen satisfaction scores improve 40% with digital-first services"
    ),
    technology_enablers=["Digital identity", "GovStack building blocks", "Open APIs", "Cloud", "AI assistants"],
    related_standards=["GovStack", "NIST SP 800-53", "ISO 27001"],
    industry_applicability=["Government", "Public Sector"],
    citations=["WEF 2024", "OECD Digital Government Review 2024", "UN E-Government Survey 2024"],
    tags=["digital government", "citizen services", "public sector", "digital identity"],
)

AI_REGULATION = TrendData(
    name="AI Regulation and Responsible AI Governance",
    description=(
        "The EU AI Act, US Executive Order on AI, and emerging global AI regulatory frameworks "
        "are requiring organisations to implement formal AI governance, risk management, "
        "and transparency practices."
    ),
    source="EU AI Act — Official Journal of the EU, 2024 + OECD AI Policy Observatory",
    source_type="regulatory",
    publication_year=2024,
    impact_level="transformational",
    maturity="growing",
    time_horizon="<1yr",
    business_impact=(
        "High-risk AI systems require conformity assessment before deployment; "
        "non-compliance fines up to €35M or 7% of global turnover under EU AI Act"
    ),
    technology_enablers=["AI model registries", "Explainability tools (SHAP, LIME)", "AI audit platforms"],
    related_standards=["ISO 42001", "NIST AI RMF", "EU AI Act", "GDPR"],
    adoption_rate="EU AI Act applies from August 2026; high-risk provisions from August 2027",
    industry_applicability=["All sectors"],
    citations=["EU AI Act 2024", "OECD 2024", "WEF AI Governance 2024"],
    tags=["AI regulation", "EU AI Act", "responsible AI", "governance", "compliance"],
)

# Supply Chain trends
SUPPLY_CHAIN_RESILIENCE = TrendData(
    name="Supply Chain Resilience and Digital Supply Networks",
    description=(
        "COVID-19 and geopolitical disruptions have accelerated investment in supply chain "
        "visibility platforms, digital supply networks, and AI-driven demand sensing to "
        "build resilient, agile supply chains."
    ),
    source="McKinsey — The resilient supply chain, 2024",
    source_type="industry_analyst",
    publication_year=2024,
    impact_level="high",
    maturity="growing",
    time_horizon="1-2yr",
    business_impact=(
        "Supply chain disruptions cost companies 45% of annual profits over 10 years (McKinsey); "
        "digital supply networks reduce inventory costs by 20-30%"
    ),
    technology_enablers=["Supply chain visibility platforms", "AI demand forecasting", "IoT tracking", "Blockchain provenance"],
    related_standards=["ISO 22000", "SCOR", "ISO 27001"],
    industry_applicability=["Manufacturing", "Retail", "Food", "Pharma"],
    citations=["McKinsey 2024", "Gartner Supply Chain Top 25 2024"],
    tags=["supply chain", "resilience", "visibility", "AI", "digital networks"],
)

# HR / Workforce trends
FUTURE_OF_WORK = TrendData(
    name="Future of Work — AI-Augmented Workforce",
    description=(
        "Generative AI is reshaping job roles, with knowledge workers using AI copilots "
        "for 30-50% of their task output. Organisations must redesign jobs, reskill workers, "
        "and implement human-AI collaboration frameworks."
    ),
    source="WEF Future of Jobs Report 2025",
    source_type="government",
    publication_year=2025,
    impact_level="transformational",
    maturity="growing",
    time_horizon="1-2yr",
    business_impact=(
        "85 million jobs displaced but 97 million new roles created by 2025 (WEF); "
        "AI copilots increase knowledge worker productivity by 20-40% (Microsoft 2024)"
    ),
    technology_enablers=["AI copilots (Microsoft 365 Copilot)", "LLMs", "HR analytics platforms", "Learning platforms"],
    related_standards=["ISO 30414", "ISO 42001"],
    adoption_rate="75% of large enterprises deploying AI copilot tools in 2025 (Gartner)",
    industry_applicability=["All sectors"],
    citations=["WEF 2025", "Microsoft Work Trend Index 2024", "BCG AI in the Workplace 2024"],
    tags=["future of work", "AI copilot", "workforce", "reskilling", "productivity"],
)

SKILLS_BASED_ORG = TrendData(
    name="Skills-based Organisation Design",
    description=(
        "Organisations are replacing role-based HR models with skills-based frameworks, "
        "matching work to skills dynamically, enabling internal talent mobility and "
        "personalised learning pathways."
    ),
    source="Deloitte 2024 Global Human Capital Trends",
    source_type="practitioner",
    publication_year=2024,
    impact_level="high",
    maturity="emerging",
    time_horizon="2-5yr",
    business_impact=(
        "Skills-based organisations are 107% more likely to place talent effectively; "
        "internal mobility reduces hiring costs by 50% (Deloitte 2024)"
    ),
    technology_enablers=["Skills taxonomies (LinkedIn, Lightcast)", "LXP learning platforms", "AI skills matching"],
    related_standards=["ISO 30414", "SHRM Competency Model"],
    industry_applicability=["All sectors"],
    citations=["Deloitte 2024", "WEF 2025", "LinkedIn Workplace Learning Report 2024"],
    tags=["skills", "talent", "workforce", "HR", "organisational design"],
)

# ---------------------------------------------------------------------------
# Domain → Trends mapping
# ---------------------------------------------------------------------------

TRENDS_BY_DOMAIN_PATTERN: dict[str, list[TrendData]] = {
    # Universal
    "_universal": [AGENTIC_AI, GENERATIVE_AI_ENTERPRISE, COMPOSABLE_ARCHITECTURE,
                   ZERO_TRUST_SECURITY, AI_REGULATION, SUSTAINABLE_IT],

    # Intelligence / Data / AI
    "intelligence": [AI_AUGMENTED_EA, KNOWLEDGE_GRAPH_AI, DATA_MESH, REAL_TIME_DATA, AGENTIC_AI],
    "data": [DATA_MESH, REAL_TIME_DATA, KNOWLEDGE_GRAPH_AI],
    "analytics": [AGENTIC_AI, KNOWLEDGE_GRAPH_AI, DATA_MESH],

    # Security
    "security": [ZERO_TRUST_SECURITY, AI_REGULATION],
    "cyber": [ZERO_TRUST_SECURITY],

    # Finance / Banking
    "banking": [OPEN_BANKING, CBDC, ZERO_TRUST_SECURITY, AI_REGULATION],
    "finance": [OPEN_BANKING, AI_REGULATION, ZERO_TRUST_SECURITY],
    "payment": [OPEN_BANKING, CBDC],
    "insurance": [AI_REGULATION, GENERATIVE_AI_ENTERPRISE, ZERO_TRUST_SECURITY],

    # Healthcare
    "health": [AI_CLINICAL_DECISION, DIGITAL_TWIN_HEALTH, AI_REGULATION],
    "clinical": [AI_CLINICAL_DECISION, DIGITAL_TWIN_HEALTH],
    "pharmaceutical": [SUPPLY_CHAIN_RESILIENCE, AI_REGULATION],

    # IT / Cloud
    "digital it": [PLATFORM_ENGINEERING, ZERO_TRUST_SECURITY, COMPOSABLE_ARCHITECTURE],
    "cloud": [PLATFORM_ENGINEERING, SUSTAINABLE_IT, ZERO_TRUST_SECURITY],

    # Telecom
    "telecom": [NETWORK_AS_A_SERVICE, AUTONOMOUS_NETWORK, AGENTIC_AI],
    "communications": [NETWORK_AS_A_SERVICE, COMPOSABLE_ARCHITECTURE],
    "regulatory (communications)": [AUTONOMOUS_NETWORK, AI_REGULATION],

    # Supply Chain / Food
    "food supply": [SUPPLY_CHAIN_RESILIENCE, SUSTAINABLE_IT],
    "supply": [SUPPLY_CHAIN_RESILIENCE],

    # Government
    "government": [DIGITAL_PUBLIC_SERVICES, AI_REGULATION, ZERO_TRUST_SECURITY],
    "regulatory": [AI_REGULATION, DIGITAL_PUBLIC_SERVICES],

    # HR / Workforce
    "human resources": [FUTURE_OF_WORK, SKILLS_BASED_ORG],
    "workforce": [FUTURE_OF_WORK, SKILLS_BASED_ORG],
    "hr": [FUTURE_OF_WORK, SKILLS_BASED_ORG],

    # Channels / Experience
    "channel": [GENERATIVE_AI_ENTERPRISE, COMPOSABLE_ARCHITECTURE, AGENTIC_AI],
    "experience": [AGENTIC_AI, GENERATIVE_AI_ENTERPRISE],

    # Backoffice
    "backoffice": [GENERATIVE_AI_ENTERPRISE, PLATFORM_ENGINEERING, AI_REGULATION],

    # Legal
    "legal": [AI_REGULATION, GENERATIVE_AI_ENTERPRISE, ZERO_TRUST_SECURITY],
}


def get_trends_for_domain(domain_name: str) -> list[TrendData]:
    """Return deduplicated trends list for a given domain name."""
    name_lower = domain_name.lower()
    seen_names: set[str] = set()
    result: list[TrendData] = []

    def add(t: TrendData):
        if t.name not in seen_names:
            seen_names.add(t.name)
            result.append(t)

    for t in TRENDS_BY_DOMAIN_PATTERN["_universal"]:
        add(t)

    for pattern, trends in TRENDS_BY_DOMAIN_PATTERN.items():
        if pattern == "_universal":
            continue
        if pattern in name_lower:
            for t in trends:
                add(t)

    return result[:5]  # Cap at 5 trends per domain for graph legibility
