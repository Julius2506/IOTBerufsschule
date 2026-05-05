#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <Wire.h>
#include <BH1750.h>

const char* ssid = "FES-SuS";
const char* password = "SuS-WLAN!Key24";

const char* mqtt_server = "10.93.134.218";
const int mqtt_port = 1883;

const char* arduino_id = "terra1";

#define DHTPIN 15
#define DHTTYPE DHT11

#define PIRPIN 27   // HC-SR501 OUT an GPIO 27

#define SOILPIN 34  // AO vom Bodenfeuchtigkeitssensor an GPIO34

// Erstmal Startwerte. Die kalibrieren wir später.
const int SOIL_DRY_RAW = 4095;  // trocken
const int SOIL_WET_RAW = 1500;  // nass

bool motionSinceLastPublish = false;

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);
BH1750 lightMeter;

unsigned long lastPublish = 0;
const unsigned long publishInterval = 5000;

void connectToWiFi() {
  Serial.println("Verbinde mit WLAN...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WLAN verbunden");
  Serial.print("ESP32 IP-Adresse: ");
  Serial.println(WiFi.localIP());
}

void connectToMQTT() {
  while (!client.connected()) {
    Serial.print("Verbinde mit MQTT... ");

    String clientId = "ESP32-" + String(arduino_id);

    if (client.connect(clientId.c_str())) {
      Serial.println("verbunden");
    } else {
      Serial.print("fehlgeschlagen, rc=");
      Serial.print(client.state());
      Serial.println(" -> neuer Versuch in 2 Sekunden");
      delay(2000);
    }
  }
}

int readSoilRaw() {
  long sum = 0;
  const int samples = 10;

  for (int i = 0; i < samples; i++) {
    sum += analogRead(SOILPIN);
    delay(5);
  }

  return sum / samples;
}

int soilRawToPercent(int rawValue) {
  // Meist gilt:
  // hoher Wert = trocken
  // niedriger Wert = feucht
  int percent = map(rawValue, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100);
  percent = constrain(percent, 0, 100);
  return percent;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();

  pinMode(PIRPIN, INPUT);
  pinMode(SOILPIN, INPUT);

  analogReadResolution(12); // ESP32: Werte von 0 bis 4095
  analogSetPinAttenuation(SOILPIN, ADC_11db);

  Wire.begin(21, 22);

  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("BH1750 gestartet");
  } else {
    Serial.println("Fehler beim Starten des BH1750");
  }

  connectToWiFi();
  client.setServer(mqtt_server, mqtt_port);

  Serial.println("PIR Bewegungssensor gestartet");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!client.connected()) {
    connectToMQTT();
  }
  
  if (digitalRead(PIRPIN) == HIGH) {
    motionSinceLastPublish = true;
  }

  client.loop();

  unsigned long now = millis();
  if (now - lastPublish >= publishInterval) {
    lastPublish = now;

    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    float lux = lightMeter.readLightLevel();

    int soilRaw = readSoilRaw();
    int soilMoisture = soilRawToPercent(soilRaw);

    bool motionDetected = motionSinceLastPublish;
    motionSinceLastPublish = false;

    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Fehler beim Lesen vom DHT11");
      Serial.println("--------------------");
      return;
    }

    String payload = "{";
    payload += "\"arduino_id\":\"" + String(arduino_id) + "\",";
    payload += "\"temperature\":" + String(temperature, 1) + ",";
    payload += "\"humidity\":" + String(humidity, 1) + ",";
    payload += "\"light\":" + String(lux, 1) + ",";
    payload += "\"motion\":";
    payload += motionDetected ? "true" : "false";
    payload += ",";
    payload += "\"soil_raw\":" + String(soilRaw) + ",";
    payload += "\"soil_moisture\":" + String(soilMoisture);
    payload += "}";

    String topic = "terrarium/" + String(arduino_id) + "/sensor";

    bool ok = client.publish(topic.c_str(), payload.c_str());

    Serial.println("Sende MQTT-Nachricht mit DHT11 + BH1750 + PIR...");
    Serial.print("Topic: ");
    Serial.println(topic);
    Serial.print("Payload: ");
    Serial.println(payload);
    Serial.print("Bewegung erkannt: ");
    Serial.println(motionDetected ? "ja" : "nein");

    Serial.print("Bodenfeuchte Rohwert: ");
    Serial.println(soilRaw);

    Serial.print("Bodenfeuchte Prozent: ");
    Serial.print(soilMoisture);
    Serial.println(" %");

    Serial.print("Erfolgreich: ");
    Serial.println(ok ? "ja" : "nein");
    Serial.println("--------------------");
  }
}