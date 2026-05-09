#!/usr/bin/env python3
"""
Ingest exported Neo4j data back into a fresh database.
Run this after loading the core capability graph to restore runtime data.
"""

import json
import ast
from neo4j import GraphDatabase
from datetime import datetime

# Update these connection details for your target database
NEO4J_URI = "bolt://localhost:7688"  # Change to your Neo4j instance
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"  # Update with your password

def parse_neo4j_node_string(node_str):
    """Parse Neo4j node string representation into dict"""
    print(f"Parsing node string: {node_str[:200]}...")
    # Extract properties from the node string
    # Format: <Node ... properties={...}>
    start = node_str.find("properties=")
    if start == -1:
        return {}

    # Find the opening brace after "properties="
    brace_start = node_str.find("{", start)
    if brace_start == -1:
        return {}

    # Count braces to find the matching closing brace
    count = 0
    end = brace_start
    for i, char in enumerate(node_str[brace_start:], brace_start):
        if char == '{':
            count += 1
        elif char == '}':
            count -= 1
            if count == 0:
                end = i
                break

    if end == brace_start:
        return {}

    # Extract the properties string
    props_str = node_str[brace_start:end+1]

    # Parse manually since neo4j.time.DateTime objects are not standard Python
    properties = {}
    # Split by commas, but be careful about nested structures
    parts = []
    current_part = ""
    in_string = False
    in_nested = 0
    escape_next = False

    for char in props_str[1:-1]:  # Skip outer braces
        if escape_next:
            current_part += char
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            current_part += char
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            current_part += char
            continue

        if not in_string:
            if char in '{[(':
                in_nested += 1
            elif char in ')]}':
                in_nested -= 1
            elif char == ',' and in_nested == 0:
                parts.append(current_part.strip())
                current_part = ""
                continue

        current_part += char

    if current_part.strip():
        parts.append(current_part.strip())

    # Parse each key-value pair
    for part in parts:
        if ':' not in part:
            continue
        key, value = part.split(':', 1)
        key = key.strip().strip("'\"")
        value = value.strip()

        # Handle different value types
        if value.startswith("'") and value.endswith("'"):
            # String
            properties[key] = value[1:-1]
        elif value.startswith('"') and value.endswith('"'):
            # String
            properties[key] = value[1:-1]
        elif value in ['True', 'False']:
            # Boolean
            properties[key] = value == 'True'
        elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            # Integer
            properties[key] = int(value)
        elif '.' in value and all(c.isdigit() or c in '.-' for c in value):
            # Float
            try:
                properties[key] = float(value)
            except:
                properties[key] = value
        elif 'neo4j.time.DateTime(' in value:
            # Convert neo4j DateTime to ISO string
            # Format: neo4j.time.DateTime(2026, 5, 4, 7, 12, 18, 852000000, tzinfo=<UTC>)
            try:
                dt_str = value.replace('neo4j.time.DateTime(', '').replace('tzinfo=<UTC>)', '').replace(')', '').strip()
                dt_parts = [int(x.strip()) for x in dt_str.split(',')]
                dt = datetime(dt_parts[0], dt_parts[1], dt_parts[2], dt_parts[3], dt_parts[4], dt_parts[5], dt_parts[6] // 1000)
                properties[key] = dt.isoformat()
                print(f"Converted {key}: {value} -> {properties[key]}")
            except Exception as e:
                print(f"Failed to convert {key}: {value} - Error: {e}")
                properties[key] = value
        else:
            # Keep as string for complex types
            properties[key] = value

    return properties

def ingest_generated_outputs(driver):
    """Ingest GeneratedOutput nodes"""
    print("Loading generated outputs...")
    with open("export_generated_outputs.json", "r") as f:
        outputs = json.load(f)

    count = 0
    with driver.session() as session:
        for item in outputs:
            props = parse_neo4j_node_string(item["o"])

            try:
                session.run("""
                    CREATE (o:GeneratedOutput {
                        cache_key: $cache_key,
                        org_type: $org_type,
                        created_at: datetime($created_at),
                        epics_count: $epics_count,
                        phases_count: $phases_count,
                        hit_count: $hit_count,
                        output_json: $output_json
                    })
                """, **props)
                count += 1
            except Exception as e:
                print(f"Error creating GeneratedOutput: {e}")
                print(f"Properties: {list(props.keys())}")

    print(f"Created {count} GeneratedOutput nodes")

def ingest_training_runs(driver):
    """Ingest TrainingRun nodes"""
    print("Loading training runs...")
    with open("export_training_runs.json", "r") as f:
        runs = json.load(f)

    count = 0
    with driver.session() as session:
        for item in runs:
            props = parse_neo4j_node_string(item["t"])

            try:
                session.run("""
                    CREATE (t:TrainingRun {
                        run_id: $run_id,
                        domain_name: $domain_name,
                        sector: $sector,
                        device: $device,
                        episodes: $episodes,
                        final_reward: $final_reward,
                        avg_reward_last10: $avg_reward_last10,
                        policy_version: $policy_version,
                        episode_log: $episode_log,
                        timestamp: datetime($timestamp)
                    })
                """, **props)
                count += 1
            except Exception as e:
                print(f"Error creating TrainingRun: {e}")
                print(f"Properties: {list(props.keys())}")

    print(f"Created {count} TrainingRun nodes")

def ingest_chat_sessions(driver):
    """Ingest ChatSession and ChatMessage nodes with relationships"""
    print("Loading chat sessions...")
    with open("export_chat_sessions.json", "r") as f:
        sessions = json.load(f)

    session_count = 0
    message_count = 0

    with driver.session() as session:
        # Group messages by session
        session_messages = {}
        for item in sessions:
            session_props = parse_neo4j_node_string(item["s"])
            message_props = parse_neo4j_node_string(item["m"])

            session_id = session_props.get("session_id")
            if not session_id:
                continue

            if session_id not in session_messages:
                session_messages[session_id] = {
                    "session": session_props,
                    "messages": []
                }

            session_messages[session_id]["messages"].append(message_props)

        # Create sessions and messages
        for session_id, data in session_messages.items():
            session_props = data["session"]
            messages = data["messages"]

            try:
                # Create session
                result = session.run("""
                    CREATE (s:ChatSession {
                        session_id: $session_id,
                        title: $title,
                        message_count: $message_count,
                        created_at: datetime($created_at),
                        last_active: datetime($last_active)
                    })
                    RETURN id(s) as session_id
                """, **session_props)
                neo4j_session_id = result.single()["session_id"]
                session_count += 1

                # Create messages and relationships
                for msg_props in messages:
                    try:
                        session.run("""
                            MATCH (s:ChatSession)
                            WHERE id(s) = $session_id
                            CREATE (s)-[:HAS_MESSAGE]->(m:ChatMessage {
                                message_id: $message_id,
                                role: $role,
                                content: $content,
                                sources_json: $sources_json,
                                created_at: datetime($created_at)
                            })
                        """, session_id=neo4j_session_id, **msg_props)
                        message_count += 1
                    except Exception as e:
                        print(f"Error creating ChatMessage: {e}")

            except Exception as e:
                print(f"Error creating ChatSession {session_id}: {e}")

    print(f"Created {session_count} ChatSession nodes and {message_count} ChatMessage nodes")

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        # Test connection
        driver.verify_connectivity()
        print("Connected to Neo4j database")

        # Ingest data
        ingest_generated_outputs(driver)
        ingest_training_runs(driver)
        ingest_chat_sessions(driver)

        print("\nIngestion complete! Runtime data has been restored.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()