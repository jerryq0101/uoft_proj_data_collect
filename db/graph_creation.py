import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

from neo4j import GraphDatabase

URI = os.getenv("N4J_DB_URI")
AUTH = ("neo4j", os.getenv("N4J_DB_PASS"))

"""
Creating, Loading and connecting courses into Neo4j

Driver.execute_query() was introduced with the version 5.8 of the driver. 
However, I am still going to use session and transaction for the sake of more control
"""

def main():
    with GraphDatabase.driver(URI, auth=AUTH) as driver: # type: ignore
        driver.verify_connectivity()

        with driver.session(database="neo4j") as session:
            session.execute_write(create_course, "MAT133Y1", "MAT133Y1: Calculus and Linear Algebra for Commerce")
            session.execute_write(create_course, "MAT135H1", "MAT135H1: Calculus I")
            session.execute_write(create_course, "MAT136H1", "MAT136H1: Calculus II")
            session.execute_write(create_course, "MAT137Y1", "MAT137Y1: Calculus with Proofs")
            session.execute_write(create_course, "MAT157Y1", "MAT157Y1: Analysis I")
            session.execute_write(create_course, "MAT223H1","MAT223H1: Linear Algebra I")
            session.execute_write(create_course, "MAT240H1", "MAT240H1: Algebra I")
            
            """
            OR (1)
            contains:
            * MAT133 Node
            * MAT135 Node
            """
            # or_latest = 1
            session.execute_write(
                gather_under_new_or_block,
                [
                    {"type": "Course", "code": "MAT133Y1"},
                    {"type": "Course", "code": "MAT135H1"}
                ],
                1
            )
            
            """
            AND (1)
            contains:
            * OR (1)
            * MAT136 Node
            """
            # and_latest = 1
            session.execute_write(
                gather_under_new_and_block,
                [
                    {"type": "Course", "code": "MAT136H1"},
                    {"type": "OR", "index": 1}
                ],
                1
            )

            """
            OR (2)
            Contains:
            * AND (1)
            * MAT137 Node
            * MAT157 Node
            """
            # or_latest = 2
            session.execute_write(
                gather_under_new_or_block,
                [
                    {"type": "AND", "index": 1},
                    {"type": "Course", "code": "MAT137Y1"},
                    {"type": "Course", "code": "MAT157Y1"}
                ],
                2
            )

            """
            OR (3)
            Contains:
            * MAT223 Node
            * MAT240 Node
            """
            # or_latest = 3
            session.execute_write(
                gather_under_new_or_block,
                [
                    {"type": "Course", "code": "MAT223H1"},
                    {"type": "Course", "code": "MAT240H1"}
                ],
                3
            )

            """
            AND (2)
            Contains:
            * OR (2)
            * OR (3)
            """
            # and_latest = 2
            session.execute_write(
                gather_under_new_and_block,
                [
                    {"type": "OR", "index": 2},
                    {"type": "OR", "index": 3}
                ],
                2
            )


"""
Gather array of existing objects under a new AND node

Objects should be of format {type: str,  code: str | index: int}
    type = "Course" | "OR" | "AND"

index = current max index of AND block + 1

"""
def gather_under_new_and_block(tx, array, index):
    # Create a new AND block with the given index
    tx.run("""
        CREATE (and_block:AND {index: $index})
        RETURN and_block.index AS index
    """, index=index)

    # ADD relationships to the AND block
    for item in array:
        if item["type"] == "Course":
            tx.run(
                """
                MATCH (c:Course {code: $code})
                MATCH (and_block:AND {index: $index})
                MERGE (and_block)-[:Contains]->(c)
                """,
                code=item["code"],
                index=index
            )
        elif item["type"] == "OR":
            tx.run(
                """
                MATCH (or_block:OR {index: $child_or_index})
                MATCH (and_block:AND {index: $and_index})
                MERGE (and_block)-[:Contains]->(or_block)
                """,
                child_or_index=item["index"],
                and_index=index
            )
        elif item["type"] == "AND":
            tx.run(
                """
                MATCH (and_block2:AND {index: $child_and_index})
                MATCH (and_block:AND {index: $and_index})
                MERGE (and_block)-[:Contains]->(and_block2)
                """,
                child_and_index = item["index"],
                and_index=index
            )


"""
Gathers existing nodes under a new OR block

Objects in array should be of format {type: str,  code: str | index: int}
    type = "Course" | "OR" | "AND"

index = current max index of OR block + 1
"""
def gather_under_new_or_block(tx, array, index):
    try:
        # Create a new OR block
        tx.run("""
            CREATE (or_block:OR {index: $index})
            RETURN or_block.index AS index
        """, index=index
        )

        for item in array:
            if item["type"] == "Course":
                tx.run(
                    """
                    MATCH (c:Course {code: $code})
                    MATCH (or_block:OR {index: $index})
                    MERGE (or_block)-[:Contains]->(c)
                    """,
                    code=item["code"],
                    index=index
                )
            elif item["type"] == "OR":
                tx.run(
                    """
                    MATCH (or_block2:OR {index: $child_or_index})
                    MATCH (or_block:OR {index: $or_index})
                    MERGE (or_block)-[:Contains]->(or_block2)
                    """,
                    child_or_index=item["index"],
                    or_index=index
                )
            elif item["type"] == "AND":
                tx.run(
                    """
                    MATCH (and_block:AND {index: $child_and_index})
                    MATCH (or_block:OR {index: $or_index})
                    MERGE (or_block)-[:Contains]->(and_block)
                    """,
                    child_and_index=item["index"],
                    or_index=index
                )

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def create_course(tx, code, full_name):
    result = tx.run("""
        CREATE (c:Course {code: $code, full_name: $full_name})
        RETURN c.code AS code
    """, code=code, full_name=full_name)
    return result.data()

if __name__ == "__main__":
    main()