# Polytropic Heat Pump — Modbus Register List

Source: `Modbus_table_for_IVS_N_.pdf` (vendor document, not in repo).
Canonical definitions: `custom_components/polytropic_heatpump/const.py`.

## Protocol

| Aspect | Value |
|---|---|
| Protocol | Modbus RTU over raw TCP |
| Slave ID | Default 17 (DIP switches; all OFF = 17), range 1–247 |
| TCP port | Default 8899 (Waveshare gateway) |
| Read | FC 0x03 — Read Holding Registers |
| Write | FC 0x06 — Write Single Register |
| Register type | 16-bit words, big-endian; signed values = two's complement |
| Coils / discrete / input regs | Not used |

## Configuration registers (read)

| Address | Constant | Description | Type | Range / Scaling |
|---:|---|---|---|---|
| 57 | `REG_COMPENSATION_TEMP` | Temperature compensation offset | int16 | ÷10 → °C, −9..+9 |
| 58 | `REG_MAX_TARGET_TEMP` | Maximum target water temperature | uint16 | ÷10 → °C, 25–60 |
| 59 | `REG_CIRC_PUMP_MODE` | Circulation pump mode | uint16 | 0 = always on, 1 = follow compressor |
| 60–61 | — | Undocumented — forbidden to read | — | — |
| 62 | `REG_RUNNING_MODE` | Supported running modes | uint16 | 0–3 |

## Telemetry registers (read, 500–523)

| Address | Constant | Description | Type | Range / Scaling |
|---:|---|---|---|---|
| 500 | `REG_ALARM_500` | Component status bitfield | uint16 | bitmask |
| 501 | `REG_ALARM_501` | Sensor faults + protections bitfield | uint16 | bitmask |
| 502 | `REG_ALARM_502` | Electrical / inverter faults bitfield | uint16 | bitmask |
| 503 | `REG_ALARM_503` | PCB comms, EEPROM, defrost bitfield | uint16 | bitmask |
| 504 | `REG_EEV1` | Electronic expansion valve 1 opening | uint16 | 0–500 steps |
| 505 | `REG_EEV2` | Electronic expansion valve 2 opening | uint16 | 0–500 steps |
| 506 | `REG_FAN_SPEED` | Fan speed 1 | uint16 | 0–999 RPM |
| 507 | `REG_FAN_SPEED_2` | Fan speed 2 | uint16 | 0–999 RPM |
| 508 | `REG_FAN_LEVEL_1` | Fan speed 1 level | uint16 | 0–3 |
| 509 | `REG_FAN_LEVEL_2` | Fan speed 2 level | uint16 | 0–3 |
| 510 | `REG_DISCHARGE_TEMP` | Refrigerant discharge temperature | int16 | ÷10 → °C |
| 511 | `REG_SUCTION_TEMP` | Refrigerant suction temperature | int16 | ÷10 → °C |
| 512 | `REG_WATER_INLET` | Water inlet temperature | int16 | ÷10 → °C, raw −30..220 |
| 513 | `REG_WATER_OUTLET` | Water outlet temperature | int16 | ÷10 → °C |
| 514 | `REG_COIL_TEMP` | Heat exchanger coil temperature | int16 | ÷10 → °C |
| 515 | `REG_AMBIENT_TEMP` | Outdoor/ambient temperature | int16 | ÷10 → °C |
| 516 | `REG_IPM_TEMP` | Inverter power module temperature | int16 | ÷10 → °C |
| 517 | `REG_TARGET_FREQ` | Target compressor frequency | uint16 | Hz, 0–120 |
| 518 | `REG_CURRENT_FREQ` | Current compressor frequency | uint16 | Hz, 0–120 |
| 519 | `REG_COMPRESSOR_OP_TIME` | Compressor total run time | uint16 | minutes, 0–65535 |
| 520 | `REG_COMPRESSOR_STOP_TIME` | Compressor total stop time | uint16 | minutes |
| 521 | `REG_AC_VOLTAGE` | AC supply voltage | uint16 | volts, 0–500 |
| 522 | `REG_AC_CURRENT` | AC supply current | uint16 | ÷10 → A, 0–1000 → 0–100 A |
| 523 | `REG_FAILURE_CODE` | Compressor driver failure code | uint16 | raw |

## Control registers (read/write, 1000–1001)

| Address | Constant | Description | Type | Encoding |
|---:|---|---|---|---|
| 1000 | `REG_CONTROL_WORD` | Control word | uint16 | bits 0–3 = mode (`CTRL_MODE_MASK = 0x000F`), bit 4 = ON/OFF (`CTRL_ON_OFF = 0x0010`) |
| 1001 | `REG_SET_TEMP` | Target water temperature setpoint | uint16 | raw = °C × 10 (250–600 → 25.0–60.0 °C) |

### Control word mode values (bits 0–3 of register 1000)

| Value | Mode | HA HVAC / preset |
|---:|---|---|
| 0 | standby | OFF |
| 1 | auto | AUTO / Normal |
| 2 | cooling | COOL / Normal |
| 3 | quick_cooling | COOL / Boost |
| 4 | low_noise_cooling | COOL / Silent |
| 5 | heating | HEAT / Normal |
| 6 | quick_heating | HEAT / Boost |
| 7 | low_noise_heating | HEAT / Silent |

## Bitfield definitions

### Word 500 — component status

