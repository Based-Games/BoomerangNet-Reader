import hid, sys
from emu.data.constants import DataConstants

class Reader:
    @classmethod        
    def loadDevice(self):
        devices = hid.enumerate(DataConstants.CARDIO_VID, DataConstants.CARDIO_PID)
        if len(devices) == 0:
            print('Unable to find any MFRC522 HID devices!\nPlease make sure to plug in the device.')
            sys.exit()

        print(f'Found {len(devices)} MFRC522 HID device(s)!\nNote that ONLY the FIRST will be used!')

        for dev_info in devices:
            if dev_info['serial_number'] != DataConstants.CARDIO_SN:
                print(f'This device serial does not match: {dev_info["serial_number"]}\nRefusing to connect!')
                continue
            
            device = hid.Device(DataConstants.CARDIO_VID, DataConstants.CARDIO_PID, DataConstants.CARDIO_SN, dev_info['path'])
            print(f'\nMFRC522 HID Information:\nSerial: {device.serial}\nProduct: {device.product}\nManufacturer: {device.manufacturer}')

            return device

    @classmethod
    def pollDevice(self, device: hid.Device):
        data = device.read(128, 200)
        print(data)
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
            card_hex = card_data
            return card_hex