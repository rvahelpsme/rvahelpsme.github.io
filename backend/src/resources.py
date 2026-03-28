import os
import gspread
import google.auth
import traceback
from gspread import authorize


def get_verified_directory():
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not sheet_id:
        print("DEBUG: GOOGLE_SHEET_ID is missing.")
        return []

    try:
        if creds_path and os.path.exists(creds_path):
            if os.path.isdir(creds_path):
                raise IsADirectoryError(f"CRITICAL: {creds_path} is a directory, not a file.")

            print(f"DEBUG: Authenticating via local file: {creds_path}")
            gc = gspread.service_account(filename=creds_path)
        else:
            print("DEBUG: Local credentials not found or empty. Using ambient Cloud authentication...")
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials, project = google.auth.default(scopes=scopes)
            gc = authorize(credentials)

        sh = gc.open_by_key(sheet_id)
        print(f"DEBUG: Successfully opened sheet: {sh.title}")

        raw_rows = sh.get_worksheet(0).get_all_records()

        verified = []
        for row in raw_rows:
            cleaned_row = {}
            has_data = False

            for key, value in row.items():
                clean_key = str(key).strip()
                if not clean_key:
                    continue

                if isinstance(value, str):
                    clean_val = value.strip()
                    if clean_val:
                        has_data = True

                    if clean_val.upper() == 'TRUE':
                        cleaned_row[clean_key] = True
                    elif clean_val.upper() == 'FALSE':
                        cleaned_row[clean_key] = False
                    else:
                        cleaned_row[clean_key] = clean_val
                else:
                    if value is not None and str(value).strip() != '':
                        has_data = True
                    cleaned_row[clean_key] = value

            if has_data:
                verified.append(cleaned_row)

        return verified

    except Exception as e:
        print(f"Directory Fetch Error: {repr(e)}")
        print("--- FULL TRACEBACK ---")
        traceback.print_exc()
        print("----------------------")
        return []