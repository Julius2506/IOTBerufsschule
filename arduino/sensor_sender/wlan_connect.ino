#include <WiFi.h>

const char* ssid = "FES-SuS";
const char* password = "SuS-WLAN!Key24";

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Starte WLAN-Verbindung...");
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

void loop() {
}