# Description: General Helper functions that don't use a Neo4j Session.
from focus_crawl import FocusExplore


def explore_all_focuses():
    """
    Finds full titles, and splits to get the upper case course code. (Also make the titles_dict, which is used for recursion)
    """
    var = FocusExplore()
    titles_dict = {}
    titles = var.crawl_focus_w_cor_full()["titles"]
    
    codes = []
    for i in range(len(titles)):
        codes.append(titles[i].split(":")[0])
        titles_dict[codes[i]] = titles[i]

    return {
        "titles_dict": titles_dict,
        "codes": codes
    }


def process_code_prereq(code):
    """
    Converts the course code to lowercase and appends "_pre" to it. For accessing output.py variable
    """
    code = code.lower()
    return code + "_pre"


def process_code_coreq(code):
    """
    Converts the course code to lowercase and appends "_cor" to it. For accessing output.py variable
    """
    code = code.lower()
    return code + "_cor"
