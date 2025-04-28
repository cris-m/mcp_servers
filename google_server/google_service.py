import base64
import io
import mimetypes
import os
import pickle
import traceback
from datetime import datetime, time, timedelta
from email.encoders import encode_base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class GoogleServiceManager:
    def __init__(
        self,
        credentials_file="client_secret.json",
        token_file="token.pickle",
        scopes=None,
    ):
        if scopes is None:
            self.SCOPES = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/calendar",
            ]
        else:
            self.SCOPES = scopes

        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = self._authenticate_credentials()

        self.gmail_service = build("gmail", "v1", credentials=self.creds)
        self.calendar_service = build("calendar", "v3", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds)

        self.MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024

    def _authenticate_credentials(self):
        """Authenticate with Google APIs and return credentials."""
        creds = None

        if os.path.exists(self.token_file) and os.path.isfile(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)

        return creds

    def _get_email_details(self, msg_id):
        message = (
            self.gmail_service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        return message

    def _get_body_from_parts(self, payload):
        if "body" in payload and payload["body"].get("data"):
            data = payload["body"]["data"]
            decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
            return decoded_data

        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain" or mime_type == "text/html":
                    if part.get("body", {}).get("data"):
                        data = part["body"]["data"]
                        return base64.urlsafe_b64decode(data).decode("utf-8")

            for part in payload["parts"]:
                body = self._get_body_from_parts(part)
                if body:
                    return body

        return ""

    def _add_attachment(self, message, file_path):
        try:
            content_type, encoding = mimetypes.guess_type(file_path)

            if content_type is None or encoding is not None:
                content_type = "application/octet-stream"

            main_type, sub_type = content_type.split("/", 1)

            with open(file_path, "rb") as file:
                file_data = file.read()

            if main_type == "text":
                attachment = MIMEText(file_data.decode("utf-8"), _subtype=sub_type)
            elif main_type == "image":
                attachment = MIMEImage(file_data, _subtype=sub_type)
            elif main_type == "audio":
                attachment = MIMEAudio(file_data, _subtype=sub_type)
            else:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(file_data)
                encode_base64(attachment)

            filename = os.path.basename(file_path)
            attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
            attachment.add_header("Content-Type", content_type)
            message.attach(attachment)
        except Exception:
            traceback.print_exc()

    def _parse_email_content(self, message):
        if "payload" not in message:
            return None

        payload = message["payload"]
        headers = payload.get("headers", [])

        email_data = {
            "id": message["id"],
            "subject": "",
            "from": "",
            "date": "",
            "body": "",
            "snippet": message.get("snippet", ""),
        }

        for header in headers:
            name = header.get("name", "").lower()
            value = header.get("value", "")

            if name == "subject":
                email_data["subject"] = value
            elif name == "from":
                email_data["from"] = value
            elif name == "date":
                email_data["date"] = value

        email_data["body"] = self._get_body_from_parts(payload)

        return email_data

    def list_emails(
        self,
        max_results=50,
        label_ids=None,
        query=None,
        include_spam_trash=False,
        page_token=None,
    ):
        try:
            if query and label_ids is None:
                label_ids = ["INBOX"]
            elif label_ids is None:
                label_ids = ["INBOX"]

            params = {
                "userId": "me",
                "maxResults": max_results,
                "includeSpamTrash": include_spam_trash,
            }

            if label_ids:
                params["labelIds"] = label_ids
            if query:
                params["q"] = query
            if page_token:
                params["pageToken"] = page_token

            results = self.gmail_service.users().messages().list(**params).execute()

            messages = results.get("messages", [])
            next_page_token = results.get("nextPageToken")

            return {
                "messages": messages,
                "next_page_token": next_page_token,
                "has_more": next_page_token is not None,
            }

        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "messages": [],
                "next_page_token": None,
                "has_more": False,
                "error": str(e),
            }

    def get_unread_emails(self, max_results=50):
        response = self.list_emails(
            max_results=max_results, label_ids=["UNREAD", "INBOX"]
        )

        emails = []
        messages = response.get("messages", [])

        for msg in messages:
            message = self._get_email_details(msg["id"])
            email_data = self._parse_email_content(message)
            if email_data:
                emails.append(email_data)

        return emails

    def mark_as_read(self, msg_id):
        return (
            self.gmail_service.users()
            .messages()
            .modify(userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]})
            .execute()
        )

    def mark_as_unread(self, msg_id):
        return (
            self.gmail_service.users()
            .messages()
            .modify(userId="me", id=msg_id, body={"addLabelIds": ["UNREAD"]})
            .execute()
        )

    def get_labels(self):
        results = self.gmail_service.users().labels().list(userId="me").execute()
        return results.get("labels", [])

    def upload_to_drive(self, file_path):
        try:

            file_metadata = {"name": os.path.basename(file_path)}

            media = MediaFileUpload(file_path, resumable=True)
            file = (
                self.drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id,webViewLink")
                .execute()
            )

            self.drive_service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"},
                fields="id",
            ).execute()

            return file["webViewLink"]
        except Exception:
            traceback.print_exc()
            return None

    def send_email(
        self, to, subject, body, cc=None, bcc=None, attachments=None, html_body=None
    ):
        message = MIMEMultipart("mixed")

        message_alt = MIMEMultipart("alternative")

        message["to"] = to if isinstance(to, str) else ", ".join(to)
        message["subject"] = subject
        if cc:
            message["cc"] = cc if isinstance(cc, str) else ", ".join(cc)
        if bcc:
            message["bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

        message_alt.attach(MIMEText(body, "plain"))

        if html_body:
            message_alt.attach(MIMEText(html_body, "html"))

        message.attach(message_alt)

        drive_links = []

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    continue

                file_size = os.path.getsize(file_path)

                if file_size > self.MAX_ATTACHMENT_SIZE:
                    drive_link = self.upload_to_drive(file_path)
                    if drive_link:
                        drive_links.append(
                            f"File: {os.path.basename(file_path)} - {drive_link}"
                        )
                else:
                    self._add_attachment(message, file_path)

        if drive_links:
            plain_part = None
            html_part = None
            for part in message_alt.get_payload():
                if part.get_content_type() == "text/plain":
                    plain_part = part
                elif part.get_content_type() == "text/html":
                    html_part = part

            if plain_part:
                drive_links_text = (
                    "\n\nLarge files have been uploaded to Google Drive:\n"
                    + "\n".join(drive_links)
                )
                plain_part.set_payload(plain_part.get_payload() + drive_links_text)

            if html_part and html_body:
                drive_links_html = "<br><br><strong>Large files have been uploaded to Google Drive:</strong><br><ul>"
                for link in drive_links:
                    file_name = link.split(" - ")[0].replace("File: ", "")
                    url = link.split(" - ")[1]
                    drive_links_html += f'<li><a href="{url}">{file_name}</a></li>'
                drive_links_html += "</ul>"
                html_part.set_payload(html_part.get_payload() + drive_links_html)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        result = (
            self.gmail_service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )
        return result

    def delete_email(self, msg_id, trash=True):
        if trash:
            return (
                self.gmail_service.users()
                .messages()
                .trash(userId="me", id=msg_id)
                .execute()
            )
        else:
            return (
                self.gmail_service.users()
                .messages()
                .delete(userId="me", id=msg_id)
                .execute()
            )

    def batch_delete_emails(self, msg_ids, trash=True):
        if trash:
            results = []
            for msg_id in msg_ids:
                result = self.delete_email(msg_id, trash=True)
                results.append(result)
            return results
        else:
            return (
                self.gmail_service.users()
                .messages()
                .batchDelete(userId="me", body={"ids": msg_ids})
                .execute()
            )

    def create_draft(
        self, to, subject, body, cc=None, bcc=None, attachments=None, html_body=None
    ):
        message = MIMEMultipart("mixed")
        message_alt = MIMEMultipart("alternative")

        message["to"] = to if isinstance(to, str) else ", ".join(to)
        message["subject"] = subject
        if cc:
            message["cc"] = cc if isinstance(cc, str) else ", ".join(cc)
        if bcc:
            message["bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

        message_alt.attach(MIMEText(body, "plain"))

        if html_body:
            message_alt.attach(MIMEText(html_body, "html"))

        message.attach(message_alt)

        drive_links = []

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    continue

                file_size = os.path.getsize(file_path)

                if file_size > self.MAX_ATTACHMENT_SIZE:

                    drive_link = self.upload_to_drive(file_path)
                    if drive_link:
                        drive_links.append(
                            f"File: {os.path.basename(file_path)} - {drive_link}"
                        )
                else:
                    self._add_attachment(message, file_path)

        if drive_links:
            plain_part = None
            html_part = None
            for part in message_alt.get_payload():
                if part.get_content_type() == "text/plain":
                    plain_part = part
                elif part.get_content_type() == "text/html":
                    html_part = part

            if plain_part:
                drive_links_text = (
                    "\n\nLarge files have been uploaded to Google Drive:\n"
                    + "\n".join(drive_links)
                )
                plain_part.set_payload(plain_part.get_payload() + drive_links_text)

            if html_part and html_body:
                drive_links_html = "<br><br><strong>Large files have been uploaded to Google Drive:</strong><br><ul>"
                for link in drive_links:
                    file_name = link.split(" - ")[0].replace("File: ", "")
                    url = link.split(" - ")[1]
                    drive_links_html += f'<li><a href="{url}">{file_name}</a></li>'
                drive_links_html += "</ul>"
                html_part.set_payload(html_part.get_payload() + drive_links_html)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        try:
            draft = (
                self.gmail_service.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw_message}})
                .execute()
            )

            return draft
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    def get_message(self, msg_id):
        try:
            message = self._get_email_details(msg_id)
            return self._parse_email_content(message)
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    def get_thread(self, thread_id):
        try:
            thread = (
                self.gmail_service.users()
                .threads()
                .get(userId="me", id=thread_id)
                .execute()
            )

            messages = []
            for message in thread.get("messages", []):
                parsed_message = self._parse_email_content(message)
                if parsed_message:
                    messages.append(parsed_message)

            return {
                "thread_id": thread_id,
                "messages": messages,
                "count": len(messages),
                "success": True,
            }
        except Exception as e:
            traceback.print_exc()
            return {
                "thread_id": thread_id,
                "messages": [],
                "count": 0,
                "success": False,
                "error": str(e),
            }

    def search_emails(self, query, max_results=50):
        try:
            response = (
                self.gmail_service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = response.get("messages", [])

            if not messages:
                return {
                    "success": True,
                    "emails": [],
                    "count": 0,
                    "message": f"No emails found matching query: '{query}'",
                }

            emails = []
            for msg in messages:
                try:
                    message = self._get_email_details(msg["id"])
                    email_data = self._parse_email_content(message)
                    if email_data:
                        emails.append(email_data)
                except Exception:
                    continue

            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "message": f"Found {len(emails)} emails matching query: '{query}'",
            }

        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "emails": [],
                "count": 0,
                "error": str(e),
                "message": f"Failed to search for emails with query: '{query}'",
            }

    def create_meeting(
        self,
        summary,
        location,
        description,
        start_time,
        end_time,
        attendees=None,
        timezone="UTC",
        send_notifications=True,
    ):
        try:
            event = {
                "summary": summary,
                "location": location,
                "description": description,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone,
                },
            }

            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            event = (
                self.calendar_service.events()
                .insert(
                    calendarId="primary",
                    body=event,
                    sendUpdates="all" if send_notifications else "none",
                )
                .execute()
            )

            return {
                "success": True,
                "event_id": event["id"],
                "html_link": event.get("htmlLink"),
                "event": event,
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create meeting",
            }

    def create_bulk_meetings(self, meeting_details_list):
        results = []
        for meeting_details in meeting_details_list:
            result = self.create_meeting(
                summary=meeting_details.get("summary"),
                location=meeting_details.get("location", ""),
                description=meeting_details.get("description", ""),
                start_time=meeting_details.get("start_time"),
                end_time=meeting_details.get("end_time"),
                attendees=meeting_details.get("attendees"),
                timezone=meeting_details.get("timezone", "UTC"),
                send_notifications=meeting_details.get("send_notifications", True),
            )
            results.append(result)

        return results

    def get_meetings_by_date(self, date, timezone="UTC"):
        try:
            time_min = datetime.combine(date, time.min).isoformat() + "Z"
            time_max = datetime.combine(date, time.max).isoformat() + "Z"

            events_result = (
                self.calendar_service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                    timeZone=timezone,
                )
                .execute()
            )

            events = events_result.get("items", [])

            return {
                "success": True,
                "events": events,
                "count": len(events),
                "date": date.strftime("%Y-%m-%d"),
                "message": f'Found {len(events)} meetings for {date.strftime("%Y-%m-%d")}',
            }

        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "events": [],
                "count": 0,
                "date": date.strftime("%Y-%m-%d"),
                "error": str(e),
                "message": f'Failed to retrieve meetings for {date.strftime("%Y-%m-%d")}',
            }

    def get_meeting_details(self, event_id):
        try:
            event = (
                self.calendar_service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )

            return {"success": True, "event": event}
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to retrieve event with ID: {event_id}",
            }

    def update_meeting(
        self,
        event_id,
        summary=None,
        location=None,
        description=None,
        start_time=None,
        end_time=None,
        attendees=None,
        timezone=None,
        send_notifications=True,
    ):
        try:

            event = (
                self.calendar_service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )

            if summary:
                event["summary"] = summary
            if location:
                event["location"] = location
            if description:
                event["description"] = description

            if start_time:
                event["start"]["dateTime"] = start_time.isoformat()
                if timezone:
                    event["start"]["timeZone"] = timezone

            if end_time:
                event["end"]["dateTime"] = end_time.isoformat()
                if timezone:
                    event["end"]["timeZone"] = timezone

            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            updated_event = (
                self.calendar_service.events()
                .update(
                    calendarId="primary",
                    eventId=event_id,
                    body=event,
                    sendUpdates="all" if send_notifications else "none",
                )
                .execute()
            )

            return {
                "success": True,
                "event": updated_event,
                "message": f"Meeting updated successfully",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update meeting with ID: {event_id}",
            }

    def delete_meeting(self, event_id, send_notifications=True):
        try:
            self.calendar_service.events().delete(
                calendarId="primary",
                eventId=event_id,
                sendUpdates="all" if send_notifications else "none",
            ).execute()

            return {
                "success": True,
                "message": f"Meeting with ID {event_id} deleted successfully",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete meeting with ID: {event_id}",
            }

    def delete_meetings_by_date(self, date, send_notifications=True):
        try:
            result = self.get_meetings_by_date(date)

            if not result["success"]:
                return result

            events = result["events"]
            deleted_count = 0
            failed_count = 0
            failed_ids = []

            for event in events:
                delete_result = self.delete_meeting(
                    event_id=event["id"], send_notifications=send_notifications
                )

                if delete_result["success"]:
                    deleted_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(event["id"])

            return {
                "success": True,
                "date": date.strftime("%Y-%m-%d"),
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "failed_ids": failed_ids,
                "message": f'Deleted {deleted_count} meetings for {date.strftime("%Y-%m-%d")}',
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "deleted_count": 0,
                "date": date.strftime("%Y-%m-%d"),
                "error": str(e),
                "message": f'Failed to delete meetings for {date.strftime("%Y-%m-%d")}',
            }

    def search_meetings(self, query, max_results=100, timezone="UTC"):
        try:
            time_min = datetime.datetime.utcnow().isoformat() + "Z"

            events_result = (
                self.calendar_service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                    q=query,
                    timeZone=timezone,
                )
                .execute()
            )

            events = events_result.get("items", [])

            return {
                "success": True,
                "events": events,
                "count": len(events),
                "query": query,
                "message": f'Found {len(events)} meetings matching query: "{query}"',
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "events": [],
                "count": 0,
                "query": query,
                "error": str(e),
                "message": f'Failed to search meetings with query: "{query}"',
            }

    def get_available_time_slots(
        self, date, working_hours=(9, 17), meeting_duration=60, timezone="UTC"
    ):
        try:
            result = self.get_meetings_by_date(date, timezone)

            if not result["success"]:
                return result

            existing_meetings = result["events"]

            start_hour, end_hour = working_hours

            tz = pytz.timezone(timezone)
            day_start = tz.localize(datetime.combine(date, time(start_hour, 0)))
            day_end = tz.localize(datetime.combine(date, time(end_hour, 0)))

            duration = timedelta(minutes=meeting_duration)

            busy_times = []
            for meeting in existing_meetings:
                start = meeting["start"].get("dateTime")
                end = meeting["end"].get("dateTime")

                if start and end:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    busy_times.append((start_dt, end_dt))

            busy_times.sort(key=lambda x: x[0])

            available_slots = []
            current_time = day_start

            for busy_start, busy_end in busy_times:

                if (busy_start - current_time) >= duration:
                    available_slots.append((current_time, busy_start))

                current_time = max(current_time, busy_end)

            if (day_end - current_time) >= duration:
                available_slots.append((current_time, day_end))

            formatted_slots = []
            for start, end in available_slots:
                slot_end = min(start + duration, end)
                formatted_slots.append(
                    {
                        "start": start.isoformat(),
                        "end": slot_end.isoformat(),
                        "duration_minutes": (slot_end - start).total_seconds() / 60,
                    }
                )

            return {
                "success": True,
                "date": date.strftime("%Y-%m-%d"),
                "available_slots": formatted_slots,
                "count": len(formatted_slots),
                "message": f'Found {len(formatted_slots)} available time slots for {date.strftime("%Y-%m-%d")}',
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "date": date.strftime("%Y-%m-%d"),
                "available_slots": [],
                "count": 0,
                "error": str(e),
                "message": f'Failed to find available time slots for {date.strftime("%Y-%m-%d")}',
            }

    def invite_to_meeting(self, event_id, attendees, send_notifications=True):
        try:
            event = (
                self.calendar_service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )

            current_attendees = event.get("attendees", [])
            current_emails = {attendee["email"] for attendee in current_attendees}

            for email in attendees:
                if email not in current_emails:
                    current_attendees.append({"email": email})

            event["attendees"] = current_attendees

            updated_event = (
                self.calendar_service.events()
                .update(
                    calendarId="primary",
                    eventId=event_id,
                    body=event,
                    sendUpdates="all" if send_notifications else "none",
                )
                .execute()
            )

            return {
                "success": True,
                "event": updated_event,
                "message": f"Successfully added {len(attendees)} attendees to the meeting",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to add attendees to meeting with ID: {event_id}",
            }

    def list_drive_files(
        self, max_results=100, query=None, order_by="modifiedTime desc"
    ):
        try:
            params = {
                "pageSize": max_results,
                "orderBy": order_by,
                "fields": "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink, webContentLink, shared)",
            }

            if query:
                params["q"] = query

            results = self.drive_service.files().list(**params).execute()
            files = results.get("files", [])

            return {
                "success": True,
                "files": files,
                "count": len(files),
                "message": f"Found {len(files)} files",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "files": [],
                "count": 0,
                "error": str(e),
                "message": "Failed to list files from Google Drive",
            }

    def search_drive_files(self, query, max_results=100, order_by="modifiedTime desc"):
        try:
            full_query = f"fullText contains '{query}' or name contains '{query}'"

            return self.list_drive_files(
                max_results=max_results, query=full_query, order_by=order_by
            )
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "files": [],
                "count": 0,
                "error": str(e),
                "message": f"Failed to search for '{query}' in Google Drive",
            }

    def upload_file(
        self, file_path, parent_folder_id=None, convert=False, description=None
    ):
        try:
            file_name = os.path.basename(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)

            if mime_type is None:
                mime_type = "application/octet-stream"

            file_metadata = {
                "name": file_name,
            }

            if description:
                file_metadata["description"] = description

            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            file = (
                self.drive_service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink, webContentLink",
                    supportsAllDrives=True,
                )
                .execute()
            )

            return {
                "success": True,
                "file": file,
                "message": f"File '{file_name}' uploaded successfully",
                "link": file.get("webViewLink"),
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to upload file: {file_path}",
            }

    def download_file(self, file_id, output_path=None):
        try:
            file = (
                self.drive_service.files()
                .get(fileId=file_id, fields="name, mimeType")
                .execute()
            )

            file_name = file.get("name", f"downloaded_{file_id}")

            if output_path is None:
                output_path = file_name

            request = self.drive_service.files().get_media(fileId=file_id)

            with io.BytesIO() as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False

                while not done:
                    _, done = downloader.next_chunk()

                fh.seek(0)

                with open(output_path, "wb") as f:
                    f.write(fh.read())

            return {
                "success": True,
                "file_path": output_path,
                "file_name": file_name,
                "message": f"File downloaded successfully to {output_path}",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to download file with ID: {file_id}",
            }

    def create_folder(self, folder_name, parent_folder_id=None, description=None):
        try:
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }

            if description:
                folder_metadata["description"] = description

            if parent_folder_id:
                folder_metadata["parents"] = [parent_folder_id]

            folder = (
                self.drive_service.files()
                .create(
                    body=folder_metadata,
                    fields="id, name, mimeType, createdTime, modifiedTime, webViewLink",
                    supportsAllDrives=True,
                )
                .execute()
            )

            return {
                "success": True,
                "folder": folder,
                "folder_id": folder.get("id"),
                "message": f"Folder '{folder_name}' created successfully",
                "link": folder.get("webViewLink"),
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create folder: {folder_name}",
            }

    def delete_file(self, file_id, permanently=False):
        try:
            if permanently:
                self.drive_service.files().delete(fileId=file_id).execute()
            else:
                self.drive_service.files().update(
                    fileId=file_id, body={"trashed": True}
                ).execute()

            return {
                "success": True,
                "file_id": file_id,
                "message": f"File with ID {file_id} {'permanently deleted' if permanently else 'moved to trash'}",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "message": f"Failed to delete file with ID: {file_id}",
            }

    def share_file(
        self, file_id, email=None, role="reader", type="user", message=None, notify=True
    ):
        try:
            permission = {"type": type, "role": role}

            if email and type != "anyone":
                permission["emailAddress"] = email

            result = (
                self.drive_service.permissions()
                .create(
                    fileId=file_id,
                    body=permission,
                    sendNotificationEmail=notify,
                    emailMessage=message,
                    fields="id",
                )
                .execute()
            )

            file = (
                self.drive_service.files()
                .get(fileId=file_id, fields="name, webViewLink, shared")
                .execute()
            )

            if type == "anyone":
                share_message = (
                    f"File is now publicly accessible with {role} permissions"
                )
            else:
                share_message = f"File shared with {email} as {role}"

            return {
                "success": True,
                "permission_id": result.get("id"),
                "file_name": file.get("name"),
                "link": file.get("webViewLink"),
                "message": share_message,
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "message": f"Failed to share file with ID: {file_id}",
            }

    def get_file_permissions(self, file_id):
        try:
            permissions = (
                self.drive_service.permissions()
                .list(
                    fileId=file_id,
                    fields="permissions(id, type, role, emailAddress, displayName, domain)",
                )
                .execute()
            )

            file = (
                self.drive_service.files()
                .get(fileId=file_id, fields="name, shared, webViewLink")
                .execute()
            )

            return {
                "success": True,
                "file_name": file.get("name"),
                "is_shared": file.get("shared", False),
                "link": file.get("webViewLink"),
                "permissions": permissions.get("permissions", []),
                "count": len(permissions.get("permissions", [])),
                "message": f"Retrieved permissions for {file.get('name')}",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "message": f"Failed to get permissions for file with ID: {file_id}",
            }

    def revoke_permission(self, file_id, permission_id):
        try:
            self.drive_service.permissions().delete(
                fileId=file_id, permissionId=permission_id
            ).execute()

            return {
                "success": True,
                "file_id": file_id,
                "permission_id": permission_id,
                "message": f"Permission {permission_id} revoked successfully",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "permission_id": permission_id,
                "error": str(e),
                "message": f"Failed to revoke permission for file with ID: {file_id}",
            }

    def copy_file(self, file_id, new_name=None, parent_folder_id=None):
        try:
            body = {}
            if new_name:
                body["name"] = new_name

            if parent_folder_id:
                body["parents"] = [parent_folder_id]

            copied_file = (
                self.drive_service.files()
                .copy(
                    fileId=file_id,
                    body=body,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink",
                )
                .execute()
            )

            return {
                "success": True,
                "file": copied_file,
                "message": f"File copied successfully as '{copied_file.get('name')}'",
                "link": copied_file.get("webViewLink"),
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "message": f"Failed to copy file with ID: {file_id}",
            }

    def move_file(self, file_id, folder_id):
        try:
            file = (
                self.drive_service.files()
                .get(fileId=file_id, fields="name, parents")
                .execute()
            )

            previous_parents = ",".join(file.get("parents", []))

            file = (
                self.drive_service.files()
                .update(
                    fileId=file_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields="id, name, parents",
                )
                .execute()
            )

            return {
                "success": True,
                "file": file,
                "message": f"File '{file.get('name')}' moved to folder with ID {folder_id}",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "folder_id": folder_id,
                "error": str(e),
                "message": f"Failed to move file with ID: {file_id}",
            }

    def rename_file(self, file_id, new_name):
        try:
            file = (
                self.drive_service.files()
                .update(
                    fileId=file_id,
                    body={"name": new_name},
                    fields="id, name, mimeType, modifiedTime",
                )
                .execute()
            )

            return {
                "success": True,
                "file": file,
                "message": f"File renamed to '{new_name}' successfully",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "message": f"Failed to rename file with ID: {file_id}",
            }

    def get_file_content(self, file_id, mime_type=None):
        try:
            file = (
                self.drive_service.files()
                .get(fileId=file_id, fields="name, mimeType")
                .execute()
            )

            file_name = file.get("name")
            file_mime_type = file.get("mimeType")

            content = None

            if file_mime_type.startswith("application/vnd.google-apps"):
                if mime_type is None:
                    if file_mime_type == "application/vnd.google-apps.document":
                        mime_type = "application/pdf"
                    elif file_mime_type == "application/vnd.google-apps.spreadsheet":
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    elif file_mime_type == "application/vnd.google-apps.presentation":
                        mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    else:
                        mime_type = "application/pdf"

                request = self.drive_service.files().export_media(
                    fileId=file_id, mimeType=mime_type
                )
            else:
                request = self.drive_service.files().get_media(fileId=file_id)

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False

            while not done:
                _, done = downloader.next_chunk()

            content = fh.getvalue()

            return {
                "success": True,
                "file_name": file_name,
                "mime_type": file_mime_type,
                "export_mime_type": (
                    mime_type
                    if file_mime_type.startswith("application/vnd.google-apps")
                    else None
                ),
                "content": content,
                "content_size": len(content),
                "message": f"Retrieved content of '{file_name}' successfully",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "message": f"Failed to get content of file with ID: {file_id}",
            }

    def get_drive_storage_info(self):
        try:
            about = self.drive_service.about().get(fields="storageQuota").execute()
            quota = about.get("storageQuota", {})

            def format_size(size_bytes):
                if size_bytes is None:
                    return "Unknown"

                size_bytes = int(size_bytes)
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if size_bytes < 1024 or unit == "TB":
                        return f"{size_bytes:.2f} {unit}"
                    size_bytes /= 1024

            usage = int(quota.get("usage", 0))
            limit = quota.get("limit")

            if limit:
                limit = int(limit)
                usage_percent = (usage / limit) * 100
            else:
                usage_percent = None

            return {
                "success": True,
                "quota": quota,
                "usage_bytes": usage,
                "limit_bytes": limit,
                "usage_formatted": format_size(usage),
                "limit_formatted": format_size(limit),
                "usage_percent": usage_percent,
                "message": "Retrieved Google Drive storage information",
            }
        except Exception as e:
            error_details = traceback.format_exc()
            print(error_details)
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get Drive storage information",
            }
