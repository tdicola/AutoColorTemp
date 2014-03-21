// Automatic Monitor Color Temperature
// Arduino Sketch
// Copyright 2014 Tony DiCola (tony@tonydicola.com)
// Released under an MIT license (http://opensource.org/licenses/MIT)

#include <Wire.h>
#include "Adafruit_TCS34725.h"

// Configure color sensor for longer (more accurate) integration time with low gain.
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_700MS, TCS34725_GAIN_1X);

void setup(void) {
  // Initialize serial connection and color sensor.
  Serial.begin(115200);
  tcs.begin();
}

void loop(void) {
  // Wait for a command to be sent on the serial port.
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '?') {
      // Take a light reading and send it to the PC.
      uint16_t r, g, b, c;
      tcs.getRawData(&r, &g, &b, &c);
      float red = r/float(c);
      float green = g/float(c);
      float blue = b/float(c);
      // Send reading as a comma separated line.
      Serial.print(red, 5);
      Serial.print(",");
      Serial.print(green, 5);
      Serial.print(",");
      Serial.println(blue, 5);
    } 
  }
  delay(10);
}
