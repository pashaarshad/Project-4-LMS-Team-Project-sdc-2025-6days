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
    Initializes the database by creating the 'users' table if it does not exist.
    Adds a default admin user with full access.
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
            
            connection.commit()
            print("Database initialized successfully.")
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            cursor.close() # type: ignore
            connection.close()
    else:
        print("Failed to initialize the database due to connection issues.")