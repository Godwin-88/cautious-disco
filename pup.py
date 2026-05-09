# run once after loading the core graph into Docker
import json                                                                                                                                                                           
from neo4j import GraphDatabase        
                                                                                                                                                                                        
driver = GraphDatabase.driver("bolt://localhost:7688", auth=("neo4j", "your-password"))                                                                                               
domains = json.load(open("export_drl_trained_domains.json"))
                                                                                                                                                                                        
with driver.session() as s:            
      for d in domains:
          s.run("MATCH (d:Domain {id: $id}) SET d.drl_trained = true", id=d["id"])

driver.close()
print(f"Marked {len(domains)} domains as DRL-trained")
