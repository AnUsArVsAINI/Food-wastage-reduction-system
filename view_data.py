"""
view_data.py  –  Shows all data in the FoodBridge SQLite database.
Run:  python view_data.py
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "food_waste.db")
con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row

TABLES = ["users", "food_listings", "food_requests"]

for table in TABLES:
    rows = con.execute(f"SELECT * FROM {table}").fetchall()
    sep  = "=" * 70
    print(f"\n{sep}")
    print(f"  TABLE: {table.upper()}  ({len(rows)} row{'s' if len(rows) != 1 else ''})")
    print(sep)

    if rows:
        cols = rows[0].keys()
        # header row
        print("  " + " | ".join(f"{str(c):<20}" for c in cols))
        print("  " + "-" * 68)
        for r in rows:
            print("  " + " | ".join(f"{str(r[c]):<20}" for c in cols))
    else:
        print("  (no data yet)")

con.close()
print("\n" + "=" * 70)
print("  Database path:", DB_PATH)
print("=" * 70)
