#include "Config.h"
#include "READERHID.h"
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN         9           // Configurable, see typical pin layout above
#define SS_PIN          10          // Configurable, see typical pin layout above

MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance.

// Number of known default keys (hard-coded)
#define NR_KNOWN_KEYS   7
// Known keys, including default MIFARE key
byte knownKeys[NR_KNOWN_KEYS][MFRC522::MF_KEY_SIZE] = {
    {0x72, 0x65, 0x74, 0x73, 0x61, 0x6d}, // Cyclon:retsam
    {0x37, 0x21, 0x53, 0x6a, 0x72, 0x40}, // T3: %!53jr@
    {0x23, 0x57, 0x6e, 0x6a, 0x30, 0x21}, // T2:#Wnj0!
    {0x44, 0x4D, 0x54, 0x23, 0x30, 0x31}, // T1:DMT#1.
    {0x21, 0x44, 0x4D, 0x54, 0x31, 0x21}, // T1:!DMT1!
    {0x5e, 0x4e, 0x21, 0x70, 0x40, 0x6a}, // T1JP:^N!p@j
    {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}  // Default MIFARE key
};

READERHID_ ReaderHID;

// Function to dump byte array to Serial (from working try_key)
void dump_byte_array(byte *buffer, byte bufferSize) {
    for (byte i = 0; i < bufferSize; i++) {
        Serial.print(buffer[i] < 0x10 ? " 0" : " ");
        Serial.print(buffer[i], HEX);
    }
}

void setup() {
    Serial.begin(9600);         // Initialize serial for debugging      // Wait for serial port (for Leonardo/Pro Micro)
    delay(500);
    SPI.begin();                // Init SPI bus
    SPI.setClockDivider(SPI_CLOCK_DIV16); // Slow SPI to 1 MHz (for 16 MHz Arduino)
    mfrc522.PCD_Init();         // Init MFRC522 card
    Serial.println(F("MFRC522-HID Initialized"));
    mfrc522.PCD_DumpVersionToSerial();  // Show MFRC522 version
}

boolean try_key(MFRC522::MIFARE_Key *key, byte keyType) {
    boolean result = false;
    byte buffer[18];
    byte status;
    byte name[32];  // Buffer for concatenated block 1 + block 2 data

    Serial.print(F("Trying key "));
    Serial.print(keyType == MFRC522::PICC_CMD_MF_AUTH_KEY_A ? "A" : "B");
    Serial.print(F(": "));
    for (byte i = 0; i < MFRC522::MF_KEY_SIZE; i++) {
        Serial.print(key->keyByte[i] < 0x10 ? " 0" : " ");
        Serial.print(key->keyByte[i], HEX);
    }
    Serial.println();

    // Authenticate for block 1
    status = mfrc522.PCD_Authenticate(keyType, 1, key, &(mfrc522.uid));
    if (status != MFRC522::STATUS_OK) {
        if (!mfrc522.PICC_IsNewCardPresent()) {
            Serial.println(F("Card no longer present"));
            return false;
        }
        if (!mfrc522.PICC_ReadCardSerial()) {
            Serial.println(F("Failed to re-select card"));
            return false;
        }
        Serial.print(F("Auth block 1 failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return false;
    }
    Serial.println(F("Auth block 1 succeeded"));

    // Read block 1
    byte byteCount = sizeof(buffer);
    status = mfrc522.MIFARE_Read(1, buffer, &byteCount);
    if (status != MFRC522::STATUS_OK) {
        Serial.print(F("Read block 1 failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return false;
    }
    memcpy(name, buffer, 16);  // Copy block 1 to name buffer
    Serial.print(F("Block 1 read:"));
    dump_byte_array(buffer, 16);
    Serial.println();

    // Authenticate for block 2
    status = mfrc522.PCD_Authenticate(keyType, 2, key, &(mfrc522.uid));
    if (status != MFRC522::STATUS_OK) {
        Serial.print(F("Auth block 2 failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return false;
    }
    Serial.println(F("Auth block 2 succeeded"));

    // Read block 2
    byteCount = sizeof(buffer);
    status = mfrc522.MIFARE_Read(2, buffer, &byteCount);
    if (status != MFRC522::STATUS_OK) {
        Serial.print(F("Read block 2 failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return false;
    }
    memcpy(name + 16, buffer, 16);  // Copy block 2 to name buffer
    Serial.print(F("Block 2 read:"));
    dump_byte_array(buffer, 16);
    Serial.println();

    // Send the 32-byte name via HID
    int sent = ReaderHID.sendData(name);
    Serial.print(F("HID data sent, bytes: "));
    Serial.println(sent);
    result = true;

    mfrc522.PICC_HaltA();       // Halt PICC
    mfrc522.PCD_StopCrypto1();  // Stop encryption on PCD
    return result;
}

void loop() {
    // Look for new cards
    if (!mfrc522.PICC_IsNewCardPresent()) {
        return;
    }
    Serial.println(F("New card detected"));

    // Select one of the cards
    if (!mfrc522.PICC_ReadCardSerial()) {
        Serial.println(F("Failed to select card"));
        return;
    }
    Serial.print(F("Card selected, UID: "));
    for (byte i = 0; i < mfrc522.uid.size; i++) {
        Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
        Serial.print(mfrc522.uid.uidByte[i], HEX);
    }
    Serial.println();

    // Get PICC type
    byte piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    Serial.print(F("PICC Type: "));
    Serial.println(mfrc522.PICC_GetTypeName(piccType));

    // Try the known default keys with both Key A and Key B
    MFRC522::MIFARE_Key key;
    boolean success = false;
    for (byte k = 0; k < NR_KNOWN_KEYS; k++) {
        // Copy the known key into the MIFARE_Key structure
        for (byte i = 0; i < MFRC522::MF_KEY_SIZE; i++) {
            key.keyByte[i] = knownKeys[k][i];
        }
        // Try Key A
        if (try_key(&key, MFRC522::PICC_CMD_MF_AUTH_KEY_A)) {
            success = true;
            Serial.println(F("Key A succeeded, delaying 3s"));
            delay(3000);  // Delay to avoid re-sending while card is present
            break;
        }
        // Try Key B
        if (try_key(&key, MFRC522::PICC_CMD_MF_AUTH_KEY_B)) {
            success = true;
            Serial.println(F("Key B succeeded, delaying 3s"));
            delay(3000);  // Delay to avoid re-sending while card is present
            break;
        }
    }
    if (!success) {
        Serial.println(F("No key succeeded"));
    }
}