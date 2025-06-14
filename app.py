from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from database.db_config import get_database_connection, init_database
import os
from dotenv import load_dotenv
import time

load_dotenv()  # Load environment variables

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')

# Add error handling for database connections
def get_db_connection():
    retries = 3
    while retries > 0:
        connection = get_database_connection()
        if connection:
            return connection
        retries -= 1
        time.sleep(1)
    return None

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
                
            except Error as e: # type: ignore
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
                
                # Get user statistics
                stats = get_user_stats(user['id'])
                current_books = get_current_books(user['id'])
                
                return render_template('dashboard.html', 
                                     fullname=user['fullname'],
                                     stats=stats,
                                     current_books=current_books)
            
            flash('Invalid email address.')
            return redirect(url_for('login'))
            
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('login'))

def get_user_stats(user_id):
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get total books borrowed
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_borrowed,
                    SUM(CASE WHEN return_date IS NOT NULL THEN 1 ELSE 0 END) as total_returned,
                    SUM(CASE WHEN return_date IS NULL THEN 1 ELSE 0 END) as currently_borrowed,
                    SUM(CASE 
                        WHEN return_date IS NULL AND CURRENT_DATE > due_date 
                        THEN DATEDIFF(CURRENT_DATE, due_date) * 10
                        ELSE 0 
                    END) as total_fine
                FROM issues_books 
                WHERE user_id = %s
            """, (user_id,))
            
            stats = cursor.fetchone()
            return {
                'total_borrowed': stats['total_borrowed'] or 0,
                'total_returned': stats['total_returned'] or 0,
                'currently_borrowed': stats['currently_borrowed'] or 0,
                'total_fine': stats['total_fine'] or 0
            }
        finally:
            cursor.close()
            connection.close()
    return {
        'total_borrowed': 0,
        'total_returned': 0,
        'currently_borrowed': 0,
        'total_fine': 0
    }

def get_current_books(user_id):
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    b.title,
                    i.issue_date,
                    i.due_date,
                    CASE 
                        WHEN i.due_date >= CURRENT_DATE 
                        THEN DATEDIFF(i.due_date, CURRENT_DATE)
                        ELSE 0
                    END as days_remaining,
                    CASE 
                        WHEN CURRENT_DATE > i.due_date 
                        THEN DATEDIFF(CURRENT_DATE, i.due_date) * 10
                        ELSE 0
                    END as fine,
                    CASE 
                        WHEN CURRENT_DATE > i.due_date THEN 1
                        ELSE 0
                    END as is_overdue
                FROM issues_books i
                JOIN books b ON i.book_id = b.book_id
                WHERE i.user_id = %s AND i.return_date IS NULL
                ORDER BY i.due_date ASC
            """, (user_id,))
            
            books = cursor.fetchall()
            for book in books:
                book['issue_date'] = book['issue_date'].strftime('%Y-%m-%d')
                book['due_date'] = book['due_date'].strftime('%Y-%m-%d')
            return books
        finally:
            cursor.close()
            connection.close()
    return []

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
            return {
                'total_titles': stats['total_books'] or 0,
                'books_borrowed': 0,  # You can update this with actual logic
                'due_returns': 0      # You can update this with actual logic
            }
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

@app.route('/admin/export-books')
def export_books():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            # Create a pandas DataFrame from the books data
            query = """
                SELECT book_id as 'Book ID', 
                       title as 'Title', 
                       author as 'Author', 
                       category as 'Category',
                       available as 'Available Copies'
                FROM books
                ORDER BY book_id
            """
            df = pd.read_sql(query, connection)
            
            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Books', index=False)
                
                # Get workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['Books']
                
                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#6B3E99',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Format headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, len(value) + 5)
            
            # Prepare the file for download
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'books_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            
        except Exception as e:
            print(f"Error exporting books: {e}")
            return {'error': 'Failed to export books'}, 500
        finally:
            connection.close()
            
    return {'error': 'Database error'}, 500

@app.route('/admin/export-issued-books')
def export_issued_books():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            query = """
                SELECT 
                    i.issue_id as 'Issue ID',
                    u.fullname as 'Member Name',
                    b.title as 'Book Title',
                    DATE_FORMAT(i.issue_date, '%Y-%m-%d %H:%i') as 'Issue Date',
                    DATE_FORMAT(i.due_date, '%Y-%m-%d') as 'Due Date',
                    CASE 
                        WHEN i.return_date IS NULL AND i.due_date < CURDATE() 
                        THEN DATEDIFF(CURDATE(), i.due_date)
                        ELSE 0 
                    END as 'Days Overdue',
                    i.status as 'Status'
                FROM issues_books i
                JOIN users u ON i.user_id = u.id
                JOIN books b ON i.book_id = b.book_id
                ORDER BY i.issue_date DESC
            """
            df = pd.read_sql(query, connection)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Issued Books', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Issued Books']
                
                # Add header formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#6B3E99',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Format all columns
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, len(value) + 5)
            
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'issued_books_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            
        finally:
            connection.close()
            
    return {'error': 'Database error'}, 500

