"""Climate platform for Polytropic Heat Pump."""
from __future__ import annotations

import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PolytropicCoordinator, device_info

_LOGGER = logging.getLogger(__name__)

DOMAIN = "polytropic_heatpump"

# Preset names
PRESET_NORMAL     = "Normal"
PRESET_BOOST      = "Boost"
PRESET_SILENT     = "Silent"

# mode_id → (HVACMode, preset)
MODE_ID_TO_HVAC_PRESET: dict[int, tuple[HVACMode, str]] = {
    0: (HVACMode.OFF,  PRESET_NORMAL),
    1: (HVACMode.AUTO, PRESET_NORMAL),
    2: (HVACMode.COOL, PRESET_NORMAL),
    3: (HVACMode.COOL, PRESET_BOOST),   # quick cooling
    4: (HVACMode.COOL, PRESET_SILENT),  # low noise cooling
    5: (HVACMode.HEAT, PRESET_NORMAL),
    6: (HVACMode.HEAT, PRESET_BOOST),   # quick heating
    7: (HVACMode.HEAT, PRESET_SILENT),  # low noise heating
}

# (HVACMode, preset) → mode_id
HVAC_PRESET_TO_MODE_ID: dict[tuple[HVACMode, str], int] = {
    v: k for k, v in MODE_ID_TO_HVAC_PRESET.items()
    if v[0] != HVACMode.OFF  # OFF has no preset concept
}

# When switching HVAC mode without changing preset, use this default mode_id
HVAC_DEFAULT_MODE_ID: dict[HVACMode, int] = {
    HVACMode.HEAT: 5,
    HVACMode.COOL: 2,
    HVACMode.AUTO: 1,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PolytropicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PolytropicClimate(coordinator, entry)])


class PolytropicClimate(CoordinatorEntity[PolytropicCoordinator], ClimateEntity):
    """Climate entity for the Polytropic heat pump."""

    _attr_has_entity_name = True
    _attr_name = "Climate"
    _attr_icon = "mdi:heat-pump"

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 25.0
    _attr_max_temp = 60.0
    _attr_target_temperature_step = 0.5

    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
    ]
    _attr_preset_modes = [PRESET_NORMAL, PRESET_BOOST, PRESET_SILENT]

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self, coordinator: PolytropicCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = device_info(entry)

    # ------------------------------------------------------------------
    # Safe mode (read-only)
    # ------------------------------------------------------------------

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Hide write controls while safe mode is enabled."""
        if self.coordinator.safe_mode:
            return ClimateEntityFeature(0)
        return self._attr_supported_features

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Only expose the current mode in safe mode (no mode switching)."""
        if self.coordinator.safe_mode:
            return [self.hvac_mode]
        return self._attr_hvac_modes

    @property
    def preset_modes(self) -> list[str] | None:
        if self.coordinator.safe_mode:
            return None
        return self._attr_preset_modes

    @property
    def extra_state_attributes(self) -> dict:
        attrs = dict(super().extra_state_attributes or {})
        attrs["safe_mode"] = self.coordinator.safe_mode
        return attrs

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _mode_id(self) -> int:
        return self.coordinator.data.get("mode_id", 0)

    @property
    def hvac_mode(self) -> HVACMode:
        if not self.coordinator.data.get("unit_on", False):
            return HVACMode.OFF
        hvac, _ = MODE_ID_TO_HVAC_PRESET.get(self._mode_id(), (HVACMode.OFF, PRESET_NORMAL))
        return hvac

    @property
    def preset_mode(self) -> str:
        _, preset = MODE_ID_TO_HVAC_PRESET.get(self._mode_id(), (HVACMode.HEAT, PRESET_NORMAL))
        return preset

    @property
    def hvac_action(self) -> HVACAction | None:
        if not self.coordinator.data.get("unit_on", False):
            return HVACAction.OFF
        if self.coordinator.data.get("defrost_active"):
            return HVACAction.DEFROSTING
        freq = self.coordinator.data.get("current_freq", 0)
        if freq == 0:
            return HVACAction.IDLE
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            return HVACAction.HEATING
        if mode == HVACMode.COOL:
            return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("water_inlet_temp")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("set_temp")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_control(on=False)
            return
        current_preset = self.preset_mode
        mode_id = HVAC_PRESET_TO_MODE_ID.get(
            (hvac_mode, current_preset),
            HVAC_DEFAULT_MODE_ID.get(hvac_mode, 5),
        )
        unit_on = self.coordinator.data.get("unit_on", False)
        await self.coordinator.async_set_control(
            mode_id=mode_id,
            on=True if not unit_on else None,
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        # When unit is off, hvac_mode reports OFF but the stored mode_id still
        # encodes the last active HVAC mode — use that so the preset change
        # sticks and is honored on next turn-on.
        stored_hvac, _ = MODE_ID_TO_HVAC_PRESET.get(
            self._mode_id(), (HVACMode.HEAT, PRESET_NORMAL)
        )
        target_hvac = stored_hvac if stored_hvac != HVACMode.OFF else HVACMode.HEAT
        mode_id = HVAC_PRESET_TO_MODE_ID.get(
            (target_hvac, preset_mode),
            HVAC_DEFAULT_MODE_ID.get(target_hvac, 5),
        )
        await self.coordinator.async_set_control(mode_id=mode_id)

    async def async_set_temperature(self, **kwargs) -> None:
        if self.coordinator.safe_mode:
            _LOGGER.warning("Safe mode is enabled — setpoint change ignored")
            return
        temp = kwargs.get("temperature")
        if temp is not None:
            await self.coordinator.async_set_target_temp(float(temp))

    async def async_turn_on(self) -> None:
        if self.coordinator.safe_mode:
            _LOGGER.warning("Safe mode is enabled — turn_on ignored")
            return
        await self.coordinator.async_turn_on()

    async def async_turn_off(self) -> None:
        if self.coordinator.safe_mode:
            _LOGGER.warning("Safe mode is enabled — turn_off ignored")
            return
        await self.coordinator.async_turn_off()
