"""
Google Sheets Database Interface for T-Shirt Distribution System
Uses gspread with service account authentication.
Implements in-memory caching to respect Sheets API rate limits.
"""

import gspread
from google.oauth2.service_account import Credentials
import hashlib
import time
import logging
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv
import json

load_dotenv()

logger = logging.getLogger("sheets_db")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Google Sheets API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet column headers (0-indexed)
COL_MARK = 1          # A: Mark
COL_NAME = 2          # B: User Name
COL_EMAIL = 3         # C: User Email
COL_PROFILE_URL = 4   # D: Google Cloud Skills Boost Profile URL
COL_DEPARTMENT = 5    # E: Department
COL_GRAD_YEAR = 6     # F: Graduation Year
COL_TSHIRT_SIZE = 7   # G: T-Shirt size


def generate_token(profile_url: str) -> str:
    """Generate a short, deterministic token from a profile URL."""
    return hashlib.sha256(profile_url.strip().encode()).hexdigest()[:12].upper()


class SheetsDB:
    """Google Sheets database wrapper with caching."""

    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.sheet_name = os.getenv("SHEET_NAME", "Sheet1")

        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID not set in .env")

        # Authenticate (Prioritize Environment Variable for Render, fallback to local file)
        google_creds_json = os.getenv("GOOGLE_CREDENTIALS")

        if google_creds_json:
            try:
                creds_info = json.loads(google_creds_json)
                credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
            except json.JSONDecodeError:
                raise ValueError("GOOGLE_CREDENTIALS env var is not valid JSON")
        else:
            creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
            if not os.path.exists(creds_path):
                raise ValueError("GOOGLE_CREDENTIALS env var not set AND credentials.json not found.")
            credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

        self.client = gspread.authorize(credentials)

        # Open the sheet
        self.spreadsheet = self.client.open_by_key(self.sheet_id)
        self.worksheet = self.spreadsheet.worksheet(self.sheet_name)

        # Cache
        self._cache: List[Dict] = []
        self._cache_time: float = 0
        self._cache_ttl: float = 15  # seconds

        # Token-to-row mapping (token -> row number in sheet, 1-indexed)
        self._token_map: Dict[str, int] = {}

        logger.info(f"✅ Connected to Google Sheet: {self.sheet_id}")

    def _refresh_cache(self, force: bool = False):
        """Refresh the in-memory cache from Google Sheets."""
        now = time.time()
        if not force and self._cache and (now - self._cache_time) < self._cache_ttl:
            return

        try:
            all_records = self.worksheet.get_all_records()
            self._cache = all_records
            self._cache_time = time.time()

            # Rebuild token map
            self._token_map = {}
            for i, record in enumerate(all_records):
                url = str(record.get("Google Cloud Skills Boost Profile URL", "")).strip()
                if url:
                    token = generate_token(url)
                    # Row in sheet is i + 2 (1-indexed header + data rows)
                    self._token_map[token] = i + 2

            logger.info(f"🔄 Cache refreshed: {len(all_records)} records, {len(self._token_map)} tokens")
        except Exception as e:
            logger.error(f"❌ Failed to refresh cache: {e}")
            raise

    def get_all_records(self) -> List[Dict]:
        """Get all records from the sheet."""
        self._refresh_cache()
        result = []
        for record in self._cache:
            url = str(record.get("Google Cloud Skills Boost Profile URL", "")).strip()
            if not url:
                continue
            token = generate_token(url)
            mark_value = str(record.get("Mark", "")).strip().upper()
            is_taken = mark_value in ("TRUE", "1", "YES")

            result.append({
                "token_id": token,
                "name": str(record.get("User Name", "")),
                "email": str(record.get("User Email", "")),
                "profile_url": url,
                "department": str(record.get("Department", "")),
                "graduation_year": str(record.get("Graduation Year", "")),
                "tshirt_size": str(record.get("T-Shirt size", "")),
                "is_taken": is_taken,
            })
        return result

    def find_by_token(self, token_id: str) -> Optional[Dict]:
        """Find a person by their token ID."""
        self._refresh_cache()
        token_id = token_id.upper()

        for record in self._cache:
            url = str(record.get("Google Cloud Skills Boost Profile URL", "")).strip()
            if not url:
                continue
            if generate_token(url) == token_id:
                mark_value = str(record.get("Mark", "")).strip().upper()
                is_taken = mark_value in ("TRUE", "1", "YES")
                return {
                    "token_id": token_id,
                    "name": str(record.get("User Name", "")),
                    "email": str(record.get("User Email", "")),
                    "profile_url": url,
                    "department": str(record.get("Department", "")),
                    "graduation_year": str(record.get("Graduation Year", "")),
                    "tshirt_size": str(record.get("T-Shirt size", "")),
                    "is_taken": is_taken,
                }
        return None

    def mark_as_taken(self, token_id: str) -> bool:
        """Mark a person's t-shirt as taken in the Google Sheet."""
        self._refresh_cache()
        token_id = token_id.upper()
        row_num = self._token_map.get(token_id)

        if row_num is None:
            logger.warning(f"⚠️ Token {token_id} not found in sheet")
            return False

        try:
            self.worksheet.update_cell(row_num, COL_MARK, "TRUE")
            # Force cache refresh on next read
            self._cache_time = 0
            logger.info(f"✅ Marked row {row_num} as TAKEN (token: {token_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark token {token_id}: {e}")
            return False

    def reset(self, token_id: str) -> bool:
        """Reset a person's t-shirt to not-taken."""
        self._refresh_cache()
        token_id = token_id.upper()
        row_num = self._token_map.get(token_id)

        if row_num is None:
            logger.warning(f"⚠️ Token {token_id} not found for reset")
            return False

        try:
            self.worksheet.update_cell(row_num, COL_MARK, "FALSE")
            self._cache_time = 0
            logger.info(f"🔄 Reset row {row_num} (token: {token_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reset token {token_id}: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get summary statistics."""
        records = self.get_all_records()
        total = len(records)
        taken = sum(1 for r in records if r["is_taken"])
        remaining = total - taken

        # Count by t-shirt size
        by_size: Dict[str, Dict[str, int]] = {}
        for r in records:
            size = r["tshirt_size"] or "Unknown"
            if size not in by_size:
                by_size[size] = {"total": 0, "taken": 0, "remaining": 0}
            by_size[size]["total"] += 1
            if r["is_taken"]:
                by_size[size]["taken"] += 1
            else:
                by_size[size]["remaining"] += 1

        return {
            "total": total,
            "taken": taken,
            "remaining": remaining,
            "by_size": by_size,
        }
