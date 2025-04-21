# File Server MCP

A Model Context Protocol (MCP) server for file system operations that provides a secure and controlled way for AI assistants to interact with your local file system.

---

## Overview

File Server MCP is built on the [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) and provides tools for:

- Listing files in directories
- Reading file contents
- Getting file information and MIME types
- Searching files by name or content

The server includes robust security features to prevent unauthorized access to sensitive files and directories.

---

## Features

- **Multiple Root Folders**: Configure one or more root folders that the AI assistant can access
- **Security Restrictions**: Built-in protection for sensitive system directories
- **Flexible Search**: Search files by name patterns or content (with regex support)
- **Resource Access**: Expose file contents and directory listings as MCP resources
- **Progress Tracking**: Support for progress reporting during long-running operations

---

## Installation

1. Clone this repository
2. Create a Python virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install "mcp[cli] uv markitdown[pdf, docx, pptx, xlsx, xls]"
   ```

---

## Configuration

The server can be configured in several ways:

### Command Line Arguments

```bash
python server.py --roots /path/to/folder1 /path/to/folder2
```

### Environment Variables

```bash
export MCP_ROOT_FOLDERS="/path/to/folder1;/path/to/folder2"
python server.py
```

### MCP Configuration File (mcp.json)

```json
{
  "mcpServers": {
    "file-mcp": {
      "command": "path/to/python",
      "args": [
        "path/to/server.py",
        "--roots",
        "C:\\Path\\To\\Folder1",
        "C:\\Path\\To\\Folder2"
      ],
      "env": {
        // "MCP_ROOT_FOLDERS": "C:\\Path\\To\\Folder3;C:\\Path\\To\\Folder4"
      }
    }
  }
}
```
---

## Security Features

The File Server MCP includes several security measures:

- Root folder validation to prevent access outside defined boundaries
- Default restrictions for sensitive system directories (e.g., /etc, C:\Windows)
- Filtering for common sensitive file patterns (config files, credentials, etc.)
- Size limits for file content searches to prevent processing extremely large files
- Binary file detection to avoid processing non-text files

---

## Available Tools

| Tool | Description |
|------|-------------|
| `list_files` | Lists files in a directory with customizable depth |
| `read_file` | Reads and returns the content of a file |
| `get_file_info` | Returns metadata about a file (size, creation date, etc.) |
| `get_file_mimetype` | Determines the MIME type of a file |
| `search_files_by_name` | Searches for files matching a name pattern |
| `search_files_by_content` | Searches for files containing specific text or matching a regex pattern |

---

## Example Usage

When connected to an AI assistant, you can use commands like:

```
List all files in my Documents folder
```

```
Search for files containing the word "important"
```

```
Read the content of C:\Users\username\Documents\notes.txt
```

---

## Customization

You can customize the server by modifying:

- Default ignore patterns for certain file types
- Additional restricted directories or files
- Search depth limits

---

## Troubleshooting

If you encounter errors:

1. Check that specified root folders exist and are accessible
2. Verify that the Python environment has the necessary permissions
3. Look for error messages in the server output (redirected to stderr)
4. Ensure the MCP configuration file has the correct format and paths

---

## Contributing

Contributions are welcome! Please follow the standard GitHub workflow:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with your changes

---

## Running with Inspector

You can run the server using the MCP Inspector tool:

```bash
mcp dev server.py:main
```

When configuring in the Inspector, use these settings:

- Transport Type: STUDIO
- Command: uv
- Arguments: run server.py --root [path/to/folder1] [path/to/folder2]

*Note: This server is meant for secure local file access and should be configured carefully to avoid exposing sensitive data.*