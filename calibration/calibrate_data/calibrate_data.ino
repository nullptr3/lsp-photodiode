/*
#################################################
###### Photodiode Data Acquisition Script #######
#### Ben Cooper @ Living Solar Panels - UCSC ####
#################################################
*/

#include "config.h"

// recordings per minute
#define freq 1

// millisecond offset
#define offset 150

// milliseconds per minute
#define MS_PER_MIN 60000

Adafruit_IO_Feed *Photodiode = io.feed("photodiode-mv");

void setup() {
  // start the serial connection
  Serial.begin(115200);

  // connect to io.adafruit.com
  Serial.print("Connecting to Adafruit IO");
  io.connect();

  // wait for connection
  while(io.status() < AIO_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  // connection confirmed
  Serial.println();
  Serial.println(io.statusText());
}

void loop() {
  // get current time (ms)
  unsigned long start = miilis();
  
  // create temp variables
  float average = 0;
  int iter = 0;

  // loop until reached freq period
  while(millis() - start + offset < MS_PER_MIN / freq) {
    average += analogReadMilliVolts(A0);
    iter++;
  }
  
  // save to data stream
  Photodiode->save(average / iter);
}