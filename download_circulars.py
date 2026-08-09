import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://maharera.maharashtra.gov.in"
START_URL = "https://maharera.maharashtra.gov.in/circular?page={}"

DOWNLOAD_DIR = "knowledge_base/circulars"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "HEAD"],
    raise_on_status=False,
)
session.mount("https://", HTTPAdapter(max_retries=retries))

downloaded = 0
skipped = 0
total_found = 0
empty_pages = 0

for page in range(0, 10):      # Increase if more pages exist

    print(f"\nChecking page {page}")

    try:
        response = session.get(
            START_URL.format(page),
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch page {page}: {e}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")

    pdf_links = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if ".pdf" in href.lower():

            pdf_links.append(urljoin(BASE_URL, href))

    pdf_links = list(set(pdf_links))
    page_found = len(pdf_links)
    total_found += page_found

    if page_found == 0:
        empty_pages += 1
    else:
        empty_pages = 0

    print(f"Found {page_found} PDFs")

    for pdf_url in pdf_links:
        filename = pdf_url.split("/")[-1]
        filepath = os.path.join(
            DOWNLOAD_DIR,
            filename
        )

        if os.path.exists(filepath):
            skipped += 1
            print(f"Skipping {filename}")
            continue

        try:
            pdf = session.get(
                pdf_url,
                headers=headers,
                timeout=60
            )
            pdf.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(pdf.content)
            downloaded += 1
            print(f"Downloaded {filename}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {pdf_url}: {e}")

    if empty_pages >= 2:
        print("No PDFs found on two consecutive pages, stopping early.")
        break

print("\nFinished")
print(f"Total PDF links found: {total_found}")
print(f"Downloaded {downloaded} files")
print(f"Skipped {skipped} existing files")