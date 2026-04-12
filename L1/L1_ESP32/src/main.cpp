// this example is public domain. enjoy! https://learn.adafruit.com/thermocouple/

#include "max6675.h"
#include "secrets.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>

int thermoDO = 19;
int thermoCS = 23;
int thermoCLK = 5;
// Replace the next variables with your SSID/Password combination

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;
const char *mqtt_server = MQTT_SERVER;

MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi()
{
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char *topic, byte *message, unsigned int length)
{
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;

  for (int i = 0; i < length; i++)
  {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  // Feel free to add more if statements to control more GPIOs with MQTT

  // If a message is received on the topic esp32/output, you check if the message is either "on" or "off".
  // Changes the output state according to the message

  //    if (String(topic) == "esp32/output")
  //{
  //  Serial.print("Changing output to ");
  //  if (messageTemp == "on")
  //  {
  //    Serial.println("on");
  //    digitalWrite(ledPin, HIGH);
  //  }
  //  else if (messageTemp == "off")
  //  {
  //    Serial.println("off");
  //    digitalWrite(ledPin, LOW);
  //  }
  //}
}
void reconnect()
{
  // Loop until we're reconnected
  while (!client.connected())
  {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("ESP8266Client"))
    {
      Serial.println("connected");
      // Subscribe
      client.subscribe("esp32/output");
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup()
{
  Serial.begin(9600);

  Serial.println("MAX6675 test");
  // wait for MAX chip to stabilize
  delay(500);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop()
{
  // basic readout test, just print the current temp
  if (!client.connected())
  {
    reconnect();
  }
  client.loop();

  Serial.print("C = ");
  Serial.println(thermocouple.readCelsius());
  Serial.print("F = ");
  Serial.println(thermocouple.readFahrenheit());

  // For the MAX6675 to update, you must delay AT LEAST 250ms between reads!
  delay(1000);
  client.publish("l1/test", String(thermocouple.readCelsius()).c_str());
}
