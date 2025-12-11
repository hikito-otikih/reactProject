import sqlite3

def clean_database(db_name='places.db', table_name='places'):
    # Connect to the database
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    cursor = conn.cursor()

    print(f"Connected to {db_name}...")

    # 1. Get all column names from the table
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
    except sqlite3.OperationalError:
        print(f"Error: Table '{table_name}' not found. Please check your table name.")
        return

    columns = [description[0] for description in cursor.description]
    
    # Identify category columns (starting with 'cat_')
    # We will strip 'cat_' from the name for the final string (e.g., 'cat_hotel' -> 'hotel')
    cat_columns = [col for col in columns if col.startswith('cat_')]
    print(f"Found {len(cat_columns)} category columns: {cat_columns}")

    # 2. Create the new 'categories' column if it doesn't exist
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN categories TEXT")
        print("Added 'categories' column.")
    except sqlite3.OperationalError:
        print("'categories' column already exists. Updating existing data.")

    # 3. Fetch all data to process
    # We select rowid to ensure we can update the exact specific row later
    cursor.execute(f"SELECT rowid, * FROM {table_name}")
    rows = cursor.fetchall()

    updates = []

    print("Processing rows...")
    for row in rows:
        # --- TASK 1: Merge Categories ---
        active_categories = []
        for cat_col in cat_columns:
            # Check if the column is 1 (true)
            if row[cat_col] == 1:
                # Remove 'cat_' prefix for a cleaner name (e.g. 'cat_tourism' -> 'tourism')
                clean_name = cat_col.replace('cat_', '')
                active_categories.append(clean_name)
        
        # Join with comma
        categories_str = ",".join(active_categories)

        # --- TASK 2: Replace '|' in openingHours ---
        opening_hours = row['openingHours']
        if opening_hours and isinstance(opening_hours, str):
            opening_hours = opening_hours.replace('|', ',')
        
        # Store the update tuple: (new_categories, new_hours, row_id)
        updates.append((categories_str, opening_hours, row['rowid']))

    # 4. Execute Bulk Update
    # We use rowid to be safe regardless of what your primary key is called
    print(f"Updating {len(updates)} rows...")
    cursor.executemany(f"""
        UPDATE {table_name} 
        SET categories = ?, 
            openingHours = ? 
        WHERE rowid = ?
    """, updates)

    conn.commit()
    conn.close()
    print("Done! Database updated.")

def delete_category_columns(db_name='places.db', table_name='places'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print(f"Checking columns in '{table_name}'...")

    # 1. Get list of all columns in the table
    # We use PRAGMA because SELECT * LIMIT 0 doesn't always work for schema inspection inside scripts easily
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    
    # Extract column names (the name is the second element in the tuple)
    all_columns = [col[1] for col in columns_info]

    # 2. Filter for columns starting with 'cat_'
    columns_to_drop = [col for col in all_columns if col.startswith('cat_')]

    if not columns_to_drop:
        print("No columns starting with 'cat_' were found.")
        conn.close()
        return

    print(f"Found {len(columns_to_drop)} columns to delete: {columns_to_drop}")
    
    # 3. Loop through and drop them
    try:
        for col in columns_to_drop:
            print(f"Dropping column: {col}")
            cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {col}")
        
        # 4. Optimize the database file size after deletion
        print("Optimizing database size (VACUUM)...")
        cursor.execute("VACUUM")
        
        conn.commit()
        print("Success! All 'cat_' columns have been deleted.")

    except sqlite3.OperationalError as e:
        print(f"\n❌ Error: {e}")
        if "near \"DROP\": syntax error" in str(e):
            print("Your SQLite version is too old to support 'DROP COLUMN'.")
    finally:
        conn.close()

# --- RUN THE FUNCTION ---
# REPLACE 'places' BELOW WITH YOUR ACTUAL TABLE NAME IF IT IS DIFFERENT
# clean_database(db_name='result/places.db', table_name='places')
delete_category_columns(db_name='result/places.db', table_name='places')
