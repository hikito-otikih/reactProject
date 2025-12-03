import sqlite3

def getID(place_name):
    conn = sqlite3.connect('category.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM places WHERE name = ?", (place_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None
def getName(place_id):
    conn = sqlite3.connect('category.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM places WHERE id = ?", (place_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

def suggest_place_by_category(category , location1 = None, location2=None):
    conn = sqlite3.connect('category.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM places WHERE category = ?", (category,))
    results = cursor.fetchall()
    conn.close()
    if location1 == None and location2 == None:



if __name__ == "__main__":
