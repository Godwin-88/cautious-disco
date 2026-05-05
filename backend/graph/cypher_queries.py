"""All Cypher query strings as module-level constants."""

# ---------------------------------------------------------------------------
# Exploration queries
# ---------------------------------------------------------------------------

GET_ALL_DOMAINS = """
MATCH (d:Domain)
WHERE d.id <> '__hub__'
OPTIONAL MATCH (d)-[:PARENT_OF]->(:SubDomain)-[:PARENT_OF]->(c:Capability)
RETURN d.id AS id, d.name AS name, count(DISTINCT c) AS capability_count
ORDER BY d.name
"""

GET_CAPABILITIES_FOR_DOMAIN = """
MATCH (d:Domain)-[:PARENT_OF]->(sd:SubDomain)-[:PARENT_OF]->(c:Capability)
WHERE ($domain_id IS NULL OR d.id = $domain_id)
RETURN c.id AS id, c.name AS name, d.name AS domain_name, sd.name AS subdomain_name,
       c.description AS description
ORDER BY d.name, sd.name, c.name
LIMIT $limit
"""

GET_DOMAIN_STATS = """
MATCH (n)
WHERE n.id <> '__hub__'
RETURN labels(n)[0] AS label, count(*) AS count
ORDER BY count DESC
"""

GET_ALL_SUBDOMAINS = """
MATCH (domain:Domain)-[:PARENT_OF]->(sd:SubDomain)
RETURN sd.id AS id, sd.name AS name, domain.name AS domain_name
ORDER BY domain_name, sd.name
"""

GET_NODE_COUNTS = """
MATCH (n)
RETURN labels(n)[0] AS label, count(*) AS count
ORDER BY count DESC
"""

# ---------------------------------------------------------------------------
# Core deep traversal for retrieval (returns enriched hierarchy)
# ---------------------------------------------------------------------------

GET_ENRICHED_CAPABILITIES_FOR_DOMAIN = """
// Try sector domains under Manage Generic Core first
MATCH (gc:Domain {name: 'Manage Generic Core'})-[:HAS_SECTOR]->(domain:Domain)
WHERE toLower(domain.name) CONTAINS toLower($org_keyword)
   OR toLower(domain.name) CONTAINS toLower($sector_keyword)
WITH domain LIMIT 5
MATCH (domain)-[:GOVERNED_BY]->(std:Standard)
MATCH (domain)-[:INFLUENCED_BY]->(trend:Trend)
MATCH (domain)-[:PARENT_OF]->(subdomain:SubDomain)
MATCH (subdomain)-[:PARENT_OF]->(cap:Capability)
OPTIONAL MATCH (cap)-[:PARENT_OF]->(subcap:SubCapability)
OPTIONAL MATCH (cap)-[:REPRESENTED_BY]->(epic:Epic)-[:HAS_FEATURE]->(feat:Feature)
RETURN
  domain {.id, .name}                                                    AS domain,
  std {.id, .name, .full_name, .publisher, .version, .year,
       .description, .key_principles, .compliance_requirements,
       .source_url, .tags}                                               AS standard,
  trend {.id, .name, .description, .source, .source_type, .publication_year,
         .impact_level, .maturity, .time_horizon, .business_impact,
         .technology_enablers, .adoption_rate}                          AS trend,
  subdomain {.id, .name, .description, .functional_scope, .business_driver,
             .grouping_rationale}                                        AS subdomain,
  cap {.id, .name, .description, .business_outcomes, .risk_factors,
       .kpis, .typical_duration_weeks, .implementation_complexity,
       .common_frameworks, .solution_patterns, .technical_requirements} AS capability,
  collect(DISTINCT subcap {.id, .name, .description}) AS subcapabilities,
  collect(DISTINCT feat.id)                            AS feature_ids,
  epic.name                                            AS epic_name
LIMIT $limit
"""

