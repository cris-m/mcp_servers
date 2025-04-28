import argparse
import logging
import os
import sys
import traceback
from typing import Any, Dict

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from web import Web


class WebMCP:
    def __init__(
        self,
        search_engine: str,
        user_agent: str = None,
        max_results: int = 10,
        load_js: bool = False,
        use_playwright: bool = False,
        use_selenium: bool = False,
    ):
        self._setup_logging()

        self.user_agent = user_agent
        self.search_engine = search_engine
        self.max_results = max_results
        self.load_js = load_js
        self.use_playwright = use_playwright
        self.use_selenium = use_selenium

        self.mcp = FastMCP(name="Web MCP", version="1.0.0", request_timeout=360)
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
            user_agent=self.user_agent,
            search_engine=self.search_engine,
            max_results=self.max_results,
            load_js=self.load_js,
            use_playwright=self.use_playwright,
            use_selenium=self.use_selenium,
        )

    def _register_tools(self):
        logging.info("Registering tools")

        @self.mcp.tool("load_url")
        async def load_url(
            url_paths: list,
            recursive: bool = False,
            depth: int = 2,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Load content from URLs.

            Args:
                url_paths: List of URLs to load.
                recursive: Whether to perform recursive loading.
                depth: Maximum depth for recursive loading.
                ctx: MCP context object.

            Return:
                A dictionary containing the retrieved content for each URL.
            """
            try:
                if ctx:
                    ctx.info(f"Loading content from {len(url_paths)} URLs")
                    if recursive:
                        ctx.info(f"Recursive loading enabled with depth {depth}")
                    ctx.report_progress(0, 100)

                docs = await self.web.load_url(url_paths, recursive, depth)

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Successfully loaded {len(docs)} documents")

                # return {"success": True, "documents": docs}
                return {
                    "success": True,
                    "documents": [
                        {
                            "source": doc.metadata.get("source"),
                            "content": doc.page_content,
                        }
                        for doc in docs
                    ],
                }
            except Exception as e:
                error_msg = f"Failed to load URLs: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("load_sitemap")
        async def load_sitemap(sitemap_url: str, ctx: Context = None) -> Dict[str, Any]:
            """Load content from a sitemap.

            Args:
                sitemap_url: URL of the sitemap to load
                ctx: MCP context object.

            Return:
                A dictionary with the content for each URL extracted from the sitemap.
            """
            try:
                if ctx:
                    ctx.info(f"Loading sitemap from {sitemap_url}")
                    ctx.report_progress(0, 100)

                docs = await self.web.load_sitemap(sitemap_url)

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Successfully loaded {len(docs)} pages from sitemap")

                # return {"success": True, "documents": docs}
                return {
                    "success": True,
                    "documents": [
                        {
                            "source": doc.metadata.get("source"),
                            "content": doc.page_content,
                        }
                        for doc in docs
                    ],
                }
            except Exception as e:
                error_msg = f"Failed to load sitemap: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("search")
        async def search(
            query: str, max_results: int = None, ctx: Context = None
        ) -> Dict[str, Any]:
            """Search using the configured search engine.

            Args:
                query: Search query.
                max_results: Maximum number of results to return.
                ctx: MCP context object.

            Return:
                A dictionary containing the results of the search operation.
            """
            try:
                if ctx:
                    ctx.info(f"Searching for: {query}")
                    ctx.info(f"Using search engine: {self.web.search_engine}")
                    ctx.report_progress(0, 100)

                if max_results:
                    self.web.max_results = max_results
                    self.web._init_search()
                results = await self.web.search(query)

                if ctx:
                    ctx.report_progress(100, 100)
                    result_count = len(results) if isinstance(results, list) else 1
                    ctx.info(f"Search complete. Found {result_count} results")

                return {"success": True, "results": results}
            except Exception as e:
                error_msg = f"Failed to perform search: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("configure_web")
        def configure_web(
            user_agent: str = None,
            search_engine: str = None,
            max_results: int = None,
            load_js: bool = None,
            use_playwright: bool = None,
            use_selenium: bool = None,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Configure the web client settings.

            Parameters:
                user_agent: A custom user agent string to use.
                search_engine: The search engine to employ (e.g., tavily, google, bing, duckduckgo, wikipedia).
                max_results: The maximum number of search results to return.
                load_js: A flag indicating whether to load JavaScript content.
                use_playwright: A flag specifying whether to use Playwright for loading.
                use_selenium: A flag specifying whether to use Selenium for loading.
                ctx: The MCP context object.

            Return:
                A dictionary containing the updated configuration.
            """
            try:

                if ctx:
                    ctx.info("Configuring web client settings")
                    ctx.report_progress(0, 100)

                settings_changed = []

                if user_agent is not None:
                    self.web.user_agent = user_agent
                    os.environ["USER_AGENT"] = user_agent
                    settings_changed.append(f"User agent: {user_agent}")

                if search_engine is not None:
                    self.web.search_engine = search_engine
                    self.web._init_search()
                    settings_changed.append(f"Search engine: {search_engine}")

                if max_results is not None:
                    self.web.max_results = max_results
                    settings_changed.append(f"Max results: {max_results}")

                if load_js is not None:
                    self.web.load_js = load_js
                    settings_changed.append(f"Load JS: {load_js}")

                if use_playwright is not None:
                    self.web.use_playwright = use_playwright
                    settings_changed.append(f"Use Playwright: {use_playwright}")

                if use_selenium is not None:
                    self.web.use_selenium = use_selenium
                    settings_changed.append(f"Use Selenium: {use_selenium}")

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Settings updated: {', '.join(settings_changed)}")

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
                error_msg = f"Failed to configure web client: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

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


def str_to_bool(value):
    return str(value).lower() in ("true", "1", "yes")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Web MCP Server")
    parser.add_argument(
        "--user-agent",
        default=os.getenv("USER_AGENT", "Mozilla/5.0 ..."),
        help="User agent string",
    )
    parser.add_argument(
        "--search-engine",
        default=os.getenv("SEARCH_ENGINE", "tavily"),
        help="Search engine name",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=int(os.getenv("MAX_RESULTS", "20")),
        help="Maximum number of results",
    )

    # Boolean flags
    default_load_js = str_to_bool(os.getenv("LOAD_JS", "false"))
    parser.add_argument(
        "--load-js",
        action="store_true",
        default=default_load_js,
        help="Enable JavaScript loading",
    )

    default_use_playwright = str_to_bool(os.getenv("USE_PLAYWRIGHT", "true"))
    parser.add_argument(
        "--use-playwright",
        action="store_true",
        default=default_use_playwright,
        help="Enable Playwright usage",
    )

    default_use_selenium = str_to_bool(os.getenv("USE_SELENIUM", "false"))
    parser.add_argument(
        "--use-selenium",
        action="store_true",
        default=default_use_selenium,
        help="Enable Selenium usage",
    )

    args = parser.parse_args()

    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument("--user-agent", type=str, help="User agent string")
    parser.add_argument(
        "--search-engine",
        type=str,
        help="Search engine (required or set SEARCH_ENGINE)",
    )
    parser.add_argument("--max-results", type=int, help="Maximum number of results")

    parser.add_argument(
        "--load-js", action="store_true", help="Enable JavaScript loading"
    )
    parser.add_argument(
        "--use-playwright", action="store_true", help="Enable Playwright usage"
    )
    parser.add_argument(
        "--use-selenium", action="store_true", help="Enable Selenium usage"
    )

    args = parser.parse_args()

    # Pull from env if CLI arg not provided
    user_agent = args.user_agent or os.getenv("USER_AGENT", "Mozilla/5.0 ...")
    search_engine = args.search_engine or os.getenv("SEARCH_ENGINE")
    max_results = args.max_results or int(os.getenv("MAX_RESULTS", "10"))
    load_js = args.load_js or str_to_bool(os.getenv("LOAD_JS", "false"))
    use_playwright = args.use_playwright or str_to_bool(
        os.getenv("USE_PLAYWRIGHT", "true")
    )
    use_selenium = args.use_selenium or str_to_bool(os.getenv("USE_SELENIUM", "false"))

    # Required value check
    if not search_engine:
        logging.error(
            "Missing search engine (use --search-engine or set SEARCH_ENGINE)."
        )
        print(
            "ERROR: Search engine is required (--search-engine or SEARCH_ENGINE).",
            file=sys.stderr,
        )
        sys.exit(1)

    server = WebMCP(
        user_agent=user_agent,
        search_engine=search_engine,
        max_results=max_results,
        load_js=load_js,
        use_playwright=use_playwright,
        use_selenium=use_selenium,
    )
    server.run()


if __name__ == "__main__":
    try:
        logging.info("Initializing Web MCP server")
        main()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
