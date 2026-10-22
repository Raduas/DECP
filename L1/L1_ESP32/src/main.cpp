#include <Arduino.h>
#include "config.h"
#include "SensorManager.h"
#include "NetworkManager.h"

// --- GLOBÁLNÍ OBJEKTY ---
AppData appData;
SensorManager sensor;
NetworkManager network(appData);

// --- STAVOVÉ PROMĚNNÉ ---
State currentState = INIT;
unsigned long lastActionTime = 0;
unsigned long lastMeasureTime = 0;
unsigned long lastBatchSendTime = 0;
const unsigned long TIMEOUT_MS = 10000;

void setup()
{
    Serial.begin(115200);
    sensor.init();
    network.init();
    Serial.println("System start. MAC: " + appData.macAddress);
}

bool checkConnection()
{
    if (!network.isConnected())
    {
        Serial.println("Chyba: Ztrata spojeni behem mereni!");
        currentState = CONNECTING;
        lastActionTime = millis();
        return false;
    }
    return true;
}

void loop()
{
    // Vždy udržujeme síť při životě
    network.loop();

    switch (currentState)
    {
    case INIT:
        Serial.println("Stav: INIT -> Pripojuji k WiFi...");
        network.connectWiFi(); // Spustí proces připojování
        currentState = CONNECTING;
        lastActionTime = millis();
        break;

    case CONNECTING:
        if (WiFi.status() != WL_CONNECTED)
        {
            if (millis() - lastActionTime > TIMEOUT_MS)
            {
                Serial.println("Chyba: Wi-Fi Timeout. Zkousim znovu...");
                currentState = INIT;
            }
            break;
        }

        if (!network.connectMQTT())
        {
            if (millis() - lastActionTime > 2000)
            {
                Serial.println("Stav: Pripojuji k MQTT...");
                lastActionTime = millis();
            }
        }
        else
        {
            Serial.println("MQTT Pripojeno!");
            currentState = REGISTERING;
        }
        break;

    case REGISTERING:
        Serial.println("Stav: REGISTERING -> Odesilam pozadavek...");
        network.sendRegistration();
        appData.isRegistered = false;
        appData.configReceived = false;
        lastActionTime = millis();
        currentState = WAITING_CONFIG;
        break;

    case WAITING_CONFIG:
        // Kontrola, zda NetworkManager zachytil l2/config/
        if (appData.configReceived)
        {
            appData.configReceived = false; // Reset flagu
            currentState = WAITING_CONFIG;  // V tvém původním kódu config padal sem
        }

        if (appData.isRegistered && appData.typeMeas)
        {
            Serial.println("Stav: Prechod do MEASURING_CONT");
            currentState = MEASURING_CONT;
        }
        else if (appData.isRegistered && !appData.typeMeas)
        {
            Serial.println("Stav: Prechod do MEASURING_START");
            currentState = MEASURING_START;
        }
        else if (millis() - lastActionTime > TIMEOUT_MS)
        { // error handling pro případ, že nedorazí registrace z L2
            Serial.println("Chyba: Timeout registrace z L2. Zkousim znovu...");
            currentState = REGISTERING;
        }
        break;

    case MEASURING_CONT:
        if (!checkConnection())
        {
            break;
        }
        if (millis() - lastMeasureTime >= appData.measureInterval)
        {
            lastMeasureTime = millis();
            float temp = sensor.getTemperature();
            if (appData.isBatch)
            {
                appData.batchMeasurements[appData.currentBatchCount] = temp;
                appData.currentBatchCount++;
                if (appData.currentBatchCount >= batchLimit or (appData.currentBatchCount > 0 && millis() - lastBatchSendTime >= appData.sendInterval))
                {
                    network.sendBatchMeasurement(appData.batchMeasurements, appData.currentBatchCount);
                    appData.currentBatchCount = 0;
                    lastBatchSendTime = millis();
                }
            }
            else
            {
                network.sendMeasurement(temp);
            }
        }
        break;

    case MEASURING_START:
        if (!checkConnection())
        {
            break;
        }
        // Podmínka pro měření: (Kontinuální) NEBO (Session + start flag)
        if (appData.start)
        {
            if (millis() - lastMeasureTime >= appData.measureInterval)
            {
                lastMeasureTime = millis();

                float temp = sensor.getTemperature();
                if (appData.isBatch)
                {
                    appData.batchMeasurements[appData.currentBatchCount] = temp;
                    appData.currentBatchCount++;
                    if (appData.currentBatchCount >= batchLimit or (appData.currentBatchCount > 0 && millis() - lastBatchSendTime >= appData.sendInterval))
                    {
                        network.sendBatchMeasurementSession(appData.batchMeasurements, appData.currentBatchCount);
                        appData.currentBatchCount = 0;
                        lastBatchSendTime = millis();
                    }
                }
                else
                {
                    network.sendMeasurementSession(temp);
                }
            }
        }
        break;

    case ERROR_STATE:
        Serial.println("Kriticka chyba HW!");
        delay(5000);
        ESP.restart();
        break;
    }
}
