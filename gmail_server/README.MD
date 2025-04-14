# Gmail Manager

A powerful Gmail management server that provides a comprehensive set of tools for email management.

## Features

- Send emails with support for:
  - Multiple recipients (To, CC, BCC)
  - HTML and plain text content
  - File attachments (automatic Drive upload for large files)
- Read and manage emails:
  - Get unread emails
  - Search emails
  - Mark emails as read/unread
  - Delete emails (trash or permanent)
  - Batch delete emails
- Google Drive integration for large attachments

1. Set up Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create OAuth 2.0 credentials
   - Download the credentials and save as `client_secret.json`

2. Place the following files in the gmail_server directory:
   - `client_secret.json` - Your Google OAuth credentials
   - `token.pickle` - Will be created automatically on first run

## Usage Examples

### Starting the Server
```python
from gmail_server.gmail import GmailManager

server = GmailManager(
    credentials_file='client_secret.json',
    token_file='token.pickle'
)
server.run()
```

### Sending Emails
```python
# Send a simple email
result = gmail.send_email(
    to="recipient@example.com",
    subject="Test Email",
    body="This is a test email"
)

# Send an email with HTML content and attachments
result = gmail.send_email(
    to="recipient@example.com",
    subject="HTML Email with Attachments",
    body="Plain text version",
    html_body="<h1>HTML Version</h1><p>This is an HTML email</p>",
    attachments=["document.pdf", "image.jpg"]
)
```

### Reading Emails
```python
# Get unread emails
unread_emails = gmail.get_unread_emails(max_results=10)
for email in unread_emails:
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"Body: {email['body']}")

# Search emails
search_results = gmail.search_emails(
    query="important subject:meeting",
    max_results=5
)
```

### Managing Emails
```python
# Mark an email as read
gmail.mark_as_read(msg_id)

# Delete an email (moves to trash)
gmail.delete_email(msg_id, trash=True)

# Batch delete emails
gmail.batch_delete_emails(msg_ids, trash=True)
```
