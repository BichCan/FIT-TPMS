"""
Chỉnh sửa dữ liệu bên dưới rồi chạy file này để cập nhật thông tin giảng viên.
Lệnh: python fill_supervisor_data.py

Danh sách giảng viên hiện có trong DB:
  ID=1  | Quản trị viên
  ID=2  | TS. Nguyễn Văn E      | faculty=KHDL
  ID=3  | PGS.TS. Trần Văn F   | faculty=KHMT
  ID=4  | ThS. Lê Thị G         | faculty=CNPM
  ID=5  | TS. Phạm Văn H        | faculty=MMT
  ID=6  | Phạm Thảo             | faculty=KHMT
  ID=7  | TS. Tống Thị Hảo Tâm | faculty=HTTT
  ID=8  | ThS. Tống Thị Minh Ngọc | faculty=CNPM
  ID=9  | ThS. Trần Thị Mỹ Diệp | faculty=KHDL
  ID=10 | TS. Đặng Minh Quân   | faculty=KHMT
  ID=11 | TS. Lưu Minh Tuấn    | faculty=MMT
  ID=12 | TS. Phạm Xuân Lâm    | faculty=HTTT
  ID=13 | ThS. Cao Thị Thu Hương | faculty=CNPM
  ID=14 | TS. Nguyễn Thanh Hương | faculty=KHDL
  ID=15 | TS. Phạm Minh Hoàn   | faculty=KHMT

Lưu ý ảnh:
  - Đặt ảnh vào thư mục: static/images/lecturers/
  - Đặt tên file ảnh tùy ý, ví dụ: nguyen_van_e.jpg
  - Điền đường dẫn vào photo_url: /static/images/lecturers/nguyen_van_e.jpg
  - Nếu chưa có ảnh, để giá trị None (sẽ dùng ảnh mặc định)
"""

import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = "FIT-TPMS.db"

# ================================================================
# ĐIỀN DỮ LIỆU THẬT CỦA TỪNG GIẢNG VIÊN VÀO ĐÂY
# Sao chép và chỉnh sửa từng dòng theo đúng ID
# ================================================================

