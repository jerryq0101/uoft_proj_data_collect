from bs4 import BeautifulSoup
import requests
from crawl import CourseExplore

base_url = "https://artsci.calendar.utoronto.ca"
eng_courses = {
    "AER": True,
    "APS": True,
    "BME": True,
    "CHE": True,
    "CIV": True,
    "ESC": True,
    "DMI": True,
    "ECE": True,
    "EDE": True,
    "MIE": True,
    "MSE": True,
    "TEP": True,
    "JCB": True,
    "JCC": True,
    "JCF": True,
    "JCH": True,
    "JCI": True,
    "JCM": True,
    "JDE": True,
    "JEB": True,
    "JEI": True,
    "JEL": True,
    "JEM": True,
    "JEN": True,
    "JFE": True,
    "JMA": True,
    "JMM": True,
    "JMY": True,
    "JMZ": True,
    "JNC": True,
    "JPB": True,
    "JSB": True
}
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

# A Class that crawls from the focus page

class FocusExplore:
    """
        Purpose: To crawl a single focus url and multiple focus urls
        Course Explore variable
    """
    def __init__(self):
        self.course_explore = CourseExplore()

    # Only support major for now
    def links_in_focus(self, title):
        pg = requests.get("https://artsci.calendar.utoronto.ca/section/Computer-Science")
        s_html = BeautifulSoup(pg.text,"html.parser")
        # print(s_html.prettify())
        thing = s_html.find("div", attrs={
            "aria-label": title
        })

        # Get all a tags in the parents
        # And then loop through, filter out utm/utsc/engineering courses
        # return links
        # we don't care about the credit requirement or any other requirement right now that is all frontend.

        # Full details is two levels up
        # print(thing.parent.parent.prettify())
        focus_page = thing.parent.parent
        all_related_courses_tags = focus_page.find_all("a")
        # print(all_related_courses_tags)
        filtered_links = []
        for a_tag in all_related_courses_tags:
            link = a_tag.attrs["href"]

            is_eng = link[8:11] in eng_courses

            if link[0:8] == "/course/" and not is_eng:
                complete_link = base_url + link
                already_visited = complete_link.lower() in filtered_links
                if not already_visited:
                    filtered_links.append(complete_link.lower())

        return filtered_links

    def crawl_focus_w_pre(self, title):
        links_arr = self.links_in_focus(title)
        
        for link in links_arr:
            self.course_explore.crawl(link)

        self.course_explore.print_results()
        return {
            "title_list": self.course_explore.title_list,
            "prereq_list": self.course_explore.prereq_list
        }

    def crawl_focus_w_cor(self, title):
        links_arr = self.links_in_focus(title)
        for link in links_arr:
            # For each link, check if its visited
            visited = self.course_explore.visited
            has_visited_capital = visited.get(link[0:-8] + link[-8:].upper(), False)
            has_visited_lower = visited.get(link[0:-8] + link[-8:].lower(), False)
            if not has_visited_capital and not has_visited_lower:
                self.course_explore.crawl_w_cor(link)

        return {
            "title_list": self.course_explore.title_list,
            "prereq_list": self.course_explore.prereq_list,
            "coreq_list": self.course_explore.coreq_list
        }

    def crawl_focus_w_cor_full(self):
        # Crawl everything and see if the lengths match up
        for title in focuses.values():
            self.crawl_focus_w_cor(title)
        
        return {
            "titles": self.course_explore.title_list,
            "prereq_list": self.course_explore.prereq_list,
            "coreq_list": self.course_explore.coreq_list
        }

if __name__ == "__main__":
    test = FocusExplore()
    title = focuses["ToC"]
    print(test.links_in_focus(title))

