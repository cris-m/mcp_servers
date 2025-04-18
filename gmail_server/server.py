import argparse
import logging
import os
import sys
import traceback
from typing import Any, Dict

from dotenv import load_dotenv
from gmail import GmailManager
from mcp.server.fastmcp import Context, FastMCP


class GmailMCP:
    def __init__(self, credentials_file: str, token_file: str):

        self._setup_logging()
        self.credentials_file = credentials_file
        self.token_file = token_file

        self.mcp = FastMCP(name="Gmail MCP", version="1.0.0", request_timeout=30)
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

    def _init_gmail(self):
        logging.info("Initializing Gmail connection")
        self.gmail = GmailManager(
            credentials_file=self.credentials_file, token_file=self.token_file
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
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Send an email using Gmail.

            Args:
                to: Recipient email address or comma-separated addresses
                subject: Email subject
                body: Plain text email body
                cc: CC recipient(s), comma-separated if multiple
                bcc: BCC recipient(s), comma-separated if multiple
                attachments: List of file paths to attach
                html_body: HTML version of the email body
                ctx: MCP context object

            Return:
                Dictionary containing the email message ID.
            """
            try:
                if ctx:
                    ctx.info(f"Sending email to: {to}")
                    ctx.report_progress(0, 100)

                    if attachments:
                        ctx.info(f"Attaching {len(attachments)} file(s)")

                if ctx:
                    ctx.report_progress(25, 100)

                result = self.gmail.send_email(
                    to=to,
                    subject=subject,
                    body=body,
                    cc=cc,
                    bcc=bcc,
                    attachments=attachments,
                    html_body=html_body,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Email sent successfully with ID: {result.get('id')}")

                return {"success": True, "message_id": result.get("id")}

            except Exception as e:
                error_msg = f"Failed to send email: {str(e)}"

                if ctx:
                    ctx.error(error_msg)
                else:
                    logging.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("list_emails")
        def list_emails(
            max_results: int = 50,
            label_ids: list = None,
            query: str = None,
            include_spam_trash: bool = False,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """List emails from Gmail with filtering options.

            Args:
                max_results: Maximum number of emails to return (default: 50)
                label_ids: List of Gmail label IDs to filter by (default: ["INBOX"])
                query: Search string to find matching emails
                include_spam_trash: Whether to include messages from SPAM and TRASH folders
                ctx: MCP context object

            Return:
                Dictionary containing success status and either a list of matching emails or an error message
            """
            try:

                if ctx:
                    ctx.info(f"Fetching up to {max_results} emails")
                    ctx.report_progress(0, 100)

                result = self.gmail.list_emails(
                    max_results=max_results,
                    label_ids=label_ids,
                    query=query,
                    include_spam_trash=include_spam_trash,
                )

                emails = []

                total = len(result.get("messages", []))

                for i, msg in enumerate(result.get("messages", [])):
                    if ctx:
                        progress = int((i / total) * 100) if total > 0 else 100
                        ctx.report_progress(progress, 100)

                    message = self.gmail.get_email_details(msg["id"])
                    email_data = self.gmail.parse_email_content(message)
                    if email_data:
                        emails.append(email_data)

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Found {len(emails)} emails")

                return {
                    "success": True,
                    "emails": emails,
                    "count": len(emails),
                    "has_more": result.get("has_more", False),
                    "next_page_token": result.get("next_page_token"),
                }
            except Exception as e:
                if ctx:
                    ctx.error(f"Failed to list emails: {str(e)}")

                return {"success": False, "error": str(e)}

        @self.mcp.tool("search_emails")
        def search_emails(
            query: str, max_results: int = 50, ctx: Context = None
        ) -> Dict[str, Any]:
            """Search emails in Gmail using the provided query.

            Args:
                query: Search string to find matching emails
                max_results: Maximum number of emails to return (default: 50)
                ctx: MCP context object

            Return:
                Dictionary containing success status and either a list of matching emails or an error message
            """
            try:
                if ctx:
                    ctx.info(f"Searching for emails matching: '{query}'")
                    ctx.info(f"Limiting results to {max_results} emails")
                    ctx.report_progress(10, 100)

                if ctx:
                    ctx.report_progress(30, 100)

                emails = self.gmail.search_emails(query, max_results)

                if ctx:
                    ctx.report_progress(80, 100)
                    found_count = len(emails) if emails else 0
                    ctx.info(f"Search complete. Found {found_count} matching emails")

                    ctx.report_progress(100, 100)

                return {"success": True, "emails": emails}
            except Exception as e:
                error_msg = f"Failed to search emails: {str(e)}"

                if ctx:
                    ctx.error(error_msg)
                else:
                    logging.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_unread_emails")
        def get_unread_emails(
            max_results: int = 50, ctx: Context = None
        ) -> Dict[str, Any]:
            """Get a list of unread emails.

            Args:
                max_results: Maximum number of emails to return
                ctx: MCP context object

            Return:
                Dictionary containing success status and either a list of unread emails or an error message.
            """
            try:
                if ctx:
                    ctx.info(f"Fetching up to {max_results} unread emails")
                    ctx.report_progress(0, 100)

                if ctx:
                    ctx.report_progress(30, 100)

                emails = self.gmail.get_unread_emails(max_results)

                if ctx:
                    ctx.report_progress(90, 100)
                    found_count = len(emails) if emails else 0
                    ctx.info(f"Found {found_count} unread emails")

                    ctx.report_progress(100, 100)

                return {"success": True, "emails": emails}
            except Exception as e:
                error_msg = f"Failed to get unread emails: {str(e)}"

                if ctx:
                    ctx.error(error_msg)
                else:
                    logging.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("mark_as_read")
        def mark_as_read(msg_id: str, ctx: Context = None) -> Dict[str, Any]:
            """Mark an email as read.

            Args:
                msg_id: The ID of the message to mark as read
                ctx: MCP context object

            Return:
                Dictionary containing success status and the result of marking the email as read.
            """
            try:
                if ctx:
                    ctx.info(f"Marking email with ID {msg_id} as read")
                    ctx.report_progress(0, 100)

                result = self.gmail.mark_as_read(msg_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info("Email successfully marked as read")

                return {"success": True, "result": result}
            except Exception as e:
                error_msg = f"Failed to mark email as read: {str(e)}"

                if ctx:
                    ctx.error(error_msg)
                else:
                    logging.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("delete_email")
        def delete_email(
            msg_id: str, trash: bool = True, ctx: Context = None
        ) -> Dict[str, Any]:
            """Delete an email.

            Args:
                msg_id: The ID of the message to delete
                trash: If True, moves to trash. If False, permanently deletes.
                ctx: MCP context object

            Return:
                Dictionary containing success status and either the result of the deletion
                or an error message if deletion failed.
            """
            try:

                action = (
                    "Moving email to trash" if trash else "Permanently deleting email"
                )

                if ctx:
                    ctx.info(f"{action} with ID {msg_id}")
                    ctx.report_progress(0, 100)

                result = self.gmail.delete_email(msg_id, trash=trash)

                if ctx:
                    ctx.report_progress(100, 100)
                    completion_msg = (
                        "Email moved to trash" if trash else "Email permanently deleted"
                    )
                    ctx.info(completion_msg)

                return {"success": True, "result": result}
            except Exception as e:
                error_msg = f"Failed to delete email: {str(e)}"

                if ctx:
                    ctx.error(error_msg)
                else:
                    logging.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("batch_delete_emails")
        def batch_delete_emails(
            msg_ids: list, trash: bool = True, ctx: Context = None
        ) -> Dict[str, Any]:
            """Delete multiple emails at once.

            Args:
                msg_ids: List of message IDs to delete
                trash: If True, moves to trash. If False, permanently deletes.
                ctx: MCP context object

            Return:
                Dictionary containing success status and either the result of the deletion
                or an error message if deletion failed.
            """
            try:
                action = (
                    "Moving emails to trash" if trash else "Permanently deleting emails"
                )

                if ctx:
                    ctx.info(f"{action}: {len(msg_ids)} emails")
                    ctx.report_progress(0, 100)

                if ctx:
                    ctx.report_progress(30, 100)

                result = self.gmail.batch_delete_emails(msg_ids, trash=trash)

                if ctx:
                    ctx.report_progress(100, 100)
                    completion_msg = (
                        "Emails moved to trash"
                        if trash
                        else "Emails permanently deleted"
                    )
                    ctx.info(f"{completion_msg}: {len(msg_ids)} emails")

                return {"success": True, "result": result}
            except Exception as e:
                error_msg = f"Failed to batch delete emails: {str(e)}"

                if ctx:
                    ctx.error(error_msg)
                else:
                    logging.error(error_msg)

                return {"success": False, "error": str(e)}

    def run(self):
        try:
            logging.info("Starting Gmail MCP")
            self.mcp.run(transport="stdio")
        except Exception as e:
            logging.error(f"Fatal error occurred: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Gmail MCP Server")
    parser.add_argument(
        "--gmail-credentials", type=str, help="Path to Gmail credentials file"
    )
    parser.add_argument("--gmail-token", type=str, help="Path to Gmail token file")
    args = parser.parse_args()

    gmail_credentials_path = args.gmail_credentials or os.environ.get(
        "GMAIL_CREDENTIALS_PATH"
    )
    gmail_token_path = args.gmail_token or os.environ.get("GMAIL_TOKEN_PATH")

    if not gmail_credentials_path:
        logging.error(
            "Missing Gmail credentials path (use --gmail-credentials or set GMAIL_CREDENTIALS_PATH)."
        )
        print("ERROR: Gmail credentials path is required.", file=sys.stderr)
        sys.exit(1)

    if not gmail_token_path:
        logging.error(
            "Missing Gmail token path (use --gmail-token or set GMAIL_TOKEN_PATH)."
        )
        print("ERROR: Gmail token path is required.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(gmail_credentials_path):
        logging.error(f"Gmail credentials file not found: {gmail_credentials_path}")
        print(
            f"ERROR: Gmail credentials file not found: {gmail_credentials_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp_server = GmailMCP(
        credentials_file=gmail_credentials_path,
        token_file=gmail_token_path,
    )
    mcp_server.run()


if __name__ == "__main__":
    try:
        logging.info("Initializing Gmail MCP server")
        main()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
