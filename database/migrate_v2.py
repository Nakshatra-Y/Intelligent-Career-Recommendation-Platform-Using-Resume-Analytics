import sqlite3
import os

def run_migration():
    # database.db is in the same directory as this script
    db_path = os.path.join(os.path.dirname(__file__), "database.db")
    print(f"Connecting to database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    new_columns = {
        'photo_filename': 'TEXT',
        'current_job_title': 'TEXT',
        'current_company': 'TEXT',
        'years_of_experience': 'TEXT',
        'skills': 'TEXT'
    }
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            print(f"Adding column '{col_name}' to 'users' table...")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        else:
            print(f"Column '{col_name}' already exists.")
            
    conn.commit()
    conn.close()
    print("Migration V2 completed successfully.")

if __name__ == '__main__':
    run_migration()
