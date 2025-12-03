"""Add Image_URLs column to existing database"""
import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'result', 'places.db')

print(f"Adding Image_URLs column to {DB_PATH}...")

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(places)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'Image_URLs' in columns:
        print("✅ Image_URLs column already exists!")
    else:
        # Add the column
        cursor.execute("ALTER TABLE places ADD COLUMN Image_URLs TEXT")
        conn.commit()
        print("✅ Image_URLs column added successfully!")
    
    # Show table structure
    cursor.execute("PRAGMA table_info(places)")
    print("\nCurrent table structure:")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")

print("\n✅ Done! You can now run scrape.py")
