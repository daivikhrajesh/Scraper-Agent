import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
import json



url = "https://www.example.com"
#url = "https://this-website-does-not-exist-123456789.com"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

except requests.exceptions.RequestException as error:
    print(f"Error while requesting website: {error}")
    exit()

soup = BeautifulSoup(response.text, "html.parser")
#print(response.status_code)
#print(soup.title.get_text())
#print(soup.h1.get_text())
#print(soup.p.get_text())

page_text = soup.get_text(separator=" ", strip=True)
# print(page_text)
links = soup.find_all("a")

base_domain = urlparse(url).netloc
internal_links = []
external_links = []




for link in links:
    href = link.get("href")
    if href:
        full_url = urljoin(url, href)
        link_domain = urlparse(full_url).netloc
        if link_domain == base_domain:
            internal_links.append(full_url)
        else:
            external_links.append(full_url)

# print("Internal Links:")
# for link in internal_links:
#     print(link)

# print("\nExternal Links:")
# for link in external_links:
#     print(link)

data = {
    "url": url,
    "title": soup.title.get_text(strip=True) if soup.title else None,
    "text": page_text,
    "internal_links": internal_links,
    "external_links": external_links
}

with open("data/scraped_data.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4, ensure_ascii=False)

#print("Data saved successfully.")

print("Website:", url)
print("Title:", soup.title.get_text(strip=True) if soup.title else "No title found")
print("Internal Links found:", len(internal_links))
print("External Links found:", len(external_links))
print("Data saved to 'data/scraped_data.json'")