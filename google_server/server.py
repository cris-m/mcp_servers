import argparse
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from dotenv import load_dotenv
from google_service import GoogleServiceManager
from mcp.server.fastmcp import Context, FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount


class GoogleMCP:
    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        use_gmail: bool = True,
        use_drive: bool = False,
        use_calendar: bool = False,
        scopes: Optional[List[str]] = None,
        request_timeout: int = 30,
    ):
        self._setup_logging()
        self.credentials_file = credentials_file
        self.token_file = token_file

        self.use_gmail = use_gmail
        self.use_drive = use_drive
        self.use_calendar = use_calendar

        self.google_manager = None

        services_active = []
        if use_gmail:
            services_active.append("Gmail")
        if use_drive:
            services_active.append("Drive")
        if use_calendar:
            services_active.append("Calendar")

        server_name = f"Google {' + '.join(services_active)} MCP"
        self.mcp = FastMCP(
            name=server_name, version="1.0.0", request_timeout=request_timeout
        )

        self._init_google_services(scopes)

        self._register_resources()
        self._register_tools()

        active_services = ", ".join(services_active)
        logging.info(f"Google MCP initialized with services: {active_services}")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def _init_google_services(self, custom_scopes: Optional[List[str]] = None):
        """Initialize Google services based on active service flags."""

        scopes = []

        if self.use_gmail:
            logging.info("Initializing Gmail service")
            scopes.extend(
                [
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.modify",
                    "https://www.googleapis.com/auth/gmail.compose",
                    "https://www.googleapis.com/auth/gmail.send",
                ]
            )

        if self.use_drive:
            logging.info("Initializing Drive service")
            scopes.append("https://www.googleapis.com/auth/drive")

        if self.use_calendar:
            logging.info("Initializing Calendar service")
            scopes.append("https://www.googleapis.com/auth/calendar")

        if custom_scopes:
            scopes = custom_scopes

        self.google_manager = GoogleServiceManager(
            credentials_file=self.credentials_file,
            token_file=self.token_file,
            scopes=scopes,
        )

    def _register_resources(self):
        """Register resources based on enabled services."""
        logging.info("Registering resources")

        if self.use_gmail:
            self._register_gmail_resources()

        if self.use_drive:
            self._register_drive_resources()

        if self.use_calendar:
            self._register_calendar_resources()

    def _register_tools(self):
        """Register tools based on enabled services."""
        logging.info("Registering tools")

        if self.use_gmail:
            self._register_gmail_tools()

        if self.use_drive:
            self._register_drive_tools()

        if self.use_calendar:
            self._register_calendar_tools()

    def _register_gmail_resources(self):
        """Register Gmail-related resources."""
        logging.info("Registering Gmail resources")

        @self.mcp.resource("gmail://profile")
        def get_gmail_profile() -> str:
            """Get user's Gmail profile information"""
            profile = (
                self.google_manager.gmail_service.users()
                .getProfile(userId="me")
                .execute()
            )
            return f"Email: {profile.get('emailAddress')}\nMessages Total: {profile.get('messagesTotal')}\nThreads Total: {profile.get('threadsTotal')}"

    def _register_drive_resources(self):
        """Register Google Drive-related resources."""
        logging.info("Registering Google Drive resources")

        @self.mcp.resource("drive://storage/quota")
        def drive_storage_quota() -> str:
            """Get Google Drive storage quota information."""
            try:
                result = self.google_manager.get_drive_storage_info()

                if result.get("success"):
                    quota = result.get("quota", {})
                    usage = result.get("usage_formatted", "Unknown")
                    limit = result.get("limit_formatted", "Unknown")
                    percent = result.get("usage_percent")

                    if percent is not None:
                        percent_str = f"{percent:.1f}%"
                    else:
                        percent_str = "Unknown"

                    return (
                        f"Drive Storage Usage: {usage} of {limit} ({percent_str})\n\n"
                        f"Storage details:\n"
                        f"- Used: {usage}\n"
                        f"- Total: {limit}\n"
                        f"- Percentage used: {percent_str}"
                    )
                else:
                    return f"Error retrieving storage information: {result.get('error', 'Unknown error')}"
            except Exception as e:
                logging.error(f"Error in storage quota resource: {str(e)}")
                return f"Error retrieving storage information: {str(e)}"

        @self.mcp.resource("drive://files/recent/{max_results}")
        def recent_drive_files(max_results: int = 10) -> str:
            """Get a list of recent files from Google Drive."""
            try:
                result = self.google_manager.list_drive_files(
                    max_results=max_results, order_by="modifiedTime desc"
                )

                if result.get("success"):
                    files = result.get("files", [])
                    if not files:
                        return "No recent files found in Google Drive."

                    file_list = []
                    for i, file in enumerate(files, 1):
                        modified_time = file.get("modifiedTime", "Unknown date")
                        file_list.append(
                            f"{i}. {file.get('name')} "
                            f"(ID: {file.get('id')}, "
                            f"Type: {file.get('mimeType', 'Unknown')}, "
                            f"Modified: {modified_time})"
                        )

                    return "Recent Drive Files:\n\n" + "\n".join(file_list)
                else:
                    return f"Error retrieving files: {result.get('error', 'Unknown error')}"
            except Exception as e:
                logging.error(f"Error in recent files resource: {str(e)}")
                return f"Error retrieving recent files: {str(e)}"

    def _register_calendar_resources(self):
        """Register Google Calendar-related resources."""
        logging.info("Registering Google Calendar resources")

        @self.mcp.resource("calendar://meetings/today")
        def todays_meetings() -> str:
            """Get all meetings scheduled for today."""
            try:

                today = datetime.now().date()
                result = self.google_manager.get_meetings_by_date(date=today)

                if result.get("success"):
                    events = result.get("events", [])
                    if not events:
                        return f"No meetings scheduled for today ({today.strftime('%Y-%m-%d')})."

                    meeting_list = []
                    for i, event in enumerate(events, 1):
                        summary = event.get("summary", "Untitled meeting")
                        start = event.get("start", {}).get("dateTime", "Unknown time")
                        end = event.get("end", {}).get("dateTime", "Unknown time")
                        location = event.get("location", "No location specified")

                        try:
                            start_dt = datetime.fromisoformat(
                                start.replace("Z", "+00:00")
                            )
                            start_str = start_dt.strftime("%H:%M")
                            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                            end_str = end_dt.strftime("%H:%M")
                            time_str = f"{start_str} - {end_str}"
                        except Exception:
                            time_str = "Time not available"

                        meeting_list.append(
                            f"{i}. {summary} ({time_str})\n"
                            f"   Location: {location}\n"
                            f"   ID: {event.get('id')}"
                        )

                    return (
                        f"Meetings for today ({today.strftime('%Y-%m-%d')}):\n\n"
                        + "\n".join(meeting_list)
                    )
                else:
                    return f"Error retrieving meetings: {result.get('error', 'Unknown error')}"
            except Exception as e:
                logging.error(f"Error in today's meetings resource: {str(e)}")
                return f"Error retrieving today's meetings: {str(e)}"

        @self.mcp.resource("calendar://meetings/upcoming/{days}")
        def upcoming_meetings(days: int = 7) -> str:
            """Get upcoming meetings for the next specified number of days."""
            try:
                now = datetime.now(timezone.utc)
                max_time = now + timedelta(days=days)

                time_min = now.isoformat().replace("+00:00", "Z")
                time_max = max_time.isoformat().replace("+00:00", "Z")

                events_result = (
                    self.google_manager.calendar_service.events()
                    .list(
                        calendarId="primary",
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy="startTime",
                        maxResults=50,
                    )
                    .execute()
                )

                events = events_result.get("items", [])
                if not events:
                    return f"No upcoming meetings scheduled for the next {days} days."

                meeting_list = []
                for i, event in enumerate(events, 1):
                    summary = event.get("summary", "Untitled meeting")
                    start = event.get("start", {}).get(
                        "dateTime", event.get("start", {}).get("date", "Unknown")
                    )

                    try:
                        if "T" in start:
                            start_dt = datetime.fromisoformat(
                                start.replace("Z", "+00:00")
                            )
                            date_str = start_dt.strftime("%Y-%m-%d")
                            time_str = start_dt.strftime("%H:%M")
                            formatted_time = f"{date_str} at {time_str}"
                        else:
                            date_obj = datetime.strptime(start, "%Y-%m-%d").date()
                            formatted_time = (
                                f"{date_obj.strftime('%Y-%m-%d')} (all day)"
                            )
                    except Exception:
                        formatted_time = start

                    location = event.get("location", "No location specified")

                    meeting_list.append(
                        f"{i}. {summary} - {formatted_time}\n"
                        f"   Location: {location}"
                    )

                return f"Upcoming meetings for the next {days} days:\n\n" + "\n".join(
                    meeting_list
                )
            except Exception as e:
                error_msg = f"Failed to retrieve upcoming meetings: {str(e)}"
                logging.error(error_msg)
                return error_msg

        @self.mcp.resource("calendar://availability/{date}")
        def availability_by_date(date: str) -> str:
            """Get available time slots for a specific date.

            Args:
                date: Date in YYYY-MM-DD format
            """
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()

                result = self.google_manager.get_available_time_slots(
                    date=date_obj, working_hours=(9, 17), meeting_duration=60
                )

                if result.get("success"):
                    slots = result.get("available_slots", [])
                    if not slots:
                        return f"No available time slots on {date}."

                    slot_list = []
                    for i, slot in enumerate(slots, 1):
                        start = slot.get("start")
                        end = slot.get("end")
                        duration = slot.get("duration_minutes", 0)

                        try:
                            start_dt = datetime.fromisoformat(
                                start.replace("Z", "+00:00")
                            )
                            start_str = start_dt.strftime("%H:%M")
                            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                            end_str = end_dt.strftime("%H:%M")

                            slot_list.append(
                                f"{i}. {start_str} - {end_str} ({int(duration)} minutes)"
                            )
                        except Exception:
                            slot_list.append(f"{i}. Time format error")

                    return f"Available time slots on {date}:\n\n" + "\n".join(slot_list)
                else:
                    return f"Error retrieving availability: {result.get('error', 'Unknown error')}"
            except Exception as e:
                logging.error(f"Error in availability resource: {str(e)}")
                return f"Error retrieving availability: {str(e)}"

    def _register_gmail_tools(self):
        """Register Gmail-related tools."""
        logging.info("Registering Gmail tools")

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

                result = self.google_manager.send_email(
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
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("create_draft_email")
        def create_draft(
            to: str,
            subject: str,
            body: str,
            cc: str = None,
            bcc: str = None,
            attachments: list = None,
            html_body: str = None,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Create a draft email in Gmail.

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
                Dictionary containing the draft details.
            """
            try:
                if ctx:
                    ctx.info(f"Creating draft email to: {to}")
                    ctx.report_progress(0, 100)

                    if attachments:
                        ctx.info(f"Attaching {len(attachments)} file(s)")

                if ctx:
                    ctx.report_progress(25, 100)

                result = self.google_manager.create_draft(
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
                    if "error" in result:
                        ctx.error(f"Failed to create draft: {result['error']}")
                    else:
                        ctx.info(
                            f"Draft created successfully with ID: {result.get('id')}"
                        )

                return (
                    result if "error" in result else {"success": True, "draft": result}
                )

            except Exception as e:
                error_msg = f"Failed to create draft: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

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

                result = self.google_manager.list_emails(
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

                    message = self.google_manager.get_email_details(msg["id"])
                    email_data = self.google_manager.parse_email_content(message)
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
                error_msg = f"Failed to list emails: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("search_emails")
        def search_emails(
            query: str, max_results: int = 100, ctx: Context = None
        ) -> Dict[str, Any]:
            """Search emails in Gmail using the provided query.

            Args:
                query: Search string to find matching emails
                max_results: Maximum number of emails to return (default: 100)
                ctx: MCP context object

            Return:
                Dictionary containing success status and either a list of matching emails or an error message
            """
            try:
                if ctx:
                    ctx.info(f"Searching for emails matching: '{query}'")
                    ctx.info(f"Limiting results to {max_results} emails")
                    ctx.report_progress(10, 100)

                result = self.google_manager.search_emails(query, max_results)

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(
                        f"Search complete. Found {result.get('count', 0)} matching emails"
                    )

                return result
            except Exception as e:
                error_msg = f"Failed to search emails: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_message")
        def get_message(msg_id: str, ctx: Context = None) -> Dict[str, Any]:
            """Get details of a specific email.

            Args:
                msg_id: The ID of the message to retrieve
                ctx: MCP context object

            Return:
                Dictionary containing the email details
            """
            try:
                if ctx:
                    ctx.info(f"Retrieving message with ID: {msg_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_message(msg_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    if "error" in result:
                        ctx.error(f"Failed to retrieve message: {result['error']}")
                    else:
                        ctx.info(
                            f"Message retrieved successfully: {result.get('subject', '')}"
                        )

                return (
                    result
                    if "error" in result
                    else {"success": True, "message": result}
                )
            except Exception as e:
                error_msg = f"Failed to get message: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_thread")
        def get_thread(thread_id: str, ctx: Context = None) -> Dict[str, Any]:
            """Get all messages in a thread.

            Args:
                thread_id: The ID of the thread to retrieve
                ctx: MCP context object

            Return:
                Dictionary containing the thread details and messages
            """
            try:
                if ctx:
                    ctx.info(f"Retrieving thread with ID: {thread_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_thread(thread_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    if not result.get("success", True):
                        ctx.error(
                            f"Failed to retrieve thread: {result.get('error', 'Unknown error')}"
                        )
                    else:
                        ctx.info(
                            f"Thread retrieved successfully with {result.get('count', 0)} messages"
                        )

                return result
            except Exception as e:
                error_msg = f"Failed to get thread: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_unread_emails")
        def get_unread_emails(
            max_results: int = 100, ctx: Context = None
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

                emails = self.google_manager.get_unread_emails(max_results)

                if ctx:
                    ctx.report_progress(90, 100)
                    found_count = len(emails) if emails else 0
                    ctx.info(f"Found {found_count} unread emails")

                    ctx.report_progress(100, 100)

                return {"success": True, "emails": emails}
            except Exception as e:
                error_msg = f"Failed to get unread emails: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("mark_as_unread")
        def mark_as_unread(msg_id: str, ctx: Context = None) -> Dict[str, Any]:
            """Mark an email as unread.

            Args:
                msg_id: The ID of the message to mark as unread
                ctx: MCP context object

            Return:
                Dictionary containing success status and the result
            """
            try:
                if ctx:
                    ctx.info(f"Marking email with ID {msg_id} as unread")
                    ctx.report_progress(0, 100)

                result = self.google_manager.mark_as_unread(msg_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info("Email successfully marked as unread")

                return {"success": True, "result": result}
            except Exception as e:
                error_msg = f"Failed to mark email as unread: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

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

                result = self.google_manager.mark_as_read(msg_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info("Email successfully marked as read")

                return {"success": True, "result": result}
            except Exception as e:
                error_msg = f"Failed to mark email as read: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

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

                result = self.google_manager.delete_email(msg_id, trash=trash)

                if ctx:
                    ctx.report_progress(100, 100)
                    completion_msg = (
                        "Email moved to trash" if trash else "Email permanently deleted"
                    )
                    ctx.info(completion_msg)

                return {"success": True, "result": result}
            except Exception as e:
                error_msg = f"Failed to delete email: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

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

                result = self.google_manager.batch_delete_emails(msg_ids, trash=trash)

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
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_labels")
        def get_labels(ctx: Context = None) -> Dict[str, Any]:
            """Get all Gmail labels.

            Args:
                ctx: MCP context object

            Return:
                Dictionary containing the list of Gmail labels
            """
            try:
                if ctx:
                    ctx.info("Fetching Gmail labels")
                    ctx.report_progress(0, 100)

                results = self.google_manager.get_labels()

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Found {len(results)} labels")

                return {"success": True, "labels": results}
            except Exception as e:
                error_msg = f"Failed to get labels: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

    def _register_drive_tools(self):
        """Register Google Drive-related tools."""
        logging.info("Registering Google Drive tools")

        @self.mcp.tool("list_drive_files")
        def list_drive_files(
            max_results: int = 100,
            query: str = None,
            order_by: str = "modifiedTime desc",
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """List files in Google Drive.

            Args:
                max_results: Maximum number of files to return
                query: Search query (see Google Drive API documentation for syntax)
                       e.g., "mimeType='application/pdf'" for PDF files
                order_by: Order by field (default: modified time descending)
                ctx: MCP context object

            Return:
                Dictionary with list of files
            """
            try:
                if ctx:
                    ctx.info(f"Listing up to {max_results} files from Google Drive")
                    if query:
                        ctx.info(f"Using query: {query}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.list_drive_files(
                    max_results=max_results, query=query, order_by=order_by
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Found {result.get('count', 0)} files")

                return result
            except Exception as e:
                error_msg = f"Failed to list Drive files: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("search_drive_files")
        def search_drive_files(
            query: str,
            max_results: int = 100,
            order_by: str = "modifiedTime desc",
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Search for files in Google Drive.

            Args:
                query: Search query string (file name and content)
                max_results: Maximum number of files to return
                order_by: Order by field
                ctx: MCP context object

            Return:
                Dictionary with search results
            """
            try:
                if ctx:
                    ctx.info(f"Searching Drive for files matching: '{query}'")
                    ctx.report_progress(0, 100)

                result = self.google_manager.search_drive_files(
                    query=query, max_results=max_results, order_by=order_by
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Found {result.get('count', 0)} matching files")

                return result
            except Exception as e:
                error_msg = f"Failed to search Drive files: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("upload_file")
        def upload_file(
            file_path: str,
            parent_folder_id: str = None,
            convert: bool = False,
            description: str = None,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Upload a file to Google Drive.

            Args:
                file_path: Path to the local file
                parent_folder_id: ID of the parent folder (None for root)
                convert: Whether to convert to Google Docs format if applicable
                description: File description
                ctx: MCP context object

            Return:
                Dictionary with uploaded file information
            """
            try:
                file_name = os.path.basename(file_path)

                if ctx:
                    ctx.info(f"Uploading file: {file_name}")
                    if parent_folder_id:
                        ctx.info(f"To folder ID: {parent_folder_id}")
                    ctx.report_progress(0, 100)

                if ctx:
                    ctx.report_progress(30, 100)

                result = self.google_manager.upload_file(
                    file_path=file_path,
                    parent_folder_id=parent_folder_id,
                    convert=convert,
                    description=description,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"File uploaded successfully: {file_name}")
                    else:
                        ctx.error(f"Failed to upload file: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to upload file: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("download_file")
        def download_file(
            file_id: str, output_path: str = None, ctx: Context = None
        ) -> Dict[str, Any]:
            """Download a file from Google Drive.

            Args:
                file_id: ID of the file to download
                output_path: Path where to save the file (if None, derived from file name)
                ctx: MCP context object

            Return:
                Path to the downloaded file
            """
            try:
                if ctx:
                    ctx.info(f"Downloading file with ID: {file_id}")
                    if output_path:
                        ctx.info(f"Saving to: {output_path}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.download_file(file_id, output_path)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(
                            f"File downloaded successfully to: {result.get('file_path')}"
                        )
                    else:
                        ctx.error(f"Failed to download file: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to download file: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("create_folder")
        def create_folder(
            folder_name: str,
            parent_folder_id: str = None,
            description: str = None,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Create a folder in Google Drive.

            Args:
                folder_name: Name of the folder to create
                parent_folder_id: ID of the parent folder (None for root)
                description: Folder description
                ctx: MCP context object

            Return:
                Dictionary with created folder information
            """
            try:
                if ctx:
                    ctx.info(f"Creating folder: {folder_name}")
                    if parent_folder_id:
                        ctx.info(f"In parent folder: {parent_folder_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.create_folder(
                    folder_name=folder_name,
                    parent_folder_id=parent_folder_id,
                    description=description,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Folder created successfully: {folder_name}")
                    else:
                        ctx.error(f"Failed to create folder: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to create folder: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("delete_drive_file")
        def delete_drive_file(
            file_id: str, permanently: bool = False, ctx: Context = None
        ) -> Dict[str, Any]:
            """Delete a file or folder from Google Drive.

            Args:
                file_id: ID of the file or folder to delete
                permanently: If True, permanently deletes file (bypassing trash)
                ctx: MCP context object

            Return:
                Dictionary with deletion status
            """
            try:
                action = "Permanently deleting" if permanently else "Moving to trash"

                if ctx:
                    ctx.info(f"{action} file with ID: {file_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.delete_file(file_id, permanently)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(
                            f"File {file_id} successfully {'deleted' if permanently else 'moved to trash'}"
                        )
                    else:
                        ctx.error(f"Failed to delete file: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to delete file: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_file_permissions")
        def get_file_permissions(file_id: str, ctx: Context = None) -> Dict[str, Any]:
            """Get sharing permissions for a file.

            Args:
                file_id: ID of the file to check
                ctx: MCP context object

            Return:
                Dictionary with file permissions
            """
            try:
                if ctx:
                    ctx.info(f"Retrieving permissions for file ID: {file_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_file_permissions(file_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Retrieved {result.get('count', 0)} permissions")
                    else:
                        ctx.error(f"Failed to get permissions: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to get file permissions: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("copy_file")
        def copy_file(
            file_id: str,
            new_name: str = None,
            parent_folder_id: str = None,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Make a copy of a file in Google Drive.

            Args:
                file_id: ID of the file to copy
                new_name: Name for the copy (None to use original name)
                parent_folder_id: ID of the destination folder (None for same location)
                ctx: MCP context object

            Return:
                Dictionary with copied file information
            """
            try:
                if ctx:
                    ctx.info(f"Copying file with ID: {file_id}")
                    if new_name:
                        ctx.info(f"New name: {new_name}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.copy_file(
                    file_id=file_id,
                    new_name=new_name,
                    parent_folder_id=parent_folder_id,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"File copied successfully")
                    else:
                        ctx.error(f"Failed to copy file: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to copy file: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("move_file")
        def move_file(
            file_id: str, folder_id: str, ctx: Context = None
        ) -> Dict[str, Any]:
            """Move a file to a different folder.

            Args:
                file_id: ID of the file to move
                folder_id: ID of the destination folder
                ctx: MCP context object

            Return:
                Dictionary with moved file status
            """
            try:
                if ctx:
                    ctx.info(f"Moving file {file_id} to folder {folder_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.move_file(file_id, folder_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"File moved successfully")
                    else:
                        ctx.error(f"Failed to move file: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to move file: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("rename_file")
        def rename_file(
            file_id: str, new_name: str, ctx: Context = None
        ) -> Dict[str, Any]:
            """Rename a file or folder.

            Args:
                file_id: ID of the file to rename
                new_name: New name for the file
                ctx: MCP context object

            Return:
                Dictionary with renamed file information
            """
            try:
                if ctx:
                    ctx.info(f"Renaming file {file_id} to '{new_name}'")
                    ctx.report_progress(0, 100)

                result = self.google_manager.rename_file(file_id, new_name)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"File renamed successfully")
                    else:
                        ctx.error(f"Failed to rename file: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to rename file: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_drive_storage_info")
        def get_drive_storage_info(ctx: Context = None) -> Dict[str, Any]:
            """Get Drive storage quota information.

            Args:
                ctx: MCP context object

            Return:
                Dictionary with storage details
            """
            try:
                if ctx:
                    ctx.info("Fetching Google Drive storage information")
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_drive_storage_info()

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        usage = result.get("usage_formatted", "Unknown")
                        limit = result.get("limit_formatted", "Unknown")
                        ctx.info(f"Drive storage: {usage} used out of {limit}")
                    else:
                        ctx.error(f"Failed to get storage info: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to get Drive storage info: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("revoke_permission")
        def revoke_permission(
            file_id: str, permission_id: str, ctx: Context = None
        ) -> Dict[str, Any]:
            """Remove sharing permission for a file.

            Args:
                file_id: ID of the file
                permission_id: ID of the permission to remove
                ctx: MCP context object

            Return:
                Dictionary with revocation status
            """
            try:
                if ctx:
                    ctx.info(f"Revoking permission {permission_id} for file {file_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.revoke_permission(file_id, permission_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Permission revoked successfully")
                    else:
                        ctx.error(f"Failed to revoke permission: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to revoke permission: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("share_file")
        def share_file(
            file_id: str,
            email: str = None,
            role: str = "reader",
            type: str = "user",
            message: str = None,
            notify: bool = True,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Share a file or folder with a user or make it public.

            Args:
                file_id: ID of the file to share
                email: Email address to share with (None for public access)
                role: Permission role ('reader', 'writer', 'commenter', 'owner')
                type: Permission type ('user', 'group', 'domain', 'anyone')
                message: Custom message to include in notification email
                notify: Whether to send notification email
                ctx: MCP context object

            Return:
                Dictionary with sharing status
            """
            try:
                if ctx:
                    if email and type != "anyone":
                        ctx.info(f"Sharing file {file_id} with {email} as {role}")
                    else:
                        ctx.info(f"Making file {file_id} publicly accessible as {role}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.share_file(
                    file_id=file_id,
                    email=email,
                    role=role,
                    type=type,
                    message=message,
                    notify=notify,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"File shared successfully")
                    else:
                        ctx.error(f"Failed to share file: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to share file: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_file_content")
        def get_file_content(
            file_id: str, mime_type: str = None, ctx: Context = None
        ) -> Dict[str, Any]:
            """Get the content of a file from Google Drive.

            Args:
                file_id: ID of the file to download
                mime_type: Mime type to export as (for Google Docs)
                ctx: MCP context object

            Return:
                Dictionary with file content
            """
            try:
                if ctx:
                    ctx.info(f"Retrieving content of file with ID: {file_id}")
                    if mime_type:
                        ctx.info(f"Exporting as MIME type: {mime_type}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_file_content(file_id, mime_type)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        file_name = result.get("file_name", "Unknown")
                        content_size = result.get("content_size", 0)
                        size_kb = content_size / 1024
                        ctx.info(
                            f"Retrieved content of '{file_name}' ({size_kb:.1f} KB)"
                        )
                    else:
                        ctx.error(f"Failed to get file content: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to get file content: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

    def _register_calendar_tools(self):
        """Register Google Calendar/Meeting-related tools."""
        logging.info("Registering Google Calendar tools")

        @self.mcp.tool("create_meeting")
        def create_meeting(
            summary: str,
            location: str,
            description: str,
            start_time: str,
            end_time: str,
            attendees: list = None,
            timezone: str = "UTC",
            send_notifications: bool = True,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Create a new meeting in Google Calendar.

            Args:
                summary: Meeting title
                location: Meeting location
                description: Meeting description
                start_time: Start time (ISO format string)
                end_time: End time (ISO format string)
                attendees: List of email addresses for attendees
                timezone: Timezone for the meeting (default: UTC)
                send_notifications: Whether to send notifications to attendees
                ctx: MCP context object

            Return:
                Dictionary containing created event details
            """
            try:

                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

                if ctx:
                    ctx.info(f"Creating meeting: {summary}")
                    if attendees:
                        ctx.info(f"With {len(attendees)} attendees")
                    ctx.report_progress(0, 100)

                result = self.google_manager.create_meeting(
                    summary=summary,
                    location=location,
                    description=description,
                    start_time=start_dt,
                    end_time=end_dt,
                    attendees=attendees,
                    timezone=timezone,
                    send_notifications=send_notifications,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Meeting created successfully")
                    else:
                        ctx.error(f"Failed to create meeting: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to create meeting: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_meetings_by_date")
        def get_meetings_by_date(
            date: str, timezone: str = "UTC", ctx: Context = None
        ) -> Dict[str, Any]:
            """Get all meetings for a specific date.

            Args:
                date: Date in YYYY-MM-DD format
                timezone: Timezone for the search
                ctx: MCP context object

            Return:
                List of events on the specified date
            """
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()

                if ctx:
                    ctx.info(f"Fetching meetings for date: {date}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_meetings_by_date(
                    date=date_obj, timezone=timezone
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(f"Found {result.get('count', 0)} meetings")

                return result
            except Exception as e:
                error_msg = f"Failed to get meetings: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_meeting_details")
        def get_meeting_details(event_id: str, ctx: Context = None) -> Dict[str, Any]:
            """Get details of a specific meeting.

            Args:
                event_id: The Google Calendar event ID
                ctx: MCP context object

            Return:
                Event details
            """
            try:
                if ctx:
                    ctx.info(f"Retrieving meeting details for event ID: {event_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_meeting_details(event_id)

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        event = result.get("event", {})
                        summary = event.get("summary", "Unknown")
                        ctx.info(f"Retrieved meeting: {summary}")
                    else:
                        ctx.error(f"Failed to retrieve meeting: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to get meeting details: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("update_meeting")
        def update_meeting(
            event_id: str,
            summary: str = None,
            location: str = None,
            description: str = None,
            start_time: str = None,
            end_time: str = None,
            attendees: list = None,
            timezone: str = None,
            send_notifications: bool = True,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Update an existing meeting in Google Calendar.

            Args:
                event_id: The Google Calendar event ID to update
                summary: Meeting title (optional)
                location: Meeting location (optional)
                description: Meeting description (optional)
                start_time: Start time in ISO format (optional)
                end_time: End time in ISO format (optional)
                attendees: List of email addresses for attendees (optional)
                timezone: Timezone for the meeting (optional)
                send_notifications: Whether to send notifications to attendees
                ctx: MCP context object

            Return:
                Updated event details
            """
            try:
                start_dt = None
                end_dt = None

                if start_time:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if end_time:
                    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

                if ctx:
                    ctx.info(f"Updating meeting with ID: {event_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.update_meeting(
                    event_id=event_id,
                    summary=summary,
                    location=location,
                    description=description,
                    start_time=start_dt,
                    end_time=end_dt,
                    attendees=attendees,
                    timezone=timezone,
                    send_notifications=send_notifications,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Meeting updated successfully")
                    else:
                        ctx.error(f"Failed to update meeting: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to update meeting: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("delete_meeting")
        def delete_meeting(
            event_id: str, send_notifications: bool = True, ctx: Context = None
        ) -> Dict[str, Any]:
            """Delete a meeting by its event ID.

            Args:
                event_id: The Google Calendar event ID to delete
                send_notifications: Whether to send cancellation notifications
                ctx: MCP context object

            Return:
                Dictionary with deletion status
            """
            try:
                if ctx:
                    ctx.info(f"Deleting meeting with ID: {event_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.delete_meeting(
                    event_id=event_id, send_notifications=send_notifications
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Meeting deleted successfully")
                    else:
                        ctx.error(f"Failed to delete meeting: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to delete meeting: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("get_available_time_slots")
        def get_available_time_slots(
            date: str,
            working_hours: tuple = (9, 17),
            meeting_duration: int = 60,
            timezone: str = "UTC",
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Find available time slots for meetings on a specific date.

            Args:
                date: Date in YYYY-MM-DD format
                working_hours: Tuple of (start_hour, end_hour) for working hours in 24-hour format
                meeting_duration: Duration of the meeting in minutes
                timezone: Timezone for the search
                ctx: MCP context object

            Return:
                List of available time slots
            """
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()

                if ctx:
                    ctx.info(
                        f"Finding available {meeting_duration}-minute slots on {date}"
                    )
                    ctx.info(
                        f"Working hours: {working_hours[0]}:00 to {working_hours[1]}:00"
                    )
                    ctx.report_progress(0, 100)

                result = self.google_manager.get_available_time_slots(
                    date=date_obj,
                    working_hours=working_hours,
                    meeting_duration=meeting_duration,
                    timezone=timezone,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Found {result.get('count', 0)} available time slots")
                    else:
                        ctx.error(f"Failed to find time slots: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to get available time slots: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("invite_to_meeting")
        def invite_to_meeting(
            event_id: str,
            attendees: list,
            send_notifications: bool = True,
            ctx: Context = None,
        ) -> Dict[str, Any]:
            """Add attendees to an existing meeting.

            Args:
                event_id: The Google Calendar event ID
                attendees: List of email addresses to add as attendees
                send_notifications: Whether to send invitation notifications
                ctx: MCP context object

            Return:
                Updated event details
            """
            try:
                if ctx:
                    ctx.info(f"Adding {len(attendees)} attendees to meeting {event_id}")
                    ctx.report_progress(0, 100)

                result = self.google_manager.invite_to_meeting(
                    event_id=event_id,
                    attendees=attendees,
                    send_notifications=send_notifications,
                )

                if ctx:
                    ctx.report_progress(100, 100)
                    if result.get("success"):
                        ctx.info(f"Attendees added successfully")
                    else:
                        ctx.error(f"Failed to add attendees: {result.get('error')}")

                return result
            except Exception as e:
                error_msg = f"Failed to invite attendees: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool("create_bulk_meetings")
        def create_bulk_meetings(
            meeting_details_list: list, ctx: Context = None
        ) -> Dict[str, Any]:
            """Create multiple meetings in Google Calendar.

            Args:
                meeting_details_list: List of dictionaries with meeting details
                    Each dictionary should contain:
                    - summary: Meeting title
                    - location: Meeting location
                    - description: Meeting description
                    - start_time: Start time in ISO format
                    - end_time: End time in ISO format
                    - attendees: List of email addresses (optional)
                    - timezone: Timezone for the meeting (optional, default: UTC)
                    - send_notifications: Whether to send notifications (optional, default: True)
                ctx: MCP context object

            Return:
                List of created event details
            """
            try:

                if ctx:
                    ctx.info(f"Creating {len(meeting_details_list)} meetings")
                    ctx.report_progress(0, 100)

                processed_meetings = []
                for i, meeting in enumerate(meeting_details_list):
                    if ctx:
                        progress = int((i / len(meeting_details_list)) * 50)
                        ctx.report_progress(progress, 100)

                    processed_meeting = meeting.copy()

                    if "start_time" in meeting and isinstance(
                        meeting["start_time"], str
                    ):
                        processed_meeting["start_time"] = datetime.fromisoformat(
                            meeting["start_time"].replace("Z", "+00:00")
                        )

                    if "end_time" in meeting and isinstance(meeting["end_time"], str):
                        processed_meeting["end_time"] = datetime.fromisoformat(
                            meeting["end_time"].replace("Z", "+00:00")
                        )

                    processed_meetings.append(processed_meeting)

                result = self.google_manager.create_bulk_meetings(processed_meetings)

                success_count = sum(1 for r in result if r.get("success", False))

                if ctx:
                    ctx.report_progress(100, 100)
                    ctx.info(
                        f"Created {success_count} out of {len(meeting_details_list)} meetings"
                    )

                return {
                    "success": True,
                    "results": result,
                    "total": len(meeting_details_list),
                    "successful": success_count,
                }
            except Exception as e:
                error_msg = f"Failed to create bulk meetings: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

    def run(self, transport="stdio", port=8000):
        """Run the MCP server with the specified transport.

        Args:
            transport: Transport method ("stdio" or "sse")
            port: Port number for SSE transport
        """
        try:
            active_services = []
            if self.use_gmail:
                active_services.append("Gmail")
            if self.use_drive:
                active_services.append("Drive")
            if self.use_calendar:
                active_services.append("Calendar")

            active_services_str = ", ".join(active_services)
            logging.info(f"Starting Google MCP with services: {active_services_str}")
            logging.info(f"Using transport: {transport}")

            if transport == "stdio":
                self.mcp.run(transport="stdio")
            elif transport == "sse":
                app = Starlette(
                    routes=[
                        Mount("/", app=self.mcp.sse_app()),
                    ]
                )

                logging.info(f"Starting SSE server on port {port}")
                uvicorn.run(app, host="0.0.0.0", port=port)
            else:
                raise ValueError(f"Unsupported transport: {transport}")

        except Exception as e:
            logging.error(f"Fatal error occurred: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


def str_to_bool(value):
    return str(value).lower() in ("true", "1", "yes", "on")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Google MCP Server")

    parser.add_argument(
        "--credentials",
        default=os.getenv("GOOGLE_CREDENTIALS_PATH"),
        help="Path to Google API credentials JSON file (required)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GOOGLE_TOKEN_PATH"),
        help="Path to token pickle file (required)",
    )

    parser.add_argument(
        "--gmail",
        action="store_true",
        default=str_to_bool(os.getenv("ENABLE_GMAIL", "false")),
        help="Enable Gmail service",
    )
    parser.add_argument(
        "--drive",
        action="store_true",
        default=str_to_bool(os.getenv("ENABLE_DRIVE", "false")),
        help="Enable Google Drive service",
    )
    parser.add_argument(
        "--calendar",
        action="store_true",
        default=str_to_bool(os.getenv("ENABLE_CALENDAR", "false")),
        help="Enable Google Calendar service",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("REQUEST_TIMEOUT", "30")),
        help="Request timeout in seconds",
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.getenv("TRANSPORT", "stdio"),
        help="Transport method (stdio or sse)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port number for SSE transport",
    )

    args = parser.parse_args()

    if not any([args.gmail, args.drive, args.calendar]):
        sys.exit(
            "Error: At least one service (Gmail, Drive, or Calendar) must be enabled."
        )

    server = GoogleMCP(
        credentials_file=args.credentials,
        token_file=args.token,
        use_gmail=args.gmail,
        use_drive=args.drive,
        use_calendar=args.calendar,
        request_timeout=args.timeout,
    )

    server.run(transport=args.transport, port=args.port)


if __name__ == "__main__":
    try:
        logging.info("Initializing Googlr MCP server")
        main()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
