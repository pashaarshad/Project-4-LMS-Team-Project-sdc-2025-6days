import mysql.connector
from mysql.connector import Error

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