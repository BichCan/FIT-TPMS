"""
Chạy file này MỘT LẦN để thêm các cột mới vào bảng lecturers.
Lệnh: python setup_supervisor_columns.py
"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "FIT-TPMS.db"

def add_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    new_columns = [
        ("photo_url",           "TEXT"),          # Đường dẫn ảnh: /static/images/lecturers/ten.jpg
        ("position",            "TEXT"),          # Chức danh: "Giảng viên cao cấp & Trưởng nhóm nghiên cứu"
        ("specialization",      "TEXT"),          # Chuyên môn chính hiển thị trên card
        ("research_interests",  "TEXT"),          # Hashtag, phân cách bằng dấu phẩy: "#AI,#BigData,#IoT"
        ("awards",              "TEXT"),          # Giải thưởng học thuật
        ("office",              "TEXT"),          # Phòng làm việc: "Phòng 402, Nhà B1"
    ]

    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE lecturers ADD COLUMN {col_name} {col_type}")
            print(f"[OK] Đã thêm cột: {col_name}")
        except sqlite3.OperationalError as e:
            print(f"[SKIP] {col_name}: {e}")

    conn.commit()
    conn.close()
    print("\nHoàn thành! Bây giờ hãy chạy fill_supervisor_data.py để nhập dữ liệu.")

if __name__ == "__main__":
    add_columns()
