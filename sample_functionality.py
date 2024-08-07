from bs4 import BeautifulSoup
import requests

## Rest of the stuff is still on Colab
## https://colab.research.google.com/drive/1G6y0wqx-njW0IZqcB3K5WlGVDWTP0H1U#scrollTo=aFaJEqFJ1OOd

def main():
    url = "https://artsci.calendar.utoronto.ca/course/mat136h1"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    pre_search(soup)

# Prerequisites Search
def pre_search(soup):
    pre_div = soup.find("div", class_="w3-row field field--name-field-prerequisite field--type-text-long field--label-inline clearfix")
    if pre_div:
        pre_div_div = pre_div.find("div", class_="w3-bar-item field__item")
        print(pre_div_div.text)
        raw_text = pre_div_div.text
        a_tags = pre_div_div.find_all("a")
        for i in a_tags:
            print(i.attrs)
            if i.attrs["href"][0:7] == '/course':
                print("yes")
                print("https://artsci.calendar.utoronto.ca" + i.attrs["href"])


if __name__ == "__main__":
    main()