"""
Script to extract title and address from places table,
remove Vietnamese tone marks, and create a temp table for fuzzy matching.
"""
import sqlite3
import constant
import unicodedata
import re

def remove_tone_marks(text: str) -> str:
    """
    Remove Vietnamese tone marks (diacritics) from text.
    """
    if not text:
        return ""
    # Normalize to NFD (decomposed form) to separate base characters from diacritics
    text = unicodedata.normalize('NFD', text)
    # Remove combining diacritical marks
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    # Normalize back to NFC (composed form)
    text = unicodedata.normalize('NFC', text)
    return text

def build_places_names_table(db_path: str = constant.original_DB_path, 
                             table_name: str = constant.places_table_name,
                             output_db_path: str = "places_names.db",
                             output_table_name: str = "places_names"):
    """
    Extract title and address from places table, remove tone marks,
    and create a new table for fuzzy matching.
    
    Args:
        db_path: Path to the original places database
        table_name: Name of the places table
        output_db_path: Path to output database
        output_table_name: Name of the output table
    """
    # Connect to original database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch all places with title and address
    cursor.execute(f"SELECT rowid, title, address FROM {table_name}")
    results = cursor.fetchall()
    conn.close()
    
    # Connect to output database
    output_conn = sqlite3.connect(output_db_path)
    output_cursor = output_conn.cursor()
    
    # Create table
    output_cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {output_table_name} (
            place_id INTEGER,
            title TEXT,
            title_no_tone TEXT,
            address TEXT,
            address_no_tone TEXT,
            PRIMARY KEY (place_id)
        )
    """)
    
    # Clear existing data
    output_cursor.execute(f"DELETE FROM {output_table_name}")
    
    # Process and insert data
    for place_id, title, address in results:
        title = title if title else ""
        address = address if address else ""
        
        title_no_tone = remove_tone_marks(title)
        address_no_tone = remove_tone_marks(address)
        
        output_cursor.execute(
            f"INSERT INTO {output_table_name} (place_id, title, title_no_tone, address, address_no_tone) VALUES (?, ?, ?, ?, ?)",
            (place_id, title, title_no_tone, address, address_no_tone)
        )
    
    output_conn.commit()
    output_cursor.close()
    output_conn.close()
    
    print(f"Successfully created {output_table_name} table with {len(results)} entries")
    print(f"Database saved to {output_db_path}")

if __name__ == "__main__":
    build_places_names_table()

