import hid, sys

VID = 0x1CCF
PID = 0x5253
SERIAL = 'MFRC522'

class MFRC522HIDReader:

    def loadDevice(self):
        devices = hid.enumerate(VID, PID)
        if len(devices) == 0:
            print('Unable to find any MFRC522 HID devices!\nPlease make sure to plug in the device.')
            sys.exit()

        print(f'Found {len(devices)} MFRC522 HID device(s)!\nNote that ONLY the FIRST will be used!')

        for dev_info in devices:
            if dev_info['serial_number'] != SERIAL:
                print(f'This device serial does not match: {dev_info["serial_number"]}\nRefusing to connect!')
                continue
            
            device = hid.Device(VID, PID, SERIAL, dev_info['path'])
            print(f'\nMFRC522 HID Information:\nSerial: {device.serial}\nProduct: {device.product}\nManufacturer: {device.manufacturer}')

            return device

    def pollDevice(self, device: hid.Device):
        data = device.read(128, 200)
        if data == b'':
            return None
        else:
            report_id = data[0]
            if report_id != 1:
                print('Unexpected report ID!')
                return None
            
            card_data = data[1:33]  # 32 bytes of block data
            # Print as string, replacing non-printable with nothing
            name_str = ''.join(chr(b) if 32 <= b <= 126 else '' for b in card_data)
            print(f'\nCard Data (as string): {name_str}')
            # Also print hex for debugging
            card_hex = card_data.hex().upper()
            print(f'Card Data (hex): {card_hex}')

if __name__ == '__main__':
    reader = MFRC522HIDReader()
    device = reader.loadDevice()

    print('\n\nReader was set up properly!')
    print('Tap a card now to read the data.')
    while True:
        try:
            reader.pollDevice(device)
        except KeyboardInterrupt:
            print('Goodbye!')
            sys.exit()