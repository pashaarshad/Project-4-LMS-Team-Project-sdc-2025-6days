import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

def get_database_connection():
    """
    Establishes a connection to the MySQL database.
    Returns the connection object if successful, otherwise None.
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='lms_db',
            user='root',
            password='root'  # Update this if you change the password
        )
        if connection.is_connected():
            print("Successfully connected to the database.")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """
    Initializes the database by creating the 'users' and 'members' tables if they do not exist.
    Adds a default admin user with full access.
    """
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create the 'users' table with necessary fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fullname VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    phone VARCHAR(20),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    reset_token VARCHAR(100),
                    reset_token_expiry DATETIME
                )
            """)
            
            # Add default admin user
            cursor.execute("""
                INSERT IGNORE INTO users (fullname, email, username, password)
                VALUES ('Admin', 'admin@lms.com', 'admin', %s)
            """, (generate_password_hash('admin'),))
            
            # Create the 'members' table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usid VARCHAR(20) UNIQUE NOT NULL,
                    fullname VARCHAR(255) NOT NULL,
                    class VARCHAR(50) NOT NULL,
                    mobile VARCHAR(20),
                    course VARCHAR(50) NOT NULL,
                    status ENUM('Active', 'Inactive') DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create the 'books' table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    book_code VARCHAR(20) UNIQUE NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    quantity INT DEFAULT 1,
                    available INT DEFAULT 1,
                    status ENUM('Available', 'Not Available') DEFAULT 'Available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add default books
            default_books = [
                ('b102', 'Python Programming', 'Py', 'Reference', 1, 1, 'Available'),
                ('a101', 'Computer Fundamentals', 'Arshading', 'Textbook', 1, 1, 'Available'),
                ('c103', 'Data Structures and Algorithms', 'Robert Sedgewick', 'Reference', 2, 2, 'Available'),
                ('d104', 'Web Development Basics', 'Jennifer Robbins', 'Technical', 1, 1, 'Available'),
                ('e105', 'Database Management Systems', 'Abraham Silberschatz', 'Textbook', 3, 3, 'Available'),
                ('f106', 'Machine Learning Fundamentals', 'Tom Mitchell', 'Reference', 1, 1, 'Available'),
                ('g107', 'JavaScript: The Good Parts', 'Douglas Crockford', 'Programming', 2, 2, 'Available'),
                ('h108', 'Clean Code', 'Robert C. Martin', 'Software Engineering', 1, 1, 'Available'),
                ('i109', 'Operating System Concepts', 'Silberschatz Galvin', 'Textbook', 2, 2, 'Available'),
                ('j110', 'Computer Networks', 'Andrew S. Tanenbaum', 'Networking', 1, 1, 'Available'),
                ('k111', 'Introduction to Algorithms', 'Thomas H. Cormen', 'Reference', 2, 2, 'Available'),
                ('l112', 'Artificial Intelligence', 'Stuart Russell', 'Reference', 1, 1, 'Available'),
                ('m113', 'Software Engineering', 'Ian Sommerville', 'Textbook', 3, 3, 'Available'),
                ('n114', 'React.js Fundamentals', 'Robin Wieruch', 'Programming', 1, 1, 'Available'),
                ('o115', 'Cloud Computing Basics', 'Thomas Erl', 'Technical', 2, 2, 'Available'),
                ('p116', 'Cyber Security Essentials', 'Chuck Easttom', 'Security', 1, 1, 'Available'),
                ('q117', 'Big Data Analytics', 'David Stephenson', 'Data Science', 2, 2, 'Available'),
                ('r118', 'DevOps Handbook', 'Gene Kim', 'Technical', 1, 1, 'Available'),
                ('s119', 'Angular Development', 'Yakov Fain', 'Programming', 2, 2, 'Available'),
                ('t120', 'Docker in Practice', 'Ian Miell', 'DevOps', 1, 1, 'Available'),
                ('u121', 'Linux Administration', 'Evi Nemeth', 'System Admin', 2, 2, 'Available'),
                ('v122', 'Node.js Design Patterns', 'Mario Casciaro', 'Programming', 1, 1, 'Available'),
                ('w123', 'Blockchain Basics', 'Daniel Drescher', 'Technical', 2, 2, 'Available'),
                ('x124', 'Data Mining Concepts', 'Jiawei Han', 'Data Science', 1, 1, 'Available'),
                ('y125', 'Information Security', 'Michael E. Whitman', 'Security', 2, 2, 'Available')
            ]
            
            cursor.executemany("""
                INSERT IGNORE INTO books (book_code, title, author, category, quantity, available, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, default_books)
            
            connection.commit()
            print("Database initialized successfully. 'users', 'members', and 'books' tables are ready.")
        except Error as e:
            print(f"Error initializing the database: {e}")
        finally:
            cursor.close() # type: ignore
            connection.close()
    else:
        print("Failed to initialize the database due to connection issues.")