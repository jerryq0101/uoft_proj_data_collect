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

class TestCoreqBuilding(unittest.TestCase):
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

    # def test_fetching_data(self):
    #     # Example test method using the session
    #     result = self.session.run("MATCH (n) RETURN count(n) AS count")
    #     count = result.single()["count"]
    #     self.assertEqual(count, 9)
    
    # Test build corequisites
    def test_build_corequisites_1(self):
        # Build entire_corequisite process
        # Sets the latest AND OR indexes in the database here
        total_corequisites_process_singular_course(self.session, "CSC108H1")

        # Check if the course has been created
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC108H1"))

        # Check if the corequisites path have been created (Should be False since no path will be created for this)
        self.assertFalse(self.session.execute_read(already_loaded_with_corequisites, "CSC108H1"))

        # Run the query and fetch the result immediately
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC108H1")
        count = result.records[0]["count"]

        # Check that there is only one of each expected root path
        self.assertEqual(count, 1)


    # Test build corequisites 2 MAT267H1 (simple case, non-existing root, existing corequisites)
    def test_build_corequisites_2(self):
        total_corequisites_process_singular_course(self.session, "MAT267H1")
        
        # Check both the root and the single corequisite exists
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT267H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT257Y1"))
        
        # Check that there is only two coreq paths created
        paths = self.driver.execute_query("MATCH (n)-[p:Coreqs_With {root: $root}]->(m) RETURN count(p) as count", root="MAT267H1")
        print(paths)
        count = paths.records[0]["count"]
        self.assertEqual(count, 2, "There should be 2 paths that has coreqs_with MAT267H1")
        
        # Check that the corequisite path is correct
        vars = self.driver.execute_query("MATCH (n:Course {code: $code})-[p:Coreqs_With {root: $root}]->(m:AND) RETURN count(p) as count", root="MAT267H1", code="MAT267H1")
        count = vars.records[0]["count"]
        self.assertEqual(count, 1, "There should be 1 path that has coreqs_with MAT267H1 and is connected to an OR node")


    # Test build corequisites 3 COG260H1 (simple case, non existing root, non-existing corequisites)
    def test_build_corequisites_3(self):
        total_corequisites_process_singular_course(self.session, "COG260H1")

        # Check both the root and the single corequisite exists
        self.assertTrue(self.session.execute_write(check_if_exists, "COG260H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "COG250Y1"))

        # Check that there is no repeat nodes
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="COG260H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 COG260H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="COG250Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 COG250Y1 node")

        # Check that there is only two coreq paths created
        paths = self.driver.execute_query("MATCH (n)-[p:Coreqs_With {root: $root}]->(m) RETURN count(p) as count", root="COG260H1")
        count = paths.records[0]["count"]
        self.assertEqual(count, 2, "There should be 2 paths that has coreqs_with COG260H1")


    # Test build corequisites 4 STA238H1 (medium case, existing root, mixed corequisites)
    def test_build_corequisites_4(self):
        # First add sta238 to the database to do existing root, if it is loaded already it means that the node will exist 
        if not already_loaded_with_corequisites(self.session, "STA238H1"):
            self.driver.execute_query("CREATE (n:Course {code: $code, full_name: $full_name}) RETURN n", code="STA238H1", full_name=titles_dict["STA238H1"])
        
        total_corequisites_process_singular_course(self.session, "STA238H1")

        # Check both the root and the single corequisite exists
        self.assertTrue(self.session.execute_write(check_if_exists, "STA238H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC108H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC110Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC148H1"))

        # Check that there is no repeat nodes
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="STA238H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 STA238H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC108H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC108H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC110Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC110Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC148H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC148H1 node")
        
        # Check that there is only 4 coreq paths created
        paths = self.driver.execute_query("MATCH (n)-[p:Coreqs_With {root: $root}]->(m) RETURN count(p) as count", root="STA238H1")
        count = paths.records[0]["count"]
        self.assertEqual(count, 5, "There should be 4 paths that has coreqs_with STA238H1")


    # Test build corequisites 5 CSC240 (hard case, existing root, mixed corequisites)
    def test_build_corequisites_5(self):
        if not already_loaded_with_corequisites(self.session, "CSC240H1"):
            self.driver.execute_query("CREATE (n:Course {code: $code, full_name: $full_name}) RETURN n", code="CSC240H1", full_name=titles_dict["CSC240H1"])

        total_corequisites_process_singular_course(self.session, "CSC240H1")

        # Check both the root and the multiple corequisites exists
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC240H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC111H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "CSC148H1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT137Y1"))
        self.assertTrue(self.session.execute_write(check_if_exists, "MAT157Y1"))

        # Check that there is no repeat nodes
        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC240H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC240H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC111H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC111H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="CSC148H1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 CSC148H1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT137Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT137Y1 node")

        result = self.driver.execute_query("MATCH (n:Course {code: $code}) RETURN count(n) AS count", code="MAT157Y1")
        count = result.records[0]["count"]
        self.assertEqual(count, 1, "There should be only 1 MAT157Y1 node")

        # Check that there is only 7 coreq paths created
        paths = self.driver.execute_query("MATCH (n)-[p:Coreqs_With {root: $root}]->(m) RETURN count(p) as count", root="CSC240H1")
        count = paths.records[0]["count"]
        self.assertEqual(count, 7, "There should be 7 paths that has coreqs_with CSC240H1")
    
    # More tests for elementary functions here


if __name__ == '__main__':
    unittest.main()