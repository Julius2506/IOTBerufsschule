#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// =========================
// Konfiguration
// =========================
const char* WIFI_SSID = "FES-SuS";
const char* WIFI_PASSWORD = "SuS-WLAN!Key24";

const char* MQTT_SERVER = "10.93.133.204";
const int MQTT_PORT = 1883;

const char* DEVICE_ID = "terra1";

#define DHTPIN 15
#define DHTTYPE DHT11

const unsigned long PUBLISH_INTERVAL_MS = 5000;

// =========================
// Objekte
// =========================
WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHTPIN, DHTTYPE);

// =========================
// Zustände
// =========================
unsigned long lastPublishTime = 0;

// =========================
// WLAN
// =========================
void connectToWiFi() {
  Serial.print("Verbinde mit WLAN");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WLAN verbunden");
  Serial.print("ESP32 IP-Adresse: ");
  Serial.println(WiFi.localIP());
}

// =========================
// MQTT
// =========================
void connectToMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Verbinde mit MQTT... ");

    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("verbunden");
    } else {
      Serial.print("fehlgeschlagen, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" -> neuer Versuch in 2 Sekunden");
      delay(2000);
    }
  }
}

// =========================
// Sensor lesen
// =========================
bool readDHT11(float &temperature, float &humidity) {
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    return false;
  }

  return true;
}

// =========================
// MQTT Payload bauen
// =========================
String buildPayload(float temperature, float humidity) {
  String payload = "{";
  payload += "\"arduino_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"temperature\":" + String(temperature, 1) + ",";
  payload += "\"humidity\":" + String(humidity, 1) + ",";
  payload += "\"light\":0";
  payload += "}";

  return payload;
}

// =========================
// Daten senden
// =========================
void publishSensorData() {
  float temperature;
  float humidity;

  if (!readDHT11(temperature, humidity)) {
    Serial.println("Fehler beim Lesen vom DHT11");
    Serial.println("--------------------");
    return;
  }

  String topic = "terrarium/" + String(DEVICE_ID) + "/sensor";
  String payload = buildPayload(temperature, humidity);

  bool ok = mqttClient.publish(topic.c_str(), payload.c_str());

  Serial.println("Sende MQTT-Nachricht...");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(payload);
  Serial.print("Erfolgreich: ");
  Serial.println(ok ? "ja" : "nein");
  Serial.println("--------------------");
}

// =========================
// Setup
// =========================
void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();

  connectToWiFi();

  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
}

// =========================
// Loop
// =========================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!mqttClient.connected()) {
    connectToMQTT();
  }

  mqttClient.loop();

  unsigned long currentTime = millis();
  if (currentTime - lastPublishTime >= PUBLISH_INTERVAL_MS) {
    lastPublishTime = currentTime;
    publishSensorData();
  }
}