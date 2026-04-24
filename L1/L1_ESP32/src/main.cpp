#include "max6675.h"
#include "secrets.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- KONFIGURACE ---
String name = "ESP32_Test";
String sensorType = "MAX6675_Thermocouple";
String convesion_rule = "LINEAR"; // Pravidlo pro převod dat, Enum: 'NONE', 'LINEAR', 'POLYNOMIAL', 'QAUDRATIC' TEXT CHECK QUAD: ax2+bx+c; LIN= a=0
int param_a = 0;                  // Ukázka dalšího parametru, který by mohl být posílán při registraci
int param_b = 0;                  // Další ukázkový parametr
int param_c = 0;                  // Třetí ukázkový parametr

int small_id = 0;
int local_channel = 0; // L2 ID senzoru, které nám přiřadí L2 po registraci
bool isRegistered = false;

// Senzor
int thermoDO = 19;
int thermoCS = 23;
int thermoCLK = 5;
MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

// Síť
const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;
const char *mqtt_server = MQTT_SERVER;

WiFiClient espClient;
PubSubClient client(espClient);
String macString;

// --- STAVOVÝ AUTOMAT ---
enum State
{
    INIT,
    CONNECTING,
    REGISTERING,
    WAITING_CONFIG,
    MEASURING,
    ERROR_STATE
};
State currentState = INIT;

// Časovače pro neblokující kód
unsigned long lastActionTime = 0;
unsigned long lastMeasureTime = 0;
const unsigned long MEASURE_INTERVAL = 5000; // 1 sekunda
const unsigned long TIMEOUT_MS = 10000;      // 10 sekund timeout

// --- MQTT CALLBACK (Asynchronní příjem dat) ---
void callback(char *topic, byte *message, unsigned int length)
{
    String msg;
    for (int i = 0; i < length; i++)
    {
        msg += (char)message[i];
    }

    Serial.print("Prijata zprava na topicu [");
    Serial.print(topic);
    Serial.print("]: ");
    Serial.println(msg);

    String responseTopic = "l1/registration/response/" + macString;
    if (String(topic) == responseTopic)
    {
        StaticJsonDocument<256> doc;

        deserializeJson(doc, msg);

        small_id = doc["short_id"];           // L2 nám přiřadí tento krátký ID pro další komunikaci
        local_channel = doc["local_channel"]; // L2 nám přiřadí tento ID SENZORU pro další komunikaci

        isRegistered = true;

        Serial.print("ID: ");
        Serial.println(small_id);

        Serial.print("Channel: ");
        Serial.println(local_channel);
    }
}

// --- SETUP ---
void setup()
{
    Serial.begin(9600);

    // Získání MAC adresy (Moderní a bezpečnější způsob na ESP32)
    WiFi.mode(WIFI_STA);
    macString = WiFi.macAddress();

    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);

    Serial.println("System start. MAC: " + macString);
}

// --- HLAVNÍ SMYČKA (STATE MACHINE) ---
void loop()
{
    // Vždy udržíme MQTT při životě a zpracujeme příchozí zprávy
    if (client.connected())
    {
        client.loop();
    }

    // Náš mozek
    switch (currentState)
    {

    case INIT:
        Serial.println("Stav: INIT -> Pripojuji k WiFi...");
        WiFi.begin(ssid, password);
        currentState = CONNECTING;
        lastActionTime = millis();
        break;

    case CONNECTING:
        // Čekáme na Wi-Fi
        if (WiFi.status() != WL_CONNECTED)
        {
            if (millis() - lastActionTime > TIMEOUT_MS)
            {
                Serial.println("Chyba: Wi-Fi Timeout. Zkousim znovu...");
                currentState = INIT;
            }
            break; // Vyskocime ze switche, at program bezi dal
        }

        // Wi-Fi připojeno, zkusíme MQTT
        if (!client.connected())
        {
            if (millis() - lastActionTime > 2000)
            { // Zkusíme se připojit každé 2s
                Serial.println("Stav: Pripojuji k MQTT...");
                String clientId = "ESP32-" + macString;
                if (client.connect(clientId.c_str()))
                {
                    Serial.println("MQTT Pripojeno!");
                    // Přihlášení k odběru odpovědi
                    String subTopic = "l1/registration/response/" + macString;
                    client.subscribe(subTopic.c_str());
                    currentState = REGISTERING;
                }
                lastActionTime = millis();
            }
        }
        else
        {
            currentState = REGISTERING;
        }
        break;

    case REGISTERING:
        Serial.println("Stav: REGISTERING -> Odesilam pozadavek...");
        {
            String payload = "{\"name\":\"" + name + "\",\"mac\":\"" + macString + "\",\"sensorType\":\"" + sensorType + "\",\"conversion\":\"" +
                             convesion_rule + "\",\"param_a\":" + String(param_a) + ",\"param_b\":" + String(param_b) + ",\"param_c\":" + String(param_c) + "  }";

            client.publish("l1/registration", payload.c_str());
        }
        isRegistered = false;
        lastActionTime = millis();
        currentState = WAITING_CONFIG;
        break;

    case WAITING_CONFIG:
        // Zde MCU nedělá nic, jen čeká na vlajku od callbacku
        if (isRegistered)
        {
            Serial.println("Stav: Prechod do MEASURING");
            currentState = MEASURING;
        }
        // Kontrola timeoutu (pokud L2 neodpoví)
        else if (millis() - lastActionTime > TIMEOUT_MS)
        {
            Serial.println("Chyba: Timeout registrace z L2. Zkousim znovu...");
            currentState = REGISTERING;
        }
        break;

    case MEASURING:
        // Kontrola, zda nám nespadlo spojení
        if (!client.connected() || WiFi.status() != WL_CONNECTED)
        {
            Serial.println("Chyba: Ztrata spojeni behem mereni!");
            currentState = CONNECTING;
            lastActionTime = millis();
            break;
        }

        // Neblokující měření
        if (millis() - lastMeasureTime >= MEASURE_INTERVAL)
        {
            lastMeasureTime = millis();

            float temp = thermocouple.readCelsius();
            Serial.print("Mereni: ");
            Serial.print(temp);
            Serial.println(" C");

            // Sestavení JSONu
            String payload = "{\"device_id\":\"" + String(small_id) + "\",\"local_channel\":\"" + String(local_channel) + "\",\"temp\":" + String(temp) + "}";
            client.publish("l1/test", payload.c_str());
        }
        break;

    case ERROR_STATE:
        // Sem pošleš MCU, pokud např. senzor nekomunikuje přes I2C
        Serial.println("Kriticka chyba HW!");
        delay(5000); // Tady jediný delay nevadí, jsme ve fatal erroru
        ESP.restart();
        break;
    }
}