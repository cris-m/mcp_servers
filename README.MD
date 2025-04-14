# MCP Server Collection

A collection of MCP (Message Control Protocol) servers for Gmail management and web searching capabilities.

## Available Servers

### 1. Gmail MCP Server
Provides comprehensive email management through Gmail API.

#### Key Features
- Email Operations:
  - Send emails with attachments
  - Read and search emails
  - Manage email status (read/unread)
  - Batch operations support
- Drive Integration for large attachments

### 2. Web MCP Server
Implements multi-engine web searching and content loading capabilities.

#### Key Features
- Multiple Search Engines:
  - Tavily Search
  - Google Custom Search
  - Bing Search
  - DuckDuckGo (fallback)
- Content Loading:
  - URL content extraction
  - Sitemap parsing
  - Recursive crawling
- Browser Automation:
  - Playwright support
  - Selenium integration

## Configuration

### Environment Files (.env)


#### Web Server (.env)
```bash
# Search Engine API Keys
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

### MCP Configuration (mcp.json)

### MCP Server Configuration

#### Gmail MCP Server Configuration
```json
{
    "mcpServers": {
        "gmail-mcp": {
            "command": "path/to/python",
            "args": ["path/to/gmail_server.py"],
            "env": {
                "CREDENTIALS_FILE": "path/to/client_secret.json",
                "TOKEN_FILE": "path/to/token.pickle"
            },
        }
    }
}
```

#### Web MCP Server Configuration
```json
{
    "mcpServers": {
        "web-mcp": {
            "command": "path/to/python",
            "args": ["path/to/web_server.py"],
            "env": {
                "TAVILY_API_KEY": "your_tavily_key",
                "GOOGLE_API_KEY": "your_google_key",
                "GOOGLE_CSE_ID": "your_cse_id",
                "BING_SUBSCRIPTION_KEY": "your_bing_key",
                "DEFAULT_SEARCH_ENGINE": "tavily",
                "DEFAULT_MAX_RESULTS": "10",
                "DEFAULT_USER_AGENT": "Mozilla/5.0",
                "DEFAULT_LOAD_JS": "false",
                "DEFAULT_USE_PLAYWRIGHT": "true",
                "DEFAULT_USE_SELENIUM": "false"
            },
            "envFile": "path/to/.env"
        }
    }
}
```

## Installation

1. Create Python virtual environment:
```bash
python -m venv env
source env/bin/activate  # Unix
.\env\Scripts\activate   # Windows
```

2. Install required packages:
```bash
# Install requirements for Gmail Server
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install
```

## Security Notes

- Store all sensitive credentials in `.env` files
- Keep `.env` files out of version control
- Implement rate limiting for production use
- Regularly update dependencies
- Monitor API usage and quotas

## Error Handling

Both servers implement comprehensive error handling:
- Detailed logging
- Error response formatting
- Graceful shutdown handling
- Exception tracking

## Logging

Logging is configured for both servers with:
- Standard output streaming
- Timestamp information
- Log levels (INFO, ERROR)
- Exception tracebacks