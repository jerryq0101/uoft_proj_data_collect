# Plan is on Ipad

# loop all course codes
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

from focus_crawl import FocusExplore
from output import *

titles_dict = {}

"""
Finds full titles, and splits to get the upper case course code. (Also make the titles_dict, which is used for recursion)
"""
def explore_all_focuses():
    var = FocusExplore()
    titles = var.crawl_focus_w_cor_full()["titles"]
    
    codes = []
    for i in range(len(titles)):
        codes.append(titles[i].split(":")[0])
        titles_dict[codes[i]] = titles[i]

    return codes


def process_code_prereq(code):
    code = code.lower()
    return code + "_pre"


def process_code_coreq(code):
    code = code.lower()
    return code + "_cor"

"""
Checks if course already exists => doesn't do anything
else => Creates a new course with course code: code, and full name: full_name
"""
def create_course(tx, code, full_name):
    node_exists = tx.run(
        """
            MATCH (c:Course {code: $code})
            WITH COUNT(c) > 0 as exists
            RETURN exists
        """,
        code=code
    ).data()[0]['exists']
    
    if node_exists:
        return
    else:
        result = tx.run("""
            CREATE (c:Course {code: $code, full_name: $full_name})
            RETURN c.code AS code
        """, code=code, full_name=full_name)
        return result.data()

def main():
    # # Testing converting code to variable
    # test_code = process_code_prereq("CSC336H1")
    # pre_list = globals()[test_code]
    # print(pre_list)
    
    # Iterating through all course codes
    all_codes = explore_all_focuses()
    all_prereq_var_names = []
    all_coreq_var_names = []
    for code in all_codes:
        pre_code = process_code_prereq(code)
        cor_code = process_code_coreq(code)
        all_prereq_var_names.append(pre_code)
        all_coreq_var_names.append(cor_code)

    # print(all_prereq_var_names)
    # print(all_coreq_var_names)

    # print(titles_dict)


    # Start Graph Driver Session

    with GraphDatabase.driver(URI, auth=AUTH) as driver: # type: ignore
        driver.verify_connectivity()

        # Set constraints and indexes from an empty database

        with driver.session(database="neo4j") as session:
            assert (len(all_codes) == len(all_prereq_var_names) == len(all_coreq_var_names)), "Lengths of all_codes, all_prereq_var_names, and all_coreq_var_names should be the same"
            
            
            # # Top Level
            # for i in range(len(all_codes)):
            #     capital_course_code = all_codes[i]

            #     current_pre_list = globals()[all_prereq_var_names[i]]

            #     # Should return a dict with "type" and "index" for us to add it to the child of current node
            #     obj = build_graph(current_pre_list, sessio, capital_course_code)
                
            #     # Add obj and a containment relationship to the current node
            #     add_to_this_course(obj, all_codes[i])
            
            # Test single variable to see it works expectedly
            current_pre_list_1 = globals()[all_prereq_var_names[0]]
            obj_1 = build_graph(current_pre_list_1, session, "CSC336H1")
            session.execute_write(add_to_this_course, obj_1, "CSC336H1", titles_dict["CSC336H1"])

            current_pre_list_2 = globals()["mat235y1_pre"]
            obj_2 = build_graph(current_pre_list_2, session, "MAT235Y1")
            session.execute_write(add_to_this_course, obj_2, "MAT235Y1", titles_dict["MAT235Y1"])


def add_to_this_course(tx, obj, code, full_title):
    node_exists = tx.run(
        """
            MATCH (c:Course {code: $code})
            WITH COUNT(c) > 0 as exists
            RETURN exists
        """,
        code=code
    ).data()[0]['exists']

    if node_exists:
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
    else:
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


and_counter = 1
or_counter = 1

def build_graph(item, session, relationship_code):
    global or_counter
    global and_counter

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
        
        # Make a new AND node, 
        # Create contains relationship with all of the children
        
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



if __name__ == "__main__":
    main()