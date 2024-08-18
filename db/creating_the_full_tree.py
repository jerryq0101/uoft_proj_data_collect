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
from graph_creation import gather_under_new_and_block, gather_under_new_or_block
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


def create_course(tx, code, full_name, min_grade="50%"):
    result = tx.run("""
        CREATE (c:Course {code: $code, full_name: $full_name, min_grade: $min_grade})
        RETURN c.code AS code
    """, code=code, full_name=full_name, min_grade=min_grade)
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

        with driver.session(database="neo4j") as session:
            # # Top Level
            # for i in range(len(all_prereq_var_names)):
            #     current_pre_list = globals()[all_prereq_var_names[i]]

            #     # Should return a dict with "type" and "index" for us to add it to the child of current node
            #     obj = build_graph(current_pre_list, session)
                
            #     # Add obj and a containment relationship to the current node
            #     add_to_this_course(obj, all_codes[i])
            
            # Test single variable to see it works expectedly
            current_pre_list = globals()[all_prereq_var_names[0]]
            obj = build_graph(current_pre_list, session)
            print(obj)

and_counter = 1
or_counter = 1

def build_graph(item, session):
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
            session.execute_write(create_course, item["code"], titles_dict[item["code"]], item["min_req"])
            return {
                "type": "Course",
                "code": item["code"]
            }
    
    elif item_type == list:
        # we know that this is an AND relationship
        
        # Make a new AND node, 
        # Create contains relationship with all of the children
        
        results = []
        for e in item:
            # result will be a dict
            result = build_graph(e, session)
            results.append(result)

            # if string search for the course code and do a containment relationship
            # if dict, check OR or AND, and then do a containment relationship
        session.execute_write(gather_under_new_and_block, results, and_counter) # type: ignore
        
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
            result = build_graph(e, session)
            results.append(result)
        
        session.execute_write(gather_under_new_or_block, results, or_counter) # type: ignore

        or_counter += 1 # type: ignore

        return {
            "type": "OR",
            "index": or_counter-1
        }


if __name__ == "__main__":
    main()