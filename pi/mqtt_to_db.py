import json
import paho.mqtt.client as mqtt
from database import get_connection

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "terrarium/+/sensor"

def get_terrarium_id_by_arduino_id(arduino_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM terrariums
            WHERE arduino_id = ?
        """, (arduino_id,))
        row = cursor.fetchone()

    if row is None:
        return None

    return row[0]

def save_reading(data):
    arduino_id = data.get("arduino_id")
    terrarium_id = get_terrarium_id_by_arduino_id(arduino_id)

    if terrarium_id is None:
        print(f"Warnung: Kein Terrarium für arduino_id='{arduino_id}' gefunden")
        return None

    with get_connection() as conn:
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

    return terrarium_id

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Mit MQTT-Broker verbunden")
        client.subscribe(MQTT_TOPIC)
        print(f"Abonniert: {MQTT_TOPIC}")
    else:
        print(f"MQTT-Verbindung fehlgeschlagen mit Code {rc}")

def on_message(client, userdata, msg):
    print(f"MQTT empfangen -> Topic: {msg.topic}")

    try:
        payload = msg.payload.decode("utf-8")
        print(f"Payload: {payload}")

        data = json.loads(payload)
        terrarium_id = save_reading(data)

        if terrarium_id is not None:
            print(f"Messwert gespeichert für Terrarium-ID {terrarium_id}")
        print("-" * 40)

    except json.JSONDecodeError:
        print("Fehler: Ungültiges JSON aus MQTT empfangen")
        print("-" * 40)
    except Exception as e:
        print(f"Fehler beim Verarbeiten der MQTT-Nachricht: {e}")
        print("-" * 40)

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Verbinde zu MQTT-Broker {MQTT_BROKER}:{MQTT_PORT} ...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()