# Broader fallback: match any domain containing the keyword
GET_CAPABILITIES_BROAD = """
MATCH (domain:Domain)
WHERE toLower(domain.name) CONTAINS toLower($keyword)
  AND domain.id <> '__hub__'
WITH domain LIMIT 3
MATCH (domain)-[:PARENT_OF]->(subdomain:SubDomain)
MATCH (subdomain)-[:PARENT_OF]->(cap:Capability)
OPTIONAL MATCH (domain)-[:GOVERNED_BY]->(std:Standard)
OPTIONAL MATCH (domain)-[:INFLUENCED_BY]->(trend:Trend)
OPTIONAL MATCH (cap)-[:PARENT_OF]->(subcap:SubCapability)
RETURN
  domain {.id, .name}                                                  AS domain,
  std {.id, .name, .publisher, .key_principles, .compliance_requirements} AS standard,
  trend {.id, .name, .source, .impact_level, .business_impact,
         .technology_enablers}                                          AS trend,
  subdomain {.id, .name, .description, .functional_scope,
             .business_driver}                                          AS subdomain,
  cap {.id, .name, .description, .business_outcomes, .risk_factors,
       .kpis, .typical_duration_weeks,
       .implementation_complexity}                                      AS capability,
  collect(DISTINCT subcap {.id, .name, .description})                  AS subcapabilities
LIMIT $limit
"""

# ---------------------------------------------------------------------------
# Vector similarity search
# ---------------------------------------------------------------------------

VECTOR_SIMILARITY_SEARCH = """
CALL db.index.vector.queryNodes($index_name, $top_k, $query_vector)
YIELD node AS cap, score
WHERE score > $min_score
MATCH (cap)<-[:PARENT_OF]-(subdomain:SubDomain)<-[:PARENT_OF]-(domain:Domain)
  WHERE domain.id <> '__hub__'
OPTIONAL MATCH (domain)-[:GOVERNED_BY]->(std:Standard)
OPTIONAL MATCH (domain)-[:INFLUENCED_BY]->(trend:Trend)
RETURN
  cap {.id, .name, .description, .business_outcomes, .risk_factors,
       .kpis, .typical_duration_weeks, .implementation_complexity}     AS capability,
  subdomain {.id, .name, .description, .functional_scope}             AS subdomain,
  domain {.id, .name}                                                  AS domain,
  std {.id, .name, .publisher, .key_principles,
       .compliance_requirements}                                        AS standard,
  trend {.id, .name, .source, .impact_level, .business_impact,
         .technology_enablers}                                          AS trend,
  score
ORDER BY score DESC
LIMIT $top_k
"""

# ---------------------------------------------------------------------------
# Standards and trends queries (for Verifier)
# ---------------------------------------------------------------------------

GET_STANDARDS_FOR_DOMAIN_NAMES = """
MATCH (domain:Domain)-[:GOVERNED_BY]->(std:Standard)
WHERE domain.name IN $domain_names
RETURN domain.name AS domain, std {.name, .publisher, .compliance_requirements, .key_principles} AS standard
"""

GET_TRENDS_FOR_DOMAIN_NAMES = """
MATCH (domain:Domain)-[:INFLUENCED_BY]->(trend:Trend)
WHERE domain.name IN $domain_names
RETURN domain.name AS domain, trend {.name, .source, .impact_level, .business_impact} AS trend
"""

# ---------------------------------------------------------------------------
# ENABLES cross-domain relationships
# ---------------------------------------------------------------------------

GET_ENABLES_GRAPH = """
MATCH (source:Domain)-[:ENABLES]->(target:Domain)
RETURN source.name AS source, target.name AS target
"""

# ---------------------------------------------------------------------------
# Enrichment update queries
# ---------------------------------------------------------------------------

SET_STANDARD_PROPERTIES = """
UNWIND $rows AS row
MATCH (n:Standard {id: row.id})
SET n.name = row.name,
    n.full_name = row.full_name,
    n.publisher = row.publisher,
    n.version = row.version,
    n.year = row.year,
    n.description = row.description,
    n.key_principles = row.key_principles,
    n.compliance_requirements = row.compliance_requirements,
    n.applicable_domains = row.applicable_domains,
    n.maturity_model = row.maturity_model,
    n.certification_body = row.certification_body,
    n.source_url = row.source_url,
    n.industry_relevance = row.industry_relevance,
    n.tags = row.tags
"""

