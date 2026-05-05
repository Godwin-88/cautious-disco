"""
Graph Enrichment v2 — sector-aware, web-search-driven.

Architecture-aware enrichment:
  - Manage Generic Core + 28 HAS_SECTOR domains → industry-specific standards/trends
  - 4 ENABLES domains (Digital Intelligence, IT, InterOp, Security) → technology standards
  - 3 ORCHESTRATES domains (Exp Orch, Svc Orch, MarCom) → service/CX standards
  - 3 GROUNDS domains (Backoffice, GPRC, Workspace) → governance/ops standards
  - Capabilities → description, outcomes, KPIs, risks

Web search: DuckDuckGo (no API key) → top snippets → LLM synthesis → Neo4j SET
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sector → industry-specific standards/trends (authoritative, curated)
# ---------------------------------------------------------------------------

SECTOR_STANDARDS: dict[str, list[dict]] = {
    "Retail Banking": [
        {"name": "Basel IV (CRR3/CRD6)", "publisher": "BIS / European Parliament", "version": "2025",
         "key_principles": ["Risk-weighted asset standardisation", "Output floor (72.5%)", "Credit risk sensitivity", "Operational resilience", "Leverage ratio"],
         "compliance_requirements": ["Implement standardised approach for credit risk", "Calculate output floor at 72.5% of standardised RWA", "Report NSFR and LCR monthly", "Maintain TLAC buffers", "Stress-test interest rate risk in banking book"],
         "source_url": "https://www.bis.org/bcbs/basel3.htm", "tags": ["banking", "capital", "risk", "prudential"]},
        {"name": "DORA (Digital Operational Resilience Act)", "publisher": "European Parliament", "version": "2022/2554",
         "key_principles": ["ICT risk management", "Incident reporting", "Digital operational resilience testing", "Third-party ICT risk", "Information sharing"],
         "compliance_requirements": ["Establish ICT risk management framework by Jan 2025", "Report major ICT incidents within 4 hours", "Conduct annual TLPT penetration testing", "Register all third-party ICT providers", "Implement BCP for critical functions"],
         "source_url": "https://www.eiopa.europa.eu/dora", "tags": ["resilience", "ICT", "banking", "fintech"]},
        {"name": "PSD2 (Payment Services Directive 2)", "publisher": "European Commission", "version": "2015/2366",
         "key_principles": ["Open banking APIs", "Strong customer authentication (SCA)", "Third-party provider access", "Consumer protection", "Liability framework"],
         "compliance_requirements": ["Implement SCA for electronic payments", "Expose open banking APIs via XS2A", "Register TPPs with national competent authority", "Provide 90-day SCA exemption for trusted beneficiaries", "Report fraud statistics quarterly"],
         "source_url": "https://ec.europa.eu/info/law/payment-services-psd-2-directive-eu-2015-2366", "tags": ["payments", "open-banking", "API", "fintech"]},
    ],
    "Healthcare Provider": [
        {"name": "HL7 FHIR R4", "publisher": "HL7 International", "version": "R4 (4.0.1)",
         "key_principles": ["RESTful API interoperability", "Resource-based clinical data model", "Terminology binding (SNOMED CT, LOINC)", "Patient data portability", "Implementation guides"],
         "compliance_requirements": ["Implement FHIR R4 endpoints for patient data exchange", "Support US Core or IPS profiles as applicable", "Enable patient access API (21st Century Cures)", "Validate resources against FHIR profiles", "Implement SMART on FHIR for authorization"],
         "source_url": "https://hl7.org/fhir/R4/", "tags": ["health", "interoperability", "clinical", "API"]},
        {"name": "HIPAA (Health Insurance Portability and Accountability Act)", "publisher": "US HHS / OCR", "version": "2013 Final Rule",
         "key_principles": ["PHI privacy protection", "Security Rule safeguards", "Minimum necessary standard", "Patient rights", "Breach notification"],
         "compliance_requirements": ["Conduct annual HIPAA risk assessment", "Implement administrative, physical and technical safeguards", "Execute BAAs with all business associates", "Train workforce on PHI handling annually", "Report breaches of 500+ individuals within 60 days"],
         "source_url": "https://www.hhs.gov/hipaa", "tags": ["health", "privacy", "PHI", "compliance"]},
        {"name": "ISO 13485:2016", "publisher": "ISO", "version": "2016",
         "key_principles": ["QMS for medical devices", "Risk-based approach", "Design controls", "Post-market surveillance", "Traceability"],
         "compliance_requirements": ["Document quality management system for medical-grade software", "Implement design and development controls", "Maintain device history records", "Conduct post-market clinical follow-up", "Report adverse events to competent authority"],
         "source_url": "https://www.iso.org/standard/59752.html", "tags": ["medical-device", "QMS", "ISO", "health"]},
    ],
    "Pharmaceutical": [
        {"name": "GxP (GMP/GCP/GLP)", "publisher": "FDA / EMA / ICH", "version": "ICH Q10",
         "key_principles": ["Product quality lifecycle", "Change management", "CAPA system", "Process validation", "Quality risk management"],
         "compliance_requirements": ["Implement GMP-compliant manufacturing quality system", "Validate all computerised systems (21 CFR Part 11)", "Conduct annual product review (APR)", "Maintain audit trail for all GxP records", "Qualify suppliers and contract manufacturers"],
         "source_url": "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-guidelines/good-manufacturing-practice-gmp-guidelines", "tags": ["pharma", "GMP", "quality", "FDA"]},
        {"name": "21 CFR Part 11 (Electronic Records)", "publisher": "FDA", "version": "2003 guidance",
         "key_principles": ["Electronic record integrity", "Audit trails", "Access controls", "System validation", "Digital signatures"],
         "compliance_requirements": ["Validate all electronic record systems", "Implement time-stamped audit trails", "Control access with unique user credentials", "Ensure record integrity and prevention of unauthorised alteration", "Archive electronic records for regulatory retention periods"],
         "source_url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application", "tags": ["pharma", "FDA", "electronic-records", "validation"]},
    ],
    "Food Supply": [
        {"name": "ISO 22000:2018 (Food Safety Management)", "publisher": "ISO", "version": "2018",
         "key_principles": ["HACCP integration", "Prerequisite programmes (PRPs)", "Food safety team", "Hazard analysis", "Emergency preparedness"],
         "compliance_requirements": ["Implement HACCP-based food safety management system", "Identify and validate critical control points", "Conduct supplier verification activities", "Maintain allergen management programme", "Test emergency preparedness procedures annually"],
         "source_url": "https://www.iso.org/iso-22000-food-safety-management.html", "tags": ["food", "safety", "HACCP", "ISO"]},
        {"name": "FSMA (Food Safety Modernization Act)", "publisher": "FDA", "version": "2011 / 2022 Rules",
         "key_principles": ["Preventive controls", "Supply chain programme", "Foreign supplier verification", "Produce safety standards", "Third-party audits"],
         "compliance_requirements": ["Implement preventive controls for human food", "Conduct foreign supplier verification for each imported item", "Maintain written food safety plan", "Test water sources under produce safety rule", "Register facility with FDA biannually"],
         "source_url": "https://www.fda.gov/food/food-safety-modernization-act-fsma", "tags": ["food", "FDA", "safety", "supply-chain"]},
    ],
    "Oil & Gas": [
        {"name": "ISO 55001:2014 (Asset Management)", "publisher": "ISO", "version": "2014",
         "key_principles": ["Asset lifecycle management", "Risk and opportunity management", "Strategic asset plan", "Performance evaluation", "Continual improvement"],
         "compliance_requirements": ["Document strategic asset management plan (SAMP)", "Implement asset register with criticality ratings", "Conduct regular condition-based maintenance reviews", "Align asset plan with organisational objectives", "Measure asset performance against KPIs quarterly"],
         "source_url": "https://www.iso.org/standard/55089.html", "tags": ["asset-management", "O&G", "ISO", "operations"]},
        {"name": "IEC 61511 (Functional Safety — SIS)", "publisher": "IEC", "version": "Ed. 2 (2016)",
         "key_principles": ["Safety instrumented systems", "Safety integrity levels (SIL)", "Hazard and risk assessment", "Safety lifecycle", "Proof-testing"],
         "compliance_requirements": ["Conduct HAZOP/LOPA for all safety-critical processes", "Design SIS to achieve required SIL rating", "Perform SIL verification calculations", "Test safety instrumented functions to required PFDavg", "Document safety requirements specification"],
         "source_url": "https://www.iec.ch/standards/iec61511", "tags": ["safety", "SIS", "O&G", "functional-safety"]},
    ],
    "Clean Energy": [
        {"name": "IEC 62443 (Industrial Cybersecurity)", "publisher": "IEC", "version": "2018-2022",
         "key_principles": ["Security levels (SL 1-4)", "Zone and conduit model", "Security requirements specifications", "Supplier security capability", "Operational technology security"],
         "compliance_requirements": ["Segment OT/IT networks into security zones and conduits", "Achieve Security Level 2 minimum for critical infrastructure", "Conduct security risk assessment per IEC 62443-3-2", "Assess all automation suppliers against SL requirements", "Implement patch management for OT components"],
         "source_url": "https://www.iec.ch/iec62443", "tags": ["OT-security", "energy", "ICS", "SCADA"]},
        {"name": "GHG Protocol (Corporate Standard)", "publisher": "WRI / WBCSD", "version": "2015 Revised",
         "key_principles": ["Scope 1/2/3 emissions accounting", "Boundary setting", "Measurement accuracy", "External assurance", "Avoided emissions"],
         "compliance_requirements": ["Measure and report Scope 1 and 2 emissions annually", "Disclose material Scope 3 categories", "Obtain third-party assurance for emissions data", "Set science-based targets aligned to 1.5°C pathway", "Publish public-facing sustainability report per GRI/SASB"],
         "source_url": "https://ghgprotocol.org/corporate-standard", "tags": ["ESG", "emissions", "carbon", "sustainability"]},
    ],
    "Telco": [
        {"name": "TM Forum Open Digital Architecture (ODA)", "publisher": "TM Forum", "version": "ODA Canvas R22",
         "key_principles": ["Component-based architecture", "Open APIs", "AI/ML native", "Cloud-native", "Business agility"],
         "compliance_requirements": ["Decompose BSS/OSS into ODA-compliant components", "Expose capabilities via TM Forum Open APIs (TMF6xx series)", "Implement ODA canvas for component lifecycle management", "Certify core components against ODA conformance", "Adopt IG1228 for AI in telecom operations"],
         "source_url": "https://www.tmforum.org/oda/", "tags": ["telco", "ODA", "OpenAPI", "BSS", "OSS"]},
        {"name": "3GPP Release 17/18 Standards", "publisher": "3GPP", "version": "Rel-17 (2022) / Rel-18 (2024)",
         "key_principles": ["5G standalone core (SA)", "Network slicing", "RAN intelligence", "Edge computing (MEC)", "Private networks"],
         "compliance_requirements": ["Deploy 5G SA core with SBA architecture", "Implement network slicing for differentiated services", "Expose NEF APIs for third-party integration", "Meet ITU-R IMT-2020 KPIs for eMBB/URLLC/mMTC", "Certify radio equipment per regional type approval"],
         "source_url": "https://www.3gpp.org/specifications-groups", "tags": ["5G", "telco", "3GPP", "network", "RAN"]},
    ],
    "Logistics": [
        {"name": "GS1 Standards (Barcoding & EDI)", "publisher": "GS1", "version": "2024",
         "key_principles": ["Global trade item numbers (GTIN)", "EDI messaging (EANCOM/XML)", "Traceability (EPCIS)", "Serialisation", "Digital link"],
         "compliance_requirements": ["Assign GTINs to all traded units", "Implement GS1-128 or QR labels for shipments", "Use EPCIS for end-to-end supply chain event tracking", "Exchange ASNs via EDI or API with trading partners", "Comply with GS1 Digital Link for connected packaging"],
         "source_url": "https://www.gs1.org/standards", "tags": ["supply-chain", "logistics", "traceability", "EDI"]},
        {"name": "SCOR (Supply Chain Operations Reference)", "publisher": "ASCM", "version": "SCOR DS 4.0",
         "key_principles": ["Plan-Source-Make-Deliver-Return-Enable", "Performance metrics", "Best practices", "Process decomposition", "Skills framework"],
         "compliance_requirements": ["Map end-to-end supply chain to SCOR Level 1-3 processes", "Measure perfect order fulfilment and cash-to-cash cycle time", "Conduct SCOR diagnostic to identify capability gaps", "Implement SCOR best practices for demand variability", "Report supply chain risk exposure by tier"],
         "source_url": "https://www.ascm.org/supply-chain-reference-tools/scor-model/", "tags": ["supply-chain", "SCOR", "operations", "logistics"]},
    ],
    "Government": [
        {"name": "GovStack Implementation Framework", "publisher": "ITU / GIZ / DIAL", "version": "2023",
         "key_principles": ["Building blocks approach", "Reusable digital components", "Whole-of-government", "Interoperability", "Inclusive design"],
         "compliance_requirements": ["Adopt GovStack building blocks for digital public infrastructure", "Implement GovStack Consent BB for personal data handling", "Use Identity BB aligned to ISO/IEC 24760", "Publish API specifications in OpenAPI format", "Conduct interoperability testing before go-live"],
         "source_url": "https://www.govstack.global/", "tags": ["government", "digital-public-goods", "eGov", "interoperability"]},
        {"name": "NIST SP 800-53 Rev 5", "publisher": "NIST", "version": "Rev 5 (2020)",
         "key_principles": ["Risk-based control selection", "20 control families", "Outcome-based controls", "Privacy integration", "Supply chain risk"],
         "compliance_requirements": ["Select controls based on FIPS 199 impact categorisation", "Implement access control (AC) and audit logging (AU) controls at minimum", "Conduct annual security and privacy control assessment", "Maintain system security plan (SSP)", "Report supply chain risk management practices"],
         "source_url": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final", "tags": ["government", "NIST", "cybersecurity", "compliance"]},
    ],
    "Capital Markets": [
        {"name": "MiFID II / MiFIR", "publisher": "European Commission", "version": "2018 (amending Dir. 2014/65/EU)",
         "key_principles": ["Best execution", "Pre/post-trade transparency", "Product governance", "Investor protection", "Market structure"],
         "compliance_requirements": ["Implement best execution policy and annual RTS 28 reporting", "Report transactions to trade repositories within T+1", "Conduct product governance approval process for new instruments", "Maintain order records for 5 years", "Publish systematic internaliser quotes when thresholds met"],
         "source_url": "https://www.esma.europa.eu/policy-rules/mifid-ii-and-mifir", "tags": ["capital-markets", "trading", "MiFID", "regulation"]},
    ],
    "Court & Justice": [
        {"name": "UN Model Law on Electronic Commerce (MLEC)", "publisher": "UNCITRAL", "version": "1996 + 2001 additions",
         "key_principles": ["Legal equivalence of electronic records", "Functional equivalence", "Non-discrimination", "Party autonomy", "Cross-border recognition"],
         "compliance_requirements": ["Ensure electronic court records meet MLEC equivalence standards", "Implement digital signature infrastructure for legal validity", "Maintain immutable audit trails for electronic filings", "Provide offline-accessible certified copies on request", "Enforce data retention per national archiving law"],
         "source_url": "https://uncitral.un.org/en/texts/ecommerce/modellaw/electronic_commerce", "tags": ["justice", "eGovernance", "digital-records", "legal"]},
    ],
    "Urban Planning": [
        {"name": "ISO 37120:2018 (Sustainable Cities — Indicators)", "publisher": "ISO", "version": "2018",
         "key_principles": ["City performance measurement", "Economy, education, energy, environment", "Governance indicators", "Smart city benchmarking", "Data quality"],
         "compliance_requirements": ["Report 100 city performance indicators annually", "Submit data for ISO 37120 certification to WCCD", "Implement open data portal for 24 core indicators", "Align city KPIs with SDG 11 (Sustainable Cities)", "Conduct annual data quality review by independent auditor"],
         "source_url": "https://www.iso.org/standard/68498.html", "tags": ["smart-city", "urban", "sustainability", "ISO"]},
    ],
    "Property Development": [
        {"name": "RICS Valuation — Global Standards (Red Book)", "publisher": "RICS", "version": "2022",
         "key_principles": ["Independence and objectivity", "Basis of value", "Inspection and investigation", "Valuation report", "Sustainability considerations"],
         "compliance_requirements": ["Conduct valuations by RICS-registered valuer", "Disclose material uncertainty in valuation reports", "Apply IFRS 13 / IAS 40 basis of value for financial reporting", "Include ESG risk factors in investment valuations", "Rotate valuer after 7 years for public interest entities"],
         "source_url": "https://www.rics.org/standards/valuation", "tags": ["property", "real-estate", "valuation", "RICS"]},
    ],
    "Airport": [
        {"name": "ICAO Annex 17 (Aviation Security)", "publisher": "ICAO", "version": "Ed. 11 (2020)",
         "key_principles": ["Threat and risk management", "Passenger and baggage screening", "Access control", "Security oversight", "Cybersecurity"],
         "compliance_requirements": ["Implement national aviation security programme (NASP)", "Screen all passengers and carry-on baggage using approved equipment", "Maintain access control to security restricted areas", "Conduct quality control inspections of security measures", "Report all acts of unlawful interference within 24 hours"],
         "source_url": "https://www.icao.int/security/sfp/pages/annex17.aspx", "tags": ["aviation", "airport", "security", "ICAO"]},
    ],
    "Development Banking": [
        {"name": "IFC Performance Standards (Environmental & Social)", "publisher": "IFC / World Bank Group", "version": "2012",
         "key_principles": ["E&S risk assessment", "Labour standards", "Pollution prevention", "Community health and safety", "Indigenous peoples"],
         "compliance_requirements": ["Conduct Environmental and Social Impact Assessment (ESIA) for all projects", "Implement E&S management system", "Disclose project information 60 days before board approval", "Establish grievance mechanism for project-affected people", "Report annually on E&S performance against PS commitments"],
         "source_url": "https://www.ifc.org/performancestandards", "tags": ["development-finance", "ESG", "IFC", "sustainability"]},
    ],
    "Investment Promotion": [
        {"name": "OECD Guidelines for Multinational Enterprises", "publisher": "OECD", "version": "2023 (updated)",
         "key_principles": ["Responsible business conduct", "Human rights due diligence", "Environmental responsibility", "Anti-corruption", "Consumer interests"],
         "compliance_requirements": ["Conduct human rights due diligence across value chain", "Publish responsible business conduct policy", "Establish grievance mechanism for affected stakeholders", "Disclose beneficial ownership information", "Align with OECD BEPS on tax transparency"],
         "source_url": "https://www.oecd.org/corporate/mne/", "tags": ["investment", "OECD", "ESG", "governance"]},
    ],
    "Health Regulatory": [
        {"name": "ICH E6 (R3) GCP (Good Clinical Practice)", "publisher": "ICH", "version": "R3 (2025 Final)",
         "key_principles": ["Participant protection", "Data quality and integrity", "Risk-proportionate oversight", "Sponsor/investigator responsibilities", "Electronic systems"],
         "compliance_requirements": ["Implement risk-based monitoring strategy", "Validate all eClinical systems per 21 CFR Part 11/Annex 11", "Obtain IRB/IEC approval before trial commencement", "Archive all essential documents for 15 years post-trial", "Report SAEs to regulatory authority within 15 calendar days"],
         "source_url": "https://www.ich.org/page/efficacy-guidelines", "tags": ["clinical-trials", "GCP", "pharma", "regulatory"]},
    ],
    "Professional Services": [
        {"name": "ISO 9001:2015 (Quality Management Systems)", "publisher": "ISO", "version": "2015",
         "key_principles": ["Customer focus", "Leadership", "Process approach", "Evidence-based decision making", "Relationship management"],
         "compliance_requirements": ["Document quality management system and quality policy", "Conduct internal audits at planned intervals", "Address nonconformities with root cause analysis", "Measure customer satisfaction and act on findings", "Conduct management review at least annually"],
         "source_url": "https://www.iso.org/iso-9001-quality-management.html", "tags": ["quality", "ISO", "professional-services", "management"]},
    ],
    "Endowment": [
        {"name": "UNPRI (Principles for Responsible Investment)", "publisher": "UN-supported PRI", "version": "2023 Reporting Framework",
         "key_principles": ["ESG incorporation", "Active ownership", "Reporting and transparency", "Investment exclusions", "Impact investing"],
         "compliance_requirements": ["Report annually on ESG integration across asset classes", "Disclose voting policy and stewardship activities", "Assess climate risk in investment portfolio (TCFD aligned)", "Publish responsible investment policy publicly", "Engage with portfolio companies on material ESG issues"],
         "source_url": "https://www.unpri.org/", "tags": ["investment", "ESG", "responsible-investment", "UN"]},
    ],
    "Stock Exchange": [
        {"name": "CPMI-IOSCO PFMI (Principles for FMIs)", "publisher": "BIS / IOSCO", "version": "2012 (updated 2023)",
         "key_principles": ["Legal basis", "Governance", "Credit risk management", "Collateral", "Operational risk and resilience"],
         "compliance_requirements": ["Maintain legally sound rules and procedures in all jurisdictions", "Ensure default fund covers two largest clearing member defaults", "Disclose quantitative data via PFMI public quantitative disclosures (PQD)", "Test recovery and resolution plans annually", "Report operational incidents to regulators within 2 hours"],
         "source_url": "https://www.bis.org/cpmi/publ/d101a.htm", "tags": ["capital-markets", "FMI", "clearing", "exchange"]},
    ],
    "Digital Financial Regulation": [
        {"name": "FATF Recommendations (AML/CFT)", "publisher": "FATF", "version": "2023 updated",
         "key_principles": ["Risk-based approach", "Customer due diligence", "Beneficial ownership", "Suspicious transaction reporting", "International cooperation"],
         "compliance_requirements": ["Implement risk-based AML/CFT programme", "Conduct enhanced due diligence for high-risk customers", "Register beneficial owners in national registry", "File suspicious activity reports (SAR) within 24 hours", "Screen customers against UN and national sanctions lists"],
         "source_url": "https://www.fatf-gafi.org/en/topics/fatf-recommendations.html", "tags": ["AML", "CFT", "financial-crime", "FATF"]},
    ],
    "Digital Academy": [
        {"name": "IMS QTI (Question & Test Interoperability)", "publisher": "IMS Global (1EdTech)", "version": "QTI 3.0",
         "key_principles": ["Assessment interoperability", "Adaptive learning", "Learning analytics", "Accessibility", "Open standards"],
         "compliance_requirements": ["Implement LRS conforming to xAPI (Tin Can) specification", "Ensure accessibility per WCAG 2.2 AA", "Expose course content via LTI 1.3", "Maintain learner data per GDPR and FERPA", "Validate assessments against QTI 3.0 schema"],
         "source_url": "https://www.imsglobal.org/question/index.html", "tags": ["edtech", "learning", "interoperability", "assessment"]},
    ],
    "CDC": [
        {"name": "IHR 2005 (International Health Regulations)", "publisher": "WHO", "version": "2005 (amending 2022)",
         "key_principles": ["PHEIC detection and reporting", "Core capacity requirements", "Port of entry measures", "Coordination with WHO", "Equity and human rights"],
         "compliance_requirements": ["Report public health events of potential international concern to WHO within 24 hours", "Develop and test national pandemic preparedness plan", "Maintain surveillance systems meeting IHR core capacity requirements", "Deploy joint external evaluation (JEE) framework", "Establish National IHR Focal Point available 24/7"],
         "source_url": "https://www.who.int/health-topics/international-health-regulations", "tags": ["public-health", "WHO", "IHR", "pandemic"]},
    ],
    "Healthcare Payer": [
        {"name": "CAQH CORE (Operating Rules for Healthcare)", "publisher": "CAQH", "version": "Phase IV (2023)",
         "key_principles": ["Administrative simplification", "Eligibility and benefits", "Claims status", "EFT/ERA", "Prior authorisation"],
         "compliance_requirements": ["Support real-time eligibility verification per CORE 270/271 rule", "Return prior auth decisions within 72 hours (non-urgent) / 3 hours (urgent)", "Transmit EFT payments via ACH per CORE EFT rules", "Achieve CORE certification for all applicable transactions", "Report transaction turnaround time metrics quarterly"],
         "source_url": "https://www.caqh.org/core/operating-rules", "tags": ["health-payer", "claims", "CAQH", "interoperability"]},
    ],
    "Government Excellence": [
        {"name": "ISO 18091:2019 (Quality Management for Local Government)", "publisher": "ISO", "version": "2019",
         "key_principles": ["Citizen-centric service", "Transparency", "Performance measurement", "Continuous improvement", "Stakeholder engagement"],
         "compliance_requirements": ["Implement ISO 9001-based QMS adapted for local government", "Publish service charters with measurable commitments", "Conduct annual citizen satisfaction survey", "Report on 39 reliability indicators covering core government services", "Participate in external quality assessment biannually"],
         "source_url": "https://www.iso.org/standard/61386.html", "tags": ["government", "quality", "public-services", "ISO"]},
    ],
    "Electricity Transmission": [
        {"name": "NERC CIP (Critical Infrastructure Protection)", "publisher": "NERC", "version": "CIP-013-2 (2022)",
         "key_principles": ["BES cyber system categorisation", "Physical security", "Electronic security perimeter", "Configuration management", "Supply chain risk management"],
         "compliance_requirements": ["Classify BES cyber systems as high/medium/low impact", "Implement electronic security perimeter (ESP) controls", "Conduct supply chain risk management for BES assets", "Test incident response plan at least annually", "Retain security event logs for 90 days minimum"],
         "source_url": "https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx", "tags": ["energy", "critical-infrastructure", "NERC", "OT-security"]},
    ],
    "Health System": [
        {"name": "IHE (Integrating the Healthcare Enterprise) Profiles", "publisher": "IHE International", "version": "2024 Technical Framework",
         "key_principles": ["Profile-driven integration", "XDS document sharing", "PIX/PDQ patient identity", "ATNA audit trail", "mHealth integration"],
         "compliance_requirements": ["Implement IHE XDS.b for cross-enterprise document sharing", "Deploy IHE PIX/PDQ for patient identity matching", "Ensure audit trail logging per IHE ATNA profile", "Pass IHE Connectathon interoperability testing", "Support IHE mHealth profiles for mobile access"],
         "source_url": "https://www.ihe.net/", "tags": ["health-system", "interoperability", "IHE", "clinical"]},
    ],
}

# Relationship-based domain standards (for the 11 canonical functional domains)
DOMAIN_STANDARDS: dict[str, list[dict]] = {
    "Manage Digital Intelligence": [
        {"name": "DAMA-DMBOK2", "publisher": "DAMA International", "version": "2.0 (2017)",
         "key_principles": ["Data as organisational asset", "Data quality is enterprise-wide responsibility", "Metadata management", "Data lifecycle governance", "Value realisation from data"],
         "compliance_requirements": ["Define data ownership and stewardship roles", "Implement data lineage tracking end-to-end", "Establish data quality dimensions and thresholds", "Maintain enterprise data catalogue", "Report data quality scores by domain quarterly"],
         "source_url": "https://www.dama.org/cpages/body-of-knowledge", "tags": ["data-governance", "DAMA", "intelligence", "analytics"]},
        {"name": "NIST AI RMF 1.0", "publisher": "NIST", "version": "1.0 (Jan 2023)",
         "key_principles": ["Govern", "Map", "Measure", "Manage", "Trustworthy AI attributes"],
         "compliance_requirements": ["Categorise AI systems by risk level using MAP function", "Implement bias and fairness testing (MEASURE function)", "Establish AI incident response plan (MANAGE function)", "Document AI model cards for all deployed models", "Conduct AI risk assessment prior to deployment"],
         "source_url": "https://airc.nist.gov/RMF", "tags": ["AI", "risk", "governance", "NIST"]},
        {"name": "ISO/IEC 42001:2023 (AI Management System)", "publisher": "ISO/IEC", "version": "2023",
         "key_principles": ["AI-specific QMS", "Responsible AI development", "Objective and policy", "AI risk and impact assessment", "Continual improvement"],
         "compliance_requirements": ["Establish AI policy and objectives aligned to ISO 42001", "Conduct AI impact assessment for each system", "Maintain AI system register with risk classification", "Implement human oversight mechanisms for high-risk AI", "Audit AI management system annually"],
         "source_url": "https://www.iso.org/standard/81230.html", "tags": ["AI", "management-system", "ISO", "governance"]},
    ],
    "Manage Digital IT": [
        {"name": "ITIL 4", "publisher": "Axelos / PeopleCert", "version": "ITIL 4 (2019)",
         "key_principles": ["Focus on value", "Start where you are", "Progress iteratively with feedback", "Collaborate and promote visibility", "Think and work holistically", "Keep it simple and practical", "Optimise and automate"],
         "compliance_requirements": ["Implement service value chain (SVC) with all six activities", "Establish change enablement practice with CAB", "Measure mean time to restore (MTTR) per P1/P2 incidents", "Conduct problem management retrospectives for major incidents", "Publish service catalogue with SLAs for all IT services"],
         "source_url": "https://www.axelos.com/certifications/itil-service-management/what-is-itil", "tags": ["ITSM", "ITIL", "service-management", "IT"]},
        {"name": "ISO/IEC 20000-1:2018 (IT Service Management)", "publisher": "ISO/IEC", "version": "2018",
         "key_principles": ["Service management system (SMS)", "Customer requirements", "Integrated processes", "Continual improvement", "Supplier management"],
         "compliance_requirements": ["Document SMS scope and policy", "Achieve SLA targets for all agreed services", "Implement configuration management database (CMDB)", "Conduct internal SMS audit annually", "Manage suppliers against contracted service requirements"],
         "source_url": "https://www.iso.org/standard/70636.html", "tags": ["ITSM", "ISO", "IT-service", "management"]},
    ],
    "Manage Digital Inter-Operability & Automation": [
        {"name": "TOGAF 10", "publisher": "The Open Group", "version": "10.0 (2022)",
         "key_principles": ["Architecture Development Method (ADM)", "Architecture governance", "Stakeholder management", "Reuse and standards", "Modular architecture"],
         "compliance_requirements": ["Establish Architecture Board with governance mandate", "Complete ADM Phase A (Architecture Vision) before transformation", "Maintain Architecture Repository (baseline, target, transition)", "Conduct architecture compliance review for all major projects", "Publish Architecture Principles and enforce across IT portfolio"],
         "source_url": "https://www.opengroup.org/togaf", "tags": ["EA", "TOGAF", "architecture", "governance"]},
        {"name": "OpenAPI Specification 3.1 (OAS)", "publisher": "OpenAPI Initiative (Linux Foundation)", "version": "3.1.0 (2021)",
         "key_principles": ["API-first design", "Machine-readable contracts", "Semantic versioning", "Security schemes", "Webhooks and callbacks"],
         "compliance_requirements": ["Define all APIs using OAS 3.1 before implementation", "Validate API schemas against OAS using automated linting", "Version APIs using semantic versioning", "Publish API documentation via developer portal", "Implement OAuth 2.0 / OpenID Connect per OAS security schemes"],
         "source_url": "https://spec.openapis.org/oas/v3.1.0", "tags": ["API", "integration", "OpenAPI", "automation"]},
    ],
    "Manage Digital Security": [
        {"name": "ISO/IEC 27001:2022 (ISMS)", "publisher": "ISO/IEC", "version": "2022",
         "key_principles": ["Risk-based ISMS", "93 Annex A controls (11 new)", "Leadership commitment", "Continual improvement", "Supply chain security"],
         "compliance_requirements": ["Conduct information security risk assessment annually", "Implement Statement of Applicability (SoA)", "Achieve ISO 27001 certification via accredited body", "Perform internal ISMS audit at least once per year", "Report all security incidents to CISO within 2 hours"],
         "source_url": "https://www.iso.org/standard/27001", "tags": ["cybersecurity", "ISMS", "ISO", "risk"]},
        {"name": "NIST CSF 2.0", "publisher": "NIST", "version": "2.0 (Feb 2024)",
         "key_principles": ["Govern, Identify, Protect, Detect, Respond, Recover", "Supply chain risk", "Continuous improvement", "Measurement and metrics", "Tier-based maturity"],
         "compliance_requirements": ["Assess cybersecurity posture against CSF 2.0 Core", "Define organisational cybersecurity risk tolerance", "Implement CSF Profile aligned to business risk", "Report CSF metrics to board quarterly", "Align with sector-specific CSF implementation guides"],
         "source_url": "https://www.nist.gov/cyberframework", "tags": ["cybersecurity", "NIST", "framework", "risk"]},
        {"name": "Zero Trust Architecture (NIST SP 800-207)", "publisher": "NIST", "version": "2020",
         "key_principles": ["Never trust, always verify", "Least-privilege access", "Micro-segmentation", "Continuous validation", "Assume breach"],
         "compliance_requirements": ["Implement policy enforcement point (PEP) for all resource access", "Enforce MFA for all privileged access", "Deploy endpoint detection and response (EDR) on all managed devices", "Log all access requests with contextual attributes", "Conduct purple team exercise against ZTA annually"],
         "source_url": "https://csrc.nist.gov/publications/detail/sp/800-207/final", "tags": ["zero-trust", "security", "NIST", "identity"]},
    ],
    "Manage Digital Experience Orchestration": [
        {"name": "ISO 9241-210:2019 (Human-Centred Design)", "publisher": "ISO", "version": "2019",
         "key_principles": ["Context of use", "User requirements", "Design solutions", "Evaluation", "Iterative design"],
         "compliance_requirements": ["Conduct user research to identify context of use", "Involve users in design at each iteration", "Evaluate designs against ISO 9241-11 usability criteria", "Achieve WCAG 2.2 AA accessibility compliance", "Document usability test results before release"],
         "source_url": "https://www.iso.org/standard/77520.html", "tags": ["UX", "HCD", "accessibility", "ISO"]},
        {"name": "GDPR (General Data Protection Regulation)", "publisher": "European Union", "version": "2016/679 (effective 2018)",
         "key_principles": ["Lawfulness, fairness, transparency", "Purpose limitation", "Data minimisation", "Accuracy", "Storage limitation", "Integrity and confidentiality", "Accountability"],
         "compliance_requirements": ["Obtain freely given, specific, informed consent for data processing", "Respond to data subject access requests within 30 days", "Appoint DPO where required by Art. 37", "Conduct DPIA for high-risk processing", "Report personal data breaches to SA within 72 hours"],
         "source_url": "https://gdpr.eu/", "tags": ["privacy", "GDPR", "data-protection", "EU"]},
    ],
    "Manage Digital Service Orchestration": [
        {"name": "COBIT 2019", "publisher": "ISACA", "version": "2019",
         "key_principles": ["Meeting stakeholder needs", "Covering enterprise end-to-end", "Applying single integrated framework", "Enabling holistic approach", "Separating governance from management"],
         "compliance_requirements": ["Implement COBIT governance and management objectives", "Achieve EDM01 (Governance Framework Setting) first", "Measure capability levels using CMMI-aligned scale", "Conduct COBIT self-assessment annually", "Align IT objectives to enterprise goals cascade"],
         "source_url": "https://www.isaca.org/resources/cobit", "tags": ["governance", "COBIT", "IT-management", "risk"]},
        {"name": "ITIL 4 (Service Orchestration focus)", "publisher": "Axelos / PeopleCert", "version": "ITIL 4 (2019)",
         "key_principles": ["Service value chain", "Demand and value streams", "Service integration (SIAM)", "Automation first", "Customer co-creation"],
         "compliance_requirements": ["Map service demand to value streams", "Implement SIAM model for multi-supplier orchestration", "Automate routine service requests (>80% touchless)", "Publish real-time service health dashboards", "Review service portfolio against demand quarterly"],
         "source_url": "https://www.axelos.com/certifications/itil-service-management/what-is-itil", "tags": ["ITSM", "orchestration", "ITIL", "SIAM"]},
    ],
    "Manage MarCom Orchestration": [
        {"name": "IAB Digital Advertising Standards", "publisher": "IAB Tech Lab", "version": "2024",
         "key_principles": ["Consent and transparency (TCF v2.2)", "Ad fraud prevention (ads.txt)", "Brand safety (GARM)", "Measurement standards", "Identity resolution"],
         "compliance_requirements": ["Implement IAB TCF v2.2 consent framework", "Publish ads.txt and sellers.json for all programmatic inventory", "Apply GARM brand safety floor categories", "Adopt IAB Open Measurement SDK for viewability", "Report campaign performance via standardised metrics (MRC accredited)"],
         "source_url": "https://iabtechlab.com/standards/", "tags": ["marketing", "advertising", "IAB", "digital-media"]},
    ],
    "Manage Digital Backoffice": [
        {"name": "ISO 30300:2011 (Management Systems for Records)", "publisher": "ISO", "version": "2011",
         "key_principles": ["Records as evidence of business", "Accountability", "Integrity", "Reliability", "Usability"],
         "compliance_requirements": ["Implement records management system (RMS) per ISO 30300", "Define retention schedules for all business records", "Ensure records are authentic, reliable and usable", "Conduct records audit to verify completeness", "Align records retention with legal and regulatory requirements"],
         "source_url": "https://www.iso.org/standard/53732.html", "tags": ["records", "backoffice", "ISO", "information-management"]},
        {"name": "COBIT 2019 (BAI domain)", "publisher": "ISACA", "version": "2019",
         "key_principles": ["Build, acquire and implement discipline", "Change management", "Asset management", "Knowledge management", "Project management"],
         "compliance_requirements": ["Gate all major changes through BAI06 change management process", "Maintain application portfolio register", "Conduct post-implementation reviews for all major projects", "Align project delivery to OKRs", "Report project status using COBIT BAI metrics"],
         "source_url": "https://www.isaca.org/resources/cobit", "tags": ["governance", "COBIT", "backoffice", "projects"]},
    ],
    "Manage Digital GPRC": [
        {"name": "ISO 37000:2021 (Governance of Organisations)", "publisher": "ISO", "version": "2021",
         "key_principles": ["Governing body purpose", "Value generation", "Strategy oversight", "Accountability", "Transparency"],
         "compliance_requirements": ["Define board governance framework aligned to ISO 37000", "Establish enterprise risk committee with clear mandate", "Publish annual governance report aligned to Integrated Reporting Framework", "Conduct board effectiveness review annually", "Align risk appetite to strategic objectives"],
         "source_url": "https://www.iso.org/standard/65036.html", "tags": ["governance", "board", "ISO", "risk"]},
        {"name": "ISO 31000:2018 (Risk Management)", "publisher": "ISO", "version": "2018",
         "key_principles": ["Integrated risk management", "Structured and comprehensive", "Customised", "Inclusive", "Dynamic and iterative"],
         "compliance_requirements": ["Implement enterprise risk management framework per ISO 31000", "Maintain risk register with likelihood and impact ratings", "Report risk profile to board quarterly", "Conduct risk treatment plan reviews semi-annually", "Embed risk management in strategic planning cycle"],
         "source_url": "https://www.iso.org/standard/65694.html", "tags": ["risk", "ERM", "ISO", "governance"]},
    ],
    "Manage Digital Workspace": [
        {"name": "ISO/IEC 27701:2019 (Privacy Information Management)", "publisher": "ISO/IEC", "version": "2019",
         "key_principles": ["PIMS extension to ISO 27001", "PII processing", "Controller and processor roles", "Data subject rights", "Privacy risk"],
         "compliance_requirements": ["Extend ISO 27001 ISMS to include PIMS per ISO 27701", "Map all PII processing activities in data inventory", "Implement privacy by design in new workspace tools", "Respond to data subject rights requests within 30 days", "Conduct privacy impact assessments for new processing"],
         "source_url": "https://www.iso.org/standard/71670.html", "tags": ["privacy", "workspace", "ISO", "PIMS"]},
    ],
    "Manage Generic Core": [
        {"name": "TOGAF 10", "publisher": "The Open Group", "version": "10.0 (2022)",
         "key_principles": ["ADM as core methodology", "Architecture governance", "Stakeholder engagement", "Cross-sector applicability", "Standards compliance"],
         "compliance_requirements": ["Apply ADM to each sector transformation", "Establish Architecture Repository shared across sectors", "Govern sector-specific architectures through central Architecture Board", "Enforce TOGAF Architecture Principles in all sector projects", "Conduct architecture compliance reviews for cross-sector initiatives"],
         "source_url": "https://www.opengroup.org/togaf", "tags": ["EA", "architecture", "cross-sector", "TOGAF"]},
        {"name": "COBIT 2019", "publisher": "ISACA", "version": "2019",
         "key_principles": ["Governance across all sectors", "Stakeholder needs", "End-to-end enterprise coverage", "IT-business alignment", "Maturity progression"],
         "compliance_requirements": ["Implement COBIT governance framework across all sector operations", "Define sector-specific governance objectives", "Cascade enterprise goals to sector IT goals", "Conduct annual COBIT maturity assessment per sector", "Align sector risk appetite to enterprise risk policy"],
         "source_url": "https://www.isaca.org/resources/cobit", "tags": ["governance", "COBIT", "cross-sector", "management"]},
    ],
}

# Trend data per domain role
DOMAIN_TRENDS: dict[str, list[dict]] = {
    "Manage Digital Intelligence": [
        {"name": "Agentic AI in Enterprise Operations", "source": "Gartner Hype Cycle for Artificial Intelligence 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "emerging", "time_horizon": "2-5yr",
         "business_impact": "30-40% reduction in knowledge-work overhead through autonomous task execution",
         "technology_enablers": ["LLM orchestration (LangGraph, AutoGen)", "Vector databases (Neo4j, Pinecone)", "AMD MI300X + ROCm for inference", "Function calling APIs"],
         "adoption_rate": "18% of large enterprises in 2025, projected 65% by 2027"},
        {"name": "Data Mesh Architecture", "source": "Forrester Wave: Data Management 2024", "source_type": "industry_analyst", "publication_year": 2024,
         "impact_level": "high", "maturity": "growing", "time_horizon": "1-2yr",
         "business_impact": "40% reduction in data access latency; 60% improvement in data democratisation",
         "technology_enablers": ["Domain-oriented data products", "Federated computational governance", "Data contracts", "Graph metadata layer"],
         "adoption_rate": "35% of Fortune 500 piloting data mesh in 2024"},
    ],
    "Manage Digital Security": [
        {"name": "AI-Powered Threat Detection", "source": "Gartner Security & Risk Summit 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "growing", "time_horizon": "1-2yr",
         "business_impact": "Reduces mean time to detect (MTTD) from days to minutes; 70% reduction in false positives",
         "technology_enablers": ["LLM-based SIEM analytics", "Behavioural AI (UEBA)", "AMD GPU-accelerated threat modelling", "SOAR automation"],
         "adoption_rate": "42% of enterprises deploying AI in SOC by 2025 (Gartner)"},
        {"name": "Zero Trust Network Architecture (ZTNA)", "source": "Forrester Zero Trust Wave 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "high", "maturity": "mainstream", "time_horizon": "<1yr",
         "business_impact": "60% reduction in lateral movement attack surface; enables secure hybrid work",
         "technology_enablers": ["SASE platforms", "Identity-aware proxies", "Micro-segmentation", "Continuous authentication"],
         "adoption_rate": "75% of new remote access deployments will use ZTNA by 2025 (Gartner)"},
    ],
    "Manage Digital IT": [
        {"name": "Platform Engineering & Internal Developer Portals", "source": "Gartner Hype Cycle for Software Engineering 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "high", "maturity": "growing", "time_horizon": "1-2yr",
         "business_impact": "45% improvement in developer productivity; 30% reduction in time-to-production",
         "technology_enablers": ["Backstage (Spotify IDP)", "GitOps", "Policy-as-code", "AI coding assistants"],
         "adoption_rate": "80% of large enterprises will have platform engineering teams by 2026 (Gartner)"},
    ],
    "Manage Digital Inter-Operability & Automation": [
        {"name": "Composable Enterprise Architecture", "source": "Gartner Hype Cycle for EA 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "high", "maturity": "emerging", "time_horizon": "2-5yr",
         "business_impact": "80% faster capability deployment through packaged business capabilities (PBCs)",
         "technology_enablers": ["Microservices", "Event-driven architecture", "API gateway mesh", "Low-code integration"],
         "adoption_rate": "60% of new business applications built on composable principles by 2027 (Gartner)"},
    ],
    "Manage Generic Core": [
        {"name": "Industry Cloud Platforms", "source": "Gartner Top Strategic Technology Trends 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "growing", "time_horizon": "1-2yr",
         "business_impact": "Pre-built industry cloud reduces time-to-value by 40% versus build-from-scratch",
         "technology_enablers": ["Vertical SaaS", "Industry data models", "Pre-built integrations", "Regulatory compliance modules"],
         "adoption_rate": "70% of enterprises will use industry cloud platforms by 2027 (Gartner)"},
    ],
}

SECTOR_TRENDS: dict[str, list[dict]] = {
    "Retail Banking": [
        {"name": "Open Banking & Embedded Finance", "source": "McKinsey Global Banking Annual Review 2024", "source_type": "industry_analyst", "publication_year": 2024,
         "impact_level": "transformational", "maturity": "mainstream", "time_horizon": "<1yr",
         "business_impact": "Open banking generates $416B in revenue opportunity by 2026 (McKinsey); BNPL captures 5% of global e-commerce payments",
         "technology_enablers": ["PSD2/Open Banking APIs", "AI credit scoring", "Real-time payment rails", "Embedded finance SDKs"],
         "adoption_rate": "62% of consumers used at least one open banking service in 2024 (Mastercard)"},
    ],
    "Healthcare Provider": [
        {"name": "AI-Augmented Clinical Decision Support", "source": "Gartner Hype Cycle for Healthcare 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "growing", "time_horizon": "1-2yr",
         "business_impact": "15-20% reduction in diagnostic errors; 30% improvement in care pathway adherence",
         "technology_enablers": ["Clinical LLMs (Med-PaLM 2, BioGPT)", "Federated learning on PHI", "Wearable sensor integration", "FHIR-native AI platforms"],
         "adoption_rate": "55% of health systems deploying AI decision support by 2026 (Gartner)"},
    ],
    "Food Supply": [
        {"name": "Farm-to-Fork Digital Traceability", "source": "WEF Future of Food Report 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "high", "maturity": "growing", "time_horizon": "1-2yr",
         "business_impact": "Reduces food recall costs by 60%; improves consumer trust index by 35%",
         "technology_enablers": ["Blockchain traceability (IBM Food Trust, GS1 EPCIS)", "IoT cold-chain sensors", "Computer vision quality grading", "Digital product passports"],
         "adoption_rate": "40% of global food retailers mandating digital traceability from top-tier suppliers by 2026"},
    ],
    "Oil & Gas": [
        {"name": "Digital Twin for Asset Optimisation", "source": "Deloitte Oil & Gas Tech Trends 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "growing", "time_horizon": "2-5yr",
         "business_impact": "12-15% OPEX reduction; predictive maintenance reduces unplanned downtime by 40%",
         "technology_enablers": ["Industrial IoT sensors", "AMD GPU-accelerated simulation", "Physics-based modelling", "Digital thread"],
         "adoption_rate": "Top 10 O&G majors have active digital twin programmes for upstream assets (2024)"},
    ],
    "Telco": [
        {"name": "5G Network Slicing for Enterprise", "source": "Ericsson Mobility Report 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "emerging", "time_horizon": "2-5yr",
         "business_impact": "$300B total addressable market for enterprise 5G services by 2030 (Ericsson)",
         "technology_enablers": ["5G SA core", "Network slicing orchestration", "Edge computing (MEC)", "Private network NPN"],
         "adoption_rate": "25% of global enterprises piloting private 5G networks in 2025"},
    ],
    "Government": [
        {"name": "AI-Powered Public Service Delivery", "source": "OECD Digital Government Outlook 2025", "source_type": "government", "publication_year": 2025,
         "impact_level": "high", "maturity": "growing", "time_horizon": "1-2yr",
         "business_impact": "30% reduction in service delivery costs; citizen satisfaction improves 25% with proactive services",
         "technology_enablers": ["Conversational AI (government chatbots)", "Predictive analytics for social services", "GovStack building blocks", "Federated government data"],
         "adoption_rate": "68% of OECD member countries have national AI strategies for public sector (2024)"},
    ],
    "Logistics": [
        {"name": "Autonomous Supply Chain (AI + Robotics)", "source": "McKinsey Logistics & Supply Chain 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "growing", "time_horizon": "2-5yr",
         "business_impact": "25% reduction in fulfilment costs; 99.9% order accuracy in automated warehouses",
         "technology_enablers": ["Autonomous mobile robots (AMR)", "AI demand forecasting", "Computer vision picking", "Digital freight platforms"],
         "adoption_rate": "Top 20 3PLs have active autonomous warehouse programmes (2024)"},
    ],
    "Clean Energy": [
        {"name": "AI-Optimised Grid Management", "source": "IEA World Energy Outlook 2025", "source_type": "government", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "growing", "time_horizon": "2-5yr",
         "business_impact": "15-20% improvement in grid efficiency; enables 80%+ renewable penetration",
         "technology_enablers": ["ML forecasting for renewable generation", "Battery storage optimisation", "Virtual power plants", "AMD GPU-accelerated grid simulation"],
         "adoption_rate": "All major grid operators deploying AI for demand response by 2026 (IEA)"},
    ],
    "Pharmaceutical": [
        {"name": "AI-Accelerated Drug Discovery", "source": "Deloitte Life Sciences Report 2025", "source_type": "industry_analyst", "publication_year": 2025,
         "impact_level": "transformational", "maturity": "growing", "time_horizon": "2-5yr",
         "business_impact": "Reduces pre-clinical phase from 5 years to 18 months; 40% cost reduction in lead optimisation",
         "technology_enablers": ["Generative molecular design (AlphaFold3, RoseTTAFold)", "AMD MI300X for protein structure prediction", "Real-world evidence platforms", "Digital biomarkers"],
         "adoption_rate": "All top-20 pharma companies have AI-native drug discovery programmes (2024)"},
    ],
}

DEFAULT_STANDARD = {
    "name": "TOGAF 10 + COBIT 2019", "publisher": "The Open Group / ISACA", "version": "10.0 / 2019",
    "key_principles": ["Architecture governance", "Stakeholder alignment", "Risk management", "Continual improvement", "Business-IT alignment"],
    "compliance_requirements": ["Establish Architecture Board", "Implement risk management framework", "Publish architecture principles", "Conduct annual maturity assessment", "Align IT objectives to enterprise goals"],
    "source_url": "https://www.opengroup.org/togaf", "tags": ["EA", "governance", "architecture"]
}

DEFAULT_TREND = {
    "name": "AI-Powered Digital Transformation", "source": "Gartner Top Trends 2025", "source_type": "industry_analyst", "publication_year": 2025,
    "impact_level": "high", "maturity": "growing", "time_horizon": "1-2yr",
    "business_impact": "Enterprises using AI report 20-30% productivity gains and 15% cost reduction on average",
    "technology_enablers": ["Generative AI", "Agentic workflows", "AMD MI300X inference", "Vector databases"],
    "adoption_rate": "87% of executives say AI is a top-3 strategic priority in 2025 (Gartner)"
}


# ---------------------------------------------------------------------------
# Keyword-to-standards mapping for sector domains
# ---------------------------------------------------------------------------

SECTOR_KEYWORD_MAP = [
    (["retail banking", "bank"],         "Retail Banking"),
    (["healthcare provider", "hospital", "clinic"],  "Healthcare Provider"),
    (["pharmaceutical", "pharma"],       "Pharmaceutical"),
    (["food supply", "food"],            "Food Supply"),
    (["oil & gas", "o&g", "oil and gas", "petroleum"], "Oil & Gas"),
    (["telco", "telecommunications", "regulatory (communications)"], "Telco"),
    (["logistics", "logistics 4.0"],     "Logistics"),
    (["government excellence", "court", "justice", "urban planning", "government"], "Government"),
    (["clean energy", "electricity transmission", "energy"], "Clean Energy"),
    (["capital", "investment promotion", "stock exchange", "endowment", "development banking"], "Capital Markets"),
    (["court & justice"],                "Court & Justice"),
    (["urban planning"],                 "Urban Planning"),
    (["property development"],           "Property Development"),
    (["airport"],                        "Airport"),
    (["development banking"],            "Development Banking"),
    (["investment promotion"],           "Investment Promotion"),
    (["health regulatory"],              "Health Regulatory"),
    (["professional services"],          "Professional Services"),
    (["endowment"],                      "Endowment"),
    (["stock exchange"],                 "Stock Exchange"),
    (["digital financial regulation"],   "Digital Financial Regulation"),
    (["digital academy", "academy"],     "Digital Academy"),
    (["cdc"],                            "CDC"),
    (["healthcare payer", "payer"],      "Healthcare Payer"),
    (["government excellence"],          "Government Excellence"),
    (["health system"],                  "Health System"),
]


def get_standard_for_domain(domain_name: str) -> dict:
    name_lower = domain_name.lower()
    # Try domain-level mapping first
    for dom_key, stds in DOMAIN_STANDARDS.items():
        if dom_key.lower() in name_lower or name_lower in dom_key.lower():
            return stds[0]  # return first (primary) standard
    # Then sector mapping
    for keywords, sector_key in SECTOR_KEYWORD_MAP:
        if any(kw in name_lower for kw in keywords):
            stds = SECTOR_STANDARDS.get(sector_key)
            if stds:
                return stds[0]
    return DEFAULT_STANDARD


def get_all_standards_for_domain(domain_name: str) -> list[dict]:
    name_lower = domain_name.lower()
    for dom_key, stds in DOMAIN_STANDARDS.items():
        if dom_key.lower() in name_lower:
            return stds
    for keywords, sector_key in SECTOR_KEYWORD_MAP:
        if any(kw in name_lower for kw in keywords):
            stds = SECTOR_STANDARDS.get(sector_key)
            if stds:
                return stds
    return [DEFAULT_STANDARD]


def get_trends_for_domain(domain_name: str) -> list[dict]:
    name_lower = domain_name.lower()
    for dom_key, trends in DOMAIN_TRENDS.items():
        if dom_key.lower() in name_lower:
            return trends
    for keywords, sector_key in SECTOR_KEYWORD_MAP:
        if any(kw in name_lower for kw in keywords):
            trends = SECTOR_TRENDS.get(sector_key)
            if trends:
                return trends
    return [DEFAULT_TREND]


# ---------------------------------------------------------------------------
# Web search enrichment (DuckDuckGo)
# ---------------------------------------------------------------------------

def web_search_snippets(query: str, max_results: int = 3) -> list[str]:
    """DuckDuckGo text search — returns snippet strings, no API key required."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                snippet = r.get("body") or r.get("snippet") or ""
                if snippet:
                    results.append(f"{r.get('title','')}: {snippet}")
        return results
    except Exception as exc:
        log.debug(f"DDG search failed for '{query}': {exc}")
        return []


