"""
Web Search Service using 100% free, open-source APIs
Supports: DuckDuckGo with optional Wikipedia (full content) and ArXiv
"""

import logging
import asyncio
import re
from typing import List, Dict
from html import unescape
import aiohttp

logger = logging.getLogger(__name__)


class WebSearchService:
    """Service for performing web searches using free open-source APIs"""

    def __init__(self):
        """Initialize the web search service"""
        self.wikipedia_api_url = "https://en.wikipedia.org/w/api.php"
        self.duckduckgo_url = "https://api.duckduckgo.com/"
        self.arxiv_url = "http://export.arxiv.org/api/query"

        logger.info(
            "✓ Web Search initialized with free open-source APIs "
            "(DuckDuckGo, Wikipedia, ArXiv)"
        )

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_wikipedia: bool = False
    ) -> List[Dict]:
        """
        Perform web search using free open-source APIs

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            include_wikipedia: Whether to include Wikipedia results

        Returns:
            List of search results with title, url, content, and source
        """
        results = []

        # Try DuckDuckGo first (fast, instant answers)
        ddg_results = await self._search_duckduckgo(query, max_results)
        results.extend(ddg_results)

        # Try Wikipedia (full article content, not just snippets)
        if include_wikipedia and len(results) < max_results:
            wiki_results = await self._search_wikipedia(
                query,
                max_results - len(results)
            )
            results.extend(wiki_results)

        # Try ArXiv for academic/research content
        if len(results) < max_results:
            arxiv_results = await self._search_arxiv(
                query,
                max_results - len(results)
            )
            results.extend(arxiv_results)

        logger.info(
            f"Web search completed: {len(results)} results for '{query}'"
        )
        return results[:max_results]

    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Search DuckDuckGo Instant Answer API (free, no API key needed)"""
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }

            timeout = aiohttp.ClientTimeout(total=10)
            max_attempts = 3

            async with aiohttp.ClientSession(timeout=timeout) as session:
                for attempt in range(1, max_attempts + 1):
                    try:
                        async with session.get(
                            self.duckduckgo_url,
                            params=params
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                results = []

                                # Abstract (main answer)
                                if data.get('Abstract'):
                                    results.append({
                                        'title': data.get('Heading', query),
                                        'url': data.get('AbstractURL', ''),
                                        'content': self._clean_text(
                                            data.get('Abstract', '')
                                        ),
                                        'source': 'duckduckgo'
                                    })

                                # Related topics
                                for topic in data.get('RelatedTopics', [])[:max_results - len(results)]:
                                    if isinstance(topic, dict) and topic.get('Text'):
                                        results.append({
                                            'title': topic.get('Text', '')[:100] + '...',
                                            'url': topic.get('FirstURL', ''),
                                            'content': self._clean_text(
                                                topic.get('Text', '')
                                            ),
                                            'source': 'duckduckgo'
                                        })

                                if results:
                                    logger.info(
                                        f"DuckDuckGo search: {len(results)} results"
                                    )
                                    return results

                                logger.info("DuckDuckGo returned no usable results")
                                return []

                            if response.status == 202 and attempt < max_attempts:
                                wait_time = attempt
                                logger.info(
                                    "DuckDuckGo returned status 202 (processing). "
                                    f"Retrying in {wait_time}s (attempt {attempt}/{max_attempts})."
                                )
                                await asyncio.sleep(wait_time)
                                continue

                            logger.warning(
                                f"DuckDuckGo returned status {response.status}"
                            )
                            break

                    except asyncio.TimeoutError:
                        if attempt < max_attempts:
                            wait_time = attempt
                            logger.info(
                                "DuckDuckGo request timed out. "
                                f"Retrying in {wait_time}s (attempt {attempt}/{max_attempts})."
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        raise

        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {str(e)}")

        return []

    async def _search_wikipedia(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Search Wikipedia and get full article content (free, no API key needed)"""
        try:
            headers = {
                "User-Agent": (
                    "EideticRAG/1.0 "
                    "(Educational; +https://github.com/user/eidetic-rag)"
                )
            }

            async with aiohttp.ClientSession() as session:
                # First, search for articles
                search_params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": max_results
                }

                async with session.get(
                    self.wikipedia_api_url,
                    params=search_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(
                            f"Wikipedia search returned status {response.status}"
                        )
                        return []

                    search_data = await response.json()
                    search_results = search_data.get("query", {}).get(
                        "search",
                        []
                    )

                    if not search_results:
                        return []

                    # Get full content for top results
                    results = []
                    for item in search_results[:max_results]:
                        title = item.get('title', '')
                        
                        # Get extract (summary) for this article
                        extract_params = {
                            "action": "query",
                            "prop": "extracts|info",
                            "exintro": 1,  # Use 1 instead of True
                            "explaintext": 1,  # Use 1 instead of True
                            "inprop": "url",
                            "titles": title,
                            "format": "json"
                        }

                        async with session.get(
                            self.wikipedia_api_url,
                            params=extract_params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as extract_response:
                            if extract_response.status == 200:
                                extract_data = await extract_response.json()
                                pages = extract_data.get('query', {}).get('pages', {})
                                
                                for page_id, page in pages.items():
                                    extract = page.get('extract', '')
                                    if extract:
                                        # Clean and truncate to reasonable length
                                        clean_content = self._clean_text(extract)
                                        if len(clean_content) > 1000:
                                            clean_content = clean_content[:1000] + "..."
                                        
                                        results.append({
                                            'title': title,
                                            'url': page.get(
                                                'fullurl',
                                                f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                                            ),
                                            'content': clean_content,
                                            'source': 'wikipedia'
                                        })

                    logger.info(
                        f"Wikipedia search: {len(results)} results with full content"
                    )
                    return results

        except Exception as e:
            logger.warning(f"Wikipedia search failed: {str(e)}")
            return []

    async def _search_arxiv(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Search ArXiv for academic papers (free, no API key needed)"""
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.arxiv_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        results = self._parse_arxiv_xml(text, max_results)
                        logger.info(
                            f"ArXiv search: {len(results)} results"
                        )
                        return results
                    else:
                        logger.warning(
                            f"ArXiv returned status {response.status}"
                        )
                        return []

        except Exception as e:
            logger.warning(f"ArXiv search failed: {str(e)}")
            return []

    def _clean_text(self, text: str) -> str:
        """Remove HTML tags and clean text for display"""
        if not text:
            return ""
        
        # Unescape HTML entities
        text = unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special search markers
        text = re.sub(r'searchmatch|class=', '', text)
        
        # Trim
        return text.strip()

    def _parse_arxiv_xml(
        self,
        xml_text: str,
        max_results: int
    ) -> List[Dict]:
        """Parse ArXiv XML response"""
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_text)
            results = []

            # ArXiv uses Atom namespace
            namespace = {
                'atom': 'http://www.w3.org/2005/Atom'
            }

            for entry in root.findall('atom:entry', namespace)[:max_results]:
                try:
                    title_elem = entry.find('atom:title', namespace)
                    summary_elem = entry.find('atom:summary', namespace)
                    id_elem = entry.find('atom:id', namespace)

                    if title_elem is not None and id_elem is not None:
                        arxiv_id = id_elem.text.split('/abs/')[-1]
                        summary = (
                            summary_elem.text.strip()
                            if summary_elem is not None
                            else ""
                        )
                        
                        # Clean and truncate summary
                        clean_summary = self._clean_text(summary)
                        if len(clean_summary) > 800:
                            clean_summary = clean_summary[:800] + "..."
                        
                        results.append({
                            'title': self._clean_text(title_elem.text.strip()),
                            'url': f"https://arxiv.org/abs/{arxiv_id}",
                            'content': clean_summary,
                            'source': 'arxiv'
                        })

                except Exception as e:
                    logger.debug(f"Error parsing ArXiv entry: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Error parsing ArXiv XML: {str(e)}")
            return []
