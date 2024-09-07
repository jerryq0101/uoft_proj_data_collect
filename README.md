# Prerequisite Visualizer (UofT) - Data Processing

---

### Scripts used for UofT data scraping and uploading to DB

### Table of Contents
- [Description](#description)
- [Files](#files)
- [Key Features](#key-features)
- [Setup and Usage](#setup-and-usage)
  - [Dependencies](#dependencies)
  - [Scraping](#scraping)
  - [Loading the Neo4j Database](#loading-the-neo4j-database-with-course-data)
- [Results and Understanding](#results-and-understanding)

---

#### Description

This repository contains the scripts used to scrape data from individual University of Toronto (UofT) course pages and upload them to a Neo4j database. These scripts are part of a larger project aimed at visualizing course prerequisites. (ADD LINKS TO OTHER REPOS)


#### Directory

- ``scraping/``: Contains scripts that fetch data from UofT pages and store them in the files/ folder.
- `db/`: Contains scripts that parse data from the files/ folder and create nodes and relationships in the Neo4j database.
- `files/`: Stores the scraped data before it's processed and uploaded to the database.
```
└── uoft_proj_data_collect/
    ├── db
    ├── files
    └── scraping
```


---

### Key Features

- Web scraping of UofT course data

- Data Parsing and structuring course prerequisites 

- Neo4j database population

- Prerequisite and corequisite relationship mapping from parsed data

---

### Setup and Usage

#### Dependencies
```
# Python libraries
neo4j==4.4.0
python-dotenv==0.19.2
requests==2.26.0
beautifulsoup4==4.10.0
```

#### Scraping

To get started in scraping, you can head to `focus_crawl.py`, which is a set of functions that allow one to crawl the entire prerequisite tree of all the Computer Science Major Focuses.

```python
# focus_crawl.py Line 176
# This would crawl and gather the entire "lineage" of prerequisites and corequisites of the courses in the ToC (Theory of Computing) focus.
# More documentation in the file on how each function should be used.

test = FocusExplore()
title = focuses["ToC"]
print(test.crawl_focus_w_cor(title))

title_list = test.course_explore.title_list
prereq_list = test.course_explore.prereq_list
coreq_list = test.course_explore.coreq_list

for i in range(len(title_list)):
    print("Title:", title_list[i])
    print("Prerequisite:", prereq_list[i])
    print("Corequisite:", coreq_list[i])
    print("\n\n")

```

Simply run `focus_crawl.py` to get all of the Theory of Computing Courses and all possible prerequisites in a printed form in the console. (Or modify it for your own use case at [Line 176](./scraping/focus_crawl.py#L176))

For targetting more individualized examples, you can run `crawl.py`, which allows one to find the prerequisite lineage of specific Arts and Science Course URLs.

```python
# crawl.py Line 364
# This finds the entire lineage of courses for CSC240H1. More functionality in crawl.py

test = CourseExplore()
url = "https://artsci.calendar.utoronto.ca/course/csc240h1"

test.crawl_w_cor(url)

result_visited = test.visited
print(result_visited)
```

Simply run `crawl.py` for the CSC240H1 lineage of courses. (Or modify it for your own use case at [Line 364](./scraping/crawl.py#L364)) 

#### Loading the Neo4j Database with Course Data

First I scraped the academic calendar, this generates a compiled list of english descriptions for each course in `files/output.txt`.

- The code for the above process can be found in `/tests/test_focus_explore.py` [Line 249](./scraping/tests/test_focus_explore.py#L249)

Due to UofT's inconsistent prerequisite description syntax, I converted the prerequisite relationships into parsable data by human labor in `files/output.py`.

This took north of 2 hours. FML.

To load the `output.py` data into a Neo4j database, first make a .env file containing your Neo4j DB details.
```
N4J_DB_URI=
N4J_DB_PASS=
```

Then, simply run `creating_the_full_tree.py`.


### Results and Understanding

I am going to explain what I mean earlier by "all possible prerequisites" or "linage of courses".

The scraping functions attempts to collect direct prerequisite data from each course page. It simultaneously collects each of those course links to traverse to next. Next and next. 

At the end, allowing us to collect data for all possible prereq courses (and prereqs of prereqs and so on) of the starting courses.

In `focus_crawl.py`, I chose the Computer Science focus courses for undergrad to traverse through, capturing all possibilities of courses for Computer science majors.

All of the course data will be in several lists. (title_list, prereq_list, coreq_list). 

The data at each index of these lists are data for one course.

E.g. 
```
Title: ECO227Y1: Foundations of Econometrics
Prerequisite: ( ECO101H1(70%),  ECO102H1(70%))/  ECO100Y5(70%)/ ( ECO101H5(70%),  ECO102H5(70%))/ ( MGEA02H3(70%),  MGEA06H3(70%));  MAT133Y1(63%)/ ( MAT135H1(60%),  MAT136H1(60%))/  MAT137Y1(55%)/  MAT157Y1(55%)
Corequisite: Recommended:  MAT223H1/  MAT240H1,  MAT235Y1/  MAT237Y1/  ECO210H1
```

By gathering all the direct prerequisite, and direct corequisite data of computer science majors, we can upload them to Neo4j and take advantage of its ability to traverse through graphs. 

This allows us to generate full prerequisite trees for each course instead of just a direct prerequisite tree that we can see on the browser.

