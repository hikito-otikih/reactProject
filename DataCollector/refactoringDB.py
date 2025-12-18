import sqlite3
import pandas as pd

def fix_opening_hours(db_path, table_name='places'):
    conn = sqlite3.connect(db_path)
    print(f"Loading data from {db_path}...")

    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        print(f"Error: {e}")
        conn.close()
        return

    # 1. Define the specific columns we want to merge
    # We generate the names explicitly (0 to 6) to avoid any sorting/regex errors
    pairs_to_remove = []
    
    def format_schedule(row):
        schedule = []
        
        # Iterate through Day 0 (Monday) to Day 6 (Sunday)
        for i in range(7):
            day_col = f"openinghours_{i}_day"
            hour_col = f"openinghours_{i}_hours"
            
            # Check if these columns exist in the database
            if day_col in df.columns and hour_col in df.columns:
                # Add to removal list (for later)
                if i == 0: # Only need to add once
                    pairs_to_remove.append(day_col)
                    pairs_to_remove.append(hour_col)

                day_val = row[day_col]
                hour_val = row[hour_col]
                
                # 2. Check for NULL values (Skip if empty)
                if pd.notna(day_val) and pd.notna(hour_val) and str(day_val).strip() != "" and str(hour_val).strip() != "":
                    schedule.append(f"{day_val}: {hour_val}")
        
        if not schedule:
            return None
            
        return " | ".join(schedule)

    print("Merging opening hours...")
    df['opening_hours'] = df.apply(format_schedule, axis=1)

    # 3. Identify columns to drop (re-verify existence)
    cols_to_drop = []
    for i in range(7):
        d = f"openinghours_{i}_day"
        h = f"openinghours_{i}_hours"
        if d in df.columns: cols_to_drop.append(d)
        if h in df.columns: cols_to_drop.append(h)
    
    if cols_to_drop:
        print(f"Dropping {len(cols_to_drop)} original columns...")
        df.drop(columns=cols_to_drop, inplace=True)

    # 4. Save fixed data
    print("Saving to database...")
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    print("Success! Opening hours fixed.")

if __name__ == "__main__":
    fix_opening_hours('result/enhanced_google_places.db')