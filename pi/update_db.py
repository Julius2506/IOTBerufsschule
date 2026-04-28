from database import get_connection

def add_column_if_missing(cursor, table_name, column_name, column_definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]

    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        print(f"Spalte hinzugefügt: {column_name}")
    else:
        print(f"Spalte existiert schon: {column_name}")

def update_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        add_column_if_missing(cursor, "sensor_readings", "soil_moisture", "REAL")
        add_column_if_missing(cursor, "sensor_readings", "motion", "INTEGER")

        conn.commit()

    print("Datenbank wurde aktualisiert.")

if __name__ == "__main__":
    update_db()