SET_TREND_PROPERTIES = """
UNWIND $rows AS row
MATCH (n:Trend {id: row.id})
SET n.name = row.name,
    n.description = row.description,
    n.source = row.source,
    n.source_type = row.source_type,
    n.publication_year = row.publication_year,
    n.impact_level = row.impact_level,
    n.maturity = row.maturity,
    n.time_horizon = row.time_horizon,
    n.business_impact = row.business_impact,
    n.technology_enablers = row.technology_enablers,
    n.related_standards = row.related_standards,
    n.adoption_rate = row.adoption_rate,
    n.industry_applicability = row.industry_applicability,
    n.citations = row.citations,
    n.tags = row.tags
"""

SET_SUBDOMAIN_PROPERTIES = """
UNWIND $rows AS row
MATCH (n:SubDomain {id: row.id})
SET n.description = row.description,
    n.functional_scope = row.functional_scope,
    n.business_driver = row.business_driver,
    n.grouping_rationale = row.grouping_rationale
"""

SET_CAPABILITY_PROPERTIES = """
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
"""

SET_VECTOR_EMBEDDING = """
MATCH (n) WHERE n.id = $node_id
CALL db.create.setVectorProperty(n, 'embedding', $embedding)
"""

# ---------------------------------------------------------------------------
# Cross-domain direct retrieval — supports questionnaire multi-domain selection
# ---------------------------------------------------------------------------

GET_ENRICHED_CAPABILITIES_BY_DOMAIN_NAMES = """
MATCH (d:Domain)-[:PARENT_OF]->(sd:SubDomain)-[:PARENT_OF]->(c:Capability)
WHERE d.name IN $domain_names AND d.id <> '__hub__'
OPTIONAL MATCH (d)-[:GOVERNED_BY]->(std:Standard)
OPTIONAL MATCH (d)-[:INFLUENCED_BY]->(trend:Trend)
OPTIONAL MATCH (c)-[:PARENT_OF]->(subcap:SubCapability)
WITH c, sd, d, std, trend,
     collect(DISTINCT subcap {.id, .name, .description}) AS subcapabilities
RETURN
  c {.id, .name, .description, .business_outcomes, .risk_factors,
     .kpis, .typical_duration_weeks, .implementation_complexity,
     .common_frameworks, .solution_patterns, .technical_requirements} AS capability,
  sd {.id, .name, .description, .functional_scope, .business_driver,
      .grouping_rationale}                                             AS subdomain,
  d {.id, .name}                                                      AS domain,
  std {.id, .name, .publisher, .key_principles,
       .compliance_requirements}                                       AS standard,
  trend {.id, .name, .source, .impact_level, .time_horizon,
         .business_impact, .technology_enablers}                       AS trend,
  subcapabilities
ORDER BY d.name, c.name
LIMIT $limit
"""

GET_DOMAINS_BY_KEYWORD = """
MATCH (d:Domain)
WHERE d.id <> '__hub__'
  AND toLower(d.name) CONTAINS toLower($keyword)
RETURN d.name AS name LIMIT 5
"""

# ---------------------------------------------------------------------------
# Training metrics — written by pipeline/train_on_graph.py
# ---------------------------------------------------------------------------

GET_CAPABILITIES_FOR_TRAINING = """
MATCH (d:Domain)-[:PARENT_OF]->(sd:SubDomain)-[:PARENT_OF]->(c:Capability)
WHERE d.name = $domain_name AND d.id <> '__hub__'
RETURN c.name AS name,
       c.implementation_complexity AS complexity,
       c.typical_duration_weeks AS duration_weeks,
       c.risk_factors AS risk_factors,
       c.kpis AS kpis,
       c.business_outcomes AS business_outcomes
ORDER BY rand() LIMIT 10
"""

