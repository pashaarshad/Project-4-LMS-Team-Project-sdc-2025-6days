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
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('signup'))

        connection = get_database_connection()
        if connection:
            cursor = connection.cursor()
            
            # Check if email or username already exists
            cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, username))
            if cursor.fetchone():
                flash('Email or username already exists!')
                return redirect(url_for('signup'))

            # Hash password and save user
            hashed_password = generate_password_hash(password)
            try:
                cursor.execute("""
                    INSERT INTO users (fullname, email, phone, username, password)
                    VALUES (%s, %s, %s, %s, %s)
                """, (fullname, email, phone, username, hashed_password))
                connection.commit()
                flash('Registration successful! Please login.')
                return redirect(url_for('login'))
            except Exception as e:
                flash('An error occurred during registration.')
                print(e)
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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_database_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user and check_password_hash(user['password'], password):
                session['username'] = user['username']
                session['fullname'] = user['fullname']
                if username == 'admin':
                    session['is_admin'] = True
                    flash(f"Welcome, {user['fullname']}!")
                    return redirect(url_for('admin_dashboard'))
                else:
                    session['is_admin'] = False
                    # Regular users can be redirected to a different page or shown an error
                    flash('Regular user login is not supported.')
                    return redirect(url_for('login'))
            
            flash('Invalid username or password.')
    
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'username' not in session or not session.get('is_admin', False):
        flash('Access denied. Admins only.')
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', fullname=session['fullname'])

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/admin/add-member', methods=['POST'])
def add_member():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Create user account with username as password
            hashed_password = generate_password_hash(data['username'])  # Using username as initial password
            cursor.execute("""
                INSERT INTO users (username, fullname, email, phone, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['username'], data['fullname'], data['email'], data['phone'], hashed_password))
            
            connection.commit()
            return {'success': True}, 200
        except Exception as e:
            print(f"Error adding member: {e}")
            return {'error': str(e)}, 500
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-member/<int:member_id>')
def get_member(member_id):
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (member_id,))
        member = cursor.fetchone()
        cursor.close()
        connection.close()
        return {'success': True, **member} if member else {'error': 'Member not found'}, 404
    return {'error': 'Database error'}, 500

@app.route('/admin/update-member', methods=['POST'])
def update_member():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET username = %s, fullname = %s, email = %s, phone = %s
                WHERE id = %s
            """, (data['username'], data['fullname'], data['email'], data['phone'], data['id']))
            connection.commit()
            return {'success': True}, 200
        except Exception as e:
            return {'error': str(e)}, 500
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/delete-member/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (member_id,))
            connection.commit()
            return {'success': True}, 200
        except Error as e:
            return {'error': str(e)}, 500
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-members')
def get_members():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, fullname, username, email, phone 
            FROM users 
            WHERE username != 'admin'
        """)
        members = cursor.fetchall()
        cursor.close()
        connection.close()
        return {'members': members}
    return {'error': 'Database error'}, 500

@app.route('/admin/export-members')
def export_members():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            # Get all members data
            query = """
                SELECT username, fullname, email, phone 
                FROM users 
                WHERE username != 'admin'
                ORDER BY fullname
            """
            df = pd.read_sql(query, connection)
            
            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Members', index=False)
                
                # Get workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['Members']
                
                # Add some formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#6B3E99',
                    'font_color': 'white'
                })
                
                # Format the header row
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Adjust columns width
                for idx, col in enumerate(df.columns):
                    worksheet.set_column(idx, idx, max(len(col) + 2, df[col].astype(str).str.len().max()))
            
            # Prepare the output
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='lms_members.xlsx'
            )
            
        except Exception as e:
            print(f"Error exporting members: {e}")
            return {'error': str(e)}, 500
        finally:
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-stats')
def get_stats():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get total members count
            cursor.execute("SELECT COUNT(*) as total FROM users WHERE username != 'admin'")
            total_members = cursor.fetchone()['total']
            
            # For now, returning placeholder values for borrowed and due (you can update these when implementing book management)
            stats = {
                'total_members': total_members,
                'books_borrowed': 0,  # Update when implementing book management
                'due_returns': 0      # Update when implementing book management
            }
            return stats
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-books')
def get_books():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM books 
                ORDER BY created_at DESC
            """)
            books = cursor.fetchall()
            return {'books': books}
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/add-book', methods=['POST'])
def add_book():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO books (book_code, title, author, category, quantity, available)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data['book_code'], data['title'], data['author'], 
                 data['category'], data['quantity'], data['quantity']))
            connection.commit()
            return {'success': True}, 200
        except Exception as e:
            return {'error': str(e)}, 500
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-book/<int:book_id>')
def get_book(book_id):
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
            book = cursor.fetchone()
            return {'success': True, **book} if book else {'error': 'Book not found'}, 404
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/update-book', methods=['POST'])
def update_book():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE books 
                SET book_code = %s, title = %s, author = %s, 
                    category = %s, quantity = %s, available = %s
                WHERE id = %s
            """, (data['book_code'], data['title'], data['author'], 
                  data['category'], data['quantity'], data['available'], data['id']))
            connection.commit()
            return {'success': True}, 200
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/delete-book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
            connection.commit()
            return {'success': True}, 200
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-book-stats')
def get_book_stats():
    if 'username' not in session or not session.get('is_admin', False):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get total books count (sum of quantities)
            cursor.execute("SELECT COUNT(*) as total_titles, SUM(quantity) as total_books FROM books")
            result = cursor.fetchone()
            total_books = result['total_books'] or 0
            total_titles = result['total_titles'] or 0
            
            # Get borrowed books count
            cursor.execute("SELECT SUM(quantity - available) as borrowed FROM books")
            borrowed = cursor.fetchone()['borrowed'] or 0
            
            stats = {
                'total_books': total_books,
                'total_titles': total_titles,
                'books_borrowed': borrowed,
                'due_returns': 0  # Will be implemented with borrowing system
            }
            return stats
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

if __name__ == '__main__':
    init_database()
    app.run(debug=True)
