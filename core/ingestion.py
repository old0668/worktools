import feedparser
import httpx
from bs4 import BeautifulSoup
import logging
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Ingestor:
    def __init__(self, sources):
        self.sources = sources
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_all(self):
        all_news = []
        for source in self.sources:
            if source['type'] == 'rss':
                all_news.extend(self.fetch_rss(source))
        return all_news

    def fetch_rss(self, source):
        logger.info(f"Fetching news from {source['name']} ({source['url']})")
        try:
            # Use httpx with headers to fetch the XML content first
            with httpx.Client(timeout=15, headers=self.headers, follow_redirects=True) as client:
                response = client.get(source['url'])
                if response.status_code != 200:
                    logger.error(f"HTTP error {response.status_code} from {source['name']}")
                    return []
                
                # Parse the content using feedparser
                feed = feedparser.parse(io.BytesIO(response.content))
                
                news_items = []
                for entry in feed.entries:
                    # Clean HTML tags from title and summary
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    
                    if '<' in title or '&' in title:
                        title = BeautifulSoup(title, "html.parser").get_text()
                    if '<' in summary or '&' in summary:
                        summary = BeautifulSoup(summary, "html.parser").get_text()

                    news_items.append({
                        'title': title,
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': summary,
                        'source': source['name']
                    })
                
                logger.info(f"Successfully fetched {len(news_items)} items from {source['name']}")
                return news_items
        except Exception as e:
            logger.error(f"Error fetching from {source['name']}: {e}")
            return []

    async def extract_full_text(self, url):
        """Extract full text from a news URL if needed."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                # Basic heuristic to find main text
                paragraphs = soup.find_all('p')
                text = " ".join([p.get_text() for p in paragraphs])
                return text
            except Exception as e:
                logger.error(f"Error extracting text from {url}: {e}")
                return ""
