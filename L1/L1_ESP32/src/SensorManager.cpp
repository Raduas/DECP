#include "SensorManager.h"

SensorManager::SensorManager() : thermocouple(PIN_THERMO_CLK, PIN_THERMO_CS, PIN_THERMO_DO) {}

void SensorManager::init()
{
    // Připrava senzoru (MAX6675 nepotřebuje speciální init() volání,
    // ale metoda se hodí pro budoucí rozšíření)
}

float SensorManager::getTemperature()
{
    return thermocouple.readCelsius();
}