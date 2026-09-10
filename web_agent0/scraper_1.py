import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse,urlunparse

def scraper_page(url):

    try:
        response = requests.get(url, timeout=10)
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

# url = "https://www.example.com"  # Replace with the desired URL

# result = scraper_page(url)

# #print(result)
# if result:
#     print("Website:", result["url"])
#     print("Title:", result["title"])
#     print("Internal links:", len(result["internal_links"]))
#     print("External links:", len(result["external_links"]))

def crawl_website(start_url, max_pages = 10):

    visited = set()
    to_visit = [start_url]
    all_pages = []
    failed_pages = []

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        print('Scraping', current_url)

        page_data = scraper_page(current_url)

        visited.add(current_url)

        if page_data:
            all_pages.append(page_data)

            for link in page_data["internal_links"]:
                parsed = urlparse(link)

                if parsed.scheme not in ['https','http']:
                    continue

                clearn_url = urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        ""
                    )
                )

                if clearn_url not in visited and clearn_url not in to_visit:
                    to_visit.append(clearn_url)
        else:
            failed_pages.append(current_url)

        if len(visited) >= max_pages:
            break
    return {
        "visited": visited,
        "pages":all_pages,
        "failed_pages":failed_pages
    }

result = crawl_website(
    "https://example.com",
    max_pages=10
)

with open("data/crawl_data.json", 'w', encoding='utf-8') as file:
    json.dump(result["pages"],file, indent=4, ensure_ascii=False)

