from dotenv import load_dotenv
from resources import get_verified_directory

load_dotenv()

def test_sheet_connection():
    print("Testing Google Sheets Connection...")
    try:
        data = get_verified_directory()
        if data:
            print(f"SUCCESS: Retrieved {len(data)} rows from the Verified Feed.")
            print(f"First Entry: {data[0]}")
        else:
            print("FAILURE: Sheet was reached but returned no data.")
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_sheet_connection()