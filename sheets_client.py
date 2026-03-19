"""
Google Sheets client — reads pending rows and marks them done.
Detects column positions by header name automatically.
"""

import os
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from dotenv import load_dotenv

load_dotenv()

SHEET_ID   = os.getenv("SHEET_ID")
SHEET_TAB  = "itenx_blog_content_strategy_60_posts"
CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = "token.pickle"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Map our internal keys to possible header names in the sheet
HEADER_ALIASES = {
    "number":            ["#", "no", "number", "no."],
    "title":             ["blog post", "title", "post title", "blog title", "# blog post"],
    "primary_keyword":   ["primary keyword", "main keyword", "keyword"],
    "secondary_1":       ["secondary keyword 1", "secondary keyword1", "secondary 1", "keyword 2"],
    "secondary_2":       ["secondary keyword 2", "secondary keyword2", "secondary 2", "keyword 3"],
    "secondary_3":       ["secondary keyword 3", "secondary keyword3", "secondary 3", "keyword 4"],
    "priority":          ["priority", "p0", "priority level"],
    "content_type":      ["content type", "type", "post type"],
    "monthly_traffic":   ["est. monthly traffic", "monthly traffic", "traffic", "est monthly traffic"],
    "target_word_count": ["target word count", "word count", "words", "length"],
    "notes":             ["notes", "note", "additional notes", "comments"],
}


class SheetsClient:
    def __init__(self):
        if not SHEET_ID:
            raise ValueError("SHEET_ID is not set in your .env file")
        creds = self._get_credentials()
        gc = gspread.authorize(creds)
        self.sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_TAB)
        self.col_map = self._detect_columns()
        self._ensure_status_column()

    def _get_credentials(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)
            print("   ✅ Google login successful — saved for future runs")

        return creds

    def _detect_columns(self) -> dict:
        """Auto-detect column positions by matching header names."""
        headers = [h.strip().lower() for h in self.sheet.row_values(1)]
        print(f"   Sheet headers detected: {headers}")

        col_map = {}
        for key, aliases in HEADER_ALIASES.items():
            for i, header in enumerate(headers):
                if header in aliases:
                    col_map[key] = i
                    break
            if key not in col_map:
                # Default fallback positions if header not found
                defaults = {
                    "number": 0, "title": 1, "primary_keyword": 2,
                    "secondary_1": 3, "secondary_2": 4, "secondary_3": 5,
                    "priority": 6, "content_type": 7, "monthly_traffic": 8,
                    "target_word_count": 9, "notes": 10,
                }
                col_map[key] = defaults.get(key, 0)

        # Status column goes at the end
        col_map["status"] = len(headers)
        # Check if status column already exists
        for i, h in enumerate(headers):
            if h == "status":
                col_map["status"] = i
                break

        print(f"   Column mapping: {col_map}")
        return col_map

    def _ensure_status_column(self):
        headers = self.sheet.row_values(1)
        status_col = self.col_map["status"]
        if status_col >= len(headers) or headers[status_col].strip().lower() != "status":
            self.sheet.update_cell(1, status_col + 1, "Status")
            print("   (Added 'Status' column to sheet header)")

    def _get(self, row: list, key: str) -> str:
        idx = self.col_map.get(key, 0)
        if idx < len(row):
            return row[idx].strip()
        return ""

    def get_next_pending_row(self) -> dict | None:
        all_rows = self.sheet.get_all_values()
        status_col = self.col_map["status"]

        for i, row in enumerate(all_rows[1:], start=2):
            while len(row) <= status_col:
                row.append("")

            status = row[status_col].strip().lower()
            if status in ("done", "error", "skip", "processing"):
                continue

            title = self._get(row, "title")
            if not title:
                continue

            return {
                "row_index":        i,
                "number":           self._get(row, "number"),
                "title":            title,
                "primary_keyword":  self._get(row, "primary_keyword"),
                "secondary_1":      self._get(row, "secondary_1"),
                "secondary_2":      self._get(row, "secondary_2"),
                "secondary_3":      self._get(row, "secondary_3"),
                "priority":         self._get(row, "priority"),
                "content_type":     self._get(row, "content_type"),
                "monthly_traffic":  self._get(row, "monthly_traffic"),
                "target_word_count":self._get(row, "target_word_count") or "2000",
                "notes":            self._get(row, "notes"),
            }

        return None

    def mark_done(self, row_index: int, sanity_doc_id: str = ""):
        note = f"Done — {sanity_doc_id}" if sanity_doc_id else "Done"
        self.sheet.update_cell(row_index, self.col_map["status"] + 1, note)

    def mark_error(self, row_index: int, error_msg: str):
        self.sheet.update_cell(row_index, self.col_map["status"] + 1, f"Error: {error_msg[:100]}")
