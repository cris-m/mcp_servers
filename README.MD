# Model Context Protocol (MCP) Servers

A collection of Model Context Protocol (MCP) servers designed to extend AI assistants with secure and controlled access to external systems and data sources.

## Overview

This repository hosts several MCP servers built on the [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) framework. Each server enables AI assistants to interact with various external systems:

- **File MCP**: Access and manipulate files on the local file system  
- **Google MCP**: Manage and interact with Google services (Gmail, Drive, Calendar)  
- **Web MCP**: Search the internet and retrieve online content  
- **Voice MCP**: Generate lifelike text-to-speech audio using advanced voice synthesis

These servers are compatible with MCP-enabled AI tools such as Cursor, Claude Desktop, and other assistants that support the protocol.

## Features

- **AI Integration**: Seamlessly extend AI assistants with file, Google services, web, and voice capabilities  
- **Modular Architecture**: Deploy servers independently or in combination  
- **Secure Access**: Built-in security controls to safeguard sensitive systems  
- **Rich Functionality**: Comprehensive toolsets tailored to each domain  
- **Progress Reporting**: Real-time updates for long-running tasks  
- **Consistent Interface**: Unified API design for ease of integration

## Installation

1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m playwright install
   ```

## Server Configuration

Each server has its own configuration requirements:

### Voice MCP

Powered by Kokoro TTS with multilingual, multi-voice capabilities.

**System Dependencies**  
- **Linux**:  
  ```bash
  sudo apt-get install espeak-ng
  ```  
- **Windows/macOS**: Install `espeak-ng` via your preferred package manager.

Install Python dependencies:
```bash
pip install mcp[cli] uv dotenv kokoro>=0.9.2 soundfile sounddevice
pip install misaki[zh,ja]  # for Japanese and Chinese support
```

Set environment variables:
```bash
export VOICE_LANG=us
export VOICE_NAME=af_nicole
export VOICE_SAMPLE_RATE=24000
```

### File MCP

Define root folders accessible by the assistant:
```bash
export MCP_ROOT_FOLDERS="/path/to/folder1;/path/to/folder2"
```

### Google MCP

Requires Google API credentials and token:
```bash
export GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
export GOOGLE_TOKEN_PATH="/path/to/token.pickle"
export ENABLE_GMAIL="true"
export ENABLE_DRIVE="true"
export ENABLE_CALENDAR="true"
```

### Web MCP

Configure search engines and browser automation settings:

```bash
# Search Engine API Keys
export TAVILY_API_KEY="your_tavily_api_key"
export GOOGLE_API_KEY="your_google_api_key" 
export GOOGLE_CSE_ID="your_custom_search_engine_id"
export BING_SUBSCRIPTION_KEY="your_bing_api_key"
export BING_SEARCH_URL="your_bing_endpoint_url"

# Search Settings
export SEARCH_ENGINE="tavily"
export MAX_RESULTS="20"

# Browser Automation
export LOAD_JS="true"
export USE_PLAYWRIGHT="true"
export USE_SELENIUM="false"
```

## Integration with AI Applications

These servers can be integrated into any MCP-compatible AI environment.

### Unified MCP Configuration

Create an `mcp_config.json` file with your server configurations:

```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "python",
      "args": [
        "voice_server.py",
        "--lang", "us",
        "--voice", "af_nicole",
        "--sample-rate", "24000"
      ],
      "env": {
        // "VOICE_LANG": "us",
        // "VOICE_NAME": "af_nicole",
        // "VOICE_SAMPLE_RATE": "24000"
      }
    },
    "file-mcp": {
      "command": "python",
      "args": [
        "file_server.py",
        "--roots",
        "/path/to/folder1",
        "/path/to/folder2"
      ]
    },
    "google-mcp": {
      "command": "python",
      "args": [
        "server.py",
        "--gmail",
        "--drive",
        "--calendar",
        "--credentials",
        "/path/to/credentials.json",
        "--token",
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

### Integration Instructions

- **Claude Desktop**: Add MCP configurations via the app settings  
- **Cursor**: Configure MCP servers through the built-in settings UI  
- **Custom Applications**: Use the [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) for integration

## Available Tools by Server

### Voice MCP
- `play_audio`: Convert text to speech and play it in-memory

### File MCP
- `list_files`: Browse directory contents  
- `read_file`: Read content of files  
- `get_file_info`: Access file metadata  
- `get_file_mimetype`: Detect MIME types  
- `search_files_by_name`: Search by filename  
- `search_files_by_content`: Search by file content

### Google MCP
- **Gmail**:
  - `send_email`: Send messages with attachments  
  - `create_draft_email`: Prepare drafts for later use
  - `list_emails`: View inbox or folders  
  - `search_emails`: Find specific emails  
  - `get_unread_emails`: Check unread messages  
  - `mark_as_read`/`mark_as_unread`: Manage message status  
  - `delete_email`: Remove specific emails  
  - `batch_delete_emails`: Bulk delete emails  
  - `get_labels`: Retrieve available labels

- **Drive**:
  - `list_drive_files`: Browse files and folders
  - `search_drive_files`: Find content in Drive
  - `upload_file`: Add new files to Drive
  - `download_file`: Save Drive files locally
  - `create_folder`: Organize content in folders
  - `get_file_permissions`: Check sharing settings
  - `share_file`: Control access to files
  - `get_drive_storage_info`: Check quota usage

- **Calendar**:
  - `create_meeting`: Schedule new events
  - `update_meeting`: Modify existing events
  - `get_meetings_by_date`: View day's schedule
  - `get_available_time_slots`: Find free time
  - `invite_to_meeting`: Add attendees
  - `delete_meeting`: Remove events
  - `create_bulk_meetings`: Schedule multiple events

### Web MCP
- `search`: Perform search queries  
- `load_url`: Fetch content from a URL  
- `load_sitemap`: Extract URLs from sitemaps  
- `configure_web`: Update client settings

## Example AI Interactions

With all MCP servers active, assistants can execute natural-language commands like:

```
"Play a poem about autumn in a French accent"
```

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
"Schedule a team meeting for tomorrow at 2pm and send calendar invites to my marketing team"
```

```
"Upload the quarterly report to my Google Drive and share it with the finance department"
```

## Security Considerations

To ensure secure deployment:

- Use unique accounts per application or context  
- Restrict file access to specific directories  
- Manage API keys securely using environment variables  
- Avoid hardcoding Google credentials in multi-user environments  
- Secure web traffic and endpoints as needed  
- Regularly audit permissions and access control settings

## Troubleshooting

If you encounter issues:

1. Ensure the MCP server processes are running  
2. Confirm your AI assistant supports MCP integration  
3. Validate the `mcp_config.json` paths and options  
4. Double-check environment variables and credentials  
5. Investigate any local firewall or network rules

## Contributing

Contributions are welcome! Please submit pull requests to the relevant MCP server directory, following standard GitHub collaboration practices.

## License

This project is released under the MIT License. Refer to individual server directories for any specific licensing details.