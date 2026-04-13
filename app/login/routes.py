from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app.database import get_db
from app.login import login_bp


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        db = get_db()
        cursor = db.cursor() 
        
        print(f"DEBUG LOGIN: Email={username}, Password={password}, Role={role}")
        
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ? AND role = ?', 
                       (username, password, role))
        user = cursor.fetchone()
        
        if user:
            print(f"DEBUG LOGIN: Success! User ID={user['id']}, Found Role={user['role']}")
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['full_name']  # ✅ Sửa: dùng full_name
            session['role'] = user['role']
            
            # ✅ Sửa: So sánh đúng với giá trị trong database
            if user['role'] == 'student':
                return redirect(url_for('registration.registration'))
            elif user['role'] == 'lecturer':
                return redirect(url_for('registrationsmanagement.registrations_management'))
            else:
                flash(f"Đăng nhập thành công với vai trò {user['role']}")
                return redirect(url_for('registration.registration'))
        else:
            flash('Tài khoản hoặc mật khẩu không đúng')
            return render_template('login.html')
    
    return render_template('login.html')


@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))