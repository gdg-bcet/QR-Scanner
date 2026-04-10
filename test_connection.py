"""Quick test to verify Google Sheets connection."""
from sheets_db import SheetsDB

db = SheetsDB()
stats = db.get_stats()
print(f"Total: {stats['total']}, Taken: {stats['taken']}, Remaining: {stats['remaining']}")
records = db.get_all_records()
if records:
    r = records[0]
    print(f"First person: {r['name']} ({r['token_id']}) - Size: {r['tshirt_size']}")
else:
    print("No records found!")
