import logging
import os
import sys
import traceback

from mcp.server.fastmcp import FastMCP
from web import Web


class WebMCP:
    def __init__(self):
        self._setup_logging()
        self.mcp = FastMCP("Web MCP")
        self.web = None
        self._init_web()
        self._register_tools()
        logging.info("Web MCP initialized")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger("WebMCP")

    def _init_web(self):
        logging.info("Initializing Web client")
        self.web = Web(
            user_agent=os.getenv(
                "DEFAULT_USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            ),
            search_engine=os.getenv("DEFAULT_SEARCH_ENGINE", "tavily"),
            max_results=int(os.getenv("DEFAULT_MAX_RESULTS", "10")),
            load_js=os.getenv("DEFAULT_LOAD_JS", "false").lower() == "true",
            use_playwright=os.getenv("DEFAULT_USE_PLAYWRIGHT", "true").lower()
            == "true",
            use_selenium=os.getenv("DEFAULT_USE_SELENIUM", "false").lower() == "true",
        )

    def _register_tools(self):
        logging.info("Registering tools")

        @self.mcp.tool("load_url")
        async def load_url(url_paths: list, recursive: bool = False, depth: int = 2):
            """Load content from URLs.

            Args:
                url_paths: List of URLs to load
                recursive: Whether to load recursively
                depth: Maximum depth for recursive loading
            """
            try:
                docs = await self.web.load_url(url_paths, recursive, depth)
                return {"success": True, "documents": docs}
            except Exception as e:
                logging.error(f"Failed to load URLs: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("load_sitemap")
        async def load_sitemap(sitemap_url: str):
            """Load content from a sitemap.

            Args:
                sitemap_url: URL of the sitemap to load
            """
            try:
                docs = await self.web.load_sitemap(sitemap_url)
                return {"success": True, "documents": docs}
            except Exception as e:
                logging.error(f"Failed to load sitemap: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("search")
        async def search(query: str, max_results: int = None):
            """Search using the configured search engine.

            Args:
                query: Search query
                max_results: Maximum number of results to return
            """
            try:
                if max_results:
                    self.web.max_results = max_results
                    self.web._init_search()
                results = await self.web.search(query)
                return {"success": True, "results": results}
            except Exception as e:
                logging.error(f"Failed to search: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("configure_web")
        def configure_web(
            user_agent: str = None,
            search_engine: str = None,
            max_results: int = None,
            load_js: bool = None,
            use_playwright: bool = None,
            use_selenium: bool = None,
        ):
            """Configure the web client settings.

            Args:
                user_agent: Custom user agent string
                search_engine: Search engine to use (tavily, google, bing, duckduckgo, wikipedia)
                max_results: Maximum number of search results
                load_js: Whether to load JavaScript content
                use_playwright: Whether to use Playwright for loading
                use_selenium: Whether to use Selenium for loading
            """
            try:
                if any(
                    [
                        user_agent,
                        search_engine,
                        max_results,
                        load_js,
                        use_playwright,
                        use_selenium,
                    ]
                ):
                    self.web = Web(
                        user_agent=user_agent or self.web.user_agent,
                        search_engine=search_engine or self.web.search_engine,
                        max_results=max_results or self.web.max_results,
                        load_js=load_js if load_js is not None else self.web.load_js,
                        use_playwright=(
                            use_playwright
                            if use_playwright is not None
                            else self.web.use_playwright
                        ),
                        use_selenium=(
                            use_selenium
                            if use_selenium is not None
                            else self.web.use_selenium
                        ),
                    )
                return {
                    "success": True,
                    "configuration": {
                        "user_agent": self.web.user_agent,
                        "search_engine": self.web.search_engine,
                        "max_results": self.web.max_results,
                        "load_js": self.web.load_js,
                        "use_playwright": self.web.use_playwright,
                        "use_selenium": self.web.use_selenium,
                    },
                }
            except Exception as e:
                logging.error(f"Failed to configure web client: {str(e)}")
                return {"success": False, "error": str(e)}

    def run(self):
        try:
            logging.info("Starting Web MCP")
            self.mcp.run(transport="stdio")
        except KeyboardInterrupt:
            logging.info("Received shutdown signal. Gracefully shutting down...")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Fatal error occurred: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    try:
        server = WebMCP()
        server.run()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
