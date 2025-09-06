import serial, sys, hid, time, argparse
from emu.data.constants import DataConstants
from emu.reader import Reader
from emu.serial import Serial

class TechnikaEmu():
    def __init__(self) -> None:
        self.card_UID = [0x00] * 4
        self.card_ID = [0x00] * 20
        self.auth_bad = False
        self.eject_tries = 0 # Max of 4 eject tries before we agree to eject when auth is bad.

        self.reading_cards = False

    def readSerial(self, com: serial.Serial, reader: hid.Device) -> None:
        '''
        Reads data from the serial port, decides what to do with said data.
        Given the opened serial port.

        Workflow:
            - Game sends request
            - Reader says "i am ready"
            - Game sends "confirmed"
            - Reader sends response
        '''
        if com.in_waiting:
            s_data = com.read_all()
            time.sleep(.025)
            com.write(b'\x06')

            confirm = com.read_all()
            time.sleep(.025)
            if confirm == b'\x05':
                status, stype = DataConstants.processRequest(s_data)
                
                # Here's where we start polling the reader.
                if stype == DataConstants.REQUEST_TYPE_STATIC:
                    if status == DataConstants.STATUS_AUTH_KEY:
                        if self.card_ID[-12:] == b'000000000000':
                            status = DataConstants.STATUS_AUTH_KEY_BAD
                            self.card_ID = [0x00] * 20
                            self.card_UID = [0x00] * 4
                            self.auth_bad = True

                    elif status == DataConstants.STATUS_FIND_CARD:
                        if self.card_ID == [0x00] * 20:
                            cardid = Reader.pollDevice(reader)
                            if cardid != None:
                                while len(cardid) < 20:
                                    cardid += b'0'
                                self.card_ID = cardid
                                self.card_UID = cardid[:4]
                                self.auth_bad = False
                                self.eject_tries = 0

                                status = DataConstants.STATUS_FIND_CARD_OK
                        else:
                            status = DataConstants.STATUS_FIND_CARD_OK

                    elif status == DataConstants.STATUS_EJECT_CARD:
                        if self.auth_bad and self.eject_tries <= 4:
                            status = DataConstants.STATUS_EJECT_CARD_NO
                            self.eject_tries += 1

                    response = DataConstants.sendGeneric(status, stype)

                elif stype == DataConstants.REQUEST_TYPE_GENERATED:
                    if status == DataConstants.STATUS_GET_UID:
                        response = DataConstants.sendUID(status, [0xA5, 0x4A, 0x0A, 0xDF])

                    elif status in [DataConstants.STATUS_GET_S0_B1, DataConstants.STATUS_GET_S0_B2]:
                        response = DataConstants.sendCardID(status, self.card_ID)

                    if DataConstants.STATUS_GET_S0_B2 == status:
                        self.card_ID = [0x00] * 20
            
                time.sleep(.025)
                com.write(response + DataConstants.calcBCC(response))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--com_port', type=str, default="COM9")
    parser.add_argument('--baud_rate', type=int, default=9600)
    parser.add_argument('--card_file', type=str, default="./cards.json")
    args = parser.parse_args()

    main_class = TechnikaEmu()
    com = Serial.openSerial(args.com_port, args.baud_rate)
    reader = Reader.loadDevice()

    print('\nWelcome to Technika-Emu!\nThis software will let you use a BN-RC522 HID Reader on DJMax Technika.')
    print('Please connect a game to get started.\n')

    while True:
        try:
            main_class.readSerial(com, reader)
        except KeyboardInterrupt:
            print('goodbye!')
            sys.exit()