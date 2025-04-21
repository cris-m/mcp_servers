# Gmail MCP

A Model Context Protocol (MCP) server for Gmail operations that provides a secure and controlled way for AI assistants to interact with your Gmail account.

---

## Overview

Gmail MCP is built on the [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) and provides tools for:

- Sending emails with attachments and HTML content
- Listing and searching emails with filtering options
- Managing emails (marking as read, deleting)
- Working with unread emails

The server includes robust authentication and provides a seamless interface between AI assistants and Gmail.

---

## Features

- **Email Management**: Send, list, search, and delete emails
- **Authentication**: Secure Gmail API access using OAuth credentials
- **Filtering Options**: Search emails by query, labels, or read status
- **Attachment Support**: Include file attachments in outgoing emails
- **HTML Content**: Support for rich HTML email formatting
- **Progress Tracking**: Support for progress reporting during operations

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
   pip install "mcp[cli] uv dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib"
   ```
I'll add detailed instructions for creating Gmail API credentials and setting up the necessary scopes. Here's the additional section for your README:

---

## Setting Up Gmail API Credentials

### Creating a Google Cloud Project and Obtaining Credentials

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Click on "Select a project" at the top of the page, then click "New Project"
   - Enter a name for your project and click "Create"

2. **Enable the Required APIs**:
   - In your new project, navigate to "APIs & Services" > "Library"
   - Search for and enable the following APIs:
     - Gmail API
     - Google Drive API (needed for attachment handling)

3. **Configure the OAuth Consent Screen**:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type (or "Internal" if you're using Google Workspace)
   - Fill in the required fields:
     - App name: "Gmail MCP"
     - User support email: Your email address
     - Developer contact information: Your email address
   - Click "Save and Continue"

4. **Add Scopes**:
   - On the "Scopes" step, click "Add or Remove Scopes"
   - Add the following scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     https://www.googleapis.com/auth/gmail.compose
     https://www.googleapis.com/auth/gmail.send
     https://www.googleapis.com/auth/drive.file
     ```
   - Click "Save and Continue" and complete the remaining steps

5. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Gmail MCP Client"
   - Click "Create"
   - Download the JSON file by clicking the download icon
   - Save this file as `credentials.json` in a secure location

6. **Add Test Users**:
   - If your app is in "External" mode and not verified, you'll need to add test users
   - Go back to "OAuth consent screen"
   - Scroll down to "Test users" and click "Add Users"
   - Add the email address(es) that will be used with the Gmail MCP
   - Note: Only these email addresses will be able to authenticate with your application until you verify your app

### First-Time Authentication

The first time you run the Gmail MCP server, it will:

1. Detect that no token file exists at the specified `--gmail-token` path
2. Open a browser window asking you to sign in with your Google account
3. Display permissions being requested and ask for your consent
4. After you approve, create a token file at the specified location

For subsequent runs, this token will be used automatically unless it expires or is revoked, in which case the authentication flow will be triggered again.

### Security Considerations

- Store your `credentials.json` and token files in a secure location
- Do not commit these files to version control
- If working in a team environment, use environment variables rather than hardcoded paths
- Consider implementing token refresh handling for long-running applications

---

## Configuration

The server can be configured in several ways:

### Command Line Arguments

```bash
python server.py --gmail-credentials /path/to/credentials.json --gmail-token /path/to/token.pickle
```

### Environment Variables

```bash
export GMAIL_CREDENTIALS_PATH="/path/to/credentials.json"
export GMAIL_TOKEN_PATH="/path/to/token.pickle"
python server.py
```

### MCP Configuration File (mcp.json)

```json
{
  "mcpServers": {
    "gmail-mcp": {
      "command": "path/to/python",
      "args": [
        "path/to/server.py",
        "--gmail-credentials",
        "/path/to/credentials.json",
        "--gmail-token",
        "/path/to/token.pickle"
      ],
      "env": {
      //   "GMAIL_CREDENTIALS_PATH": "/path/to/credentials.json",
      //   "GMAIL_TOKEN_PATH": "/path/to/token.pickle"
      }
    }
  }
}
```

**Note about authentication:**
- The `--gmail-credentials` or `GMAIL_CREDENTIALS_PATH` must point to your Google API credentials JSON file obtained from the Google Cloud Console
- The `--gmail-token` or `GMAIL_TOKEN_PATH` specifies where the authentication token will be saved after the initial OAuth flow completes
- If the token file doesn't exist, the application will initiate the OAuth authentication flow and save the resulting token to the specified location
- For subsequent runs, the existing token will be used for authentication if valid, or refreshed if expired

---

## Security Features

The Gmail MCP implements security measures:

- Secure OAuth authentication for Gmail API access
- Token management for maintaining authenticated sessions
- Progress reporting for transparency during operations
- Error handling with detailed logging

---

## Available Tools

| Tool | Description |
|------|-------------|
| `send_email` | Sends an email with optional CC, BCC, attachments, and HTML content |
| `list_emails` | Lists emails with customizable filters and limits |
| `search_emails` | Searches for emails matching specific criteria |
| `get_unread_emails` | Retrieves unread emails from the inbox |
| `mark_as_read` | Marks a specific email as read |
| `delete_email` | Deletes or moves an email to trash |
| `batch_delete_emails` | Deletes multiple emails in a single operation |

---

## Example Usage

When connected to an AI assistant, you can use commands like:

```
Send an email to john@example.com with the subject "Meeting Reminder"
```

```
List my 10 most recent unread emails
```

```
Search for emails containing "project report" from last week
```

```
Delete the email with ID 12345
```

---

## Customization

You can customize the server by modifying:

- The Gmail manager implementation in `gmail.py`
- Additional Gmail API functionality
- Error handling and logging behavior

---

## Troubleshooting

If you encounter errors:

1. Check that Gmail API credentials are valid and have the necessary permissions
2. Verify that the token file has been properly generated
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
- Command: python
- Arguments: server.py --gmail-credentials /path/to/credentials.json --gmail-token /path/to/token.json

*Note: This server provides access to your Gmail account and should be configured carefully to avoid exposing sensitive email data.*