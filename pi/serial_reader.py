import json
import serial
import time
from database import get_connection

PORT = "/dev/ttyACM0"
BAUDRATE = 9600

def get_terrarium_id_by_arduino_id(arduino_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM terrariums
        WHERE arduino_id = ?
    """, (arduino_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return row[0]

def save_reading(data):
    arduino_id = data.get("arduino_id")
    terrarium_id = get_terrarium_id_by_arduino_id(arduino_id)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sensor_readings (
            arduino_id,
            terrarium_id,
            temperature,
            humidity,
            light
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        arduino_id,
        terrarium_id,
        data.get("temperature"),
        data.get("humidity"),
        data.get("light")
    ))

    conn.commit()
    conn.close()

    return terrarium_id

def main():
    print(f"Verbinde mit {PORT} bei {BAUDRATE} Baud...")

    while True:
        try:
            with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
                print("Verbindung hergestellt. Warte auf Daten...\n")

                while True:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()

                    if not line:
                        continue

                    print(f"Rohdaten: {line}")

                    try:
                        data = json.loads(line)

                        arduino_id = data.get("arduino_id")
                        terrarium_id = save_reading(data)

                        print("Gelesene Daten:")
                        print(f"  Arduino-ID:   {arduino_id}")
                        print(f"  Terrarium-ID: {terrarium_id}")
                        print(f"  Temperatur:   {data.get('temperature')} °C")
                        print(f"  Luftfeuchte:  {data.get('humidity')} %")
                        print(f"  Licht:        {data.get('light')}")
                        
                        if terrarium_id is None:
                            print("  Warnung: Keine Zuordnung zu einem Terrarium gefunden")
                        else:
                            print("  -> Mit Terrarium verknuepft gespeichert")

                        print("-" * 40)

                    except json.JSONDecodeError:
                        print("Fehler: Ungültiges JSON empfangen")
                        print("-" * 40)

        except serial.SerialException as e:
            print(f"Serielle Verbindung fehlgeschlagen: {e}")
            print("Neuer Versuch in 3 Sekunden...\n")
            time.sleep(3)

if __name__ == "__main__":
    main()