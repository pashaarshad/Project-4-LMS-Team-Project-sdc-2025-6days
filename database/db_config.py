import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import time

load_dotenv()

def get_database_connection():
    """
    Establishes a connection to the MySQL database with retry logic.
    """
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(
                host='sql5.freesqldatabase.com',  # Hardcoded values instead of env vars
                user='sql5784235',
                password='amcfewt9BL',
                database='sql5784235',
                port=3306
            )
            if connection.is_connected():
                print(f"Successfully connected to database on attempt {attempt + 1}")
                return connection
        except Error as err:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {err}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("Failed to connect to database after all retries")
    return None

def get_sqlalchemy_engine():
    """
    Creates a SQLAlchemy engine instance using the DATABASE_URL from environment variables.
    Returns the engine instance if successful, otherwise None.
    """
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return create_engine(database_url)
    return None

def init_database():
    """
    Initializes the database by creating the 'users' and 'books' tables if they do not exist.
    Adds a default admin user with full access.
    Inserts sample IT books into the books table.
    """
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create only the users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fullname VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    phone VARCHAR(20),
                    password VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    reset_token VARCHAR(100),
                    reset_token_expiry DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add default admin user if it doesn't exist
            cursor.execute("""
                INSERT IGNORE INTO users (fullname, email, password, is_admin)
                VALUES ('Administrator', 'admin@gmail.com', 'admin', TRUE)
            """)
            
            # Create books table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    book_id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    available INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create issues_books table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issues_books (
                    issue_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    book_id INT NOT NULL,
                    issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    due_date DATETIME NOT NULL,
                    return_date DATETIME NULL,
                    status ENUM('issued', 'returned') DEFAULT 'issued',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
                )
            """)
            
            # Insert sample IT books
            sample_books = [
                ("Python Programming: An Introduction to Computer Science", "John Zelle", "Programming", 5),
                ("Clean Code: A Handbook of Agile Software", "Robert C. Martin", "Software Engineering", 3),
                ("Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", 4),
                ("Database System Concepts", "Abraham Silberschatz", "Database", 3),
                ("Computer Networks", "Andrew S. Tanenbaum", "Networking", 4),
                ("Artificial Intelligence: A Modern Approach", "Stuart Russell", "AI", 3),
                ("JavaScript: The Good Parts", "Douglas Crockford", "Web Development", 5),
                ("Design Patterns", "Erich Gamma", "Software Engineering", 3),
                ("Machine Learning: A Probabilistic Perspective", "Kevin Murphy", "AI", 2),
                ("Computer Organization and Design", "David A. Patterson", "Computer Architecture", 4)
            ]
            
            # Insert books if they don't exist
            cursor.execute("SELECT COUNT(*) FROM books")
            if cursor.fetchone()[0] == 0:
                cursor.executemany("""
                    INSERT INTO books (title, author, category, available)
                    VALUES (%s, %s, %s, %s)
                """, sample_books)
                
            connection.commit()
            print("Database initialized successfully.")
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            cursor.close() # type: ignore
            connection.close()
    else:
        print("Failed to initialize the database due to connection issues.")