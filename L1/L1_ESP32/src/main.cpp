#include <Arduino.h>
#include "Config.h"
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
const unsigned long TIMEOUT_MS = 10000;

void setup()
{
    Serial.begin(9600);
    sensor.init();
    network.init();
    Serial.println("System start. MAC: " + appData.macAddress);
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
        {
            Serial.println("Chyba: Timeout registrace z L2. Zkousim znovu...");
            currentState = REGISTERING;
        }
        break;

    case MEASURING_CONT:
    case MEASURING_START:
        if (!network.isConnected())
        {
            Serial.println("Chyba: Ztrata spojeni behem mereni!");
            currentState = CONNECTING;
            lastActionTime = millis();
            break;
        }

        // Podmínka pro měření: (Kontinuální) NEBO (Session + start flag)
        if (currentState == MEASURING_CONT || (currentState == MEASURING_START && appData.start))
        {
            if (millis() - lastMeasureTime >= appData.measureInterval)
            {
                lastMeasureTime = millis();

                float temp = sensor.getTemperature();
                Serial.printf("Mereni: %.2f C\n", temp);
                network.sendMeasurement(temp);
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