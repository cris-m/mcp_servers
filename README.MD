# Model Context Protocol (MCP) Servers

A collection of Model Context Protocol (MCP) servers that extend AI assistants with secure and controlled access to external systems and data sources.

## Overview

This repository contains multiple MCP servers built on the [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) framework. Each server provides tools for AI assistants to interact with different types of systems:

- **File MCP**: Access and manipulate files on your local file system
- **Gmail MCP**: Interact with Gmail for email management
- **Web MCP**: Search the web and access online content

These servers can be integrated with AI applications that support the MCP standard, such as Cursor, Claude Desktop, and other MCP-compatible assistants.

## Features

- **AI Integration**: Extend your AI assistants with powerful file, email, and web capabilities
- **Modular Architecture**: Use the servers independently or combine them based on your needs
- **Secure Access**: Controlled access to sensitive systems with robust security features
- **Rich Functionality**: Comprehensive tools for each system domain
- **Progress Tracking**: Real-time progress reporting for long-running operations
- **Consistent Interface**: Uniform API design across all servers

## Installation

1. Clone this repository
2. Create a Python virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install the common dependencies:
   ```bash
   pip install -r requirements.txt
   python -m playwright install
   ```

## Server Configuration

Each server requires specific configuration. Here's a quick summary:

### File MCP

Requires root folder paths to define which directories the AI can access:
```bash
export MCP_ROOT_FOLDERS="/path/to/folder1;/path/to/folder2"
```

### Gmail MCP

Requires Google API credentials and token storage:
```bash
export GMAIL_CREDENTIALS_PATH="/path/to/credentials.json"
export GMAIL_TOKEN_PATH="/path/to/token.pickle"
```

### Web MCP

Requires search engine configuration, API keys, and browser automation settings:

```bash
# Search Engine API Keys
export TAVILY_API_KEY="your_tavily_api_key"
export GOOGLE_API_KEY="your_google_api_key" 
export GOOGLE_CSE_ID="your_custom_search_engine_id"
export BING_SUBSCRIPTION_KEY="your_bing_api_key"
export BING_SEARCH_URL="your_bing_endpoint_url"

# Search Configuration
export SEARCH_ENGINE="tavily"
export MAX_RESULTS="20"

# Browser Automation Settings
export LOAD_JS="true"
export USE_PLAYWRIGHT="true"  # Enable Playwright for browser automation
export USE_SELENIUM="false"   # Or use Selenium instead of Playwright
```

## Integration with AI Applications

These MCP servers can be integrated with various AI applications that support the Model Context Protocol:

### Unified MCP Configuration

Create an `mcp_config.json` file with your configuration to use with MCP-compatible applications:

```json
{
  "mcpServers": {
    "file-mcp": {
      "command": "python",
      "args": [
        "file_server.py",
        "--roots",
        "/path/to/folder1",
        "/path/to/folder2"
      ]
    },
    "gmail-mcp": {
      "command": "python",
      "args": [
        "gmail_server.py",
        "--gmail-credentials",
        "/path/to/credentials.json",
        "--gmail-token",
        "/path/to/token.pickle"
      ]
    },
    "web-mcp": {
      "command": "python",
      "args": [
        "web_server.py",
        "--search-engine",
        "google",
        "--max-results",
        "20",
        "--load-js",
        "--use-playwright"
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

### Adding to AI Applications

- **Claude Desktop**: In settings, add your MCP servers through the MCP configuration section
- **Cursor**: Configure MCP servers in the application settings
- **Custom Applications**: Use the MCP SDK to connect to these servers programmatically

## Available Tools by Server

### File MCP
- `list_files`: Lists files in a directory
- `read_file`: Reads file content
- `get_file_info`: Gets file metadata
- `get_file_mimetype`: Determines file MIME type
- `search_files_by_name`: Searches files by name pattern
- `search_files_by_content`: Searches files by content

### Gmail MCP
- `send_email`: Sends emails with attachments
- `list_emails`: Lists emails with filtering
- `search_emails`: Searches for specific emails
- `get_unread_emails`: Gets unread emails
- `mark_as_read`: Marks emails as read
- `delete_email`: Deletes specific emails
- `batch_delete_emails`: Deletes multiple emails

### Web MCP
- `search`: Searches the web using configured engine
- `load_url`: Loads content from URLs
- `load_sitemap`: Extracts content from sitemaps
- `configure_web`: Configures web client settings

## Example AI Interactions

When connected to an AI assistant with all servers, you can use natural language commands like:

```
"Find all documents in my Downloads folder related to budget planning"
```

```
"Check my unread emails and summarize the most important ones"
```

```
"Search for the latest research on renewable energy and save key findings to a file"
```

```
"Draft an email to my team with the quarterly report from my Documents folder attached"
```

## Security Considerations

When integrating these MCP servers with AI applications:

- Use separate user accounts for different contexts/applications
- Restrict file access to specific directories
- Manage API keys securely using environment variables
- Avoid exposing sensitive Gmail credentials in multi-user environments
- Consider network security for web access functionality
- Review permissions regularly as AI capabilities evolve

## Troubleshooting

If you encounter issues with AI integration:

1. Verify the MCP servers are running correctly
2. Check that your AI application supports MCP integration
3. Ensure the MCP configuration file uses correct paths for your system
4. Confirm all required environment variables and credentials are set
5. Check for firewall or network issues that might block connections

## Contributing

Contributions to any of the MCP servers are welcome! Please follow the standard GitHub workflow and submit pull requests to the appropriate server repository.

## License

This collection of MCP servers is released under the MIT License. See individual server repositories for specific license details.