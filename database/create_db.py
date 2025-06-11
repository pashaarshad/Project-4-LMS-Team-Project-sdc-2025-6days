import mysql.connector
from mysql.connector import Error

def create_database():
    try:
        # Connect to MySQL server with correct credentials
        connection = mysql.connector.connect(
            host='sql5.freesqldatabase.com',
            user='sql5784235',
            password='amcfewt9BL',
            database='sql5784235',
            port=3306
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("Successfully connected to the database!")
            
            # Initialize database structure
            init_database_structure(cursor)
            
            connection.commit()
            print("Database initialized successfully!")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

def init_database_structure(cursor):
    # Create tables
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        fullname VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone VARCHAR(20),
        password VARCHAR(255),
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS books (
        book_id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        category VARCHAR(100) NOT NULL,
        available INT DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS issues_books (
        issue_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        book_id INT NOT NULL,
        issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date DATETIME NOT NULL,
        return_date DATETIME NULL,
        status ENUM('issued', 'returned') DEFAULT 'issued',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
    );
    """
    
    for statement in create_tables_sql.split(';'):
        if statement.strip():
            cursor.execute(statement)

if __name__ == "__main__":
    create_database()
