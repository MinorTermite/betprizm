from bs4 import BeautifulSoup
import re

html = open('tennis.html', encoding='utf-8', errors='ignore').read()
soup = BeautifulSoup(html, 'lxml')

print(html[:1000])
print("="*50)
import re
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'lxml')
print("Contains 'Djokovic'?", "Djokovic" in html)
print("Contains 'Alcaraz'?", "Alcaraz" in html)
print("Contains 'Sinner'?", "Sinner" in html)
print("Total rows with 'event':", len(soup.select('[class*="event"]')))
for el in soup.select('[class*="event"]')[:3]:
    print(el.get('class'))
