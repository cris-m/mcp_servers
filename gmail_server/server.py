import logging
import os
import sys
import traceback

from dotenv import load_dotenv
from gmail import GmailManager
from mcp.server.fastmcp import FastMCP


class GmailMCP:
    def __init__(self):
        load_dotenv()

        self._setup_logging()
        self.mcp = FastMCP("Gmail MCP")
        self.gmail = None
        self._init_gmail()
        self._register_tools()
        logging.info("Gmail MCP initialized")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger("GmailMCP")

    def _init_gmail(self):
        logging.info("Initializing Gmail connection")
        self.gmail = GmailManager(
            credentials_file=os.getenv("CREDENTIALS_FILE", "client_secret.json"),
            token_file=os.getenv("TOKEN_FILE", "token.pickle"),
        )

    def _register_tools(self):
        logging.info("Registering tools")

        @self.mcp.tool("send_email")
        def send_email(
            to: str,
            subject: str,
            body: str,
            cc: str = None,
            bcc: str = None,
            attachments: list = None,
            html_body: str = None,
        ):
            """Send an email using Gmail.

            Args:
                to: Recipient email address or comma-separated addresses
                subject: Email subject
                body: Plain text email body
                cc: CC recipient(s), comma-separated if multiple
                bcc: BCC recipient(s), comma-separated if multiple
                attachments: List of file paths to attach
                html_body: HTML version of the email body
            """
            try:
                result = self.gmail.send_email(
                    to=to,
                    subject=subject,
                    body=body,
                    cc=cc,
                    bcc=bcc,
                    attachments=attachments,
                    html_body=html_body,
                )
                return {"success": True, "message_id": result.get("id")}
            except Exception as e:
                logging.error(f"Failed to send email: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("list_emails")
        def list_emails(
            max_results: int = 50,
            label_ids: list = None,
            query: str = None,
            include_spam_trash: bool = False,
        ):
            """List emails from Gmail with filtering options.

            Args:
                max_results: Maximum number of emails to return (default: 50)
                label_ids: List of Gmail label IDs to filter by (default: ["INBOX"])
                query: Search string to find matching emails
                include_spam_trash: Whether to include messages from SPAM and TRASH folders

            Return: Dictionary containing success status and either a list of matching emails or an error message
            """
            try:
                result = self.gmail.list_emails(
                    max_results=max_results,
                    label_ids=label_ids,
                    query=query,
                    include_spam_trash=include_spam_trash,
                )

                # Process messages to get full email details
                emails = []
                for msg in result.get("messages", []):
                    message = self.gmail.get_email_details(msg["id"])
                    email_data = self.gmail.parse_email_content(message)
                    if email_data:
                        emails.append(email_data)

                return {
                    "success": True,
                    "emails": emails,
                    "count": len(emails),
                    "has_more": result.get("has_more", False),
                    "next_page_token": result.get("next_page_token"),
                }
            except Exception as e:
                logging.error(f"Failed to list emails: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("search_emails")
        def search_emails(query: str, max_results: int = 50):
            """Search emails in Gmail using the provided query.

            Args:
            query: Search string to find matching emails
            max_results: Maximum number of emails to return (default: 50)

            Return: Dictionary containing success status and either a list of matching emails or an error message
            """
            try:
                emails = self.gmail.search_emails(query, max_results)
                return {"success": True, "emails": emails}
            except Exception as e:
                logging.error(f"Failed to get unread emails: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_unread_emails")
        def get_unread_emails(max_results: int = 50):
            """Get a list of unread emails.

            Args:
                max_results: Maximum number of emails to return
            """
            try:
                emails = self.gmail.get_unread_emails(max_results)
                return {"success": True, "emails": emails}
            except Exception as e:
                logging.error(f"Failed to get unread emails: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("mark_as_read")
        def mark_as_read(msg_id: str):
            """Mark an email as read.

            Args:
                msg_id: The ID of the message to mark as read
            """
            try:
                result = self.gmail.mark_as_read(msg_id)
                return {"success": True, "result": result}
            except Exception as e:
                logging.error(f"Failed to mark email as read: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("delete_email")
        def delete_email(msg_id: str, trash: bool = True):
            """Delete an email.

            Args:
                msg_id: The ID of the message to delete
                trash: If True, moves to trash. If False, permanently deletes.
            """
            try:
                result = self.gmail.delete_email(msg_id, trash=trash)
                return {"success": True, "result": result}
            except Exception as e:
                logging.error(f"Failed to delete email: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.mcp.tool("batch_delete_emails")
        def batch_delete_emails(msg_ids: list, trash: bool = True):
            """Delete multiple emails at once.

            Args:
                msg_ids: List of message IDs to delete
                trash: If True, moves to trash. If False, permanently deletes.
            """
            try:
                result = self.gmail.batch_delete_emails(msg_ids, trash=trash)
                return {"success": True, "result": result}
            except Exception as e:
                logging.error(f"Failed to batch delete emails: {str(e)}")
                return {"success": False, "error": str(e)}

    def run(self):
        try:
            logging.info("Starting Gmail MCP")
            self.mcp.run(transport="stdio")
        except Exception as e:
            logging.error(f"Fatal error occurred: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    try:
        server = GmailMCP()
        server.run()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
