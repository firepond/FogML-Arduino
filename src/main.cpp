#include <Arduino.h>
#include <Arduino_APDS9960.h>
#include <Arduino_LSM9DS1.h>
#include <Wire.h>

// #define DATA_LOGGER
// #define DEBUG

#include "fogml_config.h"

#define LEARNING_SAMPLES 32

#define RED 22
#define BLUE 24
#define GREEN 23
#define DEBUG
// #define DATA_LOGGER
#define FULL_ACC

float my_time_series[ACC_TIME_TICKS * ACC_AXIS];
int ticks_stored;

unsigned long time_before;
unsigned long time_after;

bool learning;
int learning_samples;

float score;

void setup() {
    Serial.begin(250000);

    pinMode(RED, OUTPUT);
    pinMode(BLUE, OUTPUT);
    pinMode(GREEN, OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);

    digitalWrite(RED, LOW);
    digitalWrite(BLUE, LOW);
    digitalWrite(GREEN, LOW);
    digitalWrite(LED_BUILTIN, LOW);

    digitalWrite(RED, HIGH);
    delay(200);
    digitalWrite(RED, LOW);

    if (!IMU.begin()) {
        Serial.println("Failed to initialize IMU!");
        while (1);
    }

    if (!APDS.begin()) {
        Serial.println("Error initializing APDS9960 sensor!");
        while (1);
    }

#ifdef DEBUG
    Serial.print("Accelerometer sample rate = ");
    Serial.print(IMU.accelerationSampleRate());
    Serial.println(" Hz");
#endif

    ticks_stored = 0;

    time_before = millis();

    learning = false;
    learning_samples = 0;
}

void led_all_off() {
    digitalWrite(GREEN, HIGH);
    digitalWrite(BLUE, HIGH);
    digitalWrite(RED, HIGH);
}

void print_timeseries(int ticks, int axis, float *tab) {
    for (int i = 0; i < ticks * axis; i++) {
        Serial.print(tab[i]);

        if (i < (ticks * axis - 1)) {
            Serial.print(", ");
        } else {
            Serial.println();
        }
    }
}

void proximity_detection() {
    if (APDS.proximityAvailable()) {
        int proximity = APDS.readProximity();

        if (proximity < 10) {
            Serial.println("LEARNING!");
            learning = true;
            delay(1000);
        }
    }
}

void check_serial_command() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();  // Remove whitespace

        if (command.equalsIgnoreCase("START LEARN")) {
            Serial.println("LEARNING!");
            learning = true;
            delay(100);
        }

        // check for reset command
        if (command.equalsIgnoreCase("RESET")) {
            Serial.println("Resetting learning samples.");
            // reset time series
            learning_samples = 0;
            ticks_stored = 0;
            time_before = millis();
            for (int i = 0; i < ACC_TIME_TICKS * ACC_AXIS; i++) {
                my_time_series[i] = 0.0f;
            }

            // clear  the reservoir
            for (int i = 0; i < MY_RESERVOIR_SIZE * FOGML_VECTOR_SIZE; i++) {
                my_reservoir[i] = 0.0f;
            }
            // clean k-distance and lrd
            for (int i = 0; i < MY_RESERVOIR_SIZE; i++) {
                my_kdistance[i] = 0.0f;
                my_lrd[i] = 0.0f;
            }
            learning = false;
            my_rs_config.k = 0;
            led_all_off();
            digitalWrite(BLUE, HIGH);
            Serial.println("Reservoir and learning samples reset.");
        }
    }
}

void loop() {
    if (IMU.accelerationAvailable()) {
        IMU.readAcceleration(my_time_series[ticks_stored * ACC_AXIS + 0],
                             my_time_series[ticks_stored * ACC_AXIS + 1],
                             my_time_series[ticks_stored * ACC_AXIS + 2]);

#ifdef FOGML_SEND_DATA
        Serial.print("P0: Acc: ");
        Serial.print(my_time_series[ticks_stored * ACC_AXIS + 0]);
        Serial.print(", ");
        Serial.print(my_time_series[ticks_stored * ACC_AXIS + 1]);
        Serial.print(", ");
        Serial.print(my_time_series[ticks_stored * ACC_AXIS + 2]);
        Serial.println("");
#endif

        ticks_stored++;

        if (ticks_stored == ACC_TIME_TICKS) {
            time_after = millis();

#ifdef FOGML_SEND_DATA
            Serial.print("P1: Hz = ");
            Serial.println(1000.0 / (time_after - time_before) * ACC_TIME_TICKS);
#endif

#ifdef DATA_LOGGER
            fogml_features_logger(my_time_series);
#else
            if (learning) {
                led_all_off();
                digitalWrite(BLUE, LOW);
                foglml_reservoir(my_time_series);
                digitalWrite(BLUE, HIGH);
                learning_samples++;

                // Display progress bar
                Serial.print("\rData collecting progress: [");
                int progress_width = 20;  // Width of progress bar
                int filled = (learning_samples * progress_width) / LEARNING_SAMPLES;

                for (int i = 0; i < progress_width; i++) {
                    if (i < filled) {
                        Serial.print("=");
                    } else {
                        Serial.print(" ");
                    }
                }

                Serial.print("] ");
                Serial.print(learning_samples);
                Serial.print("/");
                Serial.print(LEARNING_SAMPLES);
                Serial.print(" (");
                Serial.print((learning_samples * 100) / LEARNING_SAMPLES);
                Serial.println("%)   ");
                if (learning_samples >= LEARNING_SAMPLES) {
                    Serial.print("  ");
                    Serial.println("  samples collected ");
                    Serial.flush();
                    Serial.println("Learning samples collected, starting learning...");
                    led_all_off();
                    fogml_learning(my_time_series);
                    learning_samples = 0;
                    learning = false;
                    digitalWrite(BLUE, HIGH);

                    Serial.println("Learning completed!");

                    // blink the green LEN three times to indicate learn end
                    for (int i = 0; i < 3; i++) {
                        digitalWrite(GREEN, LOW);
                        delay(100);
                        digitalWrite(GREEN, HIGH);
                        delay(100);
                    }
                }

            } else {
                fogml_processing(my_time_series, &score);
                fogml_classification(my_time_series);

                if (score > 2.5) {
                    digitalWrite(RED, LOW);
                } else {
                    digitalWrite(RED, HIGH);
                }
            }

            // proximity_detection();
            check_serial_command();
#endif

            ticks_stored = 0;
            time_before = millis();
        }
    }

    delay(1);
}
