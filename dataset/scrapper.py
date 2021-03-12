import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://programming.guide/java/list-of-java-exceptions.html"
STORY_LINKS = []

resp = requests.get(f"{BASE_URL}")
soup = BeautifulSoup(resp.content, "html.parser")
stories = soup.find_all("code")
contents = ''
for story in stories:
    contents += str(story.contents[0].encode('ascii', 'ignore').decode()) + '\n'

with open('programming_language_corpus/java_exceptions.txt', 'w') as java_ex:
    java_ex.write(contents)
