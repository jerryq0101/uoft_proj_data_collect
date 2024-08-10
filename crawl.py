from bs4 import BeautifulSoup
import requests

# Global Variables

# since every st georges course url uses a sibling add on with this
base_url = "https://artsci.calendar.utoronto.ca"

# Start from csc263
test_url = "https://artsci.calendar.utoronto.ca/course/csc263h1"
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


class CourseExplore:
    # Instance Variables
    # eng_courses: the courses that should not be touched in the crawlling

    def __init__(self):
        # Set some useful constants
        self.visited = {}
        # Now we don't care what order is visited, we care about if they are all visited
            # So for tests, check for all associated title existence in the dictionary.

        self.prereq_list = []
        self.title_list = []
        self.excl_list = []
        self.coreq_list = []
        self.br_list = []

    def reset_crawl(self):
        self.visited = []
        self.prereq_list = []
        self.title_list = []
        self.excl_list = []
        self.coreq_list = []
        self.br_list = []

    def print_results(self):
        assert(len(self.prereq_list) == len(self.title_list))
        children_number = len(self.prereq_list)
        for i in range(children_number):
            print("Title:", self.title_list[i])
            print("Prerequisites:", self.prereq_list[i])
            print("\n")

    def get_html(self, url):
        # process html
        pg = requests.get(url)
        s_html = BeautifulSoup(pg.text, "html.parser")
        return s_html

    # crawl: Find all of the decendent courses from a single course url
    # * title_list[i] has prereq_list[i] prerequisites
    # Prediction: the thing will end if there is no next_crawls =>  next_crawls.isempty => no more st georges prerequisite a tag links found

    def crawl(self, url):
        # make sure no infinite recursion
        # record this link into visited
        self.visited[url] = True

        s_html = self.get_html(url)
        title = self.find_title(s_html).strip()

        # Valid course operations
        if title != "Page not found" and title != "Sorry, this course is not in the current Calendar.":
            self.title_list.append(title)

            # Incrementing a valid title
            self.visited[title] = len(self.title_list)-1
            
            # Find Prerequisite Links and also add the prerequisite string into instance arr
            next_crawls = self.find_pre_links(s_html)

            # Recurse into the next prerequisite courses
            for link in next_crawls:
                has_visited = self.visited.get(link, False)
                if not has_visited:
                    self.crawl(link)

    def crawl_w_cor(self, url):
        self.visited[url] = True

        # Process Html
        s_html = self.get_html(url)

        # Find title
        title = self.find_title(s_html)

        # Valid course operations
        if title != "Page not found" and title != "Sorry, this course is not in the current Calendar.":
            self.title_list.append(title)

            # Set visited for this title to be true
            self.visited[title] = len(self.title_list) - 1

            # Finding prerequisite links (and add prerequisite string into the array)
            pre_links = self.find_pre_links(s_html)

            # Finding corequisite links
            cor_links = self.find_corequisite_links(s_html)
            cor_string = self.find_corequisites(s_html)
            self.coreq_list.append(cor_string)

            total_links = pre_links + cor_links

            for link in total_links:
                has_visited_capital = self.visited.get(link[0:-8] + link[-8:].upper(), False)
                has_visited_lower = self.visited.get(link[0:-8] + link[-8:].lower(), False)
                if not has_visited_capital and not has_visited_lower:
                    self.crawl_w_cor(link)

    # Crawl DFS, but with excl and cor courses (this might be good as a new feature)
    def crawl_w_excl_cor(self, url):
        self.visited[url] = True

        # Process Html
        s_html = self.get_html(url)

        # Find title literally
        title = self.find_title(s_html).strip()

        # Valid course operations
        if title != "Page not found" and title != "Sorry, this course is not in the current Calendar.":
            self.title_list.append(title)

            # Set visited for this title to be true
            self.visited[title] = len(self.title_list) - 1

            # Finding prerequisite links (and add prerequisite string into the array)
            pre_links = self.find_pre_links(s_html)

            # Finding exclusion links
            excl_links = self.find_exclusion_links(s_html)
            # Add exclusion string
            excl_string = self.find_exclusions(s_html)
            self.excl_list.append(excl_string)

            # Finding corequisite links
            cor_links = self.find_corequisite_links(s_html)
            cor_string = self.find_corequisites(s_html)
            self.coreq_list.append(cor_string)

            total_links = pre_links + excl_links + cor_links

            for link in total_links:
                has_visited_capital = self.visited.get(link[0:-8] + link[-8:].upper(), False)
                has_visited_lower = self.visited.get(link[0:-8] + link[-8:].lower(), False)
                if not has_visited_capital and not has_visited_lower:
                    self.crawl_w_excl_cor(link)

    # find_pre_links: Find all of the plausible prerequisite links and add them to the list
    def find_pre_links(self, s_html):
        # find prerequisite links
        pre_div = s_html.find("div",
                              class_="w3-row field field--name-field-prerequisite field--type-text-long field--label-inline clearfix")

        # prerequisites may not exist
        if pre_div:
            pre_div_div = pre_div.find("div", class_="w3-bar-item field__item")
            raw_text = pre_div_div.text

            # add into prereq list for this page
            self.prereq_list.append(raw_text)

            a_tags = pre_div_div.find_all("a")
            pre_links = []
            for i in a_tags:
                link_string = i.attrs["href"]

                # Filtering out utm / utsc / engineering people and engineering courses with broken links
                is_eng = link_string[8:11] in eng_courses
                if link_string[0:7] == '/course' and not is_eng:
                    pre_link = base_url + link_string
                    pre_links.append(pre_link)

            return pre_links

        else:
            # Some courses don't have any prereqs, add empty prerequisites.
            self.prereq_list.append("")
            return []

    ## Find the course title on a single course page
    def find_title(self, s_html):
        title_div = s_html.find("h1", class_="page-title")
        return title_div.text

    # Finding Corequisites
    def find_corequisites(self, s_html):
        coreq_div = s_html.find("div",
                                class_="w3-row field field--name-field-corequisite field--type-text-long field--label-inline clearfix")
        if coreq_div:
            coreq_div_div = coreq_div.find("div", class_="w3-bar-item field__item")
            raw_text = coreq_div_div.text
            return raw_text
        else:
            return ""

    # Find Corequisite Links
    def find_corequisite_links(self, s_html):
        coreq_div = s_html.find("div",
                                class_="w3-row field field--name-field-corequisite field--type-text-long field--label-inline clearfix")
        if coreq_div:
            a_tags = coreq_div.find_all("a")
            coreq_links = []
            for i in a_tags:
                link_string = i.attrs["href"]
                is_eng = link_string[8:11] in eng_courses
                if link_string[0:7] == '/course' and not is_eng:
                    coreq_links.append(base_url + link_string)
            return coreq_links
        else:
            return []


if __name__ == "__main__":
    test = CourseExplore()
    url = "https://artsci.calendar.utoronto.ca/course/csc240h1"

    test.crawl_w_cor(url)

    result_visited = test.visited
    print(result_visited)
    

