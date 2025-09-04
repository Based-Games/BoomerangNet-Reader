# BoomerangNet-Reader

This project implements a firmware for an Arduino (e.g., Leonardo or Pro Micro) to read data from MIFARE Classic 1K RFID cards using an MFRC522 module and send the data over USB HID. The firmware authenticates the card using a set of known keys, reads blocks 1 and 2 from sector 0, and transmits the concatenated 32-byte data as an HID report. A Python script (`rc522.py`) is provided to receive and display the HID data on a computer.

## Features
- Reads MIFARE Classic 1K RFID cards using the MFRC522 module.
- Attempts authentication with a set of predefined keys for both Key A and Key B.
- Reads blocks 1 and 2 (32 bytes total) from sector 0.
- Sends data via USB HID with a custom Vendor ID (0x1CCF) and Product ID (0x5253).
- Includes Serial debugging output for troubleshooting.
- Includes a Python script to receive and display HID data as a string and hex.

## Hardware Requirements
- **Arduino Board**: Arduino Leonardo, Pro Micro, or any board with native USB HID support (ATmega32U4-based).
  - Must support 3.3V logic or use a 3.3V level shifter if running at 5V.
- **MFRC522 RFID Module**: Compatible with MIFARE Classic 1K cards.
- **MIFARE Classic 1K Card**: Card must use one of the known keys for sector 0.
- **Wiring**:
  - SS (Slave Select): Pin 10
  - RST (Reset): Pin 9
  - SCK, MOSI, MISO: SPI pins (check your board’s pinout)
  - VCC: 3.3V
  - GND: Ground
- **Level Shifter** (if using 5V Arduino): Required for SCK, MOSI, MISO, SS, and RST to convert 5V to 3.3V.

## Software Requirements
- **Arduino IDE**: For uploading the firmware.
- **MFRC522 Library**: Install via Arduino IDE Library Manager (`MFRC522` by Miguel Balboa).
- **Python 3**: For running the `test_rc522.py` script.
- **Python `hid` Library**: Install via `pip install hid`.

## Installation
1. **Set Up Hardware**:
   - Connect the MFRC522 module to your Arduino:
     - SS → Pin 10
     - RST → Pin 9
     - SCK, MOSI, MISO → SPI pins
     - VCC → 3.3V
     - GND → Ground
   - If using a 5V Arduino, use a 3.3V level shifter for SCK, MOSI, MISO, SS, and RST.
   - Ensure the MIFARE Classic 1K card is compatible and uses a known key.

2. **Install Arduino Dependencies**:
   - Open Arduino IDE.
   - Install the `MFRC522` library via Library Manager (`Tools > Manage Libraries`).
   - Open the `RC522-HID.ino` sketch in the Arduino IDE.

3. **Upload Firmware**:
   - Connect your Arduino to your computer.
   - Select your board (e.g., `Arduino Leonardo`) and port in the Arduino IDE.
   - Upload the sketch.
   - **Note**: Due to the custom VID/PID (0x1CCF:0x5253), you may need to double-tap the reset button to enter bootloader mode for uploading or reflashing.

4. **Install Python Dependencies**:
   - Install Python 3 if not already installed.
   - Install the `hid` library:
     ```bash
     pip install hid
     ```

## Usage
1. **Monitor Serial Output**:
   - Open the Arduino IDE Serial Monitor (9600 baud).
   - Tap a MIFARE Classic 1K card to the MFRC522 antenna (within 1–2 cm).
   - Observe the debug output, which includes:
     - Card detection and UID.
     - PICC type (should be `MIFARE 1K`).
     - Authentication attempts for each key (A and B).
     - Block 1 and 2 data (if successful).
     - HID data transmission status.

2. **Run Python Script**:
   - Save `test_rc522.py` to your computer.
   - Run the script:
     ```bash
     python test_rc522.py
     ```
   - Tap a card to the MFRC522 antenna.
   - The script will display:
     - Device information (Serial: `MFRC522`, Product: `MFRC522-HID`, Manufacturer: `CrazyRedMachine`).
     - Card data as a string (non-printable characters as `.`) and hex (32 bytes from blocks 1 and 2).

## Example Output
### Serial Monitor (Successful Read)
```
MFRC522-HID Initialized
[MFRC522 version info]
New card detected
Card selected, UID:  1C  89  A7  9E
PICC Type: MIFARE 1K
Trying key A:  FF  FF  FF  FF  FF  FF
Auth block 1 succeeded
Block 1 read:  00  01  02 ... (16 bytes)
Auth block 2 succeeded
Block 2 read:  10  11  12 ... (16 bytes)
HID data sent, bytes: 33
Key A succeeded, delaying 3s
```

### Python Script (Successful Read)
```
Found 1 MFRC522 HID device(s)!
Note that ONLY the FIRST will be used!

MFRC522 HID Information:
Serial: MFRC522
Product: MFRC522-HID
Manufacturer: CrazyRedMachine

Reader was set up properly!
Tap a card now to read the data.
Received 33 bytes
Card Data (as string): ........................
Card Data (hex): 000102...101112...
```

### Serial Monitor (Failed Authentication)
```
New card detected
Card selected, UID:  1C  89  A7  9E
PICC Type: MIFARE 1K
Trying key A:  72  65  74  73  61  6D
Auth block 1 failed: Timeout in communication.
Trying key B:  72  65  74  73  61  6D
Auth block 1 failed: Timeout in communication.
[Repeat for all keys]
No key succeeded
```

## Troubleshooting
- **No Card Detected**:
  - Check wiring (SS: Pin 10, RST: Pin 9, SCK/MOSI/MISO, VCC: 3.3V, GND).
  - Ensure the card is within 1–2 cm of the antenna.
  - Test with a different MIFARE Classic 1K card.
  - Swap the MFRC522 module to rule out hardware defects.

- **Authentication Fails (Timeout)**:
  - The card may use a custom key. Add the correct key to `knownKeys` in `RC522-HID.ino` if known.
  - Use tools like `mfcuk` or `mfoc` with a Proxmark3 to recover the card’s key.
  - Increase the delay in `try_key` to `delay(200)` before `PCD_Authenticate`.
  - Try a different MFRC522 module or Arduino.

- **No HID Data in Python**:
  - Ensure Serial Monitor shows `HID data sent, bytes: 33`.
  - Comment out the `serial_number` check in `test_rc522.py`:
    ```python
    device = hid.Device(VID, PID)  // Remove serial and path
    ```
  - Increase the timeout in `test_rc522.py` to `device.read(33, 2000)`.
  - Use a USB HID sniffer (e.g., Wireshark with USB capture) to verify reports.
  - Check Device Manager (Windows) for “MFRC522-HID”.

- **Reflashing Issues**:
  - Double-tap the reset button to enter bootloader mode due to custom VID/PID.

## Notes
- **Keys**: The firmware tries a set of known keys (listed in `RC522-HID.ino`) for sector 0. Add custom keys to the `knownKeys` array if needed.
- **Card Compatibility**: Only MIFARE Classic 1K cards are supported. Other card types (e.g., MIFARE Ultralight) will fail.
- **SPI Stability**: The firmware uses a slowed SPI clock (`SPI_CLOCK_DIV16`) to improve reliability. Adjust if needed for your hardware.

## Open-source Usage
This tool uses code found from https://github.com/CrazyRedMachine/PN5180-cardio for HID and code from https://github.com/6745/Replacement-Cyclon-Technika-Reader as a basis.