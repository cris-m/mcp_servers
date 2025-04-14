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

        @self.mcp.tool("get_unread_emails")
        def get_unread_emails(max_results: int = 10):
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
