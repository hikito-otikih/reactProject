import sqlite3

# 1. KẾT NỐI (Tự động tạo file 'my_places.db' nếu chưa có)
conn = sqlite3.connect('my_places.db')

# 2. TẠO CON TRỎ
cursor = conn.cursor()

# 3. KẺ BẢNG (SCHEMA)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS places (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL
    )
''')

# 4. THÊM DỮ LIỆU (INSERT)
# Dữ liệu mẫu
data = [
    ("Salon Anh Pước", "375 Lê Văn Thọ", 10.8507, 106.6563),
    ("Chợ Bến Thành", "Quận 1", 10.7725, 106.6980)
]

cursor.executemany('''
    INSERT INTO places (name, address, latitude, longitude)
    VALUES (?, ?, ?, ?)
''', data)

# # 5. COMMIT (LƯU XUỐNG Ổ CỨNG) -> Không có dòng này là mất hết!
conn.commit()

# 6. ĐÓNG KẾT NỐI
conn.close()

print("Đã tạo file my_places.db thành công!")