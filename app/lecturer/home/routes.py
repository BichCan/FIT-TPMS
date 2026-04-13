from flask import Blueprint, render_template, request,session,redirect,url_for
from app.database import get_db

lecturer_home_bp = Blueprint(
    'lecturer_home',
    __name__,
    url_prefix='/lecturer'
)


@lecturer_home_bp.route('/home')
def home():
    if 'user_id' not in session or session.get('role') != 'lecturer':
        return redirect(url_for('login.login'))

    user_id = session['user_id']
    
    keyword = request.args.get('q', '')
    course_type = request.args.get('type', '')
    semester_id = request.args.get('semester', '')

    db = get_db()
    cursor = db.cursor()

    # Lấy học kỳ hiện tại làm mặc định nếu không có trong tham số
    cursor.execute("SELECT id FROM semesters WHERE is_current = 1")
    current_sem_row = cursor.fetchone()
    default_semester_id = str(current_sem_row['id']) if current_sem_row else ''
    
    if not semester_id:
        semester_id = default_semester_id

    # Lấy lecturer_id từ user_id trong session
    cursor.execute("SELECT lecturers.id, full_name FROM lecturers JOIN users ON lecturers.user_id = users.id WHERE users.id = ?", (user_id,))
    lecturer = cursor.fetchone()
    
    if not lecturer:
        return "Lecturer not found", 404
        
    lecturer_id = lecturer['id']

    sql = """
        SELECT classes.*, semesters.name AS semester_name, semesters.year AS semester_year,
               ct.type_name AS course_type,
               (SELECT COUNT(*) FROM class_students WHERE class_id = classes.id) as student_count
        FROM classes
        LEFT JOIN semesters ON classes.semester_id = semesters.id
        JOIN courses co ON classes.course_id = co.id
        JOIN course_types ct ON co.course_type_id = ct.id
        WHERE classes.lecturer_id = ?
    """

    params = [lecturer_id]

    if keyword:
        sql += " AND (classes.class_name LIKE ? OR classes.class_code LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])


    if semester_id:
        sql += " AND classes.semester_id = ?"
        params.append(semester_id)

    # Filter by Course Type (DA / KL)
    if course_type == 'de-an':
        sql += " AND ct.id = 1" # Giả định 1 là Đề án, 2 là Khóa luận dựa trên business thông thường
    elif course_type == 'khoa-luan':
        sql += " AND ct.id = 2"

    cursor.execute(sql, params)
    classes = cursor.fetchall()

    cursor.execute("SELECT * FROM semesters")
    semesters = cursor.fetchall()


    return render_template(
        'lecturer/home.html',
        lecturer=lecturer,
        classes=classes,
        semesters=semesters,
        selected_semester=semester_id
    )