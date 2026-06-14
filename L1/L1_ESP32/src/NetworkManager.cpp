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
    mqttClient.setBufferSize(1024);
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

void NetworkManager::sendtemp(float temp)
{
    String payload = "{\"device_id\":\"" + String(appData.small_id) +
                     "\",\"local_channel\":\"" + String(appData.local_channel) +
                     "\",\"temp\":" + String(temp) + "}"; // change to raw value
    String topic = "l1/test";
    mqttClient.publish(topic.c_str(), payload.c_str());
}
void NetworkManager::sendMeasurement(float temp)
{
    String payload = "{\"device_id\":\"" + String(appData.small_id) +
                     "\",\"local_channel\":\"" + String(appData.local_channel) +
                     "\",\"temp\":" + String(temp) + "}"; // change to raw value
    String topic = "l1/measurement/cont/stream/" + appData.macAddress;
    mqttClient.publish(topic.c_str(), payload.c_str());
    printf("Odesilam mereni: %s\n na topicu: %s", payload.c_str(), topic.c_str());
}
void NetworkManager::sendBatchMeasurement(int *measurements, int count)
{
    JsonDocument doc;
    doc["device_id"] = appData.small_id;
    doc["local_channel"] = appData.local_channel;
    JsonArray arr = doc.createNestedArray("measurements");
    for (int i = 0; i < count; i++)
    {
        arr.add(measurements[i]);
    }
    char buffer[1024];
    serializeJson(doc, buffer);
    String topic = "l1/measurement/cont/batch/" + appData.macAddress;
    mqttClient.publish(topic.c_str(), buffer);
    printf("Odesilam batch mereni: %s\n na topicu: %s", buffer, topic.c_str());
}
void NetworkManager::sendMeasurementSession(float temp)
{
    String payload = "{\"device_id\":\"" + String(appData.small_id) +
                     "\",\"local_channel\":\"" + String(appData.local_channel) +
                     "\",\"sessionName\":\"" + String(appData.sessionName) +
                     "\",\"temp\":" + String(temp) + "}"; // change to raw value
    String topic = "l1/measurement/session/stream/" + appData.macAddress;
    mqttClient.publish(topic.c_str(), payload.c_str());
    printf("Odesilam mereni: %s\n na topicu: %s", payload.c_str(), topic.c_str());
}
void NetworkManager::sendBatchMeasurementSession(int *measurements, int count)
{
    JsonDocument doc;
    doc["device_id"] = appData.small_id;
    doc["local_channel"] = appData.local_channel;
    doc["sessionName"] = appData.sessionName;
    JsonArray arr = doc.createNestedArray("measurements");
    for (int i = 0; i < count; i++)
    {
        arr.add(measurements[i]);
    }
    char buffer[1024];
    serializeJson(doc, buffer);
    String topic = "l1/measurement/session/batch/" + appData.macAddress;
    mqttClient.publish(topic.c_str(), buffer);
    printf("Odesilam batch mereni: %s\n na topicu: %s", buffer, topic.c_str());
}
void NetworkManager::sendConfigAck()
{
    JsonDocument doc;
    doc["deviceID"] = appData.macAddress;
    doc["status"] = "ok";
    char buffer[1024];
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
        String isBatchString = doc["measContinuity"].as<String>();

        appData.typeMeas = (typeMeasString == "CONTINUAL"); // false = SESSION, true = CONTINUAL
        appData.isBatch = (isBatchString == "BATCH");
        Serial.println(" isBatch: " + String(appData.isBatch));
        float hz = doc["measIntervalHz"];
        appData.measureInterval = (hz > 0.0) ? (1000.0 / hz) : 100000;
        if (appData.measureInterval > appData.sendInterval)
        {
            appData.sendInterval = appData.measureInterval; // pokud je měřicí interval delší než interval odesílání
        }
        appData.isRegistered = true;
        appData.configReceived = true;
    }
    else if (topicStr == "l2/config/" + appData.macAddress)
    {
        String typeMeasString = doc["typeMeasurement"].as<String>();
        appData.typeMeas = (typeMeasString == "CONTINUAL"); // false = SESSION, true = CONTINUAL
        if (typeMeasString == "CONTINUAL")
        {
            currentState = MEASURING_CONT; // Přechod do WAITING_CONFIG, kde se zkontroluje, zda máme všechny potřebné informace pro přechod do měření
        }
        else if (typeMeasString == "SESSION")
        {
            currentState = MEASURING_START; // Přechod do MEASURING_START, kde se čeká na startovací příznak z L1
            appData.sessionName = doc["sessionName"].as<String>();
        }
        printf("Received config: typeMeasurement=%s, sessionName=%s\n", typeMeasString.c_str(), appData.sessionName.c_str());
        String isBatchString = doc["measContinuity"].as<String>();
        appData.isBatch = (isBatchString == "BATCH");
        float hz = doc["measIntervalHz"];
        appData.measureInterval = (hz > 0.0) ? (1000.0 / hz) : 100000;
        if (appData.measureInterval > appData.sendInterval)
        {
            appData.sendInterval = appData.measureInterval; // pokud je měřicí interval delší než interval odesílání
        }
        sendConfigAck();
        appData.configReceived = true;
    }
    else if (topicStr == "l1/start/" + appData.macAddress)
    {
        appData.start = doc["is_active"];
    }
}