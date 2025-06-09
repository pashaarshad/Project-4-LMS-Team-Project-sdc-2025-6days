from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from database.db_config import get_database_connection, init_database
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key

@app.route('/')
@app.route('/login')
def login():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        
        connection = get_database_connection()
        if connection:
            try:
                cursor = connection.cursor()
                
                # Check if email already exists
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already exists!')
                    return redirect(url_for('signup'))
                
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (fullname, email, phone)
                    VALUES (%s, %s, %s)
                """, (name, email, phone))
                
                connection.commit()
                flash('Registration successful! Please login.')
                return redirect(url_for('login'))
                
            except Error as e:
                flash('Registration failed!')
                print(f"Error: {e}")
            finally:
                cursor.close()
                connection.close()
        
    return render_template('signup.html')

@app.route('/forget-password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form['email']
        connection = get_database_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user:
                # Generate reset token and expiry
                reset_token = secrets.token_hex(16)
                reset_token_expiry = datetime.now() + timedelta(hours=1)
                
                # Update user record with reset token
                cursor.execute("""
                    UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE email = %s
                """, (reset_token, reset_token_expiry, email))
                connection.commit()
                
                # Simulate sending email (replace with actual email logic)
                print(f"Password reset link: http://localhost:5000/reset-password/{reset_token}")
                flash('Password reset link has been sent to your email.')
            else:
                flash('Email not found.')
            
            cursor.close()
            connection.close()
        else:
            flash('Database connection error.')
    
    return render_template('forget-password.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form['email']
    password = request.form['password']
    
    # Check if password is '123' for students
    if password != '123':
        flash('Invalid password. Please use 123 as password.')
        return redirect(url_for('login'))
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s AND is_admin = 0", (email,))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['fullname'] = user['fullname']
                flash(f"Welcome, {user['fullname']}!")
                return render_template('dashboard.html', fullname=user['fullname'])
            
            flash('Invalid email address.')
            return redirect(url_for('login'))
            
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('login'))

@app.route('/admin-login', methods=['POST'])
def admin_login():
    email = request.form['admin_email']
    password = request.form['admin_password']
    
    if email == 'admin@gmail.com' and password == 'admin':
        session['is_admin'] = True
        session['email'] = email
        session['fullname'] = 'Administrator'
        flash('Welcome, Administrator!')
        return redirect(url_for('admin_dashboard'))  # This will now work
    
    flash('Invalid admin credentials')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')  # Add this new route
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Access denied. Admins only.')
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', fullname=session.get('fullname'))

@app.route('/admin/add-member', methods=['POST'])
def add_member():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO users (fullname, email, phone)
                VALUES (%s, %s, %s)
            """, (data['fullname'], data['email'], data['phone']))
            
            connection.commit()
            return {'success': True}, 200
        except Exception as e:
            print(f"Error adding member: {e}")
            return {'error': str(e)}, 500
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-members')
def get_members():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, fullname, email, phone 
            FROM users 
            WHERE is_admin = 0
            ORDER BY id
        """)
        members = cursor.fetchall()
        cursor.close()
        connection.close()
        return {'members': members}
    return {'error': 'Database error'}, 500

@app.route('/admin/edit-member/<int:member_id>', methods=['GET'])
def get_member(member_id):
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, fullname, email, phone FROM users WHERE id = %s", (member_id,))
            member = cursor.fetchone()
            return {'success': True, 'member': member} if member else {'error': 'Member not found'}, 404
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/update-member', methods=['POST'])
def update_member():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET fullname = %s, email = %s, phone = %s
                WHERE id = %s
            """, (data['fullname'], data['email'], data['phone'], data['id']))
            connection.commit()
            return {'success': True}, 200
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/delete-member/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s AND is_admin = 0", (member_id,))
            connection.commit()
            return {'success': True}, 200
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/books', methods=['GET'])
def get_books():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT book_id, title, author, category, available 
                FROM books 
                ORDER BY book_id
            """)
            books = cursor.fetchall()
            return {'books': books}
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-book-stats')
def get_book_stats():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_books,
                    SUM(available) as available_books
                FROM books
            """)
            stats = cursor.fetchone()
            return {'total_books': stats['total_books'], 
                    'total_available': stats['available_books']}
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/add-book', methods=['POST'])
def add_book():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO books (title, author, category, available)
                VALUES (%s, %s, %s, %s)
            """, (data['title'], data['author'], data['category'], data['available']))
            connection.commit()
            return {'success': True}, 200
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/edit-book/<int:book_id>')
def get_book(book_id):
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT book_id, title, author, category, available 
                FROM books WHERE book_id = %s
            """, (book_id,))
            book = cursor.fetchone()
            return {'success': True, 'book': book} if book else {'error': 'Book not found'}, 404
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/update-book', methods=['POST'])
def update_book():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE books 
                SET title = %s, author = %s, category = %s, available = %s
                WHERE book_id = %s
            """, (data['title'], data['author'], data['category'], 
                  data['available'], data['book_id']))
            connection.commit()
            return {'success': True}, 200
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/delete-book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
            connection.commit()
            return {'success': True}, 200
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_database()
    app.run(debug=True)
