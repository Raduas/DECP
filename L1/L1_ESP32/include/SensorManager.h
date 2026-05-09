#pragma once
#include <max6675.h>
#include "Config.h"

class SensorManager
{
public:
    SensorManager();
    void init();
    float getTemperature();

private:
    MAX6675 thermocouple;
};