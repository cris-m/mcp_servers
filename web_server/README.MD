# Web

A versatile web server that provides comprehensive tools for web crawling, searching, and content loading through multiple search engines.

## Features

- Web searching with support for:
  - Multiple search engines (Tavily, Google, Bing, DuckDuckGo)
  - Configurable result limits
  - Advanced search parameters
- Content loading capabilities:
  - Single and multiple URL loading
  - Sitemap parsing
  - Recursive crawling
  - JavaScript rendering support
- Browser automation options:
  - Playwright integration
  - Selenium support
  - Configurable user agents

## Setup

1. Set up API credentials:
   - Tavily API: Register at [Tavily](https://tavily.io/)
   - Google Custom Search: Configure at [Google Cloud Console](https://console.cloud.google.com/)
   - Bing Search: Get API key from [Bing Web Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)

2. Configure environment:
   - Create `.env` file in the web_server directory
   - Add your API keys and default settings
   - Install required packages

## Usage Examples

### Starting the Server
```python
from web_server.web import Web

web_client = Web(
    search_engine="tavily",
    max_results=10,
    load_js=False,
    use_playwright=True
)
web_client.run()
```

### Performing Web Searches
```python
# Basic search
results = await web_client.search(
    query="python programming",
    max_results=5
)

# Advanced search with specific engine
results = await web_client.search(
    query="machine learning tutorials",
    search_engine="google",
    max_results=10
)
```

### Loading Content
```python
# Load single URL
content = await web_client.load_url(
    url_paths=["https://example.com"]
)

# Load multiple URLs recursively
content = await web_client.load_url(
    url_paths=["https://example.com"],
    recursive=True,
    depth=2
)

# Load sitemap
content = await web_client.load_sitemap(
    "https://example.com/sitemap.xml"
)
```

### Configuration Examples
```python
# Configure web client
web_client.configure_web(
    user_agent="Custom User Agent",
    search_engine="tavily",
    max_results=15,
    load_js=True,
    use_playwright=True
)
```

## Required Environment Variables
```bash
# API Keys
TAVILY_API_KEY=your_tavily_key
GOOGLE_API_KEY=your_google_key
GOOGLE_CSE_ID=your_cse_id
BING_SUBSCRIPTION_KEY=your_bing_key

# Default Settings
DEFAULT_SEARCH_ENGINE=tavily
DEFAULT_MAX_RESULTS=10
DEFAULT_USER_AGENT=Mozilla/5.0
DEFAULT_LOAD_JS=false
DEFAULT_USE_PLAYWRIGHT=true
DEFAULT_USE_SELENIUM=false
```

## Installation

```bash
# Install required packages
pip install fastmcp python-dotenv requests beautifulsoup4 playwright selenium google-search-results langchain-tavily

# Install Playwright browsers
python -m playwright install
```

## Security Notes
- Store API keys securely in `.env`
- Never commit sensitive credentials
- Implement rate limiting for production use
- Keep dependencies updated