GET_DOMAIN_RELATIONSHIP_FLAGS = """
MATCH (d:Domain {name: $domain_name})
RETURN
  count { (d)-[:HAS_SECTOR]->() }     > 0 AS is_sector_hub,
  count { (d)<-[:ENABLES]-() }        > 0 AS is_enabled,
  count { (d)-[:ORCHESTRATES]->() }   > 0 AS is_orchestrator,
  count { (d)-[:GOVERNED_BY]->() }    > 0 AS is_governed,
  count { ()<-[:HAS_SECTOR]-(d) }     > 0 AS is_sector_child,
  count { (d)-[:ENABLES]->() }        > 0 AS enables_others,
  count { (d)-[:INFLUENCED_BY]->() }  > 0 AS has_trend
"""

UPSERT_TRAINING_RUN = """
MERGE (tr:TrainingRun {run_id: $run_id})
SET tr += $props,
    tr.timestamp = datetime()
"""

SET_DOMAIN_TRAINING_STATUS = """
MATCH (d:Domain {name: $domain_name})
SET d.drl_trained = true,
    d.drl_final_reward = $final_reward,
    d.drl_last_trained = datetime(),
    d.drl_policy_version = $policy_version
"""

GET_TRAINING_METRICS = """
MATCH (tr:TrainingRun)
RETURN tr.run_id        AS run_id,
       tr.domain_name   AS domain_name,
       tr.sector        AS sector,
       tr.episodes      AS episodes,
       tr.final_reward  AS final_reward,
       tr.avg_reward_last10 AS avg_reward_last10,
       tr.device        AS device,
       tr.policy_version AS policy_version,
       toString(tr.timestamp) AS ts
ORDER BY tr.timestamp DESC
LIMIT 200
"""

GET_ENRICHMENT_COVERAGE = """
MATCH (d:Domain) WHERE d.id <> '__hub__'
OPTIONAL MATCH (d)-[:GOVERNED_BY]->(std:Standard)
OPTIONAL MATCH (d)-[:INFLUENCED_BY]->(trend:Trend)
RETURN d.name                                               AS domain,
       std.name IS NOT NULL                                 AS has_standard,
       (std.compliance_requirements IS NOT NULL
        AND size(std.compliance_requirements) > 0)          AS standard_enriched,
       trend.name IS NOT NULL                               AS has_trend,
       (trend.business_impact IS NOT NULL
        AND trend.business_impact <> '')                    AS trend_enriched,
       coalesce(d.drl_trained, false)                       AS drl_trained,
       d.drl_final_reward                                   AS drl_reward,
       toString(d.drl_last_trained)                         AS drl_last_trained
ORDER BY d.name
"""

# ---------------------------------------------------------------------------
# Questionnaire: hierarchical domain → subdomain → capability selection
# ---------------------------------------------------------------------------

GET_SUBDOMAINS_FOR_DOMAINS = """
MATCH (d:Domain)-[:PARENT_OF]->(sd:SubDomain)
WHERE d.name IN $domain_names
RETURN sd.id AS id, sd.name AS name, d.name AS domain_name,
       sd.functional_scope AS functional_scope
ORDER BY d.name, sd.name
"""

GET_CAPABILITIES_FOR_SUBDOMAINS = """
MATCH (sd:SubDomain)-[:PARENT_OF]->(c:Capability)
WHERE sd.id IN $subdomain_ids
RETURN c.id AS id, c.name AS name, sd.name AS subdomain_name, sd.id AS subdomain_id,
       c.description AS description, c.implementation_complexity AS complexity,
       c.typical_duration_weeks AS duration_weeks
ORDER BY sd.name, c.name
"""

