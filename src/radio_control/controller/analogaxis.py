from abc import ABC, abstractmethod
from dataclasses import dataclass

from controller.controllerdata import AxisInput
from controller.controllerdefs import ControllerType
from controller.speed import Speed
from controller.xboxdefs import XboxControllerTrigger


@dataclass(frozen=True)
class AnalogStickThreshold:
    zero: float = 0.2
    low: float = 0.4
    middle: float = 0.6
    high: float = 0.8


@dataclass(frozen=True)
class AnalogStickRoundedValue:
    zero: int = Speed.Zero
    low: int = Speed.Slow
    middle: int = Speed.Middle
    high: int = Speed.High
    max: int = Speed.Max


@dataclass(frozen=True)
class TriggerThreshold:
    zero: float = 0.2
    low: float = 0.65
    middle: float = 1.1
    high: float = 1.6


@dataclass(frozen=True)
class TriggerRoundedValue:
    zero: int = Speed.Zero
    low: int = Speed.Slow
    middle: int = Speed.Middle
    high: int = Speed.High
    max: int = Speed.Max


class AnalogAxisConverter(ABC):
    def __init__(
        self,
        stick_threshold: AnalogStickThreshold,
        stick_rounded_value: AnalogStickRoundedValue,
        trigger_threshold: TriggerThreshold,
        trigger_rounded_value: TriggerRoundedValue,
    ) -> None:
        self._stick_threshold = stick_threshold
        self._stick_rounded_value = stick_rounded_value
        self._trigger_threshold = trigger_threshold
        self._trigger_rounded_value = trigger_rounded_value

    def _is_positive(self, value: float) -> bool:
        return value >= 0

    def _round_stick_value(self, value: float) -> int:
        abs_value = abs(value)

        if abs_value < self._stick_threshold.zero:
            return self._stick_rounded_value.zero
        elif abs_value < self._stick_threshold.low:
            return self._stick_rounded_value.low
        elif abs_value < self._stick_threshold.middle:
            return self._stick_rounded_value.middle
        elif abs_value < self._stick_threshold.high:
            return self._stick_rounded_value.high
        else:
            return self._stick_rounded_value.max

    def _round_trigger_value(self, value: float) -> int:
        if value < self._trigger_threshold.zero:
            return self._trigger_rounded_value.zero
        elif value < self._trigger_threshold.low:
            return self._trigger_rounded_value.low
        elif value < self._trigger_threshold.middle:
            return self._trigger_rounded_value.middle
        elif value < self._trigger_threshold.high:
            return self._trigger_rounded_value.high
        else:
            return self._trigger_rounded_value.max

    @abstractmethod
    def convert(self, index: int, value: float) -> AxisInput:
        pass


class SimpleAnalogAxisConverter(AnalogAxisConverter):
    def __init__(self) -> None:
        super().__init__(
            AnalogStickThreshold(),
            AnalogStickRoundedValue(),
            TriggerThreshold(),
            TriggerRoundedValue(),
        )

    def convert(self, index: int, value: float) -> AxisInput:
        axis = AxisInput()
        axis.positive = self._is_positive(value)
        axis.value = value
        return axis


class XboxAnalogAxisConverter(AnalogAxisConverter):
    def __init__(self) -> None:
        super().__init__(
            AnalogStickThreshold(),
            AnalogStickRoundedValue(),
            TriggerThreshold(),
            TriggerRoundedValue(),
        )

    def convert(self, index: int, value: float) -> AxisInput:
        axis = AxisInput()

        if index in list(map(lambda x: x.value, XboxControllerTrigger)):
            axis.positive = True
            axis.value = self._round_trigger_value(1 + value)
        else:
            axis.positive = self._is_positive(value)
            axis.value = self._round_stick_value(value)

        return axis


class AnalogAxisConverterFactory:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_converter(controller_type: ControllerType) -> AnalogAxisConverter:
        if controller_type == ControllerType.Xbox:
            return XboxAnalogAxisConverter()
        else:
            return SimpleAnalogAxisConverter()
