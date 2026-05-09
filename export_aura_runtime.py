# export_aura_runtime.py               
import json
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(                                                                                                                                                        
      os.getenv("NEO4J_URI"),
      auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),                                                                                                                  
  )                                      

EXPORTS = {
      "generated_outputs": "MATCH (o:GeneratedOutput) RETURN o",
      "training_runs":     "MATCH (t:TrainingRun) RETURN t",
      "chat_sessions":     "MATCH (s:ChatSession)-[:HAS_MESSAGE]->(m:ChatMessage) RETURN s, m",
      "external_systems":  "MATCH (e:ExternalSystem)-[:SUPPORTS]->(c:Capability) RETURN e, c.id AS cap_id",                                                                             
      "drl_trained_domains": "MATCH (d:Domain) WHERE d.drl_trained = true RETURN d.id AS id, d.name AS name",                                                                           
  }                                                                                                                                                                                     
                                                                                                                                                                                        
with driver.session() as session:                                                                                                                                                     
      for name, query in EXPORTS.items():
          rows = [dict(r) for r in session.run(query)]
          with open(f"export_{name}.json", "w") as f:                                                                                                                                   
              json.dump(rows, f, indent=2, default=str)
          print(f"{name}: {len(rows)} rows")                                                                                                                                            
                                                                                                                                                                                        
driver.close()

