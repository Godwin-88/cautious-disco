import os
import sys
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# The path to your Cypher script
CYPHER_FILE = "capability_canvas (3).cypher"

def run_migration():
    if not all([URI, USERNAME, PASSWORD]):
        print("Error: Neo4j credentials not found in environment variables.")
        sys.exit(1)

    if not os.path.exists(CYPHER_FILE):
        print(f"Error: Cypher file '{CYPHER_FILE}' not found.")
        sys.exit(1)

    print(f"Connecting to Neo4j at {URI}...")
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    try:
        with driver.session(database=DATABASE) as session:
            with open(CYPHER_FILE, "r") as f:
                content = f.read()
                
                # Split content into individual statements by semicolon
                # This regex handles statements ending with ; while ignoring potential semicolons inside strings
                statements = [s.strip() for s in re.split(r';(?=(?:[^\'"]*[\'"][^\'"]*[\'"])*[^\'"]*$)', content) if s.strip()]

                print(f"Found {len(statements)} statements to execute.")

                for i, statement in enumerate(statements):
                    try:
                        session.run(statement)
                        if i % 10 == 0 or i == len(statements) - 1:
                            print(f"Executed {i + 1}/{len(statements)}...")
                    except Exception as e:
                        print(f"\nError in statement {i + 1}:")
                        print(f"Statement: {statement[:100]}...")
                        print(f"Error: {e}")
                        # Optional: choose whether to continue or stop on error
                        # sys.exit(1)

        print("\nMigration completed successfully.")

    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    run_migration()
