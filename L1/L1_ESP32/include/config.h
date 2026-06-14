#pragma once
#include <Arduino.h>

// --- KONFIGURACE ZAŘÍZENÍ ---
const String DEVICE_NAME = "ESP32_Test";
const String SENSOR_TYPE = "MAX6675_Thermocouple";
const String CONVERSION_RULE = "LINEAR";
const int PARAM_A = 0;
const int PARAM_B = 0;
const int PARAM_C = 0;
const int batchLimit = 100; // Kolik měření čekat před odesláním v Batch režimu

// --- PINY ---
const int PIN_THERMO_DO = 19;
const int PIN_THERMO_CS = 23;
const int PIN_THERMO_CLK = 5;

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
extern State currentState;

// --- STRUKTURA PRO SDÍLENÁ DATA---
// Tuto strukturu bude upravovat NetworkManager (když přijde MQTT)
// a číst ji bude hlavní program.
struct AppData
{
    String macAddress;
    int small_id = 0;
    int local_channel = 0;
    bool isRegistered = false;
    bool configReceived = false; // Příznak pro přechod do WAITING_CONFIG
    bool typeMeas = false;       // 0 = SESSION, 1 = CONTINUAL
    bool start = false;
    unsigned long measureInterval = 5000;

    bool isBatch = false;               // Dead value pro budoucí rozšíření
    unsigned long sendInterval = 10000; // Interval odesílání v Batch režimu
    int currentBatchCount = 0;
    int batchMeasurements[batchLimit]; // Pole pro uchování měření v Batch režimu
    String sessionName;
};
