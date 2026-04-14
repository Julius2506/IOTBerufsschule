from database import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arduino_id TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            light INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Datenbank und Tabelle wurden erstellt.")

if __name__ == "__main__":
    init_db()