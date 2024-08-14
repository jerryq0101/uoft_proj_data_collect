import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

from neo4j import GraphDatabase

URI = os.getenv("N4J_DB_URI")
AUTH = ("neo4j", os.getenv("N4J_DB_PASS"))


with GraphDatabase.driver(URI, auth=AUTH) as driver: # type: ignore
    driver.verify_connectivity()

    records, summar, keys = driver.execute_query(
        "MATCH (n) RETURN n LIMIT 5"
    )

    for thing in records:
        print(thing)