#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "FES-SuS";
const char* password = "SuS-WLAN!Key24";

const char* mqtt_server = "10.93.133.204";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastPublish = 0;

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

    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);

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

void setup() {
  Serial.begin(115200);
  delay(1000);

  connectToWiFi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  if (!client.connected()) {
    connectToMQTT();
  }

  client.loop();

  unsigned long now = millis();
  if (now - lastPublish > 5000) {
    lastPublish = now;

    const char* topic = "terrarium/terra1/sensor";
    const char* payload = "{\"arduino_id\":\"terra1\",\"temperature\":24.5,\"humidity\":60.2,\"light\":320}";

    bool ok = client.publish(topic, payload);

    Serial.println("Sende MQTT-Testnachricht...");
    Serial.print("Topic: ");
    Serial.println(topic);
    Serial.print("Payload: ");
    Serial.println(payload);
    Serial.print("Erfolgreich: ");
    Serial.println(ok ? "ja" : "nein");
    Serial.println("--------------------");
  }
}