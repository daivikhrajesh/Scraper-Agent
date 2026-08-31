import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse

def scraper_page(url):

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses

    except requests.exceptions.RequestException as error:
        print(f"Error scraping {url}: {error}")
        return None

    soup=BeautifulSoup(response.content, 'html.parser')

    title = soup.title.get_text(strip=True) if soup.title else 'No title found'

    page_text = soup.get_text(separator=' ', strip=True)

    base_domain=urlparse(url).netloc

    internal_links = []
    external_links = []

    links = soup.find_all('a')

    for link in links:
        href = link.get('href')
        if href:
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            if parsed_url.netloc == base_domain:
                internal_links.append(full_url)
            else:
                external_links.append(full_url)

    data = {
        'url': url,
        'title': title,
        'text': page_text,
        'internal_links': internal_links,
        'external_links': external_links
    }

    return data

url = "https://www.example.com"  # Replace with the desired URL

result = scraper_page(url)

#print(result)
if result:
    print("Website:", result["url"])
    print("Title:", result["title"])
    print("Internal links:", len(result["internal_links"]))
    print("External links:", len(result["external_links"]))