#include "NetworkManager.h"

NetworkManager *NetworkManager::instance = nullptr;

NetworkManager::NetworkManager(AppData &data) : appData(data), mqttClient(espClient)
{
    instance = this;
}

void NetworkManager::init()
{
    WiFi.mode(WIFI_STA);
    appData.macAddress = WiFi.macAddress();
    mqttClient.setServer(MQTT_SERVER, 1883);
    mqttClient.setCallback(mqttCallbackWrapper);
}

void NetworkManager::loop()
{
    if (mqttClient.connected())
    {
        mqttClient.loop();
    }
}

bool NetworkManager::connectWiFi()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        return false; // Ještě není připojeno
    }
    return true;
}

bool NetworkManager::connectMQTT()
{
    if (!mqttClient.connected())
    {
        String clientId = "ESP32-" + appData.macAddress;
        if (mqttClient.connect(clientId.c_str()))
        {
            String subReg = "l1/registration/response/" + appData.macAddress;
            String subConfig = "l2/config/" + appData.macAddress;
            String subStart = "l1/start/" + appData.macAddress;

            mqttClient.subscribe(subReg.c_str());
            mqttClient.subscribe(subConfig.c_str());
            mqttClient.subscribe(subStart.c_str());
            return true;
        }
        return false;
    }
    return true;
}

bool NetworkManager::isConnected()
{
    return (WiFi.status() == WL_CONNECTED && mqttClient.connected());
}

void NetworkManager::sendRegistration()
{
    String payload = "{\"name\":\"" + DEVICE_NAME + "\",\"mac\":\"" + appData.macAddress +
                     "\",\"sensorType\":\"" + SENSOR_TYPE + "\",\"conversion\":\"" + CONVERSION_RULE +
                     "\",\"param_a\":" + String(PARAM_A) + ",\"param_b\":" + String(PARAM_B) +
                     ",\"param_c\":" + String(PARAM_C) + "}";
    mqttClient.publish("l1/registration", payload.c_str());
}

void NetworkManager::sendMeasurement(float temp)
{
    String payload = "{\"device_id\":\"" + String(appData.small_id) +
                     "\",\"local_channel\":\"" + String(appData.local_channel) +
                     "\",\"temp\":" + String(temp) + "}";
    mqttClient.publish("l1/test", payload.c_str());
}

void NetworkManager::sendConfigAck()
{
    JsonDocument doc;
    doc["deviceID"] = appData.macAddress;
    doc["status"] = "ok";
    char buffer[128];
    serializeJson(doc, buffer);
    String topic = "l1/config_ack/" + appData.macAddress;
    mqttClient.publish(topic.c_str(), buffer);
    printf("Odesilam config ACK: %s\n", buffer);
}

void NetworkManager::mqttCallbackWrapper(char *topic, byte *message, unsigned int length)
{
    if (instance)
    {
        instance->handleCallback(topic, message, length);
    }
}

void NetworkManager::handleCallback(char *topic, byte *message, unsigned int length)
{
    String msg;
    for (int i = 0; i < length; i++)
    {
        msg += (char)message[i];
    }
    Serial.println("Prijata zprava na [" + String(topic) + "]: " + msg);

    String topicStr = String(topic);
    JsonDocument doc;
    deserializeJson(doc, msg);

    if (topicStr == "l1/registration/response/" + appData.macAddress)
    {
        appData.small_id = doc["short_id"];
        appData.local_channel = doc["local_channel"];

        String typeMeasString = doc["typeMeasurement"].as<String>();
        appData.typeMeas = (typeMeasString == "CONTINUAL");

        float hz = doc["measIntervalHz"];
        appData.measureInterval = (hz > 0.0) ? (1000.0 / hz) : 100000;
        appData.isRegistered = true;
    }
    else if (topicStr == "l2/config/" + appData.macAddress)
    {
        String typeMeasString = doc["typeMeasurement"].as<String>();
        appData.typeMeas = (typeMeasString == "CONTINUAL");

        float hz = doc["measIntervalHz"];
        appData.measureInterval = (hz > 0.0) ? (1000.0 / hz) : 100000;

        sendConfigAck();
        appData.configReceived = true; // Flag pro změnu stavu v main.cpp
    }
    else if (topicStr == "l1/start/" + appData.macAddress)
    {
        appData.start = doc["start"];
    }
}