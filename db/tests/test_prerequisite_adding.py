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
    total_prerequisites_process_singular_course,
    total_corequisites_process_singular_course,
    titles_dict,
    and_counter,
    or_counter
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

    # Six test cases of different corequisites

    # 1 simple list based MAT377H1 uoft
    def test_build_prerequisites_1(self):
        # Build prerequisites
        total_prerequisites_process_singular_course(self.session, "MAT377H1")

        # Check if the course and its prerequisite nodes have been created 
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT377H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT247H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT257Y1"))

        # Check if the count of the prerequisite nodes is correct
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT377H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT377H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT247H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT247H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT257Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT257Y1 node")

        # Check if # of prerequisite paths are correct
        self.assertTrue(self.session.execute_read(already_loaded_with_prerequisites, "MAT377H1"))

        paths = self.driver.execute_query("MATCH (n)-[p:Contains {root: $root}]->(m) RETURN count(p) as count", root="MAT377H1")
        count = paths.records[0]["count"]
        self.assertEqual(count, 3, "There should be 3 paths from MAT377H1")

        # Check if each path is correct. Three individual checks
        path = self.driver.execute_query("MATCH (n:Course {code: $root})-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="MAT377H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from MAT377H1 to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT247H1", root="MAT377H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to MAT247H1")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT257Y1", root="MAT377H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to MAT257Y1")


    # 2 (Case 6: Everything Exists, just connect)
    def test_build_prerequisite_2(self):
        # test case consideration, CSC240
        total_prerequisites_process_singular_course(self.session, "CSC240H1")

        # check for existence of all relevant course nodes
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC240H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC165H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC110Y1"))
        
        # check for duplication of course nodes
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC240H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC240H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC165H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC165H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC110Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC110Y1 node")

        # check number of prerequisite paths that has been created
        result = self.driver.execute_query("MATCH (n)-[p:Contains {root: $root}]->(m) RETURN count(p) as count", root="CSC240H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 4, "There should be 4 paths that has prerequisites with CSC240H1")

        # check existence of each custom path of the root node
        path = self.driver.execute_query("MATCH (n:Course {code: $root})-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="CSC240H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from CSC240H1 to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:OR) RETURN count(p) as count", root="CSC240H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to OR with the root CSC240H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root, min_req: $min_req}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC165H1", root="CSC240H1", min_req="85%")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC165H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root, min_req: $min_req}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC110Y1", root="CSC240H1", min_req="70%")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC110Y1")


    # 2.5 (Case 2, nothing exists, build all)
    def test_build_prerequisite_3(self):
        # CSC324 is good
        total_prerequisites_process_singular_course(self.session, "CSC324H1")

        # Check if course and its prerequisite nodes have been created
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC324H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC263H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC265H1"))

        # Check if the count of prerequisite nodes is correct
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC324H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC324H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC263H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC263H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC265H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC265H1 node")

        # Check the number of prerequisite paths that has been created
        result = self.driver.execute_query("MATCH (n)-[p:Contains {root: $root}]->(m) RETURN count(p) as count", root="CSC324H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 4, "There should be 3 paths that has prerequisites with CSC324H1")

        # Check existence of each custom path of the root node
        path = self.driver.execute_query("MATCH (n:Course {code: $root})-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="CSC324H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from CSC324H1 to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:OR) RETURN count(p) as count", root="CSC324H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to OR with the root CSC324H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC263H1", root="CSC324H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC263H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC265H1", root="CSC324H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC265H1")


    # 3 (Case 1, all prerequisites exist, add root)
    def test_build_prerequisite_4(self):
        # CSC236 is perfect, only csc236 is missing
        total_prerequisites_process_singular_course(self.session, "CSC236H1")

        # Check if course and its prerequisite nodes have been created
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC236H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC165H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC148H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC111H1"))

        # Check if the count of prerequisite nodes is correct
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC236H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC236H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC165H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC165H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC148H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC148H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC111H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC111H1 node")

        # Check for the number of prerequisite paths that has been created is correct
        result = self.driver.execute_query("MATCH (n)-[p:Contains {root: $root}]->(m) RETURN count(p) as count", root="CSC236H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 6, "There should be 6 paths that has prerequisites with CSC236H1")

        # Check for the existence of each custom path of the root node
        path = self.driver.execute_query("MATCH (n:Course {code: $root})-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="CSC236H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from CSC236H1 to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:OR) RETURN count(p) as count", root="CSC236H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to OR with the root CSC236H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC111H1", root="CSC236H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC111H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="CSC236H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC148H1", root="CSC236H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to CSC148H1")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC165H1", root="CSC236H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC165H1")
    

    # 3.5 (Case 4, root exists, no prerequisites exist, build prerequisites)
    def test_build_prerequisite_5(self):
        # Artificially add root node
        node_exists = self.session.execute_read(check_if_exists, "CIN301Y1")
        if not node_exists:
            self.session.execute_write(create_course, "CIN301Y1", "CIN301Y1: Film Cultures II: Politics and Global Media")
        
        # Build prerequisites
        total_prerequisites_process_singular_course(self.session, "CIN301Y1")

        # Check if course and its prerequisite nodes have been created
        self.assertTrue(self.session.execute_write(check_if_exists, "CIN301Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CIN105Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CIN201Y1"))

        # Check if the count of prerequisite nodes is correct
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CIN301Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CIN301Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CIN105Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CIN105Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CIN201Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CIN201H1 node")

        # Check for the number of prerequisite paths that has been created is correct
        result = self.driver.execute_query("MATCH (n)-[p:Contains {root: $root}]->(m) RETURN count(p) as count", root="CIN301Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 3, "There should be 3 paths that has prerequisites with CIN301Y1")

        # Check for the existence of each custom path of the root node
        path = self.driver.execute_query("MATCH (n:Course {code: $root})-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="CIN301Y1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from CIN301Y1 to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", root="CIN301Y1", code="CIN105Y1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to CIN105Y1")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", root="CIN301Y1", code="CIN201Y1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to CIN201Y1")


    # 4 (Case 3 root and some prerequisites don't exist, some requisites exist, add root and build some prerequisites)
    def test_build_prerequisites_6(self):
        # CSC446H1 is a good example
        total_prerequisites_process_singular_course(self.session, "CSC446H1")

        # Check if course and its prerequisite nodes have been created
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC446H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC336H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT237Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT257Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "APM346H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT351Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT244H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT267H1"))
        
        # Check if the count of prerequisite nodes is correct
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC446H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC446H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC336H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC336H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT237Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT237Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT257Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT257Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="APM346H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 APM346H1 node")
        
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT351Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT351Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT244H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT244H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT267H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT267H1 node")
        
        # Check for the number of prerequisite paths that has been created is correct
        result = self.driver.execute_query("MATCH (n)-[p:Contains {root: $root}]->(m) RETURN count(p) as count", root="CSC446H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 11, "There should be 11 paths that has prerequisites with CSC446H1")

        # Check for the existence of each custom path of the root node
        path = self.driver.execute_query("MATCH (n:Course {code: $root})-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from CSC446H1 to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:OR) RETURN count(p) as count", root="CSC446H1") 
        count = path.records[0]["count"]
        self.assertEqual(count, 2, "There should be 2 paths from AND to OR with the root CSC446H1")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root, min_req: $min_req}]->(m:Course {code: $code}) RETURN count(p) as count", min_req="75%", code="CSC336H1", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to CSC336H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT237Y1", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT237Y1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT257Y1", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT257Y1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="APM346H1", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to APM346H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT351Y1", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to APM346H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:OR) RETURN count(p) as count", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to OR with the root CSC446H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT244H1", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT244H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT267H1", root="CSC446H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT267H1")


    # 4.5 (Case 5, the root exists, some prerequisites exist, some prerequisites don't exist, build prerequisites)
    def test_build_prerequisites_7(self):
        # Artificially add root node
        node_exists = self.session.execute_read(check_if_exists, "MAT309H1")
        if not node_exists:
            self.session.execute_write(create_course, "MAT309H1", "MAT309H1: Introduction to Mathematical Logic")

        # MAT309 is a good example
        total_prerequisites_process_singular_course(self.session, "MAT309H1")

        # Check if course and its prerequisite nodes have been created
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT309H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT257Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT223H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT240H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT235Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT237Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT246H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT157Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC236H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC240H1"))

        # Check if the count of prerequisite nodes is correct
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT309H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT309H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT257Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT257Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT223H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT223H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT240H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT240H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT235Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT235Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT237Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT237Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT246H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT246H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT157Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT157Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC236H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC236H1 node")

        # Check for the number of prerequisite paths that has been created is correct
        result = self.driver.execute_query("MATCH (n)-[p:Contains {root: $root}]->(m) RETURN count(p) as count", root="MAT309H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 15, "There should be 10 paths that has prerequisites with MAT309H1")

        # Check for the existence of each custom path of the root node
        path = self.driver.execute_query("MATCH (n:Course {code: $root})-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from MAT309H1 to AND")

        path = self.driver.execute_query("MATCH (n:AND)-[p:Contains {root: $root}]->(m:OR) RETURN count(p) as count", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 4, "There should be 4 paths from AND to OR with the root MAT309H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT257Y1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from AND to MAT257Y1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:AND) RETURN count(p) as count", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to AND")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT223H1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT223H1")
        
        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT240H1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT240H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT235Y1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT235Y1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT237Y1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT237Y1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT246H1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT246H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="MAT157Y1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to MAT157Y1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC236H1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC236H1")

        path = self.driver.execute_query("MATCH (n:OR)-[p:Contains {root: $root}]->(m:Course {code: $code}) RETURN count(p) as count", code="CSC240H1", root="MAT309H1")
        count = path.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path from OR to CSC240H1")

    # Test already_loaded_with_prerequisites
    def test_already_loaded_with_prerequisites(self):
        # Three test cases
        # Case 1: node not exist
        self.assertFalse(self.session.execute_read(already_loaded_with_prerequisites, "CSC420H1"))
        # Case 2: node exists ^ not loaded with prerequisites
        self.assertFalse(self.session.execute_read(already_loaded_with_prerequisites, "MAT247H1"))
        # Case 3: node exists ^ loaded with prerequisites
        self.assertTrue(self.session.execute_read(already_loaded_with_prerequisites, "MAT377H1"))

    # Test Latest AND OR indicies - WILL FAIL after testing due to database value changes
    def test_set_latest_and_or_indexes(self):
        # Test the ability for it to get and set them
        result = self.driver.execute_query("""
                MATCH (and:AND), (or:OR)
                RETURN max(and.index) AS max_and_index, max(or.index) AS max_or_index
        """)
        set_latest_and_or_indexes(result)



if __name__ == "__main__":
    unittest.main()