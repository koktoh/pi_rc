from enum import IntEnum

from controller.controllerdata import AxisInput, ControllerInput


class XboxControllerButton(IntEnum):
    A = 0
    B = 1
    X = 3
    Y = 4
    LeftBumper = 6
    RightBumper = 7
    Back = 10
    Start = 11
    LeftStick = 13
    RightStick = 14
    Guide = 12


class XboxControllerHat(IntEnum):
    HatX = 0
    HatY = 1


class XboxControllerStick(IntEnum):
    LeftX = 0
    LeftY = 1
    RightX = 2
    RightY = 3


class XboxControllerTrigger(IntEnum):
    Left = 5
    Right = 4


class XboxControllerInputHelper:
    @staticmethod
    def ButtonA(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.A]

    @staticmethod
    def ButtonB(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.B]

    @staticmethod
    def ButtonX(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.X]

    @staticmethod
    def ButtonY(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.Y]

    @staticmethod
    def ButtonBack(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.Back]

    @staticmethod
    def ButtonStart(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.Start]

    @staticmethod
    def ButtonGuide(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.Guide]

    @staticmethod
    def BumperLeft(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.LeftBumper]

    @staticmethod
    def BumperRight(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.RightBumper]

    @staticmethod
    def ButtonStickLeft(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.LeftStick]

    @staticmethod
    def ButtonStickRight(input: ControllerInput) -> bool:
        return input.buttons[XboxControllerButton.RightStick]

    @staticmethod
    def HatX(input: ControllerInput) -> int:
        return input.hats[0][XboxControllerHat.HatX]

    @staticmethod
    def HatY(input: ControllerInput) -> int:
        return input.hats[0][XboxControllerHat.HatY]

    @staticmethod
    def StickLeftX(input: ControllerInput) -> AxisInput:
        return input.axes[XboxControllerStick.LeftX]

    @staticmethod
    def StickLeftY(input: ControllerInput) -> AxisInput:
        return input.axes[XboxControllerStick.LeftY]

    @staticmethod
    def StickRightX(input: ControllerInput) -> AxisInput:
        return input.axes[XboxControllerStick.RightX]

    @staticmethod
    def StickRightY(input: ControllerInput) -> AxisInput:
        return input.axes[XboxControllerStick.RightY]

    @staticmethod
    def TriggerLeft(input: ControllerInput) -> AxisInput:
        return input.axes[XboxControllerTrigger.Left]

    @staticmethod
    def TriggerRight(input: ControllerInput) -> AxisInput:
        return input.axes[XboxControllerTrigger.Right]
