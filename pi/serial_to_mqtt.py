import json
import time
import serial
import paho.mqtt.client as mqtt

SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 9600

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

def main():
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    print(f"Verbinde mit Serial-Port {SERIAL_PORT} bei {BAUDRATE} Baud...")

    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as ser:
                print("Serial-Verbindung hergestellt. Warte auf Arduino-Daten...\n")

                while True:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()

                    if not line:
                        continue

                    print(f"Rohdaten von Serial: {line}")

                    try:
                        data = json.loads(line)
                        arduino_id = data.get("arduino_id")

                        if not arduino_id:
                            print("Fehler: Keine arduino_id im JSON gefunden")
                            print("-" * 40)
                            continue

                        topic = f"terrarium/{arduino_id}/sensor"
                        payload = json.dumps(data)

                        mqtt_client.publish(topic, payload)
                        print(f"MQTT veröffentlicht -> Topic: {topic}")
                        print(f"Payload: {payload}")
                        print("-" * 40)

                    except json.JSONDecodeError:
                        print("Fehler: Ungültiges JSON von Serial empfangen")
                        print("-" * 40)

        except serial.SerialException as e:
            print(f"Serial-Verbindung fehlgeschlagen: {e}")
            print("Neuer Versuch in 3 Sekunden...\n")
            time.sleep(3)

if __name__ == "__main__":
    main()