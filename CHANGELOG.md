# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- Config flow setup always failed with a generic "unknown" error: `_probe()` was called but never defined (`NameError`, introduced in 1c792bc). Added the missing helper, which now reads holding register 62 (safe, outside forbidden 60–61) to verify bridge connectivity before creating the entry.
- Remove dead `client = ModbusRTUClient(...)` left behind by the same refactor (the probe creates its own client).
- Replace unused `REG_CONTROL_WORD` import with `REG_RUNNING_MODE` in config_flow.py.

### Added
- **ESPHome Pico 2 W RS485 bridge** (`esphome/heatpump-bridge.yaml`): transparent Modbus RTU-over-TCP server on port 8899 that replaces the Waveshare RS485-to-ETH gateway. Uses `nebulous/esphome-uart-link` (`uart_tcp_server` + `uart_bridge`), Waveshare Pico-2CH-RS485 channel 0 (GPIO0/GPIO1), exclusive client mode, board `rpipico2w`. The HA integration is unchanged and connects to the Pico exactly as it did to the gateway.
- `esphome/secrets.yaml.example` — template for WiFi SSID/password and AP password.
- `esphome/.gitignore` — excludes local `secrets.yaml` and `.esphome/` build artifacts.

## [1.2.0] - 2026-05-24

- Coalesce mode + power writes when turning the heat pump on from OFF, one modbus write instead of two
- Allow preset (Silent/Normal/Boost) changes while the unit is off, the new preset is honored on next turn-on
- "off + silent → on + normal" now sends a single write instead of three

## [1.1.0] - 2026-04-20

- Batch reads instead of fetching each one separately. 7+ seconds to 1 second for each fetch.
- Clean up unused files
- Fix defrost status for climate entity
- Fix order in const.py to match modbus docs
- Make update interval configurable
- Start with an empty cache
- Share device_info from coordinator
- Validate ranges, return unknown instead of out of bounds values

## [1.0.6] - 2026-04-20

- Add debug logging toggle to options flow
- Improve CRC error visibility and add write retry

## [1.0.5] - 2026-04-16

- Add coordinator lock to avoid modbus conflicts

## [1.0.4] - 2026-04-10

- Ignore occasionally failed fetch

## [1.0.3] - 2026-04-10

- Name EEV opening 2 correctly

## [1.0.2] - 2026-04-09

- Make icon backgrounds transparent

## [1.0.1] - 2026-04-09

- Fix CRC errors
- Fix brand logo location

## [1.0.0] - 2026-04-09

- Initial release