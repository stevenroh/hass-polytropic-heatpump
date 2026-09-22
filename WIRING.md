# Wiring & Pin Setup Guide — Heat Pump RS485 Bridge

Hardware: **Raspberry Pi Pico 2 W** + **Waveshare Pico-2CH-RS485** (SP3485 transceiver)

## Architecture

```
HA integration ──TCP:8899 (raw RTU+CRC)──► uart_tcp_server
                                              │
                                         uart_bridge
                                              │
                                    uart GPIO0/GPIO1 (UART0)
                                              │
                                         SP3485 transceiver
                                              │
                                    RS485 A+/B-/GND ──► heat pump (slave 17)
```

## Pico ↔ RS485 HAT (stacked)

The Pico-2CH-RS485 stacks directly onto the Pico's 40-pin header. Align the
USB connector end of the HAT with the USB connector of the Pico — do not
mount it reversed.

Internal UART wiring (channel 0, used by this project):

| RS485 HAT | Pico pin | GPIO | Function |
|-----------|----------|------|----------|
| `TX_CH0`  | 1        | **GP0** | UART0 TX → SP3485 DI |
| `RX_CH0`  | 2        | **GP1** | UART0 RX ← SP3485 RO |
| `VCC`     | 39       | VSYS | Power (from Pico) |
| `GND`     | 38       | GND  | Ground |

Channel 1 (`GP4`/`GP5`) is unused — leave unconnected.

These match `esphome/heatpump-bridge.yaml`:

```yaml
uart:
  id: hp_uart
  tx_pin: GPIO0   # TX_CH0
  rx_pin: GPIO1   # RX_CH0
```

## DE/RE direction control — AUTO ✓

