#include <FastLED.h>

#define LED_PIN 5
#define NUM_LEDS 150
#define LED_TYPE WS2811
#define COLOR_ORDER GRB
#define NUM_BATCH 3
#define BAUDRATE 115200
#define UPDATES_PER_SECOND 240

CRGB leds[NUM_LEDS];
CRGB buffer[NUM_LEDS];
int ptr = NUM_LEDS;

void setup()
{
    Serial.begin(BAUDRATE);
    Serial.setTimeout(0);

    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    // FastLED.setBrightness(100);
}

CRGB current;

void read_current()
{
    if (Serial.available() >= 3)
    {
        Serial.readBytes((char *)&current, sizeof(CRGB));
    }
}

void update()
{
    for (int i = 0; i < NUM_LEDS; i++)
    {
        leds[i] = buffer[(ptr + i) % NUM_LEDS];
    }
}

void loop()
{
    if (ptr % NUM_BATCH == 0)
    {
        read_current();
    }

    buffer[ptr] = current;

    update();

    ptr -= 1;

    if (ptr < 0)
    {
        ptr = NUM_LEDS;
    }

    FastLED.show();
    // FastLED.delay(1000 / UPDATES_PER_SECOND);
}