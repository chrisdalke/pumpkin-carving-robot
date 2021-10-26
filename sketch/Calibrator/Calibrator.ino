#include <Wire.h>
#include <VL53L0X.h>

VL53L0X sensor;

void setup()
{
  Serial.begin(115200);
  
  // Configure Sensor
  Wire.begin();
  sensor.setTimeout(500);
  while (!sensor.init())
  {
    Serial.println("Failed to detect and initialize sensor!");
    delay(1000);
  }
  sensor.setMeasurementTimingBudget(200000);
}

void loop()
{ 
  if( Serial.available() > 0 )
  {
    byte inByte = Serial.read();
    if (inByte == 0x0F)
    {
      // Poll sensor
      uint16_t reading = sense(20);

      // Pack data
      uint8_t packet[3];
      packet[0] = 0x0F;
      packet[1] = (reading & 0xFF00) >> 8;
      packet[2] = (reading & 0x00FF);

      // Write data
      for (uint8_t i=0; i<3; i++)
      {
        Serial.println(packet[i]);
      }
    }
  }
}

/*
 * Poll the ToF sensor to get a reading. The reading is an 
 * average over the number of samples specified.
 */
uint16_t sense(byte numSamples)
{
  uint16_t total = 0;

  for (int i=0; i < numSamples; i++)
  {
    total += sensor.readRangeSingleMillimeters();
  }

  return (uint16_t) (total/numSamples);
}
