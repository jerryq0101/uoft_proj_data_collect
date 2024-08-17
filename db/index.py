import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

from neo4j import GraphDatabase

URI = os.getenv("N4J_DB_URI")
AUTH = ("neo4j", os.getenv("N4J_DB_PASS"))

"""
Driver.execute_query() was introduced with the version 5.8 of the driver. 
However, I am still going to use session and transaction for the sake of more control
"""

def main():
    with GraphDatabase.driver(URI, auth=AUTH) as driver: # type: ignore
        driver.verify_connectivity()

        # Setup the database
        driver.execute_query("CREATE CONSTRAINT unique_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE")

        with driver.session(database="neo4j") as session:
            results = session.execute_read(get_names)
            print(results)

            # test adding a name
            # try:
            #     result2 = session.execute_write(add_name, "Vincent Bisset de Gramont")
            #     print(result2)
            # except:
            #     print("Name already exists")


            

def add_name(tx, name):
    result = tx.run("""
        CREATE (a:Course {name: $name1})
        RETURN a.name AS name
    """, name1=name)
    return result.data()

def get_names(tx):
    result = tx.run("""
        MATCH (a:Course)
        RETURN a.code AS code
    """)
    return result.data()


if __name__ == "__main__":
    main()