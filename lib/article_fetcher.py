import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}
TIMEOUT = 15
MAX_LINKED_PAGES = 5
MAX_TEXT_LENGTH = 5000
MAX_LINKED_TEXT_LENGTH = 2000


def _extract_text(soup):
    """Extract main text content from a BeautifulSoup parsed page."""
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'iframe']):
        tag.decompose()

    content = soup.find('article') or soup.find('main') or soup.find('body')
    if not content:
        return ''

    text = content.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def _extract_links(soup, base_url):
    """Extract article-body links, resolved to absolute URLs."""
    content = soup.find('article') or soup.find('main') or soup.find('body')
    if not content:
        return []

    base_domain = urlparse(base_url).netloc
    links = []
    seen = set()

    for a_tag in content.find_all('a', href=True):
        href = a_tag['href']
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)

        if parsed.scheme not in ('http', 'https'):
            continue
        if absolute in seen:
            continue
        if '#' in absolute:
            absolute = absolute.split('#')[0]
        if not absolute or absolute == base_url:
            continue

        seen.add(absolute)
        links.append(absolute)

        if len(links) >= MAX_LINKED_PAGES:
            break

    return links


def _is_medium(url):
    """Check if a URL is a Medium article (medium.com or custom domain on Medium)."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return 'medium.com' in host


def _to_scribe_url(url):
    """Convert a medium.com URL to its scribe.rip equivalent."""
    return url.replace('medium.com', 'scribe.rip', 1)


def _fetch_with_session(url):
    """Fetch a URL using a requests Session for cookie/redirect support."""
    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    return response


def fetch_article(url):
    """Fetch an article URL and extract its text content and links.

    Returns:
        dict with keys: title, main_text, links
    """
    # For Medium URLs, go through scribe.rip to avoid 403s
    if _is_medium(url):
        try:
            scribe_url = _to_scribe_url(url)
            response = _fetch_with_session(scribe_url)
        except Exception:
            # If scribe.rip fails, try the original URL anyway
            response = _fetch_with_session(url)
    else:
        response = _fetch_with_session(url)

    soup = BeautifulSoup(response.content, 'lxml')

    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else 'Untitled'

    main_text = _extract_text(soup)[:MAX_TEXT_LENGTH]
    links = _extract_links(soup, url)

    return {
        'title': title,
        'main_text': main_text,
        'links': links,
    }


def _fetch_single_page(url):
    """Fetch a single linked page and return its text."""
    try:
        response = _fetch_with_session(url)
        soup = BeautifulSoup(response.content, 'lxml')
        text = _extract_text(soup)[:MAX_LINKED_TEXT_LENGTH]
        return {'url': url, 'text': text}
    except Exception:
        return {'url': url, 'text': ''}


def fetch_linked_pages(links):
    """Fetch multiple linked pages concurrently.

    Returns:
        list of dicts with keys: url, text
    """
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_single_page, url): url for url in links[:MAX_LINKED_PAGES]}
        for future in as_completed(futures):
            result = future.result()
            if result['text']:
                results.append(result)

    return results