SUPERVISOR_DATA = [
    {
        "id": 2,
        "photo_url": "/static/images/lecturers/lam.jpg",   # Đổi tên file ảnh thật
        "position": "Trưởng khoa",                                    # Chức danh
        "specialization": "Khoa học dữ liệu",                       # Chuyên môn chính
        "bio": " 2012 - 2017: Tiến sỹ Khoa học máy tính , Đại học Quốc Lập Trung Ương Đài Loan \n - 2007 - 2009: Thạc sỹ Công nghệ thông tin, Đại học Bách Khoa Hà Nội \n - 2001 -2006: Kỹ sư Công nghệ thông tin, Đại học Bách Khoa Hà Nội",
        "research_interests": "#DCông nghệ giáo dục,#MachineLearning,#Analytics",  # Hashtag, cách nhau bởi dấu phẩy
        "awards": "Chu Văn Huy, Phạm Xuân Lâm, Lê Quang Minh, Trần Đức Minh (2025).Improving the efficiency of Sentiment Analysis System based on intergration with RPA and KBS \n Phạm Xuân Lâm, Nguyễn Đức Thuận, Nguyễn Lê Ngọc Hà (2025).Đề xuất hệ thống hỗ trợ học tập theo nguyên tắc kiến tạo dựa trên nền tảng Google Codelabs",                                               # Để None nếu không có giải thưởng
        "office": "Số điện thoại: 0937638683 \n Email: lampx@neu.edu.vn",
    },
    {
        "id": 3,
        "photo_url": "/static/images/lecturers/nam.jpg",
        "position": "Thạc sĩ",
        "specialization": "Mạng máy tính",
        "bio": "PGS.TS. với hơn 20 năm kinh nghiệm nghiên cứu và giảng dạy về mạng máy tính và bảo mật.",
        "research_interests": "#NetworkSecurity,#IoT,#CloudComputing",
        "awards": "Giải thưởng Nhà khoa học tiêu biểu 2022",
        "office": "Phòng 402, Nhà B1, Khoa CNTT",
    },
    {
        "id": 4,
        "photo_url": "/static/images/lecturers/thao.jpg",
        "position": "Thạc sĩ, Giảng viên",
        "specialization": "Công nghệ phần mềm",
        "bio": "Chuyên gia về kỹ thuật phần mềm và phát triển ứng dụng web hiện đại.",
        "research_interests": "#SoftwareEngineering,#WebDev,#Agile",
        "awards": None,
        "office": "Phòng 205, Nhà A2, Khoa CNTT",
    },
    {
        "id": 5,
        "photo_url": "/static/images/lecturers/tam.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Mạng máy tính & Truyền thông",
        "bio": "Chuyên gia về hệ thống mạng, bảo mật và các công nghệ truyền thông hiện đại.",
        "research_interests": "#Networking,#Wireless,#5G",
        "awards": None,
        "office": "Phòng 310, Nhà B2, Khoa CNTT",
    },
    {
        "id": 6,
        "photo_url": "/static/images/lecturers/thien.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Khoa học máy tính",
        "bio": "Nghiên cứu và giảng dạy các lĩnh vực cốt lõi của khoa học máy tính.",
        "research_interests": "#ComputerScience,#Algorithms,#AI",
        "awards": None,
        "office": "Phòng 401, Nhà B1, Khoa CNTT",
    },
    {
        "id": 7,
        "photo_url": "/static/images/lecturers/viet.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Hệ thống thông tin",
        "bio": "Chuyên gia về hệ thống thông tin doanh nghiệp và quản trị dữ liệu.",
        "research_interests": "#InformationSystems,#ERP,#DataManagement",
        "awards": None,
        "office": "Phòng 202, Nhà A1, Khoa CNTT",
    },
    {
        "id": 8,
        "photo_url": "/static/images/lecturers/thang.png",
        "position": "Thạc sĩ, Giảng viên",
        "specialization": "Công nghệ phần mềm",
        "bio": "Chuyên về kiểm thử phần mềm, đảm bảo chất lượng và phát triển phần mềm agile.",
        "research_interests": "#SoftwareTesting,#QA,#Agile",
        "awards": None,
        "office": "Phòng 206, Nhà A2, Khoa CNTT",
    },
    {
        "id": 9,
        "photo_url": "/static/images/lecturers/diep.jpg",
        "position": "Thạc sĩ, Giảng viên",
        "specialization": "Khoa học dữ liệu",
        "bio": "Nghiên cứu về phân tích dữ liệu lớn, học máy và khai phá dữ liệu.",
        "research_interests": "#BigData,#DataMining,#Visualization",
        "awards": None,
        "office": "Phòng 302, Nhà A1, Khoa CNTT",
    },
    {
        "id": 10,
        "photo_url": "/static/images/lecturers/quan.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Khoa học máy tính",
        "bio": "Nghiên cứu chuyên sâu về thuật toán, lý thuyết tính toán và trí tuệ nhân tạo.",
        "research_interests": "#Algorithms,#AI,#DeepLearning",
        "awards": None,
        "office": "Phòng 403, Nhà B1, Khoa CNTT",
    },
    {
        "id": 11,
        "photo_url": "/static/images/lecturers/tuan.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Mạng máy tính",
        "bio": "Chuyên gia về mạng không dây, Internet vạn vật (IoT) và bảo mật mạng.",
        "research_interests": "#IoT,#WirelessNetwork,#NetworkSecurity",
        "awards": None,
        "office": "Phòng 311, Nhà B2, Khoa CNTT",
    },
    {
        "id": 12,
        "photo_url": "/static/images/lecturers/kien.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Hệ thống thông tin",
        "bio": "Nghiên cứu về hệ thống phân tán, điện toán đám mây và kiến trúc phần mềm.",
        "research_interests": "#DistributedSystems,#CloudComputing,#Microservices",
        "awards": None,
        "office": "Phòng 203, Nhà A1, Khoa CNTT",
    },
    {
        "id": 13,
        "photo_url": "/static/images/lecturers/huong.png",
        "position": "Thạc sĩ, Giảng viên",
        "specialization": "Công nghệ phần mềm",
        "bio": "Chuyên về lập trình hướng đối tượng, thiết kế phần mềm và các công nghệ web.",
        "research_interests": "#OOP,#WebTechnology,#SoftwareDesign",
        "awards": None,
        "office": "Phòng 207, Nhà A2, Khoa CNTT",
    },
    {
        "id": 14,
        "photo_url": "/static/images/lecturers/thuong.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Khoa học dữ liệu",
        "bio": "Nghiên cứu về học máy, xử lý ngôn ngữ tự nhiên và phân tích dữ liệu.",
        "research_interests": "#MachineLearning,#NLP,#DataAnalysis",
        "awards": None,
        "office": "Phòng 303, Nhà A1, Khoa CNTT",
    },
    {
        "id": 15,
        "photo_url": "/static/images/lecturers/hoan.jpg",
        "position": "Tiến sĩ, Giảng viên",
        "specialization": "Khoa học máy tính",
        "bio": "Chuyên gia về mật mã học, bảo mật thông tin và an toàn hệ thống.",
        "research_interests": "#Cryptography,#InfoSecurity,#SystemSecurity",
        "awards": None,
        "office": "Phòng 404, Nhà B1, Khoa CNTT",
    },
]

# ================================================================

def fill_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updated = 0
    for sv in SUPERVISOR_DATA:
        cursor.execute("""
            UPDATE lecturers SET
                photo_url           = ?,
                position            = ?,
                specialization      = ?,
                bio                 = ?,
                research_interests  = ?,
                awards              = ?,
                office              = ?
            WHERE id = ?
        """, (
            sv["photo_url"],
            sv["position"],
            sv["specialization"],
            sv["bio"],
            sv["research_interests"],
            sv["awards"],
            sv["office"],
            sv["id"],
        ))
        updated += cursor.rowcount
        print(f"[OK] ID={sv['id']} cập nhật xong")
    conn.commit()
    conn.close()
    print(f"\nHoàn thành! Đã cập nhật {updated} giảng viên.")

if __name__ == "__main__":
    fill_data()
