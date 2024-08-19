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

import unittest
from creating_the_full_tree import (
    check_if_exists,
    create_course,
    set_latest_and_or_indexes,
    already_loaded_with_prerequisites,
    add_to_this_course,
    build_graph,
    gather_under_new_or_block,
    gather_under_new_and_block,
    build_corequisites,
    gather_co_new_or_block,
    gather_co_new_and_block,
    add_co_to_this_course,
    already_loaded_with_corequisites,
    total_corequisites_process_singular_course,
    titles_dict
)

class TestPrereqBuilding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = GraphDatabase.driver(URI, auth=AUTH) # type: ignore
        cls.driver.verify_connectivity()
        cls.session = cls.driver.session(database="neo4j")

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        cls.driver.close()

    def setUp(self):
        result = self.driver.execute_query("""
            MATCH (and:AND), (or:OR)
            RETURN max(and.index) AS max_and_index, max(or.index) AS max_or_index
        """)
        set_latest_and_or_indexes(result)
    
    # Five test cases of different corequisites

    # 1 simple list based 

    # 2 levels no containment with existing nodes, root exists

    # 2.5 levels no containment with existing nodes, root doesn't exist

    # 3 levels some containment with existing nodes, root exists
    
    # 3.5 levels some containment with existing nodes, root doesn't exist

    # 4 levels the root exists, entire containment with existing nodes 

    # 4.5 levels the root doesn't exist, entire containment with existing nodes

    # 5 levels the root exists, entire containment with existing nodes with corequisite connections. And min grade requirements

    # 5.5 levels the root doesn't exist, entire containment with existing nodes with corequisite connections. And min grade requirements
