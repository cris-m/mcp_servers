# Google MCP

A Model Context Protocol (MCP) server for Google service operations that provides a secure and controlled way for AI assistants to interact with your Google account.

---

## Overview

Google MCP is built on the [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) and provides tools for accessing multiple Google services:

- **Gmail**: Send emails, create drafts, list/search messages, and manage email status
- **Google Drive**: Manage files, folders, permissions, and storage information
- **Google Calendar**: Create and manage meetings, check availability, and handle event invitations

The server includes robust authentication and provides a seamless interface between AI assistants and Google services.

---

## Features

### Gmail
- **Email Management**: Send, list, search, draft, and delete emails
- **Filtering Options**: Search emails by query, labels, or read status
- **Attachment Support**: Include file attachments in outgoing emails
- **HTML Content**: Support for rich HTML email formatting
- **Message Organization**: Mark messages as read/unread, manage labels

### Google Drive
- **File Operations**: List, search, upload, download, copy, and move files
- **Folder Management**: Create and organize folders
- **Sharing**: Control file permissions and sharing settings
- **Storage Info**: Monitor Drive quota and usage
- **Content Access**: Retrieve and export file content in various formats

### Google Calendar
- **Meeting Management**: Create, update, and delete calendar events
- **Scheduling**: Find available time slots for meetings
- **Invitations**: Add and manage meeting attendees
- **Date-Based Search**: Find meetings for specific dates
- **Bulk Operations**: Create multiple calendar events at once

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

---

## Setting Up Google API Credentials

### Creating a Google Cloud Project and Obtaining Credentials

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Click on "Select a project" at the top of the page, then click "New Project"
   - Enter a name for your project and click "Create"

2. **Enable the Required APIs**:
   - In your new project, navigate to "APIs & Services" > "Library"
   - Search for and enable the following APIs:
     - Gmail API
     - Google Drive API
     - Google Calendar API

