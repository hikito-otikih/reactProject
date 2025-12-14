import sqlite3
import json

def clean_database(db_name='places.db', table_name='places'):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"Connected to {db_name}...")

    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
    except sqlite3.OperationalError:
        print(f"Error: Table '{table_name}' not found. Please check your table name.")
        return

    columns = [description[0] for description in cursor.description]
    cat_columns = [col for col in columns if col.startswith('cat_')]
    
    # Flag to determine if we should update categories
    update_categories = False

    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN categories TEXT")
        print("Added 'categories' column. Will populate it.")
        update_categories = True
    except sqlite3.OperationalError:
        print("'categories' column already exists. Skipping category aggregation; only updating openingHours.")
        update_categories = False

    cursor.execute(f"SELECT rowid, * FROM {table_name}")
    rows = cursor.fetchall()

    updates = []

    print("Processing rows...")
    for row in rows:
        # 1. Always process openingHours
        opening_hours = row['openingHours']
        if opening_hours and isinstance(opening_hours, str):
            opening_hours = opening_hours.replace('|', ',')
        
        # 2. Only process categories if the column was just created
        if update_categories:
            active_categories = []
            for cat_col in cat_columns:
                if row[cat_col] == 1:
                    clean_name = cat_col.replace('cat_', '')
                    active_categories.append(clean_name)
            categories_str = ",".join(active_categories)
            
            # Tuple structure: (categories, openingHours, rowid)
            updates.append((categories_str, opening_hours, row['rowid']))
        else:
            # Tuple structure: (openingHours, rowid)
            updates.append((opening_hours, row['rowid']))

    if not updates:
        print("No rows to update.")
        conn.close()
        return

    print(f"Updating {len(updates)} rows...")
    
    # 3. Execute the appropriate query based on the flag
    if update_categories:
        cursor.executemany(f"""
            UPDATE {table_name} 
            SET categories = ?, 
                openingHours = ? 
            WHERE rowid = ?
        """, updates)
    else:
        cursor.executemany(f"""
            UPDATE {table_name} 
            SET openingHours = ? 
            WHERE rowid = ?
        """, updates)

    conn.commit()
    conn.close()
    print("Done! Database updated.")

def delete_category_columns(db_name='places.db', table_name='places'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print(f"Checking columns in '{table_name}'...")

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    
    all_columns = [col[1] for col in columns_info]

    columns_to_drop = [col for col in all_columns if col.startswith('cat_')]

    if not columns_to_drop:
        print("No columns starting with 'cat_' were found.")
        conn.close()
        return

    print(f"Found {len(columns_to_drop)} columns to delete: {columns_to_drop}")
    
    try:
        for col in columns_to_drop:
            print(f"Dropping column: {col}")
            cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {col}")
        
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

def refactor_and_fill(db_name, table_name='places'):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()

    print(f"Connected to {db_name}...")

    print("Filling missing ratings with 3...")
    cursor.execute(f"""
        UPDATE {table_name} 
        SET rating = 3 
        WHERE rating IS NULL OR rating = ''
    """)
    print(f"Ratings updated. (Rows affected: {cursor.rowcount})")

    print("Refactoring openingHours to JSON...")
    
    cursor.execute(f"SELECT rowid, openingHours FROM {table_name}")
    rows = cursor.fetchall()

    updates = []

    for row in rows:
        raw_hours = row['openingHours']
        
        if not raw_hours:
            continue
            
        if raw_hours.strip().startswith('{'):
            continue

        try:
            days_list = raw_hours.split(',')
            schedule_dict = {}
            
            for day_segment in days_list:
                if ':' in day_segment:
                    day, time = day_segment.split(':', 1)
                    clean_day = day.strip()
                    clean_time = time.strip().replace('\u202f', ' ') 
                    schedule_dict[clean_day] = clean_time
            
            if schedule_dict:
                json_output = json.dumps(schedule_dict, ensure_ascii=False)
                updates.append((json_output, row['rowid']))
                
        except Exception as e:
            print(f"Skipping row {row['rowid']} due to error: {e}")

    if updates:
        print(f"Updating openingHours for {len(updates)} rows...")
        cursor.executemany(f"UPDATE {table_name} SET openingHours = ? WHERE rowid = ?", updates)
    else:
        print("No openingHours needed updating.")

    conn.commit()
    conn.close()
    print("Done! Database updated.")

# --- RUN THE FUNCTION ---
# REPLACE 'places' BELOW WITH YOUR ACTUAL TABLE NAME IF IT IS DIFFERENT
clean_database(db_name='result/places.db', table_name='places')
# delete_category_columns(db_name='result/places.db', table_name='places')
refactor_and_fill(db_name='result/places.db', table_name='places')