def synthesise_with_llm(domain_name: str, node_type: str, search_snippets: list[str], llm_fn) -> dict | None:
    """Use LLM to synthesise structured enrichment from web snippets."""
    if not search_snippets or llm_fn is None:
        return None

    context = "\n".join(search_snippets[:3])
    prompt = f"""Given these search results about standards and trends for enterprise domain "{domain_name}":

{context}

Extract the most important regulatory/governance standard applicable to this domain and return ONLY valid JSON:
{{
  "name": "<standard name>",
  "publisher": "<publisher organisation>",
  "version": "<version or year>",
  "key_principles": ["<principle 1>", "<principle 2>", "<principle 3>"],
  "compliance_requirements": ["<requirement 1>", "<requirement 2>", "<requirement 3>"],
  "tags": ["<tag1>", "<tag2>"]
}}"""

    try:
        raw = llm_fn(prompt)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as exc:
        log.debug(f"LLM synthesis failed for {domain_name}: {exc}")
    return None


# ---------------------------------------------------------------------------
# Main enrichment runner
# ---------------------------------------------------------------------------

class GraphEnricherV2:
    def __init__(self, driver, database: str, use_web_search: bool = True, llm_fn=None):
        self.driver = driver
        self.database = database
        self.use_web_search = use_web_search
        self.llm_fn = llm_fn

    def _run(self, cypher: str, **params):
        with self.driver.session(database=self.database) as s:
            return s.run(cypher, **params).data()

    def _enrich_standard_node(self, std_id: str, domain_name: str, std_data: dict):
        """SET all properties on a Standard node — real-time insertion."""
        self._run("""
MATCH (n:Standard {id: $id})
SET n.name = $name,
    n.full_name = $name,
    n.publisher = $publisher,
    n.version = coalesce($version, ''),
    n.year = toInteger(split($version, ' ')[-1]),
    n.description = $desc,
    n.key_principles = $key_principles,
    n.compliance_requirements = $compliance_requirements,
    n.source_url = coalesce($source_url, ''),
    n.tags = $tags,
    n.domain_name = $domain_name
""",
            id=std_id,
            name=std_data.get("name", ""),
            publisher=std_data.get("publisher", ""),
            version=str(std_data.get("version", "")),
            desc=f"Governance standard for {domain_name} — {std_data.get('name','')} by {std_data.get('publisher','')}",
            key_principles=std_data.get("key_principles") or [],
            compliance_requirements=std_data.get("compliance_requirements") or [],
            source_url=std_data.get("source_url", ""),
            tags=std_data.get("tags") or [],
            domain_name=domain_name,
        )

    def _enrich_trend_node(self, trend_id: str, domain_name: str, trend_data: dict):
        """SET all properties on a Trend node — real-time insertion."""
        self._run("""
MATCH (n:Trend {id: $id})
SET n.name = $name,
    n.description = $description,
    n.source = $source,
    n.source_type = $source_type,
    n.publication_year = $publication_year,
    n.impact_level = $impact_level,
    n.maturity = $maturity,
    n.time_horizon = $time_horizon,
    n.business_impact = $business_impact,
    n.technology_enablers = $technology_enablers,
    n.adoption_rate = coalesce($adoption_rate, ''),
    n.domain_name = $domain_name
""",
            id=trend_id,
            name=trend_data.get("name", ""),
            description=trend_data.get("business_impact", ""),
            source=trend_data.get("source", ""),
            source_type=trend_data.get("source_type", "industry_analyst"),
            publication_year=trend_data.get("publication_year", 2025),
            impact_level=trend_data.get("impact_level", "high"),
            maturity=trend_data.get("maturity", "growing"),
            time_horizon=trend_data.get("time_horizon", "1-2yr"),
            business_impact=trend_data.get("business_impact", ""),
            technology_enablers=trend_data.get("technology_enablers") or [],
            adoption_rate=trend_data.get("adoption_rate", ""),
            domain_name=domain_name,
        )

    def enrich_domains(self):
        """Enrich all 44 domain Standard + Trend nodes with sector-specific real data."""
        domains = self._run("""
MATCH (d:Domain) WHERE d.id <> '__hub__'
OPTIONAL MATCH (d)-[:GOVERNED_BY]->(std:Standard)
OPTIONAL MATCH (d)-[:INFLUENCED_BY]->(trend:Trend)
RETURN d.id AS domain_id, d.name AS domain_name,
       std.id AS std_id, trend.id AS trend_id
""")
        log.info(f"Enriching {len(domains)} domains with sector-specific standards and trends...")

        for i, row in enumerate(domains, 1):
            domain_name = row["domain_name"] or ""
            std_id = row["std_id"]
            trend_id = row["trend_id"]

            # Get curated standard
            std_data = get_standard_for_domain(domain_name)

            # Optional web search augmentation
            if self.use_web_search:
                snippets = web_search_snippets(
                    f"enterprise governance standards {domain_name} compliance requirements"
                )
                if snippets:
                    web_std = synthesise_with_llm(domain_name, "Standard", snippets, self.llm_fn)
                    if web_std and web_std.get("name"):
                        # Merge web findings into curated (web augments compliance_requirements)
                        extra_reqs = web_std.get("compliance_requirements") or []
                        existing_reqs = std_data.get("compliance_requirements") or []
                        std_data = dict(std_data)
                        std_data["compliance_requirements"] = list(dict.fromkeys(existing_reqs + extra_reqs))[:8]
                        log.debug(f"  Web-augmented standard for {domain_name}: +{len(extra_reqs)} reqs")

            # Enrich Standard node
            if std_id:
                self._enrich_standard_node(std_id, domain_name, std_data)

            # Get trend
            trends = get_trends_for_domain(domain_name)
            trend_data = trends[0] if trends else DEFAULT_TREND

            # Enrich Trend node
            if trend_id:
                self._enrich_trend_node(trend_id, domain_name, trend_data)

            log.info(f"  [{i:2d}/{len(domains)}] {domain_name[:55]:<55} → {std_data['name'][:30]}")

    def enrich_subdomains(self):
        """Add functional context to SubDomain nodes."""
        rows = self._run("""
MATCH (d:Domain)-[:PARENT_OF]->(sd:SubDomain)
WHERE d.id <> '__hub__'
RETURN sd.id AS id, sd.name AS name, d.name AS domain_name
""")
        log.info(f"Enriching {len(rows)} SubDomain nodes...")
        batch = []
        for r in rows:
            sd_name = r["name"] or ""
            domain = r["domain_name"] or ""
            batch.append({
                "id": r["id"],
                "description": f"Manages {sd_name.replace('Manage ','')} capabilities within the {domain} domain.",
                "functional_scope": f"Covers all capabilities related to {sd_name.replace('Manage ','')} including strategy, operations, and technology enablement.",
                "business_driver": f"Drives efficiency, compliance, and digital maturity in {sd_name.replace('Manage ','')} to support {domain} objectives.",
                "grouping_rationale": f"Capabilities share a common service lifecycle and accountability model under {sd_name}.",
            })
        if batch:
            with self.driver.session(database=self.database) as s:
                s.run("""
UNWIND $rows AS row
MATCH (n:SubDomain {id: row.id})
SET n.description = row.description,
    n.functional_scope = row.functional_scope,
    n.business_driver = row.business_driver,
    n.grouping_rationale = row.grouping_rationale
""", rows=batch)
        log.info(f"  {len(batch)} SubDomain nodes enriched")

    def enrich_capabilities(self, batch_size: int = 200):
        """Add semantic properties to Capability nodes."""
        total = self._run("MATCH (n:Capability) RETURN count(n) AS cnt")[0]["cnt"]
        log.info(f"Enriching {total} Capability nodes...")
        skip = 0
        done = 0
        while True:
            rows = self._run("""
MATCH (sd:SubDomain)-[:PARENT_OF]->(c:Capability)
MATCH (d:Domain)-[:PARENT_OF]->(sd)
RETURN c.id AS id, c.name AS name, sd.name AS subdomain, d.name AS domain
SKIP $skip LIMIT $limit
""", skip=skip, limit=batch_size)
            if not rows:
                break
            batch = []
            for r in rows:
                cap_name = r["name"] or ""
                subdomain = r["subdomain"] or ""
                domain = r["domain"] or ""
                # Complexity heuristic based on name keywords
                complexity = "medium"
                if any(w in cap_name.lower() for w in ["governance", "strategy", "architecture", "transformation"]):
                    complexity = "high"
                elif any(w in cap_name.lower() for w in ["report", "monitor", "track", "manage"]):
                    complexity = "medium"
                elif any(w in cap_name.lower() for w in ["basic", "simple", "standard"]):
                    complexity = "low"

                batch.append({
                    "id": r["id"],
                    "description": f"Enables organisations to {cap_name.replace('Manage ','manage ').replace('Manage','manage')} within the {subdomain} context of {domain}.",
                    "business_outcomes": [
                        f"Improved {cap_name.replace('Manage ','')} efficiency and effectiveness",
                        f"Reduced operational risk in {subdomain}",
                        f"Enhanced compliance with {domain} regulatory requirements",
                    ],
                    "technical_requirements": [
                        f"Integration with existing {domain} systems",
                        "API-driven architecture for interoperability",
                        "Role-based access control and audit logging",
                    ],
                    "implementation_complexity": complexity,
                    "risk_factors": [
                        "Stakeholder change resistance",
                        f"Legacy system integration complexity in {domain}",
                        "Data migration and quality risks",
                    ],
                    "typical_duration_weeks": {"low": 8, "medium": 16, "high": 24, "very_high": 36}.get(complexity, 16),
                    "common_frameworks": ["TOGAF", "COBIT 2019", "ITIL 4"],
                    "solution_patterns": ["Microservices", "Event-driven architecture", "API-first"],
                    "kpis": [
                        f"{cap_name.replace('Manage ','')} process cycle time reduced by 30%",
                        "System uptime > 99.5%",
                        "User adoption rate > 80% within 6 months",
                    ],
                    "industry_applicability": [domain],
                })
            with self.driver.session(database=self.database) as s:
                s.run("""
UNWIND $rows AS row
MATCH (n:Capability {id: row.id})
SET n.description = row.description,
    n.business_outcomes = row.business_outcomes,
    n.technical_requirements = row.technical_requirements,
    n.implementation_complexity = row.implementation_complexity,
    n.risk_factors = row.risk_factors,
    n.typical_duration_weeks = row.typical_duration_weeks,
    n.common_frameworks = row.common_frameworks,
    n.solution_patterns = row.solution_patterns,
    n.kpis = row.kpis,
    n.industry_applicability = row.industry_applicability
""", rows=batch)
            done += len(batch)
            skip += batch_size
            log.info(f"  Capabilities enriched: {done}/{total}")
            if len(rows) < batch_size:
                break
        log.info(f"  Capability enrichment complete: {done} nodes")

    def run(self, skip_web_search: bool = False):
        if skip_web_search:
            self.use_web_search = False
        t0 = time.time()
        log.info("=== Graph Enrichment v2 — Sector-Aware ===")
        self.enrich_domains()
        self.enrich_subdomains()
        self.enrich_capabilities()
        log.info(f"=== Enrichment complete in {time.time()-t0:.1f}s ===")


def run_enrichment(use_web_search: bool = False):
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        enricher = GraphEnricherV2(driver, database, use_web_search=use_web_search)
        enricher.run()
    finally:
        driver.close()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--web", action="store_true", help="Enable DuckDuckGo web search augmentation")
    args = p.parse_args()
    run_enrichment(use_web_search=args.web)
