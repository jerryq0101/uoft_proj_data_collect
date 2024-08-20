# TODO
# - Testing the corequisites tree building
# - Structure of the file and compart
# - Naming scheme of functions and docstring practices

import sys
import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

from neo4j import GraphDatabase

URI = os.getenv("N4J_DB_URI")
AUTH = ("neo4j", os.getenv("N4J_DB_PASS"))

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add the 'files' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'files'))

from lib import explore_all_focuses, process_code_coreq, process_code_prereq
from output import *


"""
Checks if node exists
"""
def check_if_exists(tx, code):
    node_exists = tx.run(
        """
            MATCH (c:Course {code: $code})
            WITH COUNT(c) > 0 as exists
            RETURN exists
        """,
        code=code
    ).data()[0]['exists']
    return node_exists

"""
Creates a new Course node if course does not exist already
"""
def create_course(tx, code, full_name):
    node_exists = check_if_exists(tx, code)
    
    if node_exists:
        return
    else:
        result = tx.run("""
            CREATE (c:Course {code: $code, full_name: $full_name})
            RETURN c.code AS code
        """, code=code, full_name=full_name)
        return result.data()

and_counter = 1
or_counter = 1

titles_dict = output_titles_dict

def main():
    global and_counter
    global or_counter
    global titles_dict
    
    # Setting up the global variables
    all_codes = output_codes
    titles_dict = output_titles_dict
    all_prereq_var_names = []
    all_coreq_var_names = []
    for code in all_codes:
        pre_code = process_code_prereq(code)
        cor_code = process_code_coreq(code)
        all_prereq_var_names.append(pre_code)
        all_coreq_var_names.append(cor_code)

    # Start Graph Driver Session
    with GraphDatabase.driver(URI, auth=AUTH) as driver: # type: ignore
        driver.verify_connectivity()

        with driver.session(database="neo4j") as session:
            assert (len(all_codes) == len(all_prereq_var_names) == len(all_coreq_var_names)), "Lengths of all_codes, all_prereq_var_names, and all_coreq_var_names should be the same"

            # Sets the latest AND OR indexes in the database here
            result = driver.execute_query("""
                MATCH (and:AND), (or:OR)
                RETURN max(and.index) AS max_and_index, max(or.index) AS max_or_index
            """)
            set_latest_and_or_indexes(result)

            # Top Level
            for i in range(len(all_codes)):
                capital_course_code = all_codes[i]
                total_prerequisites_process_singular_course(session, capital_course_code)
                total_corequisites_process_singular_course(session, capital_course_code)
                
            

"""
Entire process of checking if prerequisites are already loaded, building the prerequisite tree, adding the prerequisite tree to the root node. (Note still have to call the and or function helper)
"""
def total_prerequisites_process_singular_course(session, code):
    global titles_dict

    # Check if course already has prerequisites loaded
    already_has_prereqs = session.execute_write(already_loaded_with_prerequisites, code)

    # At this point, the node might not exist, or it might exist with no prerequisites yet

    # Build the prerequisite tree
    if not already_has_prereqs:
        processed_pre_string = process_code_prereq(code)
        current_pre_list = globals()[processed_pre_string]
        obj = build_graph(current_pre_list, session, code)
        # Add the prerequisite tree to the root course
        session.execute_write(add_to_this_course, obj, code, titles_dict[code]) # type: ignore

"""
Syncs the latest AND + OR indexes in the database to here, so that there is no duplication indexing issues. Call this before any insertion operation.
"""
def set_latest_and_or_indexes(result):
    global and_counter
    global or_counter
    # Set initial index counts for the AND and OR blocks, so that when adding mid way there are no issues.

    # Process the result to get the maximum indexes
    for record in result.records:
        max_and_index = record["max_and_index"]
        max_or_index = record["max_or_index"]
        # Set and_counter and or_counter to the max indexes
        if max_and_index is not None:
            and_counter = max_and_index + 1
        elif max_and_index is None:
            and_counter = 1
        if max_or_index is not None:
            or_counter = max_or_index + 1
        elif max_or_index is None:
            or_counter = 1
        print(f"Max AND index: {max_and_index}, Max OR index: {max_or_index}")

    
"""
Checks if a specific relationship that indicates the course is already loaded with prerequisites exists
"""
def already_loaded_with_prerequisites(tx, code):
    node_exists = check_if_exists(tx, code)
    if node_exists:
        relationship_exists = tx.run(
            """
                MATCH (c:Course {code: $code})-[:Contains {root: $code}]->(and:AND)
                WITH COUNT(and) > 0 as exists
                RETURN exists
            """,
            code=code
        ).data()[0]['exists']
        return relationship_exists
    else:
        return False


