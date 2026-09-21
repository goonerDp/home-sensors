"""BLE peripheral exposing BME280 readings over GATT.

Uses the standard Bluetooth SIG Environmental Sensing service (0x181A), so any
generic BLE app can read the values without knowing anything about this project.
"""

import bluetooth
import struct
from micropython import const

# IRQ event codes. The full list lives in the MicroPython bluetooth docs;
# these are the only two this peripheral needs to react to.
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

_ENV_SENSE_UUID = bluetooth.UUID(0x181A)

# Standard SIG characteristics, each with its own fixed wire format:
#   0x2A6E Temperature - sint16, unit 0.01 C
#   0x2A6F Humidity    - uint16, unit 0.01 %
#   0x2A6D Pressure    - uint32, unit 0.1 Pa
_FLAGS = bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY
_TEMP_CHAR = (bluetooth.UUID(0x2A6E), _FLAGS)
_HUMID_CHAR = (bluetooth.UUID(0x2A6F), _FLAGS)
_PRESS_CHAR = (bluetooth.UUID(0x2A6D), _FLAGS)

_ENV_SENSE_SERVICE = (_ENV_SENSE_UUID, (_TEMP_CHAR, _HUMID_CHAR, _PRESS_CHAR))

# Advertising data type codes, defined by the Bluetooth Core Specification.
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x03)

_MAX_ADV_PAYLOAD = const(31)


def build_adv_payload(name=None, services=None):
    """Assemble an advertising payload from length-type-value chunks.

    Every chunk is: one length byte, one type byte, then the value.
    The whole payload must fit in 31 bytes - that is a hard radio limit.
    """
    payload = bytearray()

    def append(adv_type, value):
        payload.extend(struct.pack("BB", len(value) + 1, adv_type))
        payload.extend(value)

    # 0x06 = LE General Discoverable + BR/EDR not supported.
    append(_ADV_TYPE_FLAGS, struct.pack("B", 0x06))

    if name:
        append(_ADV_TYPE_NAME, name.encode())

    if services:
        for uuid in services:
            raw = bytes(uuid)
            if len(raw) == 2:
                append(_ADV_TYPE_UUID16_COMPLETE, raw)

    if len(payload) > _MAX_ADV_PAYLOAD:
        raise ValueError("adv payload is {} bytes, max is 31".format(len(payload)))
    return payload


class BLESensor:
    def __init__(self, ble, name="esp32-sensor"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        # Registering the service returns one value handle per characteristic,
        # in the same order they were declared above.
        ((self._temp_h, self._humid_h, self._press_h),) = self._ble.gatts_register_services(
            (_ENV_SENSE_SERVICE,)
        )

        self._connections = set()
        self._payload = build_adv_payload(name=name, services=[_ENV_SENSE_UUID])
        self._advertise()
        print("BLE up | name:", name, "| mac:", self.mac())

    def mac(self):
        """Return this device's BLE address as a readable string."""
        _addr_type, addr = self._ble.config("mac")
        return ":".join("{:02X}".format(b) for b in addr)

    def _irq(self, event, data):
        """Called from the BLE stack. Keep it short - it runs in an IRQ context."""
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("central connected:", conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            print("central disconnected:", conn_handle)
            # Advertising stops on connect, so restart it to stay findable.
            self._advertise()

    def update(self, temp_c, pressure_pa, humidity_pct, notify=True):
        """Write the latest readings into the GATT table, in SIG wire format."""
        self._ble.gatts_write(self._temp_h, struct.pack("<h", int(round(temp_c * 100))))
        self._ble.gatts_write(self._humid_h, struct.pack("<H", int(round(humidity_pct * 100))))
        self._ble.gatts_write(self._press_h, struct.pack("<I", int(round(pressure_pa * 10))))

        # A read always returns whatever was last written. A notify additionally
        # pushes the value to anyone currently connected and subscribed.
        if notify:
            for conn_handle in self._connections:
                for handle in (self._temp_h, self._humid_h, self._press_h):
                    self._ble.gatts_notify(conn_handle, handle)

    def _advertise(self, interval_us=250_000):
        """250 ms between packets: quick to discover, fine while debugging."""
        self._ble.gap_advertise(interval_us, adv_data=self._payload)