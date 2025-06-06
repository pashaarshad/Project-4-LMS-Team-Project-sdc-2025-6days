import mysql.connector
from mysql.connector import Error

def get_database_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='lms_db',
            user='root',
            password='root'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    connection = get_database_connection()
    if connection:
        cursor = connection.cursor()
        
        # Updated users table with new fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                reset_token VARCHAR(100),
                reset_token_expiry DATETIME
            )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