"""
Adds the prerequisite tree to the root course, after finishing constructing the tree
"""
def add_to_this_course(tx, obj, code, full_title):
    node_exists = tx.run(
        """
            MATCH (c:Course {code: $code})
            WITH COUNT(c) > 0 as exists
            RETURN exists
        """,
        code=code
    ).data()[0]['exists']

    if node_exists and obj is not None:
        # node exists, list of pre/cor is not empty => match + add relationship

        # match to it and add a containment relationship
        # obj should be a dict with "type": "AND", because the pre and coreq list are always lists
        tx.run(
            """
                MATCH (c:Course {code: $code})
                MATCH (and_block:AND {index: $index})
                MERGE (c)-[:Contains {root: $parent}]->(and_block)
            """,
            code=code,
            index=obj["index"],
            parent=code
        )
    elif not node_exists and obj is not None:
        # node not exist and list of pre/cor is not empty => create + add relationship

        # create the course and add a containment relationship
        tx.run(
            """
                CREATE (c:Course {code: $code, full_name: $full_title})
                WITH c
                MATCH (and_block:AND {index: $index})
                MERGE (c)-[:Contains {root: $parent}]->(and_block)
            """,
            code=code,
            index=obj["index"],
            parent=code,
            full_title=full_title
        )
    elif not node_exists and obj is None:
        # node not exist, and list of corequisites is empty => create a node and add nothing
        tx.run(
            """
                CREATE (c:Course {code: $code, full_name: $full_title})
            """,
            code=code,
            full_title=full_title
        )
    else:
        return


"""
Recursion on the list items of prerequisites to build a prerequisite tree for one course
"""
def build_graph(item, session, relationship_code):
    global or_counter
    global and_counter
    global titles_dict

    item_type = type(item)
    
    if item_type == str or item_type == dict:
        # This is a single course, string = no grade requirement, dict = grade requirement
        # Create a new node with the course code
        # If it is a dict, add the grade requirement
        if item_type == str:
            session.execute_write(create_course, item, titles_dict[item])
            return {
                "type": "Course",
                "code": item
            }
        else:
            session.execute_write(create_course, item["code"], titles_dict[item["code"]])
            return {
                "type": "Course",
                "code": item["code"],
                "min_req": item["min_req"]
            }
    
    elif item_type == list:
        # we know that this is an AND relationship
        
        # Case when pre / coreq array is empty (when first called) => Return nothing 
        if not item:
            return
        
        results = []
        for e in item:
            # result will be a dict
            result = build_graph(e, session, relationship_code)
            results.append(result)

            # if string search for the course code and do a containment relationship
            # if dict, check OR or AND, and then do a containment relationship
        session.execute_write(gather_under_new_and_block, results, and_counter, relationship_code) # type: ignore
        
        and_counter += 1 # type: ignore

        # Returns for the future 
        return {
            "type": "AND",
            "index": and_counter-1
        }

    elif item_type == tuple:
        # We know that this is an OR relationship
        
        results = []

        for e in item:
            result = build_graph(e, session, relationship_code)
            results.append(result)
        
        session.execute_write(gather_under_new_or_block, results, or_counter, relationship_code) # type: ignore

        or_counter += 1 # type: ignore

        return {
            "type": "OR",
            "index": or_counter-1
        }


"""
Modified gather_under_new_or_block
- Gathers existing nodes under a new OR block. 
- Adds a parent relationship to each connection *
- IF course has a min grade requirement, also add that to the contains relationship.

Objects in array should be of format {type: str,  code: str | index: int}
    type = "Course" | "OR" | "AND"

index = current max index of OR block + 1
"""
def gather_under_new_or_block(tx, array, index, relationship_code):
    try:
        # Create a new OR block
        tx.run("""
            CREATE (or_block:OR {index: $index})
            RETURN or_block.index AS index
        """, index=index
        )

        for item in array:
            if item["type"] == "Course":
                # check if there is a min grade requirement
                if "min_req" in item:
                    tx.run(
                        """
                        MATCH (c:Course {code: $code})
                        MATCH (or_block:OR {index: $index})
                        MERGE (or_block)-[:Contains {root: $parent, min_req: $min_req}]->(c)
                        """,
                        code=item["code"],
                        index=index,
                        parent=relationship_code,
                        min_req=item["min_req"]
                    )
                else:
                    tx.run(
                        """
                        MATCH (c:Course {code: $code})
                        MATCH (or_block:OR {index: $index})
                        MERGE (or_block)-[:Contains {root: $parent, min_req: $min_req}]->(c)
                        """,
                        code=item["code"],
                        index=index,
                        parent=relationship_code,
                        min_req="50%"
                    )
            elif item["type"] == "OR":
                tx.run(
                    """
                    MATCH (or_block2:OR {index: $child_or_index})
                    MATCH (or_block:OR {index: $or_index})
                    MERGE (or_block)-[:Contains {root: $parent}]->(or_block2)
                    """,
                    child_or_index=item["index"],
                    or_index=index,
                    parent=relationship_code
                )
            elif item["type"] == "AND":
                tx.run(
                    """
                    MATCH (and_block:AND {index: $child_and_index})
                    MATCH (or_block:OR {index: $or_index})
                    MERGE (or_block)-[:Contains {root: $parent}]->(and_block)
                    """,
                    child_and_index=item["index"],
                    or_index=index,
                    parent=relationship_code
                )

    except Exception as e:
        print(f"An error occurred: {str(e)}")