| Mask | Constant | Meaning |
|---|---|---|
| 0x0001 | `BIT500_HIGH_PRESSURE_SWITCH` | High pressure switch |
| 0x0002 | `BIT500_LOW_PRESSURE_SWITCH` | Low pressure switch |
| 0x0008 | `BIT500_WATER_FLOW_SWITCH` | Water flow switch |
| 0x0020 | `BIT500_WATER_PUMP` | Circulation water pump running |
| 0x0040 | `BIT500_ELECTRIC_HEATER` | Electric (aux) heater |
| 0x0080 | `BIT500_FOUR_WAY_VALVE` | Four-way reversing valve |
| 0x0100 | `BIT500_BOTTOM_PLATE_HEATER` | Bottom plate heater |
| 0x0200 | `BIT500_COMPRESSOR_HEATER` | Compressor crankcase heater |

### Word 501 — sensor faults / protections

| Mask | Constant | Code | Meaning |
|---|---|---|---|
| 0x0001 | `BIT501_FAULT_WATER_INLET` | AL03 | Water inlet sensor fault |
| 0x0002 | `BIT501_FAULT_WATER_OUTLET` | AL04 | Water outlet sensor fault |
| 0x0004 | `BIT501_FAULT_COIL` | AL05 | Coil sensor fault |
| 0x0008 | `BIT501_FAULT_AMBIENT` | AL06 | Ambient sensor fault |
| 0x0010 | `BIT501_PROT_AMBIENT_LOW` | AL14 | Ambient-too-low protection |
| 0x0020 | `BIT501_FAULT_DISCHARGE` | AL01 | Discharge sensor fault |
| 0x0040 | `BIT501_FAULT_SUCTION` | AL02 | Suction sensor fault |
| 0x0080 | `BIT501_PROT_DELTA_T_HIGH` | AL15 | ΔT-high protection |
| 0x0100 | `BIT501_PROT_DELTA_T_HIGH_3X` | AL16 | ΔT-high ×3 protection |
| 0x0200 | `BIT501_PROT_OVERCOOL` | AL17 | Overcool protection |
| 0x0400 | `BIT501_PROT_HIGH_PRESSURE` | AL10 | High pressure protection |
| 0x0800 | `BIT501_PROT_HIGH_PRESS_3X` | AL11 | High pressure ×3 protection |
| 0x1000 | `BIT501_PROT_LOW_PRESSURE` | AL12 | Low pressure protection |
| 0x2000 | `BIT501_PROT_LOW_PRESS_3X` | AL13 | Low pressure ×3 protection |
| 0x4000 | `BIT501_PROT_WATER_FLOW` | FLO | Water-flow protection |
| 0x8000 | `BIT501_PROT_ANTIFREEZE` | — | Antifreeze protection |

### Word 502 — electrical / inverter faults

| Mask | Constant | Code | Meaning |
|---|---|---|---|
| 0x0001 | `BIT502_FAULT_DISCHARGE_HIGH` | AL18 | Discharge temp too high |
| 0x0002 | `BIT502_FAULT_AC_VOLTAGE` | AL19 | AC voltage fault |
| 0x0004 | `BIT502_FAULT_DC_CURRENT` | AL21 | DC main-line current fault |
| 0x0008 | `BIT502_FAULT_AC_CURRENT` | AL20 | AC current fault |
| 0x0010 | `BIT502_FAULT_COMP_OVERCURR` | AL22 | Compressor over-current |
| 0x0020 | `BIT502_FAULT_IPM_OVERHEAT` | AL23 | IPM overheat |
| 0x0040 | `BIT502_FAULT_IPM` | AL24 | IPM fault |
| 0x0080 | `BIT502_FAULT_COMP_DRIVER` | AL25 | Compressor driver fault |
| 0x0100 | `BIT502_FAULT_FAN1` | AL09 | DC fan motor 1 fault |
| 0x0400 | `BIT502_FAULT_DRIVER_COMMS` | EA07 | Driver PCB comms fault |

### Word 503 — PCB comms / defrost

| Mask | Constant | Code | Meaning |
|---|---|---|---|
| 0x0001 | `BIT503_FAULT_MAIN_PCB_COMMS` | AL07 | Main PCB comms fault |
| 0x0002 | `BIT503_FAULT_EEPROM` | AL08 | EEPROM read error |
| 0x8000 | `BIT503_DEFROST` | — | Defrost active |

## Polling batches

Per coordinator cycle (`coordinator.py::_poll_all`), four FC 0x03 requests:

| Block | Start | Count | Contents |
|---|---:|---:|---|
| A | 57 | 3 | Compensation temp, max target temp, circ pump mode |
| B | 62 | 1 | Running mode (isolated to skip registers 60–61) |
| C | 500 | 24 | All alarms + telemetry (500–523) |
| D | 1000 | 2 | Control word + setpoint |

Writes (FC 0x06), serialized by an `asyncio.Lock`:

- **1000** — read-modify-write for mode bits and/or ON bit
- **1001** — setpoint write, `round(°C × 10)`, clamped 25.0–60.0 °C

> **Safe mode (default ON):** all FC 0x06 writes are blocked at the coordinator
> and climate entity layers. Only FC 0x03 reads are performed until the user
> disables safe mode under **Configure**.

## Derived values (not registers)

| Value | Formula |
|---|---|
| Input power | V × A |
| Compressor load | freq / 120 × 100 % |
| ΔT | outlet − inlet |

Out-of-range raw values map to `None` (HA "unknown"); disconnected probes report −32768.