@app.route('/admin/get-circulation-stats')
def get_circulation_stats():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COUNT(*) as under_circulation,
                    SUM(CASE WHEN due_date = CURDATE() THEN 1 ELSE 0 END) as due_today,
                    SUM(CASE WHEN due_date < CURDATE() AND return_date IS NULL THEN 1 ELSE 0 END) as overdue,
                    COUNT(DISTINCT user_id) as members_borrowed
                FROM issues_books 
                WHERE return_date IS NULL
            """)
            stats = cursor.fetchone()
            return stats if stats else {'under_circulation': 0, 'due_today': 0, 'overdue': 0, 'members_borrowed': 0}
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/get-issued-books')
def get_issued_books():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    i.issue_id,
                    i.issue_date,
                    i.due_date,
                    i.return_date,
                    u.fullname as user_name,
                    u.id as user_id,
                    b.title as book_title,
                    b.book_id,
                    DATEDIFF(CURDATE(), i.due_date) as days_overdue
                FROM issues_books i
                JOIN users u ON i.user_id = u.id
                JOIN books b ON i.book_id = b.book_id
                WHERE i.return_date IS NULL
                ORDER BY i.issue_date DESC
            """)
            issues = cursor.fetchall()
            return {'issues': issues}
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/issue-book', methods=['POST'])
def issue_book():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    data = request.json
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Check if book is available
            cursor.execute("SELECT available FROM books WHERE book_id = %s", (data['book_id'],))
            book = cursor.fetchone()
            
            if not book or book[0] <= 0:
                return {'error': 'Book not available'}, 400
            
            # Calculate due date from due_days
            due_date = datetime.now() + timedelta(days=int(data['due_days']))
            
            # Create issue record with proper datetime values
            cursor.execute("""
                INSERT INTO issues_books 
                (user_id, book_id, issue_date, due_date, status) 
                VALUES (%s, %s, NOW(), %s, 'issued')
            """, (data['user_id'], data['book_id'], due_date))
            
            # Update book availability
            cursor.execute("""
                UPDATE books 
                SET available = available - 1 
                WHERE book_id = %s
            """, (data['book_id'],))
            
            connection.commit()
            return {'success': True}, 200
            
        except Exception as e:
            print(f"Error issuing book: {e}")
            return {'error': str(e)}, 500
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/return-book/<int:issue_id>', methods=['POST'])
def return_book(issue_id):
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Get book ID and check if already returned
            cursor.execute("""
                SELECT book_id, return_date 
                FROM issues_books 
                WHERE issue_id = %s
            """, (issue_id,))
            result = cursor.fetchone()
            
            if not result:
                return {'error': 'Issue record not found'}, 404
            
            if result[1] is not None:  # Check if already returned
                return {'error': 'Book already returned'}, 400
            
            book_id = result[0]
            
            # Update issue record with return date and status
            cursor.execute("""
                UPDATE issues_books 
                SET return_date = CURRENT_TIMESTAMP,
                    status = 'returned'
                WHERE issue_id = %s
            """, (issue_id,))
            
            # Increment available count for the book
            cursor.execute("""
                UPDATE books 
                SET available = available + 1 
                WHERE book_id = %s
            """, (book_id,))
            
            connection.commit()
            return {
                'success': True,
                'message': 'Book returned successfully'
            }, 200
            
        except Exception as e:
            print(f"Error returning book: {e}")
            return {'error': str(e)}, 500
        finally:
            cursor.close()
            connection.close()
    
    return {'error': 'Database error'}, 500

@app.route('/admin/reports')
def reports():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('reports.html', fullname=session.get('fullname'))

@app.route('/admin/get-reports')
def get_reports():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    i.issue_id,
                    u.fullname as user_name,
                    b.title as book_title,
                    i.issue_date,
                    i.due_date,
                    i.return_date,
                    CASE 
                        WHEN i.return_date IS NULL AND CURRENT_DATE > i.due_date 
                        THEN DATEDIFF(CURRENT_DATE, i.due_date)
                        ELSE 0 
                    END as days_overdue
                FROM issues_books i
                JOIN users u ON i.user_id = u.id
                JOIN books b ON i.book_id = b.book_id
                ORDER BY i.issue_date DESC
            """)
            reports = cursor.fetchall()
            return {'reports': reports}
        finally:
            cursor.close()
            connection.close()
    return {'error': 'Database error'}, 500

@app.route('/admin/export-reports')
def export_reports():
    if not session.get('is_admin'):
        return {'error': 'Unauthorized'}, 401
    
    connection = get_database_connection()
    if connection:
        try:
            query = """
                SELECT 
                    i.issue_id as 'Issue ID',
                    u.fullname as 'Member Name',
                    b.title as 'Book Title',
                    DATE_FORMAT(i.issue_date, '%Y-%m-%d') as 'Issue Date',
                    DATE_FORMAT(i.due_date, '%Y-%m-%d') as 'Due Date',
                    DATE_FORMAT(i.return_date, '%Y-%m-%d') as 'Return Date',
                    CASE 
                        WHEN i.return_date IS NULL AND CURRENT_DATE > i.due_date 
                        THEN DATEDIFF(CURRENT_DATE, i.due_date)
                        ELSE 0 
                    END as 'Days Overdue',
                    CASE 
                        WHEN i.return_date IS NOT NULL THEN 'Completed'
                        ELSE 'Borrowed'
                    END as 'Status'
                FROM issues_books i
                JOIN users u ON i.user_id = u.id
                JOIN books b ON i.book_id = b.book_id
                ORDER BY i.issue_date DESC
            """
            df = pd.read_sql(query, connection)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Library Reports', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Library Reports']
                
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#6B3E99',
                    'font_color': 'white',
                    'border': 1
                })
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, len(value) + 5)
            
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'library_reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        finally:
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