**Confirmed from schematic** ([Pico-2CH-RS485.pdf](https://files.waveshare.com/upload/0/02/Pico-2CH-RS485.pdf)):

- `RE` (pin 2) and `DE` (pin 3) of the SP3485 are **tied together**
- Driven by an NPN transistor (S1) whose base is fed from `TX_CH0`
- Pull-up R2 (4.7 kΩ) to 3V3 when transistor is off

Operating principle:

| TX_CH0 state | Transistor S1 | DE/RE level | SP3485 mode |
|--------------|---------------|-------------|-------------|
| Idle (HIGH)  | ON            | LOW         | Driver Hi-Z, **receiver enabled** |
| Start bit (LOW) | OFF        | HIGH        | **Driver enabled**, receiver disabled |

This is classic **auto-direction**: direction follows the TX line automatically.
No GPIO is required to toggle DE/RE — `uart_bridge` works as-is.

> The YAML comment about "confirm auto DE/RE" is resolved: **the board uses
> auto-direction, not GPIO-driven DE/RE.**

## RS485 bus → heat pump

Wire from the **channel 0** terminal block (or header H1/H2) on the HAT:

| HAT terminal | Heat pump RS485 port | Notes |
|--------------|----------------------|-------|
| `485_A_1` (A) | **A+ / D+** | Non-inverting |
| `485_B_1` (B) | **B− / D−** | Inverting |
| `GND`         | **GND** (if available) | Recommended for common reference |

### Polarity check

If communication fails after wiring, **swap A and B** — RS485 A/B polarity is
the most common wiring mistake. The SMAJ12CA TVS diodes on the HAT protect
against surges but do not correct swapped polarity.

### Termination (120 Ω)

The HAT has an on-board **120 R** resistor (R8) between A and B, enabled by
solder jumpers / headers **H1/H2**:

| Scenario | Termination |
|----------|-------------|
| This bridge is the **only** device at the far end of the cable, heat pump has its own termination | **Enable** (bridge the jumper) |
| Multiple devices on the bus, termination already at each physical end | **Disable** (leave jumper open) |
| Short cable (< 5 m), single slave | Usually fine either way |

For a typical point-to-point link (bridge ↔ heat pump only), enable termination
on the HAT if the heat pump side already terminates, or enable it on both ends.

### Bias resistors

R7/R9 (4.7 kΩ) provide failsafe biasing on A/B — always present, no action needed.

## Full pin summary

```
┌─────────────────────────────────────────────────────┐
│                 Pico 2 W                           │
│                                                     │
│  GP0 (TX0) ──► TX_CH0 ──► SP3485 DI               │
│  GP1 (RX0) ◄── RX_CH0 ◄── SP3485 RO               │
│                             SP3485 DE/RE ◄── auto  │
│                                  │    (via S1 from  │
│                                  │     TX_CH0)      │
│                             SP3485 A ──► 485_A_1   │
│                             SP3485 B ──► 485_B_1   │
│                                  │                  │
│                             [120R + TVS + bias]     │
└──────────────────────────┬──────────────────────────┘
                           │
                    RS485 A+ / B- / GND
                           │
                    ┌──────▼──────┐
                    │  Heat pump  │
                    │  slave 17   │
                    └─────────────┘
```

## Serial settings (must match heat pump)

| Parameter | Value | Where |
|-----------|-------|-------|
| Baud rate | **9600** (verify!) | `uart_baud` in YAML |
| Data bits | 8 | fixed in YAML |
| Parity | None | fixed in YAML |
| Stop bits | 1 | fixed in YAML |
| Slave address | **17** (DIP SW1 all OFF) | heat pump PCB |

> Common Polytropic default is 9600 8N1 — confirm against the unit manual or
> an existing gateway config before flashing.

## TCP / network side

| Setting | Value |
|---------|-------|
| TCP port | **8899** (HA integration default) |
| Client mode | `exclusive` — one Modbus master at a time |
| Protocol | Raw Modbus RTU+CRC over plain TCP (**not** Modbus TCP/MBAP) |
| WiFi | DHCP or static (`manual_ip` in YAML); note the IP for HA setup |

## Powering on the Pico

| Method | How | When to use |
|--------|-----|-------------|
| **USB** (simplest) | Micro-USB cable to any 5V USB source (phone charger, power bank, HA server) | Bench setup, first flash, most installs |
| **VSYS** (pin 39) | Feed 5V directly to VSYS + GND | Permanent install without a dangling USB cable |
| **VBUS** (pin 40) | Only live when USB is connected | Not a standalone supply — don't use alone |

- The stacked HAT draws power from **VSYS**, so both Pico and RS485 transceiver are powered from the same source.
- Total draw is well under 500 mA — any 5V/1A USB adapter is sufficient.
- For a clean permanent supply near the heat pump: 5V wall adapter → VSYS + GND (or USB).

**Power-on sequence:**

1. Wire RS485 A/B/GND to the heat pump first.
2. Apply power (USB or VSYS).
3. Pico boots → ESPHome joins WiFi → `uart_tcp_server` listens on `:8899`.
4. `TX1_LED` / `RX1_LED` on the HAT blink during Modbus traffic.

## Flash & verify

1. Copy `esphome/secrets.yaml.example` → `esphome/secrets.yaml`, fill in WiFi.
2. Set `uart_baud` (and parity/stop_bits if non-default) to match the heat pump.
3. Flash: `esphome run esphome/heatpump-bridge.yaml`
4. Note the bridge's IP (ESPHome dashboard, router, or serial log).
5. In HA: **Settings → Integrations → Polytropic Heat Pump**
   - Host: bridge IP
   - Port: `8899`
   - Slave: `17`
6. Config flow probes register 62 — success means full path works
   (TCP → bridge → RS485 → heat pump → response).

### Quick bench test (no HA)

```bash
# Read holding register 62 (running modes), slave 17
# Frame: 11 03 00 3E 00 01 [CRC]
printf '\x11\x03\x00\x3e\x00\x01\x04\x0c' | nc -q 1 <bridge-ip> 8899 | xxd
```

Expected response starts with `11 03 02 ...` followed by CRC.
No response → check wiring/A-B polarity, baud rate, slave DIP switches.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| HA probe: `cannot_connect` | Wrong IP, bridge not on WiFi, port not 8899 |
| HA probe: `modbus_error` | A/B swapped, wrong baud, wrong slave addr, DE/RE issue |
| Intermittent CRC errors | A/B loose, missing GND, baud mismatch, termination missing on long cable |
| Works with `nc` but not HA | Stray `nc` session still connected (`exclusive` mode — it owns the bus) |
| No TX LED activity | Logger claiming UART0 — ensure `hardware_uart: USB_CDC` if validation warns |
