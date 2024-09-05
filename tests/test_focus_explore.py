# Test if it reads the focus page correctly

import unittest

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from focus_crawl import FocusExplore
from bs4 import BeautifulSoup


# Useful Variables
focuses = {
    "AI": "Focus in Artificial Intelligence (Major) - ASFOC1689K",
    "NLP": "Focus in Computational Linguistics and Natural Language Processing (Major) - ASFOC1689M",
    "CS": "Focus in Computer Systems (Major) - ASFOC1689P",
    "CV": "Focus in Computer Vision (Major) - ASFOC1689L",
    "GD": "Focus in Game Design (Major) - ASFOC1689N",
    "HCI": "Focus in Human-Computer Interaction (Major) - ASFOC1689Q",
    "SC": "Focus in Scientific Computing (Major) - ASFOC1689O",
    "TLI": "Focus in Technology Leadership (Computer Science Major) - ASFOC1689U",
    "ToC": "Focus in Theory of Computation (Major) - ASFOC1689R",
    "WIT": "Focus in Web and Internet Technologies (Major) - ASFOC1689S"
}

class TestFocusExplore(unittest.TestCase):
    def setUp(self):
        self.test = FocusExplore()


    def test_links_in_focus_ai(self):
        title = "AI"
        result_links = self.test.links_in_focus(focuses[title])
        expected_links = {
            "https://artsci.calendar.utoronto.ca/course/csc336h1": True,
            "https://artsci.calendar.utoronto.ca/course/mat235y1": True,
            "https://artsci.calendar.utoronto.ca/course/mat237y1": True,
            "https://artsci.calendar.utoronto.ca/course/mat257y1": True,
            "https://artsci.calendar.utoronto.ca/course/apm236h1": True,
            "https://artsci.calendar.utoronto.ca/course/mat224h1": True,
            "https://artsci.calendar.utoronto.ca/course/mat247h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta238h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta248h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta261h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta302h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta347h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc401h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc485h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc320h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc321h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc420h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc413h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc421h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc304h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc384h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc486h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc311h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta314h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc412h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta414h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc324h1": True,
            "https://artsci.calendar.utoronto.ca/course/cog250y1": True,
            "https://artsci.calendar.utoronto.ca/course/psy270h1": True,
            "https://artsci.calendar.utoronto.ca/course/phl232h1": True,
            "https://artsci.calendar.utoronto.ca/course/phl342h1": True,
        }

        for link in result_links:
            lower_case = link.lower()
            key_exists = expected_links.get(lower_case, False)
            self.assertTrue(key_exists)
            del expected_links[lower_case]
        
        self.assertEqual(expected_links, {})


    def test_links_in_focus_nlp(self):
        title = "NLP"
        result_links = self.test.links_in_focus(focuses[title])
        expected_links = [
            "https://artsci.calendar.utoronto.ca/course/csc318h1",
            "https://artsci.calendar.utoronto.ca/course/csc401h1",
            "https://artsci.calendar.utoronto.ca/course/csc485h1",
            "https://artsci.calendar.utoronto.ca/course/lin101h1",
            "https://artsci.calendar.utoronto.ca/course/lin200h1",
            "https://artsci.calendar.utoronto.ca/course/csc309h1",
            "https://artsci.calendar.utoronto.ca/course/csc413h1",
            "https://artsci.calendar.utoronto.ca/course/csc421h1",
            "https://artsci.calendar.utoronto.ca/course/csc321h1",
            "https://artsci.calendar.utoronto.ca/course/csc311h1",
            "https://artsci.calendar.utoronto.ca/course/csc428h1",
            "https://artsci.calendar.utoronto.ca/course/csc486h1",
            "https://artsci.calendar.utoronto.ca/course/psy100h1",
            "https://artsci.calendar.utoronto.ca/course/cog250y1",
            "https://artsci.calendar.utoronto.ca/course/csc384h1",
            "https://artsci.calendar.utoronto.ca/course/csc420h1",
        ]
        for i in range(len(result_links)):
            result_links[i] = result_links[i].lower()

        self.assertEqual(expected_links, result_links, "Expected links should equal to result links")


    def test_links_in_focus_cs(self):
        title = "CS"
        result_links = self.test.links_in_focus(focuses[title])
        expected_links = [
            "https://artsci.calendar.utoronto.ca/course/csc209h1",
            "https://artsci.calendar.utoronto.ca/course/csc343h1",
            "https://artsci.calendar.utoronto.ca/course/csc367h1",
            "https://artsci.calendar.utoronto.ca/course/csc369h1",
            "https://artsci.calendar.utoronto.ca/course/csc457h1",
            "https://artsci.calendar.utoronto.ca/course/csc458h1",
            "https://artsci.calendar.utoronto.ca/course/csc324h1",
            "https://artsci.calendar.utoronto.ca/course/csc368h1",
            "https://artsci.calendar.utoronto.ca/course/csc385h1",
            "https://artsci.calendar.utoronto.ca/course/csc443h1",
            "https://artsci.calendar.utoronto.ca/course/csc469h1",
            "https://artsci.calendar.utoronto.ca/course/csc488h1",
            "https://artsci.calendar.utoronto.ca/course/csc301h1",
            "https://artsci.calendar.utoronto.ca/course/csc309h1",
            "https://artsci.calendar.utoronto.ca/course/csc410h1",
        ]
        
        for i in range(len(result_links)):
            print(result_links[i])
            result_links[i]  = result_links[i].lower()
        
        self.assertEqual(result_links, expected_links)


    def test_links_in_focus_cv(self):
        title = "CV"
        result_links = self.test.links_in_focus(focuses[title])
        expected_links = [
            "https://artsci.calendar.utoronto.ca/course/mat235y1",
            "https://artsci.calendar.utoronto.ca/course/mat237y1",
            "https://artsci.calendar.utoronto.ca/course/mat257y1",
            "https://artsci.calendar.utoronto.ca/course/csc320h1",
            "https://artsci.calendar.utoronto.ca/course/csc336h1",
            "https://artsci.calendar.utoronto.ca/course/csc311h1",
            "https://artsci.calendar.utoronto.ca/course/csc420h1",
            "https://artsci.calendar.utoronto.ca/course/csc412h1",
            "https://artsci.calendar.utoronto.ca/course/csc417h1",
            "https://artsci.calendar.utoronto.ca/course/csc317h1",
            "https://artsci.calendar.utoronto.ca/course/csc418h1",
            "https://artsci.calendar.utoronto.ca/course/csc419h1",
            "https://artsci.calendar.utoronto.ca/course/apm462h1",
            "https://artsci.calendar.utoronto.ca/course/cog250y1",
            "https://artsci.calendar.utoronto.ca/course/csc384h1",
            "https://artsci.calendar.utoronto.ca/course/csc485h1",
            "https://artsci.calendar.utoronto.ca/course/csc486h1",
            "https://artsci.calendar.utoronto.ca/course/phl232h1",
            "https://artsci.calendar.utoronto.ca/course/phy385h1",
            "https://artsci.calendar.utoronto.ca/course/psl440y1",
            "https://artsci.calendar.utoronto.ca/course/psy270h1",
            "https://artsci.calendar.utoronto.ca/course/psy280h1",
            "https://artsci.calendar.utoronto.ca/course/sta257h1",
            "https://artsci.calendar.utoronto.ca/course/sta261h1",
        ]
        for i in range(len(result_links)):
            result_links[i] = result_links[i].lower()

        self.assertEqual(expected_links, result_links, "Expected links should equal to result links")


    def test_links_in_focus_hci(self):
        title = "HCI"
        result_links = self.test.links_in_focus(focuses[title])
        expected_links = {
            "https://artsci.calendar.utoronto.ca/course/csc300h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc301h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc318h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc428h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta238h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta248h1": True,
            "https://artsci.calendar.utoronto.ca/course/soc204h1": True,
            "https://artsci.calendar.utoronto.ca/course/psy201h1": True,
            "https://artsci.calendar.utoronto.ca/course/psy100h1": True,
            "https://artsci.calendar.utoronto.ca/course/soc100h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc302h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc309h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc311h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc316h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc320h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc384h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc401h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc404h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc420h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc454h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc485h1": True,
            "https://artsci.calendar.utoronto.ca/course/sta313h1": True,
            "https://artsci.calendar.utoronto.ca/course/env281h1": True,
            "https://artsci.calendar.utoronto.ca/course/env381h1": True,
            "https://artsci.calendar.utoronto.ca/course/ire260h1": True,
            "https://artsci.calendar.utoronto.ca/course/cog250y1": True,
            "https://artsci.calendar.utoronto.ca/course/cog260h1": True,
            "https://artsci.calendar.utoronto.ca/course/cog341h1": True,
            "https://artsci.calendar.utoronto.ca/course/cog343h1": True,
            "https://artsci.calendar.utoronto.ca/course/cog344h1": True
        }

        for link in result_links:
            lower_case = link.lower()
            key_exists = expected_links.get(lower_case, False)
            self.assertTrue(key_exists)
            del expected_links[lower_case]

        self.assertEqual(expected_links, {})


    def test_links_in_focus_toc(self):
        title = "ToC"
        result_links = self.test.links_in_focus(focuses[title])
        print(result_links)
        expected_links = {
            "https://artsci.calendar.utoronto.ca/course/csc373h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc463h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc304h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc310h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc336h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc436h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc438h1": True,
            "https://artsci.calendar.utoronto.ca/course/mat309h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc448h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc473h1": True,
            "https://artsci.calendar.utoronto.ca/course/mat332h1": True,
            "https://artsci.calendar.utoronto.ca/course/mat344h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc494h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc495h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc240h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc265h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc236h1": True,
            "https://artsci.calendar.utoronto.ca/course/csc263h1": True
        }
        
        for link in result_links:
            lower_case = link.lower()
            print(lower_case)
            key_exists = expected_links.get(lower_case, False)
            print(key_exists)
            self.assertTrue(key_exists)
            del expected_links[lower_case]

        self.assertEqual(expected_links, {})


    def test_everything(self):
        # Crawl everything and see if the lengths match up
        for title in focuses.values():
            self.test.crawl_focus_w_cor(title)

        title_list = self.test.course_explore.title_list
        prereq_list = self.test.course_explore.prereq_list
        coreq_list = self.test.course_explore.coreq_list

        self.assertEqual(len(title_list), len(prereq_list), "you have to work whatfwasdsafsdfsa")
        self.assertEqual(len(title_list), len(coreq_list), "YOU HAVE TO WORK V2")

        f = open("/Users/jerryqi/PycharmProjects/pythonProject/files/output.txt", "a")
        
        for i in range(len(title_list)):
            print("Title:", title_list[i])
            print("Prerequisite:", prereq_list[i])
            print("Corequisite:", coreq_list[i])
            print("\n\n")
            f.write("Title: " + title_list[i] + "\n")
            f.write("Prerequisite: " + prereq_list[i] + "\n")
            f.write("Corequisite: " + coreq_list[i] + "\n")
            f.write("\n\n")

        f.close()

        print(self.test.course_explore.visited)

        return title_list


if __name__ == "__main__":
    unittest.main()

