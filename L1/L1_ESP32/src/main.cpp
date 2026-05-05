#include "max6675.h"
#include "secrets.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- KONFIGURACE ---

String name = "ESP32_Test";
String sensorType = "MAX6675_Thermocouple";
String convesion_rule = "LINEAR"; // Pravidlo pro převod dat, Enum: 'NONE', 'LINEAR', 'POLYNOMIAL', 'QAUDRATIC' TEXT CHECK QUAD: ax2+bx+c; LIN= a=0

int param_a = 0; // Ukázka dalšího parametru, který by mohl být posílán při registraci
int param_b = 0; // Další ukázkový parametr
int param_c = 0; // Třetí ukázkový parametr
int small_id = 0;
int local_channel = 0; // L2 ID senzoru, které nám přiřadí L2 po registraci
bool isRegistered = false;
bool config = false;
bool typeMeas = false;
bool start = false;
String typeMeasString;

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
    MEASURING_START,
    MEASURING_CONT,
    ERROR_STATE
};
State currentState = INIT;

// Časovače pro neblokující kód
unsigned long lastActionTime = 0;
unsigned long lastMeasureTime = 0;
unsigned long MEASURE_INTERVAL = 5000;
float hz = 0;
const unsigned long TIMEOUT_MS = 10000;
void sendConfigAck()
{
    JsonDocument doc;
    doc["deviceID"] = macString;
    doc["status"] = "ok";
    char buffer[128];
    serializeJson(doc, buffer);
    String topic = "l1/config_ack/" + macString;
    client.publish(topic.c_str(),
                   buffer);
    printf("Odesilam config ACK: %s\n", buffer);
}
// --- MQTT CALLBACK (Asynchronní příjem dat) ---
void callback(char *topic, byte *message, unsigned int length)
{
    String msg;
    for (int i = 0; i < length; i++)
    {
        msg += (char)message[i];
    }

    Serial.print("Prijata zprava na topicu [" + String(topic) + "] s obsahem: " + msg);
    String responseTopic = "l1/registration/response/" + macString;
    if (String(topic) == responseTopic)
    {
        JsonDocument doc;
        deserializeJson(doc, msg);
        small_id = doc["short_id"];                           // L2 nám přiřadí tento krátký ID pro další komunikaci
        local_channel = doc["local_channel"];                 // L2 nám přiřadí tento ID SENZORU pro další komunikaci
        typeMeasString = doc["typeMeasurement"].as<String>(); // L2 nám přiřadí tento typ měření (nepovinné, záleží na implementaci L2)
        hz = doc["measIntervalHz"];                           // L2 nám přiřadí tento interval pro měření (nepovinné, záleží na implementaci L2)
        if (hz > 0.0)
        {
            MEASURE_INTERVAL = (1000.0 / hz);
        }
        else
        {
            Serial.println("ERROR: hz = 0");
            MEASURE_INTERVAL = 100000;
        }
        if (typeMeasString == "SESSION")
        {
            typeMeas = 0;
        }
        else if (typeMeasString == "CONTINUAL")
        {
            typeMeas = 1;
        }
        isRegistered = true;
        Serial.print("ID: " + String(small_id) + " | local_channel: " + String(local_channel));
    }
    String updateTopic = "l2/config/" + macString;
    if (String(topic) == updateTopic)
    {

        JsonDocument doc;
        deserializeJson(doc, msg);
        printf("Prijata konfigurace: %s\n", msg.c_str());
        typeMeasString = doc["typeMeasurement"].as<String>(); // L2 nám přiřadí tento typ měření (nepovinné, záleží na implementaci L2)
        hz = doc["measIntervalHz"];                           // L2 nám přiřadí tento interval pro měření (nepovinné, záleží na implementaci L2)
        if (hz > 0.0)
        {
            MEASURE_INTERVAL = (1000.0 / hz);
        }
        else
        {
            Serial.println("ERROR: hz = 0");
            MEASURE_INTERVAL = 100000;
        }
        if (typeMeasString == "SESSION")
        {
            typeMeas = 0;
        }
        else if (typeMeasString == "CONTINUAL")
        {
            typeMeas = 1;
        }
        sendConfigAck();
        currentState = WAITING_CONFIG;
    }
    String startTopic = "l1/start/" + macString;
    if (String(topic) == startTopic)
    {
        JsonDocument doc;
        deserializeJson(doc, msg);
        start = doc["start"];
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
                    Serial.println("MQTT Pripojeno!"); // Přihlášení k odběru odpovědi
                    String subReg = "l1/registration/response/" + macString;
                    String subConfig = "l2/config/" + macString;
                    String subStart = "l1/start/" + macString;
                    client.subscribe(subReg.c_str());
                    client.subscribe(subConfig.c_str());
                    client.subscribe(subStart.c_str());
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
        if (isRegistered && typeMeas) // Pokud jsme zaregistrováni a máme nastavený typ měření, můžeme přejít do měření
        {
            Serial.println("Stav: Prechod do MEASURING_CONT");
            currentState = MEASURING_CONT;
        }
        else if (isRegistered && !typeMeas) // Pokud jsme zaregistrováni, ale nemáme nastavený typ měření, můžeme přejít do měření, ale upozorníme na to
        {
            Serial.println("Stav: Prechod do MEASURING_START");
            currentState = MEASURING_START;
        }
        // Kontrola timeoutu (pokud L2 neodpoví)
        else if (millis() - lastActionTime > TIMEOUT_MS)
        {
            Serial.println("Chyba: Timeout registrace z L2. Zkousim znovu...");
            currentState = REGISTERING;
        }
        break;

    case MEASURING_CONT:
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

    case MEASURING_START:
        // Kontrola, zda nám nespadlo spojení
        if (!client.connected() || WiFi.status() != WL_CONNECTED)
        {
            Serial.println("Chyba: Ztrata spojeni behem mereni!");
            currentState = CONNECTING;
            lastActionTime = millis();
            break;
        }
        // Neblokující měření
        if (start && millis() - lastMeasureTime >= MEASURE_INTERVAL)
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