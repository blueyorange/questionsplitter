import requests
import bs4
import os

allowedExtension= 'pdf'
OUTPUT_FOLDER = os.path.join(os.getcwd(),'downloads/Paper3')
os.chdir(OUTPUT_FOLDER)
res = requests.get('https://www.physicsandmathstutor.com/past-papers/gcse-physics/cie-igcse-paper-3/')
res.raise_for_status()
soup = bs4.BeautifulSoup(res.text, features="html.parser")

for a in soup.find_all('a', href=True):
    url = a['href']
    if url[0:5]=='https' and url[-3:]=='pdf':
        res = requests.get(url)
        f = open(os.path.basename(url), 'wb')
        for chunk in res.iter_content(100000):
            f.write(chunk)
        f.close()

