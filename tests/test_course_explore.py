import unittest

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawl import CourseExplore
import requests
from bs4 import BeautifulSoup

class TestCourseExplore(unittest.TestCase):
    def setUp(self):
        self.course_explore = CourseExplore()

    def setupShtml(self, url):
        pg = requests.get(url)
        s_html = BeautifulSoup(pg.text, 'html.parser')
        return s_html

    # Check if all of my functions work individually
    def test_reset_crawl(self):
        self.course_explore.visited = ['url1', 'url2']
        self.course_explore.prereq_list = ['prereq1', 'prereq2']
        self.course_explore.title_list = ['title1', 'title2']

        self.course_explore.reset_crawl()

        self.assertEqual(self.course_explore.visited, [])
        self.assertEqual(self.course_explore.prereq_list, [])
        self.assertEqual(self.course_explore.title_list, [])

    # Check if links are returned correctly, and filters out utsc/utm/engineering
    def test_pre_links(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/csc311h1"
        links = self.course_explore.find_pre_links(self.setupShtml(test_url))

        expected_links = [
            "https://artsci.calendar.utoronto.ca/course/CSC207H1",
            "https://artsci.calendar.utoronto.ca/course/CSC180H1",
            "https://artsci.calendar.utoronto.ca/course/MAT235Y1",
            "https://artsci.calendar.utoronto.ca/course/MAT237Y1",
            "https://artsci.calendar.utoronto.ca/course/MAT257Y1",
            "https://artsci.calendar.utoronto.ca/course/MAT135H1",
            "https://artsci.calendar.utoronto.ca/course/MAT136H1",
            "https://artsci.calendar.utoronto.ca/course/MAT137Y1",
            "https://artsci.calendar.utoronto.ca/course/MAT157Y1",
            "https://artsci.calendar.utoronto.ca/course/MAT194H1",
            "https://artsci.calendar.utoronto.ca/course/MAT195H1",
            "https://artsci.calendar.utoronto.ca/course/MAT223H1",
            "https://artsci.calendar.utoronto.ca/course/MAT240H1",
            "https://artsci.calendar.utoronto.ca/course/STA237H1",
            "https://artsci.calendar.utoronto.ca/course/STA247H1",
            "https://artsci.calendar.utoronto.ca/course/STA255H1",
            "https://artsci.calendar.utoronto.ca/course/STA257H1",
            "https://artsci.calendar.utoronto.ca/course/STA286H1",
            "https://artsci.calendar.utoronto.ca/course/MAT194H1",
            "https://artsci.calendar.utoronto.ca/course/MAT195H1",
            "https://artsci.calendar.utoronto.ca/course/CHM139H1",
        ]
        self.assertEqual(expected_links, links)

    # Tests if prerequisite string is simply returned correctly, there is no filtering here
    def test_prereq_string(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/csc311h1"
        self.course_explore.find_pre_links(self.setupShtml(test_url))

        result_string = self.course_explore.prereq_list[0].replace(" ", "")
        expected_result = "CSC207H1/ APS105H1/ APS106H1/ ESC180H1/ CSC180H1; MAT235Y1/​ MAT237Y1/​ MAT257Y1/​ (minimum of 77% in MAT135H1 and MAT136H1)/ (minimum of 73% in MAT137Y1)/ (minimum of 67% in MAT157Y1)/ MAT291H1/ MAT294H1/ (minimum of 77% in MAT186H1, MAT187H1)/ (minimum of 73% in MAT194H1, MAT195H1)/ (minimum of 73% in ESC194H1, ESC195H1); MAT223H1/ MAT240H1/ MAT185H1/ MAT188H1; STA237H1/ STA247H1/ STA255H1/ STA257H1/ STA286H1/ CHE223H1/ CME263H1/ MIE231H1/ MIE236H1/ MSE238H1/ ECE286H1".replace(" ", "")
        self.assertEqual(result_string, expected_result)

    # Test if page doesn't have prereq
    def test_prereq_noprereq(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/csc108h1"
        result = self.course_explore.find_pre_links(self.setupShtml(test_url))
        saved_prereqs = self.course_explore.prereq_list
        self.assertEqual(result, [], "Prerequisite Links failed when there should be no prerequisites")
        self.assertEqual(saved_prereqs, [''], "Should have a single item to cover up the spot")

    def test_prereq_noprereq2(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/CSC421H1"
        result = self.course_explore.find_pre_links(self.setupShtml(test_url))
        saved_prereqs = self.course_explore.prereq_list
        self.assertEqual(result, [], "Prerequisite Links failed when there should be no prerequisites")
        self.assertEqual(saved_prereqs, [''], "Should have a single item to cover up the spot")

    # Crawl testing
    # Test if page not found is avoided and not on my calendar is avoided
    def test_crawl_pagenotfound(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/CSC421H1"
        self.course_explore.crawl(test_url)
        result_titles = self.course_explore.title_list
        result_prereqs = self.course_explore.prereq_list
        self.assertEqual(result_titles, [], "Should have nothing in the title because page is null")
        self.assertEqual(result_prereqs, [], "Should have nothing in the course prereqs to match the title")

    # Test if courses are visited at an expected order for small courses
        # check if the title to prerequisite is as expected

    # TEST CSC108 - no prerequisites
    def test_crawl_test1(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/csc108h1"
        self.course_explore.crawl(test_url)
        result_titles = self.course_explore.title_list
        result_prereqs = self.course_explore.prereq_list
        result_visited = self.course_explore.visited

        self.assertEqual(result_titles, ["CSC108H1: Introduction to Computer Programming"], "Should only have a single title")
        self.assertEqual(result_prereqs, [""], "Should have a single item of 0 prereq, matching with CSC108")

        self.assertTrue(result_visited["https://artsci.calendar.utoronto.ca/course/csc108h1"], "Should have only visited CSC108")
        # Delete the (valid) title and the (visited) link since they are both recorded
        del result_visited["https://artsci.calendar.utoronto.ca/course/csc108h1"]
        del result_visited["CSC108H1: Introduction to Computer Programming"]
        self.assertTrue(result_visited == {})

    # TEST CSC165 - Prerequisites
    def test_crawl_test2(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/csc236h1"
        self.course_explore.crawl(test_url)
        result_titles = self.course_explore.title_list
        result_prereqs = self.course_explore.prereq_list
        # This is a dictionary now
        result_visited = self.course_explore.visited

        expected_titles = ["CSC236H1: Introduction to the Theory of Computation",
                           "CSC148H1: Introduction to Computer Science",
                           "CSC108H1: Introduction to Computer Programming",
                           "CSC165H1: Mathematical Expression and Reasoning for Computer Science",
                           "CSC111H1: Foundations of Computer Science II",
                           "CSC110Y1: Foundations of Computer Science I"]
        expected_prereqs = ["(60% or higher in CSC148H1, 60% or higher in CSC165H1) / (60% or higher in CSC111H1)",
                            "CSC108H1/ (equivalent programming experience)",
                            "",
                            "",
                            "CSC110Y1 (70% or higher)",
                            ""]
        expected_visited = ["https://artsci.calendar.utoronto.ca/course/csc236h1",
                            "https://artsci.calendar.utoronto.ca/course/csc148h1",
                            "https://artsci.calendar.utoronto.ca/course/csc108h1",
                            "https://artsci.calendar.utoronto.ca/course/csc165h1",
                            "https://artsci.calendar.utoronto.ca/course/csc111h1",
                            "https://artsci.calendar.utoronto.ca/course/csc110y1"]

        # Checks
        # Checking Valid Titles
        self.assertEqual(result_titles, expected_titles, "Titles should be equal w/o formatting")
        # Checking Expected visited (Valid and "page not found", "Sorry this course is not in your calendar")
        print(result_visited)
        for i in range(len(expected_visited)):
            print(result_visited)
            capital_case = expected_visited[i][:-8] + expected_visited[i][-8:].upper()
            lower_case = expected_visited[i][:-8] + expected_visited[i][-8:].lower()
            capital_has_visited = result_visited.get(capital_case, False)
            lower_has_visited = result_visited.get(lower_case, False)
            print(capital_case, lower_case, capital_has_visited, lower_has_visited)

            self.assertTrue(capital_has_visited or lower_has_visited)
            if capital_has_visited:
                del result_visited[capital_case]
            else:
                del result_visited[lower_case]


        # delete all the rest of stuff in expected visited, and seeing if those are the only visited
        for i in range(len(expected_titles)):
            del result_visited[expected_titles[i]]
        self.assertTrue(result_visited == {})

        self.assertEqual(len(result_prereqs), len(expected_prereqs), "Prereqs lengths should be equal")
        self.assertEqual(len(result_prereqs), len(result_titles), "Prereq amount should be equal to title amount")
        for i in range(len(result_prereqs)):
            self.assertEqual(result_prereqs[i].replace(" ", ""), expected_prereqs[i].replace(" ",""), "Prereq should be equal by removing spaces")

    # TEST CSC258 MORE COMPLEX PRE
    def test_crawl_test3(self):
        url = "https://artsci.calendar.utoronto.ca/course/csc258h1"

        visited = {
            "https://artsci.calendar.utoronto.ca/course/csc258h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc148h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc108h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc165h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc240h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc110y1": True,
            "https://artsci.calendar.utoronto.ca/course/csc111h1": True
        }

        expected_title_list = [
            "CSC258H1: Computer Organization",
            "CSC148H1: Introduction to Computer Science",
            "CSC108H1: Introduction to Computer Programming",
            "CSC165H1: Mathematical Expression and Reasoning for Computer Science",
            "CSC240H1: Enriched Introduction to the Theory of Computation",
            "CSC110Y1: Foundations of Computer Science I",
            "CSC111H1: Foundations of Computer Science II"
        ]

        expected_pre_list = [
            "(60% or higher in (CSC148H1/CSC148H5/CSCA48H3), 60% or higher in (CSC165H1/CSC240H1/MAT102H5/MATA67H3/CSCA67H3))/60% or higher in CSC111H1",

            "CSC108H1/(equivalent programming experience)",

            "",

            "",

            "CSC110Y1 (with a minimum mark of at least 70%)/CSC165H1 (with a minimum mark of at least 85%)/students with a strong mathematical background who have not completed CSC110Y1 or CSC165H1 may enrol in CSC240H1 as an enriched alternative to CSC165H1",

            "",

            "CSC110Y1 (70% or higher)",
        ]

        self.course_explore.crawl(url)

        result_titles = self.course_explore.title_list
        result_prereqs = self.course_explore.prereq_list
        result_visited = self.course_explore.visited
        

        # Check if all the titles are correct order
        self.assertEqual(len(expected_title_list), len(result_titles), "Title lengths should be equal")
        self.assertEqual(expected_title_list, result_titles, "Title list should be equal")
    

        # Check all the prereqs are correct
        self.assertEqual(len(expected_pre_list), len(result_prereqs), "Prereqs lengths should be equal")
        for i in range(len(expected_pre_list)):
            self.assertEqual(expected_pre_list[i].replace(" ", ""), result_prereqs[i].replace(" ", ""), "Prereq should be equal by removing spaces")

        print(result_visited)
        # Check if all of the visiteds are correct
        for key in visited:
            print(key)
            upper_case = key[0:-8] + key[-8:].upper()
            lower_case = key[0:-8] + key[-8:].lower()
            print(upper_case, lower_case)

            key_is_upper_case = result_visited.get(upper_case, False)
            key_is_lower_case = result_visited.get(lower_case, False)
            self.assertTrue(key_is_upper_case or key_is_lower_case, f"Should have visited {key} either in upper or lower case")
            
            # delete key depending on upper or lower case
            if key_is_upper_case: del result_visited[upper_case]
            else: del result_visited[lower_case]

        # Check if the visited has extra elements => extra titles or extra links => FUCK
        
        # delete all titles
        for i in expected_title_list:
            del result_visited[i]

        self.assertTrue(result_visited == {})

    # 300 + 400 level tests
    def test_crawl_test4(self):
        test_url = "https://artsci.calendar.utoronto.ca/course/csc311h1"
        self.course_explore.crawl(test_url)
        result_visited = self.course_explore.visited
        result_titles = self.course_explore.title_list

        expected_visited = [
            "https://artsci.calendar.utoronto.ca/course/csc311h1",
            "https://artsci.calendar.utoronto.ca/course/csc207h1",
            "https://artsci.calendar.utoronto.ca/course/csc148h1",
            "https://artsci.calendar.utoronto.ca/course/csc108h1",
            "https://artsci.calendar.utoronto.ca/course/csc111h1",
            "https://artsci.calendar.utoronto.ca/course/csc110y1",
            "https://artsci.calendar.utoronto.ca/course/CSC180H1",
            "https://artsci.calendar.utoronto.ca/course/mat235y1",
            "https://artsci.calendar.utoronto.ca/course/mat133y1",
            "https://artsci.calendar.utoronto.ca/course/mat135h1",
            "https://artsci.calendar.utoronto.ca/course/mat136h1",
            "https://artsci.calendar.utoronto.ca/course/mat137y1",
            "https://artsci.calendar.utoronto.ca/course/mat157y1",
            "https://artsci.calendar.utoronto.ca/course/mat237y1",
            "https://artsci.calendar.utoronto.ca/course/mat138h1",
            "https://artsci.calendar.utoronto.ca/course/mat246h1",
            "https://artsci.calendar.utoronto.ca/course/mat223h1",
            "https://artsci.calendar.utoronto.ca/course/mat240h1",
            "https://artsci.calendar.utoronto.ca/course/mat257y1",
            "https://artsci.calendar.utoronto.ca/course/mat247h1",
            "https://artsci.calendar.utoronto.ca/course/mat194h1",
            "https://artsci.calendar.utoronto.ca/course/mat195h1",
            "https://artsci.calendar.utoronto.ca/course/sta237h1",
            "https://artsci.calendar.utoronto.ca/course/sta247h1",
            "https://artsci.calendar.utoronto.ca/course/sta255h1",
            "https://artsci.calendar.utoronto.ca/course/sta220h1",
            "https://artsci.calendar.utoronto.ca/course/sta221h1",
            "https://artsci.calendar.utoronto.ca/course/sta288h1",
            "https://artsci.calendar.utoronto.ca/course/bio230h1",
            "https://artsci.calendar.utoronto.ca/course/bio130h1",
            "https://artsci.calendar.utoronto.ca/course/chm135h1",
            "https://artsci.calendar.utoronto.ca/course/chm136h1",
            "https://artsci.calendar.utoronto.ca/course/CHM138H1",
            "https://artsci.calendar.utoronto.ca/course/CHM139H1",
            "https://artsci.calendar.utoronto.ca/course/chm151y1",
            "https://artsci.calendar.utoronto.ca/course/bio255h1",
            "https://artsci.calendar.utoronto.ca/course/psy201h1",
            "https://artsci.calendar.utoronto.ca/course/psy100h1",
            "https://artsci.calendar.utoronto.ca/course/cog250y1",
            "https://artsci.calendar.utoronto.ca/course/ggr270h1",
            "https://artsci.calendar.utoronto.ca/course/eeb225h1",
            "https://artsci.calendar.utoronto.ca/course/bio120h1",
            "https://artsci.calendar.utoronto.ca/course/eco220y1",
            "https://artsci.calendar.utoronto.ca/course/eco101h1",
            "https://artsci.calendar.utoronto.ca/course/eco102h1",
            "https://artsci.calendar.utoronto.ca/course/eco105y1",
            "https://artsci.calendar.utoronto.ca/course/sta257h1",
            "https://artsci.calendar.utoronto.ca/course/STA286H1"
        ]

        expected_titles = [
            "CSC311H1: Introduction to Machine Learning",
            "CSC207H1: Software Design",
            "CSC148H1: Introduction to Computer Science",
            "CSC108H1: Introduction to Computer Programming",
            "CSC111H1: Introduction to Computational Thinking",
            "CSC110Y1: Computer Science Fundamentals",
            "CSC180H1: Introduction to Computer Programming",
            "MAT235Y1: Calculus III",
            "MAT133Y1: Calculus and Linear Algebra for Commerce",
            "MAT135H1: Calculus I (for Physical Sciences and Engineering)",
            "MAT136H1: Calculus II (for Physical Sciences and Engineering)",
            "MAT137Y1: Calculus",
            "MAT157Y1: Analysis I",
            "MAT237Y1: Multivariable Calculus",
            "MAT138H1: Introduction to Proofs",
            "MAT246H1: Abstract Algebra I",
            "MAT223H1: Linear Algebra I",
            "MAT240H1: Algebra I",
            "MAT257Y1: Analysis II",
            "MAT247H1: Algebra II",
            "MAT194H1: Mathematics for Commerce",
            "MAT195H1: Calculus II for Commerce",
            "STA237H1: Probability with Computer Applications",
            "STA247H1: Probability with Computer Applications II",
            "STA255H1: Statistical Theory",
            "STA220H1: The Practice of Statistics I",
            "STA221H1: The Practice of Statistics II",
            "STA288H1: Data Science I",
            "BIO230H1: Introduction to Evolutionary and Ecological Genetics",
            "BIO130H1: Molecular and Cell Biology",
            "CHM135H1: Introductory Chemistry",
            "CHM136H1: Organic Chemistry I",
            "CHM138H1: Introductory Organic Chemistry I",
            "CHM139H1: Introductory Organic Chemistry II",
            "CHM151Y1: Chemistry: The Molecular Science",
            "BIO255H1: Introduction to Molecular Genetics and Genomics",
            "PSY201H1: Statistics I",
            "PSY100H1: Introduction to Psychology",
            "COG250Y1: Introduction to Cognitive Science",
            "GGR270H1: Quantitative Methods in Geography",
            "EEB225H1: Mathematical Methods in Ecology and Evolution",
            "BIO120H1: Adaptation and Biodiversity",
            "ECO220Y1: Quantitative Methods in Economics",
            "ECO101H1: Introduction to Microeconomics",
            "ECO102H1: Introduction to Macroeconomics",
            "ECO105Y1: Principles of Economics",
            "STA257H1: Probability and Statistics II",
            "STA286H1: Statistics for Pharmacology"
        ]

        for item in expected_visited:
            capital_case = item[0:-8] + item[-8:].upper()
            lower_case = item[0:-8] + item[-8:].lower()
            capital_has_visited = result_visited.get(capital_case, False)
            lower_has_visited = result_visited.get(lower_case, False)

            self.assertTrue(capital_has_visited or lower_has_visited, f"Should have visited {item} either in upper or lower case")
            if capital_has_visited:
                del result_visited[capital_case]
            else :
                del result_visited[lower_case]

        for item in result_titles:
            del result_visited[item]
        
        self.assertTrue(result_visited == {})
        
        
        print(result_visited)


    # TEST PRE + COR
    # For the request, I am going to do PRE + COR only first.

    # TEST PRE + COR + EXCL


if __name__ == '__main__':
    test = TestCourseExplore()