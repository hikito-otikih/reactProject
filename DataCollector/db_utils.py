"""Database utility functions for querying places"""
import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(SCRIPT_DIR, 'result')

def search_by_name(name, exact=True, limit=10):
    """Search for places by name with fuzzy matching support
    
    Args:
        name: The name to search for
        exact: If True, search for exact match. If False, fuzzy search
        limit: Maximum number of results to return (only for fuzzy search)
    
    Returns:
        List of rowids matching the query
    """
    db_path = os.path.join(RESULT_DIR, 'places.db')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        if exact:
            cursor.execute("SELECT rowid FROM places WHERE Name = ?", (name,))
            return [row[0] for row in cursor.fetchall()]

        # Split search term into keywords for better matching
        keywords = name.lower().split()

        # Build query to match any keyword
        conditions = []
        params = []
        for keyword in keywords:
            conditions.append("LOWER(Name) LIKE ?")
            params.append(f"%{keyword}%")

        query = f"SELECT rowid FROM places WHERE {' OR '.join(conditions)} LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [row[0] for row in cursor.fetchall()]

def search_by_category(category, limit=10):
    """Search for places by category
    
    Args:
        category: Category to search for (e.g., 'restaurant', 'cafe')
        limit: Maximum number of results
    
    Returns:
        List of rowids for matching places
    """
    db_path = os.path.join(RESULT_DIR, 'places.db')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT rowid FROM places WHERE Categories LIKE ? LIMIT ?",
            (f"%{category}%", limit)
        )
        return [row[0] for row in cursor.fetchall()]

def get_all_places():
    """Get all places from database
    
    Returns:
        List of all rowids
    """
    db_path = os.path.join(RESULT_DIR, 'places.db')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid FROM places")
        return [row[0] for row in cursor.fetchall()]

if __name__ == "__main__":
    # Test search by name
    print("🔍 Searching for 'Starbucks' (exact match)...")
    result = search_by_name("Starbucks", exact=True)
    if result:
        print(f"✅ Found rowids: {result}")
    else:
        print("❌ No exact match found.")
    
    print("\n🔍 Searching for 'coffee' (fuzzy match)...")
    results = search_by_name("coffee", exact=False, limit=5)
    if results:
        print(f"✅ Found {len(results)} result(s): {results}")
    else:
        print("❌ No fuzzy matches found.")