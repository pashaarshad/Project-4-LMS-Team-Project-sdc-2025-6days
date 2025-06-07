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
            
            connection.commit()
            print("Database initialized successfully. 'users', 'members', and 'books' tables are ready.")
        except Error as e:
            print(f"Error initializing the database: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("Failed to initialize the database due to connection issues.")