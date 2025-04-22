import base64
import mimetypes
import os
import pickle
import traceback
from email.encoders import encode_base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class GmailManager:
    def __init__(
        self,
        credentials_file="client_secret.json",
        token_file="token.pickle",
        scopes=None,
    ):
        load_dotenv()
        if scopes is None:
            self.SCOPES = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/drive.file",
            ]
        else:
            self.SCOPES = scopes

        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._authenticate()
        self.MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024

    def _authenticate(self):
        self.creds = None

        if os.path.exists(self.token_file) and os.path.isfile(self.token_file):
            with open(self.token_file, "rb") as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            with open(self.token_file, "wb") as token:
                pickle.dump(self.creds, token)

        return build("gmail", "v1", credentials=self.creds)

    def _get_email_details(self, msg_id):
        message = (
            self.service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        return message

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

            results = self.service.users().messages().list(**params).execute()

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

    def parse_email_content(self, message):
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

    def get_unread_emails(self, max_results=50):
        response = self.list_emails(
            max_results=max_results, label_ids=["UNREAD", "INBOX"]
        )

        emails = []
        messages = response.get("messages", [])

        for msg in messages:
            message = self._get_email_details(msg["id"])
            email_data = self.parse_email_content(message)
            if email_data:
                emails.append(email_data)

        return emails

    def mark_as_read(self, msg_id):
        return (
            self.service.users()
            .messages()
            .modify(userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]})
            .execute()
        )

    def mark_as_unread(self, msg_id):
        return (
            self.service.users()
            .messages()
            .modify(userId="me", id=msg_id, body={"addLabelIds": ["UNREAD"]})
            .execute()
        )

    def get_labels(self):
        results = self.service.users().labels().list(userId="me").execute()
        return results.get("labels", [])

    def upload_to_drive(self, file_path):
        try:
            drive_service = build("drive", "v3", credentials=self.creds)
            file_metadata = {"name": os.path.basename(file_path)}

            media = MediaFileUpload(file_path, resumable=True)
            file = (
                drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id,webViewLink")
                .execute()
            )

            drive_service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"},
                fields="id",
            ).execute()

            return file["webViewLink"]
        except Exception:
            traceback.print_exc()
            return None

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
            self.service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )
        return result

    def delete_email(self, msg_id, trash=True):
        if trash:
            return (
                self.service.users().messages().trash(userId="me", id=msg_id).execute()
            )
        else:
            return (
                self.service.users().messages().delete(userId="me", id=msg_id).execute()
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
                self.service.users()
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
                self.service.users()
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
            return self.parse_email_content(message)
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    def get_thread(self, thread_id):
        try:
            thread = (
                self.service.users().threads().get(userId="me", id=thread_id).execute()
            )

            messages = []
            for message in thread.get("messages", []):
                parsed_message = self.parse_email_content(message)
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
                self.service.users()
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
                    email_data = self.parse_email_content(message)
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