GET_CAPABILITIES_BY_IDS = """
MATCH (cap:Capability)
WHERE cap.id IN $capability_ids
MATCH (cap)<-[:PARENT_OF]-(subdomain:SubDomain)<-[:PARENT_OF]-(domain:Domain)
  WHERE domain.id <> '__hub__'
OPTIONAL MATCH (domain)-[:GOVERNED_BY]->(std:Standard)
OPTIONAL MATCH (domain)-[:INFLUENCED_BY]->(trend:Trend)
OPTIONAL MATCH (cap)-[:PARENT_OF]->(subcap:SubCapability)
WITH cap, subdomain, domain, std, trend,
     collect(DISTINCT subcap {.id, .name, .description}) AS subcapabilities
RETURN
  cap {.id, .name, .description, .business_outcomes, .risk_factors,
       .kpis, .typical_duration_weeks, .implementation_complexity,
       .common_frameworks, .solution_patterns, .technical_requirements} AS capability,
  subdomain {.id, .name, .description, .functional_scope, .business_driver,
             .grouping_rationale}                                        AS subdomain,
  domain {.id, .name}                                                   AS domain,
  std {.id, .name, .full_name, .publisher, .version, .key_principles,
       .compliance_requirements}                                         AS standard,
  trend {.id, .name, .source, .impact_level, .time_horizon, .business_impact,
         .technology_enablers}                                           AS trend,
  subcapabilities
ORDER BY domain.name, subdomain.name, cap.name
"""

# ---------------------------------------------------------------------------
# Output caching
# ---------------------------------------------------------------------------

STORE_GENERATED_OUTPUT = """
MERGE (o:GeneratedOutput {cache_key: $cache_key})
SET o.org_type         = $org_type,
    o.output_json      = $output_json,
    o.capability_ids   = $capability_ids,
    o.phases_count     = $phases_count,
    o.epics_count      = $epics_count,
    o.created_at       = datetime(),
    o.hit_count        = coalesce(o.hit_count, 0)
WITH o
UNWIND $capability_ids AS cap_id
  MATCH (c:Capability {id: cap_id})
  MERGE (o)-[:COVERS]->(c)
"""

GET_CACHED_OUTPUT = """
MATCH (o:GeneratedOutput {cache_key: $cache_key})
SET o.hit_count      = coalesce(o.hit_count, 0) + 1,
    o.last_accessed  = datetime()
RETURN o.output_json AS output_json
"""

FIND_SIMILAR_CACHED_OUTPUT = """
MATCH (o:GeneratedOutput)-[:COVERS]->(c:Capability)
WHERE c.id IN $capability_ids
  AND (toLower(o.org_type) CONTAINS toLower($org_keyword)
       OR toLower($org_keyword) CONTAINS toLower(o.org_type))
WITH o, count(DISTINCT c) AS matching_caps
WHERE matching_caps >= $min_match
SET o.hit_count = coalesce(o.hit_count, 0) + 1,
    o.last_accessed = datetime()
RETURN o.output_json AS output_json, matching_caps
ORDER BY matching_caps DESC, o.created_at DESC
LIMIT 1
"""

# ---------------------------------------------------------------------------
# Network graph and ArchiMate views
# ---------------------------------------------------------------------------

GET_NETWORK_GRAPH = """
MATCH (d:Domain) WHERE d.id <> '__hub__'
OPTIONAL MATCH (d)-[r:ENABLES|ORCHESTRATES|HAS_SECTOR]->(t:Domain)
  WHERE t.id <> '__hub__'
WITH collect(DISTINCT {id: d.id, name: d.name,
                        sector: coalesce(d.sector,''),
                        drl_trained: coalesce(d.drl_trained, false)}) AS nodes,
     collect(DISTINCT CASE WHEN t IS NOT NULL
               THEN {source: d.id, target: t.id, type: type(r)}
               ELSE null END) AS raw_edges
RETURN nodes,
       [e IN raw_edges WHERE e IS NOT NULL] AS edges
"""

GET_ARCHIMATE_CAPABILITIES = """
MATCH (d:Domain)-[:PARENT_OF]->(sd:SubDomain)-[:PARENT_OF]->(c:Capability)
WHERE d.id <> '__hub__'
WITH c, sd, d,
     collect(DISTINCT c.common_frameworks) AS fw,
     collect(DISTINCT c.technical_requirements) AS tr_list
RETURN c.id AS id, c.name AS name,
       c.description AS description,
       c.implementation_complexity AS complexity,
       d.name AS domain_name, sd.name AS subdomain_name,
       c.common_frameworks AS frameworks,
       c.technical_requirements AS technical_requirements,
       c.business_outcomes AS business_outcomes
ORDER BY d.name, c.name
LIMIT 500
"""
