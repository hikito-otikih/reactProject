import sqlite3
import os

def merge_to_new_db(db1_path, db2_path, output_path):
    """
    Merges two databases into a NEW file, keeping only common tables and common columns.
    """
    # Remove output file if it exists to start fresh
    if os.path.exists(output_path):
        os.remove(output_path)

    # Connect to the NEW database
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()

    try:
        print(f"Creating new database: {output_path}")
        
        # Attach the two source databases
        # We use 'db1' and 'db2' as aliases for the SQL queries
        cursor.execute(f"ATTACH DATABASE '{db1_path}' AS db1")
        cursor.execute(f"ATTACH DATABASE '{db2_path}' AS db2")

        # 1. Find Common Tables
        cursor.execute("SELECT name FROM db1.sqlite_master WHERE type='table'")
        tables1 = set(row[0] for row in cursor.fetchall())
        
        cursor.execute("SELECT name FROM db2.sqlite_master WHERE type='table'")
        tables2 = set(row[0] for row in cursor.fetchall())

        common_tables = tables1.intersection(tables2)
        print(f"Found {len(common_tables)} common tables: {common_tables}")

        for table in common_tables:
            if table.startswith('sqlite_'): continue

            # 2. Find Common Columns for each table
            cursor.execute(f"PRAGMA db1.table_info({table})")
            cols1_info = {row[1]: row[2] for row in cursor.fetchall()} # Dictionary of Name: Type
            
            cursor.execute(f"PRAGMA db2.table_info({table})")
            cols2_names = set(row[1] for row in cursor.fetchall())

            # intersection of column names
            common_cols = set(cols1_info.keys()).intersection(cols2_names)
            
            if not common_cols:
                print(f"  - Skipping table '{table}': No common columns found.")
                continue

            # Sort columns to ensure consistent order
            sorted_cols = sorted(list(common_cols))
            cols_string = ", ".join(f'"{c}"' for c in sorted_cols)
            
            # 3. Create Table in New DB
            # We construct a CREATE TABLE statement using the types from db1
            col_defs = ", ".join(f'"{col}" {cols1_info[col]}' for col in sorted_cols)
            create_query = f"CREATE TABLE main.{table} ({col_defs})"
            cursor.execute(create_query)
            
            print(f"  - Processing table '{table}'...")
            print(f"    - Merging {len(sorted_cols)} columns.")

            # 4. Insert Data from DB1
            # INSERT OR IGNORE handles duplicate IDs gracefully
            cursor.execute(f"INSERT OR IGNORE INTO main.{table} ({cols_string}) SELECT {cols_string} FROM db1.{table}")
            
            # 5. Insert Data from DB2
            cursor.execute(f"INSERT OR IGNORE INTO main.{table} ({cols_string}) SELECT {cols_string} FROM db2.{table}")
            
            # Check row count
            cursor.execute(f"SELECT count(*) FROM main.{table}")
            count = cursor.fetchone()[0]
            print(f"    - Total rows in merged table: {count}")

        conn.commit()
        print("\nMerge completed successfully.")

    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    finally:
        if conn:
            conn.close()

# --- Execution ---
if __name__ == "__main__":
    # Adjust filenames as needed
    merge_to_new_db(
        db1_path='result/google_places.db', 
        db2_path='result/enhance.db', 
        output_path='result/enhanced_google_places.db'
    )