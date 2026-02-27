from bs4 import BeautifulSoup

html = open('popular.html', encoding='utf-8', errors='ignore').read()
soup = BeautifulSoup(html, 'lxml')
for a in soup.find_all('a', href=True):
    href = a['href']
    if '/Tennis/' in href or '/e-Sports/' in href or '/Basketball/' in href or '/Ice+Hockey/' in href or '/Volleyball/' in href:
        print(href)
