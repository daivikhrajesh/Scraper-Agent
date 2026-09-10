import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse,urlunparse
import urllib.robotparser
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def normalize_domain(domain):
    if domain.startswith('www.'):
        return domain[4:]
    return domain

def normalize_url(url):

    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path

    if path != "/" and path.endswith("/"):
        path = path[:-1]

    clean_url = urlunparse(
        (
            scheme,
            netloc,
            path,
            parsed.params,
            parsed.query,
            ""
        )
    )

    return clean_url

def create_robots_parser(start_url):

    robots_url = urljoin(start_url, "/robots.txt")

    parser = urllib.robotparser.RobotFileParser()

    parser.set_url(robots_url)

    try:
        parser.read()
    except Exception as error:
        print(f"Could not read robots.txt: {error}")

    return parser

def scraper_page(url, base_domain,session):

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()  

    except requests.exceptions.RequestException as error:
        print(f"Error scraping {url}: {error}")
        return None

    soup=BeautifulSoup(response.content, 'html.parser')

    title = soup.title.get_text(strip=True) if soup.title else 'No title found'

    page_text = soup.get_text(separator=' ', strip=True)

    internal_links = []
    external_links = []

    links = soup.find_all('a')

    for link in links:
        href = link.get('href')
        if href:
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            link_domain = normalize_domain(parsed_url.netloc)

            if link_domain == base_domain:
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
def create_session():
    USER_AGENT = "ScraperAgent/1.0"
    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9"
    })

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

def should_skip_url(url):

    parsed = urlparse(url)

    if parsed.scheme not in ["http", "https"]:
        return True

    blocked_paths = [
        "/login",
        "/logout",
        "/cart",
        "/checkout"
    ]

    for blocked_path in blocked_paths:
        if parsed.path.startswith(blocked_path):
            return True

    return False

def discover_sitemap(start_url):

    sitemap_url = urljoin(start_url, "/sitemap.xml")

    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"No sitemap found: {error}")
        return []

    soup = BeautifulSoup(response.content, "xml")

    sitemap_urls = []

    for loc in soup.find_all("loc"):
        sitemap_urls.append(loc.get_text(strip=True))

    return sitemap_urls

def get_robots_txt(start_url):

    robots_url = urljoin(start_url, "/robots.txt")

    try:
        response = requests.get(robots_url, timeout=10)
        response.raise_for_status()

    except requests.exceptions.RequestException as error:
        print(f"No robots.txt found: {error}")
        return None

    return response.text

def get_file_type(url):

    parsed = urlparse(url)

    path = parsed.path.lower()

    file_extensions = {
        ".pdf": "pdf",
        ".csv": "csv",
        ".json": "json",
        ".xml": "xml",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".gif": "image",
        ".webp": "image",
        ".zip": "archive",
        ".doc": "document",
        ".docx": "document",
        ".xls": "spreadsheet",
        ".xlsx": "spreadsheet"
    }

    for extension, file_type in file_extensions.items():

        if path.endswith(extension):
            return file_type

    return None


def crawl_website(start_url, max_pages = 10, delay=1):
    start_time = time.time()
    start_url = normalize_url(start_url)
    base_domain = normalize_domain(urlparse(start_url).netloc)
    robots_parser = create_robots_parser(start_url)
    session =create_session()
    to_visit = [start_url]
    visited = set()
    to_visit = [start_url]
    all_pages = []
    failed_pages = []
    files_found=[]
    seen_files = set()
    skipped_urls = 0
    robots_blocked = 0

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        if not robots_parser.can_fetch("*", current_url):
            print("Blocked by robots.txt:", current_url)
            robots_blocked += 1
            visited.add(current_url)
            continue

        print('Scraping', current_url)

        page_data = scraper_page(current_url, base_domain,session)

        visited.add(current_url)

        if page_data:
            all_pages.append(page_data)

            for link in page_data["internal_links"]:

                clean_url = normalize_url(link)

                if should_skip_url(clean_url):
                    skipped_urls += 1
                    continue
                if not robots_parser.can_fetch("*", clean_url):
                    robots_blocked += 1
                    continue
                file_type = get_file_type(clean_url)

                if file_type:
                    if clean_url not in seen_files:
                        files_found.append({
                            "url": clean_url,
                            "type": file_type
                        })
                        seen_files.add(clean_url)
                    continue

                if clean_url not in visited and clean_url not in to_visit:
                    to_visit.append(clean_url)
        else:
            failed_pages.append(current_url)
        time.sleep(delay)

        if len(visited) >= max_pages:
            break
    end_time = time.time()
    elapsed_time = end_time - start_time
    return {
        "visited": visited,
        "pages":all_pages,
        "failed_pages":failed_pages,
        "files": files_found,
        "skipped_urls": skipped_urls,
        "robots_blocked": robots_blocked,
        "elapsed_time": elapsed_time
    }
result = crawl_website(
    "https://example.com",
    max_pages=10,
    delay=1
)

with open("data/crawl_data.json", "w", encoding="utf-8") as file:
    json.dump(
        result["pages"],
        file,
        indent=4,
        ensure_ascii=False
    )

with open("data/files_found.json", "w", encoding="utf-8") as file:
    json.dump(
        result["files"],
        file,
        indent=4,
        ensure_ascii=False
    )

print("\n--- Crawl Summary ---")
print("Visited:", len(result["visited"]))
print("Pages stored:", len(result["pages"]))
print("Files found:", len(result["files"]))
print("Failed pages:", len(result["failed_pages"]))
print("Skipped URLs:", result["skipped_urls"])
print("Blocked by robots:", result["robots_blocked"])
print("Elapsed time:", round(result["elapsed_time"], 2), "seconds")