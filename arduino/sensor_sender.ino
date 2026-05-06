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

#define SOILPIN 34  // AO vom Bodenfeuchtigkeitssensor an D34

#define LEDPIN 26   // LED an D26

// Kalibrierwerte vom Bodenfeuchtigkeitssensor
const int SOIL_DRY_RAW = 4095;
const int SOIL_WET_RAW = 1290;

// MQTT Topics für LED
const char* ledCommandTopic = "terrarium/terra1/led/set";
const char* ledStateTopic   = "terrarium/terra1/led/state";

bool motionSinceLastPublish = false;
bool ledState = false;

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);
BH1750 lightMeter;

unsigned long lastPublish = 0;
const unsigned long publishInterval = 5000;

void publishLedState() {
  if (client.connected()) {
    client.publish(ledStateTopic, ledState ? "ON" : "OFF", true);
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";

  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  message.trim();

  Serial.print("MQTT-Befehl empfangen auf Topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(message);

  if (String(topic) == ledCommandTopic) {
    if (message == "ON" || message == "on" || message == "1" || message == "true") {
      ledState = true;
      digitalWrite(LEDPIN, HIGH);
      Serial.println("LED eingeschaltet");
      publishLedState();
    } 
    else if (message == "OFF" || message == "off" || message == "0" || message == "false") {
      ledState = false;
      digitalWrite(LEDPIN, LOW);
      Serial.println("LED ausgeschaltet");
      publishLedState();
    }
  }
}

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

      client.subscribe(ledCommandTopic);
      Serial.print("LED-Command-Topic abonniert: ");
      Serial.println(ledCommandTopic);

      publishLedState();
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
  // Hoher Wert = trocken
  // Niedriger Wert = feucht
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

  pinMode(LEDPIN, OUTPUT);
  digitalWrite(LEDPIN, LOW);

  analogReadResolution(12); // ESP32: Wertebereich 0 bis 4095
  analogSetPinAttenuation(SOILPIN, ADC_11db);

  // BH1750 starten
  Wire.begin(21, 22);        // SDA = GPIO21, SCL = GPIO22
  Wire.setClock(100000);    

  Serial.println("Starte BH1750...");

  bool bh1750_ok = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23);

  if (bh1750_ok) {
    Serial.println("BH1750 gestartet auf Adresse 0x23");
  } else {
    Serial.println("BH1750 konnte NICHT gestartet werden auf Adresse 0x23");
  }

  delay(500); 

  connectToWiFi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  Serial.println("PIR Bewegungssensor gestartet");
  Serial.println("Bodenfeuchtigkeitssensor gestartet");
  Serial.println("LED-Steuerung gestartet");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!client.connected()) {
    connectToMQTT();
  }

  client.loop();

  if (digitalRead(PIRPIN) == HIGH) {
    motionSinceLastPublish = true;
  }

  unsigned long now = millis();

  if (now - lastPublish >= publishInterval) {
    lastPublish = now;

    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    // BH1750 auslesen
    float lux = lightMeter.readLightLevel();

    if (lux < 0) {
      Serial.print("BH1750 Fehlercode: ");
      Serial.println(lux);
      lux = 0;
    }

    // Bodenfeuchtigkeit auslesen
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
    payload += "\"soil_moisture\":" + String(soilMoisture) + ",";
    payload += "\"led\":";
    payload += ledState ? "true" : "false";
    payload += "}";

    String topic = "terrarium/" + String(arduino_id) + "/sensor";

    bool ok = client.publish(topic.c_str(), payload.c_str());

    Serial.println("Sende MQTT-Nachricht mit DHT11 + BH1750 + PIR + Bodenfeuchtigkeit + LED...");
    Serial.print("Topic: ");
    Serial.println(topic);
    Serial.print("Payload: ");
    Serial.println(payload);

    Serial.print("Temperatur: ");
    Serial.print(temperature);
    Serial.println(" °C");

    Serial.print("Luftfeuchtigkeit: ");
    Serial.print(humidity);
    Serial.println(" %");

    Serial.print("Lichtwert: ");
    Serial.print(lux);
    Serial.println(" lx");

    Serial.print("Bewegung erkannt: ");
    Serial.println(motionDetected ? "ja" : "nein");

    Serial.print("Bodenfeuchte Rohwert: ");
    Serial.println(soilRaw);

    Serial.print("Bodenfeuchte Prozent: ");
    Serial.print(soilMoisture);
    Serial.println(" %");

    Serial.print("LED Status: ");
    Serial.println(ledState ? "AN" : "AUS");

    Serial.print("Erfolgreich: ");
    Serial.println(ok ? "ja" : "nein");
    Serial.println("--------------------");
  }
}