from __future__ import annotations
import copy

import queue
from enum import Enum, auto
from dataclasses import dataclass, field


class ControllerEventType(Enum):
    Empty = auto()
    Connected = auto()
    Disconnected = auto()
    InputChanged = auto()
    Quit = auto()


@dataclass
class AxisInput:
    positive: bool = field(init=False, default=True)
    value: float = field(init=False, default=0)

    def replace(self) -> AxisInput:
        replaced = AxisInput()
        replaced.positive = self.positive
        replaced.value = self.value
        return replaced

    def copy(self, source: AxisInput) -> None:
        self.positive = source.positive
        self.value = source.value

    def reset(self) -> None:
        self.positive = True
        self.value = 0


@dataclass
class ControllerInput:
    buttons: list[bool] = field(init=False, default_factory=list)
    hats: list[tuple[int, int]] = field(init=False, default_factory=list)
    axes: list[AxisInput] = field(init=False, default_factory=list)

    def replace(self) -> ControllerInput:
        replaced = ControllerInput()
        replaced.buttons = copy.copy(self.buttons)
        replaced.hats = copy.deepcopy(self.hats)
        replaced.axes = copy.deepcopy(self.axes)
        return replaced

    def copy(self, source: ControllerInput) -> None:
        self.buttons = copy.copy(source.buttons)
        self.hats = copy.deepcopy(source.hats)
        self.axes = copy.deepcopy(source.axes)

    def reset(self) -> None:
        self.buttons.clear()
        self.hats.clear()
        self.axes.clear()


@dataclass
class ControllerData:
    event: ControllerEventType = ControllerEventType.Empty
    controller_input: ControllerInput = field(init=False)

    def __post_init__(self) -> None:
        self.controller_input = ControllerInput()


class ControllerDataQueue:
    def __init__(self) -> None:
        self._queue = queue.SimpleQueue()

    def put(self, data: ControllerData) -> None:
        self._queue.put(data)

    def put_nowait(self, data: ControllerData) -> None:
        self._queue.put_nowait(data)

    def get(self) -> ControllerData:
        return self._queue.get()

    def get_nowait(self) -> ControllerData:
        if self._queue.empty():
            return ControllerData()

        return self._queue.get_nowait()

    def clear(self) -> None:
        while not self._queue.empty():
            self._queue.get_nowait()