3. **Configure the OAuth Consent Screen**:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type (or "Internal" if you're using Google Workspace)
   - Fill in the required fields:
     - App name: "Google MCP"
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
     https://www.googleapis.com/auth/drive
     https://www.googleapis.com/auth/calendar
     ```
   - Click "Save and Continue" and complete the remaining steps

5. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Google MCP Client"
   - Click "Create"
   - Download the JSON file by clicking the download icon
   - Save this file as `client_secret.json` in a secure location

6. **Add Test Users**:
   - If your app is in "External" mode and not verified, you'll need to add test users
   - Go back to "OAuth consent screen"
   - Scroll down to "Test users" and click "Add Users"
   - Add the email address(es) that will be used with the Google MCP
   - Note: Only these email addresses will be able to authenticate with your application until you verify your app

### First-Time Authentication

The first time you run the Google MCP server, it will:

1. Detect that no token file exists at the specified `--token` path
2. Open a browser window asking you to sign in with your Google account
3. Display permissions being requested and ask for your consent
4. After you approve, create a token file at the specified location

For subsequent runs, this token will be used automatically unless it expires or is revoked, in which case the authentication flow will be triggered again.

---

## Configuration

The server can be configured in several ways:

### Command Line Arguments

```bash
python server.py --credentials /path/to/client_secret.json --token /path/to/token.pickle --gmail --drive --calendar
```

Available command line arguments:

| Argument | Description |
|----------|-------------|
| `--credentials` | Path to Google API credentials JSON file |
| `--token` | Path to token pickle file |
| `--gmail` | Enable Gmail service |
| `--drive` | Enable Google Drive service |
| `--calendar` | Enable Google Calendar service |
| `--timeout` | Request timeout in seconds (default: 30) |
| `--transport` | Transport method ("stdio" or "sse") |
| `--port` | Port number for SSE transport (default: 8000) |

### Environment Variables

```bash
export GOOGLE_CREDENTIALS_PATH="/path/to/client_secret.json"
export GOOGLE_TOKEN_PATH="/path/to/token.pickle"
export ENABLE_GMAIL="true"
export ENABLE_DRIVE="true"
export ENABLE_CALENDAR="true"
export REQUEST_TIMEOUT="30"
export TRANSPORT="stdio"
export PORT="8000"
python server.py
```

### MCP Configuration File (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "google_mcp": {
      "command": "path/to/python",
      "args": [
        "path/to/server.py",
        "--gmail",
        "--drive",
        "--calendar",
        "--credentials",
        "/path/to/client_secret.json",
        "--token",
        "/path/to/token.pickle"
      ],
      "env": {
        // Optional environment variables
      }
    }
  }
}
```

---

## Available Resources

| Resource | Description |
|----------|-------------|
| `gmail://profile` | Get user's Gmail profile information |
| `drive://storage/quota` | Get Google Drive storage quota information |
| `drive://files/recent/{max_results}` | Get a list of recent files from Google Drive |
| `calendar://meetings/today` | Get all meetings scheduled for today |
| `calendar://meetings/upcoming/{days}` | Get upcoming meetings for the next specified number of days |
| `calendar://availability/{date}` | Get available time slots for a specific date |

---

## Available Tools

### Gmail Tools

| Tool | Description |
|------|-------------|
| `send_email` | Sends an email with optional CC, BCC, attachments, and HTML content |
| `create_draft_email` | Creates a draft email with optional attachments and formatting |
| `list_emails` | Lists emails with customizable filters and limits |
| `search_emails` | Searches for emails matching specific criteria |
| `get_message` | Gets details of a specific email by ID |
| `get_thread` | Gets all messages in a thread by thread ID |
| `get_unread_emails` | Retrieves unread emails from the inbox |
| `mark_as_read` | Marks a specific email as read |
| `mark_as_unread` | Marks a specific email as unread |
| `delete_email` | Deletes or moves an email to trash |
| `batch_delete_emails` | Deletes multiple emails in a single operation |
| `get_labels` | Gets all Gmail labels |

### Google Drive Tools

| Tool | Description |
|------|-------------|
| `list_drive_files` | Lists files in Google Drive with filtering options |
| `search_drive_files` | Searches for files matching specific criteria |
| `upload_file` | Uploads a file to Google Drive |
| `download_file` | Downloads a file from Google Drive |
| `create_folder` | Creates a new folder in Google Drive |
| `delete_drive_file` | Deletes a file or folder (trash or permanent) |
| `get_file_permissions` | Gets sharing permissions for a file |
| `copy_file` | Makes a copy of a file |
| `move_file` | Moves a file to a different folder |
| `rename_file` | Renames a file or folder |
| `get_drive_storage_info` | Gets Drive storage quota information |
| `revoke_permission` | Removes sharing permission for a file |
| `share_file` | Shares a file with users or makes it public |
| `get_file_content` | Gets the content of a file |

### Google Calendar Tools

| Tool | Description |
|------|-------------|
| `create_meeting` | Creates a new meeting in Google Calendar |
| `get_meetings_by_date` | Gets all meetings for a specific date |
| `get_meeting_details` | Gets details of a specific meeting |
| `update_meeting` | Updates an existing meeting |
| `delete_meeting` | Deletes a meeting |
| `get_available_time_slots` | Finds available time slots for meetings on a specific date |
| `invite_to_meeting` | Adds attendees to an existing meeting |
| `create_bulk_meetings` | Creates multiple meetings in a single operation |

---

## Example Usage

When connected to an AI assistant like Claude, you can use natural language commands:

```
Send an email to john@example.com with the subject "Meeting Reminder"
```

```
List my 10 most recent unread emails
```

```
Search for files in my Google Drive containing "project report"
```

```
Create a meeting titled "Team Sync" for tomorrow at 2pm, invite the team, and add notes about quarterly goals
```

---

## Running with MCP Inspector

You can run the server using the MCP Inspector tool:

```bash
mcp dev server.py:main
```

---

## Security Notes

* Store your credentials and token files in a secure location
* Do not commit these files to version control
* Consider using environment variables for sensitive paths
* Review all requested scopes to ensure they match your usage needs
* This server provides access to your Google account data, so configure it carefully

---

## Transport Options

The server supports two transport methods:

1. **stdio** (Standard Input/Output): Default method, suitable for local operation with Claude Desktop
2. **sse** (Server-Sent Events): For running as a web server, allowing remote connections

Note: When using SSE transport, you may need additional configuration to connect with Claude Desktop, which primarily supports stdio transport.

---

## Troubleshooting

If you encounter errors:

1. Check that Google API credentials are valid and have the necessary permissions
2. Verify that the token file has been properly generated
3. Look for error messages in the server output (redirected to stderr)
4. Ensure the MCP configuration file has the correct format and paths
5. Verify that at least one service (Gmail, Drive, or Calendar) is enabled