"""
Modified gather_under_new_and_block
- Gather array of existing objects under a new AND node
- Adds a parent relationship (as root) to each connection *

Objects should be of format {type: str,  code: str | index: int}
    type = "Course" | "OR" | "AND"

index = current max index of AND block + 1

"""
def gather_under_new_and_block(tx, array, index, relationship_code):
    # Create a new AND block with the given index
    tx.run("""
        CREATE (and_block:AND {index: $index})
        RETURN and_block.index AS index
    """, index=index)

    # ADD relationships to the AND block
    for item in array:
        if item["type"] == "Course":
            # check if min grade is in item
            if "min_req" in item:
                tx.run(
                    """
                    MATCH (c:Course {code: $code})
                    MATCH (and_block:AND {index: $index})
                    MERGE (and_block)-[:Contains {root: $parent, min_req: $min_req}]->(c)
                    """,
                    code=item["code"],
                    index=index,
                    parent=relationship_code,
                    min_req=item["min_req"]
                )
            else:
                tx.run(
                    """
                    MATCH (c:Course {code: $code})
                    MATCH (and_block:AND {index: $index})
                    MERGE (and_block)-[:Contains {root: $parent, min_req: $min_req}]->(c)
                    """,
                    code=item["code"],
                    index=index,
                    parent=relationship_code,
                    min_req="50%"
                )
        elif item["type"] == "OR":
            tx.run(
                """
                MATCH (or_block:OR {index: $child_or_index})
                MATCH (and_block:AND {index: $and_index})
                MERGE (and_block)-[:Contains {root: $parent}]->(or_block)
                """,
                child_or_index=item["index"],
                and_index=index,
                parent=relationship_code
            )
        elif item["type"] == "AND":
            tx.run(
                """
                MATCH (and_block2:AND {index: $child_and_index})
                MATCH (and_block:AND {index: $and_index})
                MERGE (and_block)-[:Contains {root: $parent}]->(and_block2)
                """,
                child_and_index = item["index"],
                and_index=index,
                parent=relationship_code
            )



"""
________________________________________________________Corequisites________________________________________________________

"""

def gather_co_new_or_block(tx, array, index, relationship_code):
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
                    MERGE (or_block)-[:Coreqs_With {root: $parent}]->(c)
                    """,
                    code=item["code"],
                    index=index,
                    parent=relationship_code
                )
            elif item["type"] == "OR":
                tx.run(
                    """
                    MATCH (or_block2:OR {index: $child_or_index})
                    MATCH (or_block:OR {index: $or_index})
                    MERGE (or_block)-[:Coreqs_With {root: $parent}]->(or_block2)
                    """,
                    child_or_index=item["index"],
                    or_index=index,
                    parent=relationship_code
                )
            elif item["type"] == "AND":
                tx.run(
                    """
                    MATCH (and_block:AND {index: $child_and_index})
                    MATCH (or_block:OR {index: $or_index})
                    MERGE (or_block)-[:Coreqs_With {root: $parent}]->(and_block)
                    """,
                    child_and_index=item["index"],
                    or_index=index,
                    parent=relationship_code
                )

    except Exception as e:
        print(f"An error occurred: {str(e)}")


def gather_co_new_and_block(tx, array, index, relationship_code):
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
                MERGE (and_block)-[:Coreqs_With {root: $parent}]->(c)
                """,
                code=item["code"],
                index=index,
                parent=relationship_code,
            )
                
        elif item["type"] == "OR":
            tx.run(
                """
                MATCH (or_block:OR {index: $child_or_index})
                MATCH (and_block:AND {index: $and_index})
                MERGE (and_block)-[:Coreqs_With {root: $parent}]->(or_block)
                """,
                child_or_index=item["index"],
                and_index=index,
                parent=relationship_code
            )
        elif item["type"] == "AND":
            tx.run(
                """
                MATCH (and_block2:AND {index: $child_and_index})
                MATCH (and_block:AND {index: $and_index})
                MERGE (and_block)-[:Coreqs_With {root: $parent}]->(and_block2)
                """,
                child_and_index = item["index"],
                and_index=index,
                parent=relationship_code
            )


