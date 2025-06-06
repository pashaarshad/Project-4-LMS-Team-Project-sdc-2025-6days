from flask import Flask, render_template, request, redirect, url_for, flash
from database.db_config import get_database_connection, init_database
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

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
                # Here you would typically set up a session
                flash('Login successful!')
                return redirect(url_for('dashboard'))
            
            flash('Invalid username or password.')
    
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    # Add authentication check here later
    return "Welcome to Dashboard!"  # Replace with actual dashboard template

if __name__ == '__main__':
    init_database()
    app.run(debug=True)
