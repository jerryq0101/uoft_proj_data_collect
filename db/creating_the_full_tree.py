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
Recommendations: (If you are gonna read this code)
- Start reading from main(), and go down to total_prerequisites_process_singular_course()
- and_counter and or_counter are global variables that are used to prevent duplication errors
- output_titles_dict is a global variable from another file output.py, containing scraped relationships


General Idea of the way the graph is constructed:
- Every course should be a node on neo4j
- Contains is the relationship for prerequisite trees
- Coreqs_With is the relationship for corequisite trees
- AND and OR are the intermediary nodes that are used to build the individual prerequisite and corequisite trees
- EACH course node (that has prerequisites) will have one outward directed Contains (with root: course_code) relationship (to an AND node), 
and that AND node with have outward directed Contains (with root: course_code) relationships to the prerequisite Course nodes, so on and so forth.
This allows us to identify differing root prerequisite trees from each other.
- The above is same with Corequisite Trees, but with Coreqs_With (root: course_code) relationship labels instead.
- The Grade requirements are stored as properties of Contains relationships, e.g. a course without specific grade requirement means a passing 
requirement, which is min_req: 50% (Also I am 99.99% sure there is no coreqs with a grade requirement )

- On Neo4j, AND indexes should never be duplicated, same with OR
- Course nodes should also never be duplicated (one per course)
- Contains and Coreqs_With relationships with same root and same start node and same end node, should (likely) be never be duplicated as well 
(there may be exceptions with esoteric prerequisites)
"""


def check_if_exists(tx, code):
    """
    Checks if node exists on neo4j database

    Args:
    - code (str): The code of the course to check for 

    Returns:
    - (bool): True if node exists, False otherwise
    """
    node_exists = tx.run(
        """
            MATCH (c:Course {code: $code})
            WITH COUNT(c) > 0 as exists
            RETURN exists
        """,
        code=code
    ).data()[0]['exists']
    return node_exists


def create_course(tx, code, full_name):
    """
    Creates a new Course node if course does not exist already

    Args:
    - code (str): The code of the course to create
    - full_name (str): The full name of the course to create

    Returns:
    - (dict): The result of the query
    """
    node_exists = check_if_exists(tx, code)
    
    if node_exists:
        return
    else:
        result = tx.run("""
            CREATE (c:Course {code: $code, full_name: $full_name})
            RETURN c.code AS code
        """, code=code, full_name=full_name)
        return result.data()

# REDUNDANCY INDEXING Global Variables
and_counter = 1
or_counter = 1

titles_dict = output_titles_dict

def main():
    """
    Main function to create the data of prerequisites of individual courses into Neo4j.
    """
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


def total_prerequisites_process_singular_course(session, code):
    """
    Entire process of checking if prerequisites are already loaded, building the prerequisite tree, adding the prerequisite tree to the root node. (Note still have to call the and or function helper)
    - All while checking for duplication of nodes and relationships in the database so that no repetition occurs.

    Args:
    - session (Neo4jDriver.session)
    - code (str): the code of the course (that exists on neo4j) to add prerequisites to

    """
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



def set_latest_and_or_indexes(result):
    """
    Syncs the latest AND + OR indexes in the database to here, so that there is no duplication indexing issues. Call this before any insertion operation.

    Args:
    - result (Neo4jDriver.Result): The result of the initial query to get the max indexes of AND and OR

    Note:
    - This function should be called before any insertion operation to prevent any AND OR indexing issues with the Database. 
    like this 

    # Sets the latest AND OR indexes in the database here
    result = driver.execute_query(
        MATCH (and:AND), (or:OR)
        RETURN max(and.index) AS max_and_index, max(or.index) AS max_or_index
    )
    set_latest_and_or_indexes(result)

    """
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


def already_loaded_with_prerequisites(tx, code):
    """
    Checks if a specific relationship that indicates the course is already loaded with prerequisites exists (The outward directed AND relationship)

    Args:
    - tx (Neo4jDriver.Transaction)
    - code (str): The code of the course to check for

    Returns:
    - (bool): True if the relationship exists, False otherwise
    """
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


def add_to_this_course(tx, obj, code, full_title):
    """
    Adds the prerequisite tree to the root course.
    - Prerequisite tree from the AND node downwards is constructed with build_graph
    - Then, this function connects the root course node to the AND node.
    
    Args:
    - tx (Neo4jDriver.Transaction)
    - obj (dict): The object to add to the course
    - code (str): The code of the course to add to
    - full_title (str): The full title of the course to add to

    """
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


def build_graph(item, session, relationship_code):
    """
    Recursion on the list items of prerequisites to build a prerequisite tree for one course.

    Args:
    - item (str | dict | list | tuple)
    - session (Neo4jDriver.Session)
    - relationship_code (str): The code of the course that is the root of the prerequisite tree

    Returns:
    - (dict): The indexed AND root of the incomplete prerequisite tree
    """
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


def gather_under_new_or_block(tx, array, index, relationship_code):
    """
    gather_under_new_or_block
    - Gathers existing nodes under a new OR block. 
    - Adds a parent relationship to each connection *
    - IF course has a min grade requirement, also add that to the contains relationship.

    Objects in array should be of format {type: str,  code: str | index: int}
        type = "Course" | "OR" | "AND"

    (expectation) index = current max index of OR block + 1 

    Args:
    - tx (Neo4jDriver.Transaction)
    - array (list): The list of objects to gather under the new OR block
    - index (int): The current max index + 1 of the OR block (to prevent duplication errors)
    - relationship_code (str): Course that is the root of these Contains relationships (param of Contains relationship on Neo4j)

    """
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


def gather_under_new_and_block(tx, array, index, relationship_code):
    """
    Modified gather_under_new_and_block
    - Gather array of existing objects under a new AND node
    - Adds a parent relationship (as root) to each connection *

    Objects should be of format {type: str,  code: str | index: int}
        type = "Course" | "OR" | "AND"

    index = current max index of AND block + 1

    Args:
    - tx (Neo4jDriver.Transaction)
    - array (list): The list of objects to gather under the new AND block
    - index (int): The current max index + 1 of the AND block (to prevent duplication errors)
    - relationship_code (str): Course that is the root of these Contains relationships (param of Contains relationship on Neo4j)

    """
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
    """
    Gathering array of objects under a new OR block (with relationship_code as the Coreqs_With relationship param)

    Objects should be of format {type: str,  code: str | index: int}
        type = "Course" | "OR" | "AND"
    
    (expectation) index = current max index of OR block + 1

    Args:
    - tx (Neo4jDriver.Transaction)
    - array (list): The list of objects to gather under the new OR block
    - index (int): The current max index + 1 of the OR block (to prevent duplication errors)
    - relationship_code (str): Course that is the root of these Coreqs_With relationships (param of Coreqs_With relationship on Neo4j)
    """
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
    """
    Gathering array of objects under a new AND block (with relationship_code as the Coreqs_With relationship param)

    Objects should be of format {type: str,  code: str | index: int}
        type = "Course" | "OR" | "AND"
    
    (expectation) index = current max index of AND block + 1

    Args:
    - tx (Neo4jDriver.Transaction)
    - array (list): The list of objects to gather under the new AND block
    - index (int): The current max index + 1 of the AND block (to prevent duplication errors)
    - relationship_code (str): Course that is the root of these Coreqs_With relationships (param of Coreqs_With relationship on Neo4j)
    """
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


def build_corequisites(item, session, relationship_code):
    """
    Recursive function for building the corequisite tree onto Neo4j for one course. Aside from the actual corequisite tree course root.

    item: something in the array / tuple that is looked deeper into
    session: the neo4j session
    relationship_code: the root of the corequisite relationship

    Args:
    - item (str | dict | list | tuple)
    - session (Neo4jDriver.Session)
    - relationship_code (str): The code of the course that is the root of the corequisite tree

    Returns:
    - (dict): The indexed AND root of the incomplete corequisite tree
    """
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


def total_corequisites_process_singular_course(session, code):
    """
    Sub process of checking if corequiites are already loaded, building the corequisites tree, adding the corequisite tree to the root node

    Args:
    - session (Neo4jDriver.Session)
    - code (str): The code of the course to process

    """
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


def add_co_to_this_course(tx, obj, code, full_title):
    """
    Adds the corequisite tree to the root course, after finishing constructing the tree with AND root.

    Args:
    - tx (Neo4jDriver.Transaction)
    - obj (dict): The neo4j details of AND index to add to the course
    - code (str): The code of the course to add to
    - full_title (str): The full title of the course to add to
    """
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


def already_loaded_with_corequisites(tx, code):
    """
    Checks whether a course already has its corequisites loaded. (Via Checking the direct Coreqs_With AND relationship from the course node).
    Obviously if the course doesn't exist yet on neo4j, it doesn't have its corequisites loaded.

    Args:
    - tx (Neo4jDriver.Transaction)
    - code (str): The code of the course to check

    Returns:
    - (bool): Whether the course has its corequisites loaded
    """
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