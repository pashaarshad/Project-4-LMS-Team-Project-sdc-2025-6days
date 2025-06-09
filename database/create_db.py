import mysql.connector
from mysql.connector import Error

def create_database():
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root'  # Change this to your MySQL root password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Read SQL script
            with open('setup_database.sql', 'r') as file:
                sql_script = file.read()
            
            # Execute each statement in the script
            for statement in sql_script.split(';'):
                if statement.strip():
                    cursor.execute(statement + ';')
            
            connection.commit()
            print("Database created successfully!")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    create_database()
