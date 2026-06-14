#pragma once

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"
#include "Config.h"
class NetworkManager
{
public:
    NetworkManager(AppData &data);
    void init();
    void loop();
    bool connectWiFi();
    bool connectMQTT();
    bool isConnected();

    void sendRegistration();
    void sendMeasurement(float temp);
    void sendtemp(float temp);
    void sendBatchMeasurement(int *measurements, int count);
    void sendMeasurementSession(float temp);
    void sendBatchMeasurementSession(int *measurements, int count);

private:
    AppData &appData;
    WiFiClient espClient;
    PubSubClient mqttClient;

    void sendConfigAck();

    // MQTT Callback musí být statický, abychom ho mohli předat do PubSubClient
    static void mqttCallbackWrapper(char *topic, byte *message, unsigned int length);
    void handleCallback(char *topic, byte *message, unsigned int length);

    // Globální pointer na instanci (potřebný pro statický callback)
    static NetworkManager *instance;
};