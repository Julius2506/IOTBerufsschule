from database import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            temperature_min REAL,
            temperature_max REAL,
            humidity_min REAL,
            humidity_max REAL,
            light_min INTEGER,
            light_max INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS terrariums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            arduino_id TEXT NOT NULL UNIQUE,
            preset_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (preset_id) REFERENCES presets(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arduino_id TEXT NOT NULL,
            terrarium_id INTEGER,
            temperature REAL,
            humidity REAL,
            light INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (terrarium_id) REFERENCES terrariums(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Datenbank und Tabellen wurden erstellt.")

if __name__ == "__main__":
    init_db()