"""
Recursive function for corequisites

item: something in the array / tuple that is looked deeper into
session: the neo4j session
relationship_code: the root of the corequisite relationship
"""
def build_corequisites(item, session, relationship_code):
    global or_counter
    global and_counter
    global titles_dict

    item_type = type(item)
    
    if item_type == str:
        # This part is different because there is no grade requirement in a corequisite
        session.execute_write(create_course, item, titles_dict[item])
        return {
            "type": "Course",
            "code": item
        }
    elif item_type == list:

        # Case: When pre / coreq array is empty (when first called) => return Nothing 
        if not item:
            return 
        
        results = []
        for e in item:
            result = build_corequisites(e, session, relationship_code)
            results.append(result)
        
        session.execute_write(gather_co_new_and_block, results, and_counter, relationship_code)
        and_counter += 1

        return {
            "type": "AND",
            "index": and_counter - 1
        }
    elif item_type == tuple:
        results = []
        for e in item:
            result = build_corequisites(e, session, relationship_code)
            results.append(result)
        
        session.execute_write(gather_co_new_or_block, results, or_counter, relationship_code)
        or_counter += 1

        return {
            "type": "OR",
            "index": or_counter - 1
        }


"""
Entire process of checking if corequiites are already loaded, building the corequisites tree, adding the corequisite tree to the root node
"""
def total_corequisites_process_singular_course(session, code):
    global titles_dict

    # Check if course already has corequisites loaded
    already_has_coreqs = session.execute_write(already_loaded_with_corequisites, code)

    # At this point, the node might not exist, or it might exist with no prerequisites yet

    # Build the corequisites tree
    if not already_has_coreqs:
        processed_coreq_string = process_code_coreq(code)
        current_cor_list = globals()[processed_coreq_string]
        obj = build_corequisites(current_cor_list, session, code)
        # Add the corequisites tree to the root course
        session.execute_write(add_co_to_this_course, obj, code, titles_dict[code]) # type: ignore


"""
Adds the corequisite tree to the root course, after finishing constructing the tree
"""
def add_co_to_this_course(tx, obj, code, full_title):
    node_exists = tx.run(
        """
            MATCH (c:Course {code: $code})
            WITH COUNT(c) > 0 as exists
            RETURN exists
        """,
        code=code
    ).data()[0]['exists']

    if node_exists and obj is not None:
        # node exists, list of pre/cor is not empty => match + add relationship

        # match to it and add a containment relationship
        # obj should be a dict with "type": "AND", because the pre and coreq list are always lists
        tx.run(
            """
                MATCH (c:Course {code: $code})
                MATCH (and_block:AND {index: $index})
                MERGE (c)-[:Coreqs_With {root: $parent}]->(and_block)
            """,
            code=code,
            index=obj["index"],
            parent=code
        )
    elif not node_exists and obj is not None:
        # node not exist and list of pre/cor is not empty => create + add relationship

        # create the course and add a containment relationship
        tx.run(
            """
                CREATE (c:Course {code: $code, full_name: $full_title})
                WITH c
                MATCH (and_block:AND {index: $index})
                MERGE (c)-[:Coreqs_With {root: $parent}]->(and_block)
            """,
            code=code,
            index=obj["index"],
            parent=code,
            full_title=full_title
        )
    elif not node_exists and obj is None:
        # node not exist, and list of corequisites is empty => create a node and add nothing
        tx.run(
            """
                CREATE (c:Course {code: $code, full_name: $full_title})
            """,
            code=code,
            full_title=full_title
        )
    else:
        return


"""
Checks whether a course already has its corequisites loaded
"""
def already_loaded_with_corequisites(tx, code):
    node_exists = check_if_exists(tx, code)
    if node_exists:
        relationship_exists = tx.run(
            """
                MATCH (c:Course {code: $code})-[:Coreqs_With {root: $code}]->(and:AND)
                WITH COUNT(and) > 0 as exists
                RETURN exists
            """,
            code=code
        ).data()[0]['exists']
        return relationship_exists
    else:
        return False


if __name__ == "__main__":
    main()