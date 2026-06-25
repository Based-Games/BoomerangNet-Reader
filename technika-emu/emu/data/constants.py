from dataclasses import dataclass
from typing import Optional

@dataclass
class Packet:
    command: str
    sector: int
    payload: bytes
    checksum: int
    raw: bytes

class DataConstants:
    """
    Technika/CardIO protocol definitions.
    """

    CARDIO_VID = 0x1CCF
    CARDIO_PID = 0x5253
    CARDIO_SN = "MFRC522"

    CARD_UID_SIZE = 4
    CARD_ID_SIZE = 20
    
    RESPONSE_INIT = b'\x02\x00\x03\x31\x30\x59\x03'

    RESPONSE_AUTH_OK = b"\x02\x00\x04\x35\x32\x00\x59\x03"
    RESPONSE_AUTH_BAD = b"\x02\x00\x04\x35\x32\x00\x4e\x03"

    RESPONSE_CARD_FALSE = b"\x02\x00\x03\x31\x30\x4e\x03"
    RESPONSE_CARD_TRUE = b"\x02\x00\x03\x35\x30\x59\x03"

    RESPONSE_EJECT_OK = b"\x02\x00\x03\x32\x30\x59\x03"
    RESPONSE_EJECT_NO = b"\x02\x00\x03\x32\x30\x4e\x03"

    RESPONSE_UID_HEADER = b"\x02\x00\x07\x35\x31\x59"

    AUTH_KEYS = {
        bytes.fromhex("37 21 53 6A 72 40"): "TECHNIKA",
        bytes.fromhex("5E 4E 21 70 40 6A"): "TECHNIKA1_JP",
        bytes.fromhex("23 57 6E 6A 30 21"): "TECHNIKA2",
        b"retsam": "CYCLON",
    }

    CMD_READER_INIT = "10"
    CMD_EJECT_CARD = "20"
    CMD_CARD_PRESENT = "30"
    CMD_FIND_CARD = "50"
    CMD_GET_UID = "51"
    CMD_AUTH = "52"
    CMD_READ_BLOCK = "53"

    @classmethod
    def calc_bcc(cls, data: bytes) -> bytes:
        bcc = 0

        for byte in data:
            bcc ^= byte

        return bytes([bcc])

    @classmethod
    def verify_bcc(cls, packet: bytes) -> bool:
        if len(packet) < 2:
            return False

        return cls.calc_bcc(packet[:-1])[0] == packet[-1]

    @classmethod
    def parse_packet(cls, data: bytes) -> Packet:
        if data[0:2] != b"\x02\x00":
            raise ValueError("Invalid header")

        if data[-2] != 0x03:
            raise ValueError("Invalid ETX")

        command = data[3:5].decode("ascii")
        sector = data[5]
        payload = data[6:-2]

        print(
            f"CMD={command} "
            f"SECTOR={sector} "
            f"PAYLOAD={payload.hex(' ')}"
        )

        return Packet(
            command=command,
            sector=sector,
            payload=payload,
            checksum=data[-1],
            raw=data
        )

    @classmethod
    def identify_auth_key(cls, payload: bytes) -> Optional[str]:
        return cls.AUTH_KEYS.get(payload)

    @classmethod
    def build_uid_response(cls, uid: list[int]) -> bytes:
        data = (
            cls.RESPONSE_UID_HEADER +
            bytes(uid) +
            b"\x03"
        )

        return data + cls.calc_bcc(data)

    @classmethod
    def build_block_response(cls, sector: int, block: int, card_id: list[int]) -> bytes:
        header = bytes([
            0x02,
            0x00,
            0x15,
            0x35,
            0x33,
            sector,  # dynamic sector
            block,   # dynamic block
            0x59,
        ])

        if sector == 0:
            if block == 1:
                payload = bytes(card_id[:16])
            elif block == 2:
                payload = bytes(card_id[16:20]) + (b"\x00" * 12)
        else:
            payload = b"\x00" * 16

        data = header + payload + b"\x03"
        return data + cls.calc_bcc(data)

    @classmethod
    def build_static_response(cls, response: bytes) -> bytes:
        return response + cls.calc_bcc(response)
