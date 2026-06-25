import argparse
import sys
import time

from emu.data.constants import Packet, DataConstants
from emu.reader import Reader
from emu.serial import Serial

class TechnikaEmu:

    def __init__(self):
        self.card_UID = [0x00] * 4
        self.card_ID = [0x00] * 20
        self.auth_bad = False
        self.eject_tries = 0

    def process_request(self, packet: Packet):
        cmd = packet.command
        if cmd == DataConstants.CMD_READER_INIT:
            return DataConstants.build_static_response(
                DataConstants.RESPONSE_INIT
            )
        
        elif cmd == DataConstants.CMD_EJECT_CARD:
            if self.auth_bad and self.eject_tries < 4:
                self.eject_tries += 1

                return DataConstants.build_static_response(
                    DataConstants.RESPONSE_EJECT_NO
                )

            self.card_ID = [0x00] * 20
            self.card_UID = [0x00] * 4
            return DataConstants.build_static_response(
                DataConstants.RESPONSE_EJECT_OK
            )
        
        elif cmd == DataConstants.CMD_CARD_PRESENT:
            if self.card_ID == [0x00] * 20:
                return DataConstants.build_static_response(
                    DataConstants.RESPONSE_CARD_FALSE
                )

            return DataConstants.build_static_response(
                DataConstants.RESPONSE_CARD_TRUE
            )
        
        elif cmd == DataConstants.CMD_GET_UID:
            return DataConstants.build_uid_response(
                self.card_UID
            )

        elif cmd == DataConstants.CMD_AUTH:
            game = DataConstants.identify_auth_key(packet.payload)
            if game:
                print(f"AUTH: {game}")
                self.auth_bad = False

                response = bytes([
                    0x02,
                    0x00,
                    0x04,
                    0x35,
                    0x32,
                    packet.sector,
                    0x59,
                    0x03,
                ])

                print(response)

                return DataConstants.build_static_response(response)

            print("AUTH FAILED")
            self.auth_bad = True
            return DataConstants.build_static_response(
                DataConstants.RESPONSE_AUTH_BAD
            )

        elif cmd == DataConstants.CMD_READ_BLOCK:
            if len(packet.payload) == 0:
                return None
            block = packet.payload[0]

            store = self.card_ID
            if packet.sector == 15 and block == 2:
                self.card_ID = [0x00] * 20
                self.card_UID = [0x00] * 4

            return DataConstants.build_block_response(
                packet.sector,
                block,
                store
            )

        return None

    def readSerial(self, com, reader):
        if not com.in_waiting:
            return

        request = com.read_all()
        com.write(b"\x06")
        time.sleep(.002)

        confirm = com.read_all()
        if confirm != b"\x05":
            return

        try:
            packet = DataConstants.parse_packet(request)
        except Exception as e:
            print(f"Packet parse failed: {e}")
            return

        if packet.command == DataConstants.CMD_FIND_CARD:
            if self.card_ID == [0x00] * 20:
                cardid = Reader.pollDevice(reader)

                if cardid is not None:
                    while len(cardid) < 20:
                        cardid += b"0"

                    self.card_ID = list(cardid[:20])
                    self.card_UID = list(cardid[:4])
                    self.auth_bad = False
                    self.eject_tries = 0

            response = DataConstants.build_static_response(
                DataConstants.RESPONSE_CARD_TRUE
                if self.card_ID != [0x00] * 20
                else DataConstants.RESPONSE_CARD_FALSE
            )

        else:
            response = self.process_request(packet)

        if response:
            com.write(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--com_port",
        type=str,
        default="COM9"
    )
    parser.add_argument(
        "--baud_rate",
        type=int,
        default=9600
    )
    args = parser.parse_args()

    emulator = TechnikaEmu()
    com = Serial.openSerial(
        args.com_port,
        args.baud_rate
    )
    reader = Reader.loadDevice()

    print("Technika Emulator Started")
    while True:
        try:
            emulator.readSerial(
                com,
                reader
            )

        except KeyboardInterrupt:
            print("goodbye!")
            sys.exit()