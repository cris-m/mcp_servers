# Web MCP

A Model Context Protocol (MCP) server for web operations that provides a secure and controlled way for AI assistants to interact with web content, search engines, and URLs.

## Overview

Web MCP is built on the [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) and provides tools for:

- Searching the web using various search engines
- Loading content from URLs
- Extracting content from sitemaps
- Configuring web client settings and behavior

The server includes support for multiple search engines and browser automation tools to enhance web content retrieval.

## Features

- **Multiple Search Engines**: Support for Tavily, Google, Bing, DuckDuckGo, and Wikipedia
- **URL Content Loading**: Retrieve content from single or multiple URLs
- **Sitemap Extraction**: Parse and load content from website sitemaps
- **Configurable Settings**: Adjust user agent, search parameters, and browser automation
- **JavaScript Support**: Option to load JavaScript-rendered content
- **Browser Automation**: Support for Playwright and Selenium for advanced content retrieval
- **Progress Tracking**: Support for progress reporting during long-running operations

## Installation

1. Clone this repository
2. Create a Python virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install fastmcp python-dotenv requests beautifulsoup4 playwright selenium google-search-results langchain-tavily
   ```
4. Install Playwright browsers:
   ```bash
   python -m playwright install
   ```

## Setting Up Search API Keys

The Web MCP server requires API keys for the search engines you want to use. Here's how to set up the most common ones:

### Tavily API Key

1. Visit [Tavily AI](https://tavily.com/) and sign up for an account
2. Navigate to your dashboard to obtain your API key
3. Set the environment variable:
   ```bash
   export TAVILY_API_KEY=your_api_key_here
   ```

### Google Custom Search Engine

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project and enable the Custom Search API
3. Create API credentials to get your API key
4. Go to the [Programmable Search Engine](https://programmablesearchengine.google.com/) site
5. Create a new search engine and get your Search Engine ID
6. Set the environment variables:
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   export GOOGLE_CSE_ID=your_search_engine_id_here
   ```

### Bing Search API

1. Go to the [Microsoft Azure Portal](https://portal.azure.com/)
2. Create a Bing Search resource
3. Obtain your API key and endpoint URL from the resource overview
4. Set the environment variables:
   ```bash
   export BING_SUBSCRIPTION_KEY=your_api_key_here
   export BING_SEARCH_URL=your_endpoint_url_here
   ```

## Configuration

The server can be configured in several ways:

### Command Line Arguments

```bash
python server.py --search-engine tavily --max-results 20 --user-agent "Mozilla/5.0..." --use-playwright
```

### Environment Variables

```bash
export SEARCH_ENGINE=tavily
export MAX_RESULTS=20
export USER_AGENT="Mozilla/5.0..."
export USE_PLAYWRIGHT=true
python server.py
```

### MCP Configuration File (mcp.json)

```json
{
  "mcpServers": {
    "web-mcp": {
      "command": "path/to/python",
      "args": [
        "path/to/server.py",
        "--search-engine",
        "tavily",
        "--max-results",
        "20",
        // "--load-js",
		// "--use-playwright",
		// "--use-selenium"
      ],
      "env": {
         // "TAVILY_API_KEY": "your_api_key_here",
         "USER_AGENT": "Mozilla/5.0...",
         // "SEARCH_ENGINE": "tavily",
         // "MAX_RESULTS": "20",
         // "LOAD_JS": "true",
         // "USE_PLAYWRIGHT": "true"
      }
    }
  }
}
```

**Note about configuration:**
- The `--search-engine` or `SEARCH_ENGINE` parameter is required
- Depending on which search engine you choose, you'll need to set the appropriate API key environment variables

## Security Features

The Web MCP implements security measures:

- Configurable user agent to control browser identification
- Options to use Playwright or Selenium for secure browser automation
- Progress reporting for transparency during operations
- Error handling with detailed logging

## Available Tools

| Tool | Description |
|------|-------------|
| `search` | Searches the web using the configured search engine |
| `load_url` | Loads content from one or more URLs with optional recursive loading |
| `load_sitemap` | Extracts and loads content from a website's sitemap |
| `configure_web` | Configures web client settings (search engine, user agent, etc.) |

## Example Usage

When connected to an AI assistant, you can use commands like:

```
Search for recent news about artificial intelligence
```

```
Load the content from https://example.com
```

```
Extract information from the sitemap at https://example.com/sitemap.xml
```

```
Configure the web client to use Google search with 10 max results
```

## Browser Automation Options

The Web MCP server supports multiple approaches for loading web content:

- **Basic HTTP requests**: Default for simple content retrieval
- **Playwright**: Recommended for JavaScript-heavy websites (enable with `--use-playwright`)
- **Selenium**: Alternative browser automation option (enable with `--use-selenium`)

You can also enable JavaScript processing with the `--load-js` flag, which works in conjunction with browser automation.

## Customization

You can customize the server by modifying:

- The Web implementation in `web.py`
- Default search engines and parameters
- Browser automation behavior
- Error handling and logging

## Troubleshooting

If you encounter errors:

1. Check that the required API keys are correctly set as environment variables
2. Verify that the search engine parameter is correctly specified
3. Look for error messages in the server output (redirected to stderr)
4. For Playwright or Selenium issues, ensure the browser dependencies are correctly installed

## Contributing

Contributions are welcome! Please follow the standard GitHub workflow:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with your changes

## Running with Inspector

You can run the server using the MCP Inspector tool:

```bash
mcp dev server.py:main
```

When configuring in the Inspector, use these settings:

- Transport Type: STUDIO
- Command: python
- Arguments: server.py --search-engine tavily --max-results 20

*Note: This server provides access to web content and search functionality. Use appropriate API keys and configure search engines according to your use case.*