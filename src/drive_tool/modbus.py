"""Small read-only Modbus RTU adapter.

Only function 03 (Read Holding Registers) is exposed in this first release.
No drive-control or parameter-write commands are implemented.
"""
from dataclasses import dataclass
from typing import Optional

try:
    from pymodbus.client import ModbusSerialClient
except ImportError:  # pragma: no cover - reported to the UI
    ModbusSerialClient = None


@dataclass
class ModbusSettings:
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    slave_id: int = 1
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    timeout: float = 1.0


class ReadOnlyModbus:
    def __init__(self):
        self.client = None
        self.settings: Optional[ModbusSettings] = None

    @property
    def connected(self) -> bool:
        return bool(self.client and self.client.connected)

    def connect(self, settings: ModbusSettings) -> None:
        if ModbusSerialClient is None:
            raise RuntimeError("pymodbus is not installed. Run: pip install -r requirements.txt")
        self.close()
        client = ModbusSerialClient(
            port=settings.port,
            baudrate=settings.baudrate,
            parity=settings.parity,
            stopbits=settings.stopbits,
            bytesize=settings.bytesize,
            timeout=settings.timeout,
        )
        if not client.connect():
            raise ConnectionError(f"Could not open serial port {settings.port}")
        self.client = client
        self.settings = settings

    def read_holding(self, address: int, count: int = 1):
        if not self.connected or not self.settings:
            raise ConnectionError("Not connected")
        if not 0 <= address <= 65535 or not 1 <= count <= 125:
            raise ValueError("Invalid Modbus register address/count")
        # pymodbus renamed the unit argument to device_id in newer releases.
        try:
            result = self.client.read_holding_registers(
                address=address, count=count, device_id=self.settings.slave_id
            )
        except TypeError:
            result = self.client.read_holding_registers(
                address=address, count=count, slave=self.settings.slave_id
            )
        if result.isError():
            raise IOError(str(result))
        return list(result.registers)

    def close(self):
        if self.client:
            try:
                self.client.close()
            finally:
                self.client = None
                self.settings = None
