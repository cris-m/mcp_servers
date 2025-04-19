import os
import re
from typing import List

import bs4
from bs4 import BeautifulSoup
from langchain_community.document_loaders import (
    PlaywrightURLLoader,
    SeleniumURLLoader,
    WebBaseLoader,
)
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.document_loaders.sitemap import SitemapLoader
from langchain_community.utilities import (
    BingSearchAPIWrapper,
    DuckDuckGoSearchAPIWrapper,
    WikipediaAPIWrapper,
)
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_tavily import TavilySearch


class Web:
    def __init__(
        self,
        search_engine: str,
        user_agent: str = None,
        max_results: int = 10,
        load_js: bool = False,
        use_playwright: bool = False,
        use_selenium: bool = False,
    ):
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        os.environ["USER_AGENT"] = self.user_agent

        self.search_engine = search_engine
        self.max_results = max_results
        self.load_js = load_js
        self.use_playwright = use_playwright
        self.use_selenium = use_selenium

        self._init_search()

    def _init_search(self):
        if self.search_engine == "tavily":
            self.searcher = TavilySearch(max_results=self.max_results)
        elif self.search_engine == "google":
            self.searcher = GoogleSearchAPIWrapper(k=self.max_results)
        elif self.search_engine == "bing":
            self.searcher = BingSearchAPIWrapper(
                k=self.max_results, bing_subscription_key="", user_agent=self.user_agent
            )
        elif self.search_engine == "duckduckgo":
            self.searcher = DuckDuckGoSearchAPIWrapper(max_results=self.max_results)
        elif self.search_engine == "wikipedia":
            self.searcher = WikipediaAPIWrapper()
        else:
            raise ValueError(f"Unsupported search engine: {self.search_engine}")

    def _bs4_extractor(self, html: str) -> str:
        try:
            if html.strip().startswith("<?xml") or html.strip().startswith("<xml"):
                soup = BeautifulSoup(html, "xml")
            else:
                soup = BeautifulSoup(html, "lxml")

            extracted_text = soup.get_text(separator=" ", strip=True)
            cleaned_text = re.sub(r"\n{3,}", "\n\n", extracted_text)
            cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
            return cleaned_text
        except Exception:
            return html

    async def load_url(
        self, url_paths: List[str], recursive: bool = False, depth: int = 5
    ):
        if recursive:
            loader = RecursiveUrlLoader(
                url=url_paths[0],
                max_depth=depth,
                use_async=True,
                extractor=self._bs4_extractor,
                headers={"User-Agent": self.user_agent},
            )
            return await loader.aload()

        if self.load_js:
            if self.use_playwright:
                loader = PlaywrightURLLoader(
                    urls=url_paths,
                    remove_selectors=["header", "footer", "nav"],
                    continue_on_failure=True,
                )
            elif self.use_selenium:
                loader = SeleniumURLLoader(
                    urls=url_paths,
                    browser="chrome",
                    headless=True,
                )
            else:
                loader = PlaywrightURLLoader(
                    urls=url_paths,
                    remove_selectors=["header", "footer", "nav"],
                    continue_on_failure=True,
                    browser_kwargs={"user_agent": self.user_agent},
                )
        else:
            loader = WebBaseLoader(
                web_paths=url_paths,
                requests_kwargs={"headers": {"User-Agent": self.user_agent}},
                bs_kwargs={"parse_only": bs4.SoupStrainer()},
                bs_get_text_kwargs={"separator": " | ", "strip": True},
            )

        if hasattr(loader, "alazy_load"):
            docs = []
            async for doc in loader.alazy_load():
                docs.append(doc)
            return docs
        else:
            return loader.load()

    def load_sitemap(self, sitemap_url: str):
        """Load content from a sitemap."""
        loader = SitemapLoader(
            web_path=sitemap_url,
            filter_urls=[".*"],
            requests_kwargs={"headers": {"User-Agent": self.user_agent}},
        )
        return loader.load()

    async def search(self, query: str, **kwargs):
        if self.search_engine == "tavily":
            return await self.searcher.ainvoke(query, **kwargs)
        elif self.search_engine == "wikipedia":
            return self.searcher.run(query)
        else:
            return self.searcher.run(query)
