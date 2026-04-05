from flask import render_template, request
from app.database import get_db
from app.supervisor import supervisor_bp

FACULTY_MAP = {
    'HTTT': 'Hệ thống thông tin',
    'KHMT': 'Khoa học máy tính',
    'CNPM': 'Công nghệ phần mềm',
    'MMT':  'Mạng máy tính',
    'KHDL': 'Khoa học dữ liệu',
}

@supervisor_bp.route("/giang-vien")
def supervisors():
    q = request.args.get("q", "").strip()
    conn = get_db()

    sql = """
        SELECT l.id, u.full_name, u.email, u.phone,
               l.faculty, l.degree, l.specialization,
               l.photo_url, l.position
        FROM lecturers l
        JOIN users u ON l.user_id = u.id
        WHERE l.is_active = 1 AND l.id != 1
    """
    params = []
    if q:
        sql += " AND (u.full_name LIKE ? OR l.specialization LIKE ? OR l.faculty LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    sql += " ORDER BY u.full_name"

    lecturers = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template("supervisors.html",
                           lecturers=lecturers,
                           faculty_map=FACULTY_MAP,
                           q=q)


@supervisor_bp.route("/giang-vien/<int:lecturer_id>")
def supervisor_detail(lecturer_id):
    conn = get_db()
    lecturer = conn.execute("""
        SELECT l.id, u.full_name, u.email, u.phone,
               l.faculty, l.degree, l.specialization,
               l.photo_url, l.position, l.research_interests,
               l.awards, l.office, l.bio
        FROM lecturers l
        JOIN users u ON l.user_id = u.id
        WHERE l.id = ?
    """, (lecturer_id,)).fetchone()
    conn.close()

    if not lecturer:
        return "Không tìm thấy giảng viên", 404

    return render_template("supervisor_detail.html",
                           lecturer=lecturer,
                           faculty_map=FACULTY_MAP)
