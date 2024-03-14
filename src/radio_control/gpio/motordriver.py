import threading
import time
from logging import getLogger
from typing import Optional

import pigpio

import gpio.pigpiohelper as pigpiohelper
from baseclass import NamedClass


class ThreadedServo(NamedClass):
    """
    A class for controlling the servo motor.

    Methods:
        move(step: int, interval: float, clockwise: bool) -> None:
            Move the servo motor clockwise or counterclockwise until it reaches its limit or stop() is called.

        initial() -> None:
            Move to initial position (normally 0 degrees).

        stop() -> None:
            Stop the servo motor.

        quit() -> None:
            Quit ThreadedServo.
    """

    _VALID_PIN_VALUES = [12, 13, 18, 19]

    def __init__(
        self,
        pin: int,
        min_pulse_width: float,
        max_pulse_width: float,
        frame_width: float,
        initial_pulse_width: Optional[float] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Initializes ThreadedServo.

        Args:
            pin (int): The pin number that outputs PWM. Should be one of 12, 13, 18, or 19 for hardware PWM.
            min_pulse_width (float): Minimum pulse width in milliseconds.
            max_pulse_width (float): Maximum pulse width in milliseconds.
            frame_width (float): Frame width in milliseconds.
            initial_pulse_width (float, optional): Pulse width for the initial position in milliseconds (normally 0 degrees).
                If set to `None`, it is calculated based on min_pulse_width and max_pulse_width.
            name (str, optional): Name of instance. If not set, the class name will be used.

        Returns:
            None

        Raises:
            ValueError: Raised if `pin` has an invalid value (not 12, 13, 18, or 19).
        """
        if name is None:
            super().__init__(self.__class__.__name__)
        else:
            super().__init__(name)

        self._logger = getLogger(self._name)

        self._logger.info("Start initializing %s.", self._name)

        if pin not in self._VALID_PIN_VALUES:
            raise ValueError(
                f"Invalid value for 'pin'. Must be one of: {', '.join(map(str, self._VALID_PIN_VALUES))}."
            )

        self._pin = pin
        self._min_duty = int(1000 * 1000 * min_pulse_width / frame_width)
        self._max_duty = int(1000 * 1000 * max_pulse_width / frame_width)

        if initial_pulse_width is None:
            pulse_width = (max_pulse_width - min_pulse_width) / 2 + min_pulse_width
            self._initial_duty = int(1000 * 1000 * pulse_width / frame_width)
        else:
            self._initial_duty = int(1000 * 1000 * initial_pulse_width / frame_width)

        self._freq = int(1000 / frame_width)

        self._current_duty = self._initial_duty

        self._clockwise = True
        self._step = 1000
        self._interval = 0.05

        self._servo = pigpiohelper.get_instance()
        self._servo.set_mode(self._pin, pigpio.ALT0)

        self._exit = False

        self._running_event = threading.Event()
        self._running_event.clear()
        self._servo_thread = threading.Thread(
            name=f"{self._name}RunningThread", target=self._run
        )
        self._servo_thread.start()

        self.initial()

        self._logger.debug("Pin:%d", self._pin)
        self._logger.debug("Min dutycycle:%d", self._min_duty)
        self._logger.debug("Max dutycycle:%d", self._max_duty)
        self._logger.debug("Initial dutycycle:%d", self._initial_duty)
        self._logger.debug("Frequency:%d", self._freq)

        self._logger.info("End initializing %s.", self._name)

    def _run(self) -> None:
        while True:
            self._running_event.wait()

            if self._exit:
                break

            if self._clockwise:
                self._current_duty += self._step

                if self._current_duty > self._max_duty:
                    self._current_duty = self._max_duty
                    self.stop()
                    continue
            else:
                self._current_duty -= self._step

                if self._current_duty < self._min_duty:
                    self._current_duty = self._min_duty
                    self.stop()
                    continue

            self._servo.hardware_PWM(self._pin, self._freq, self._current_duty)
            time.sleep(self._interval)

    def move(self, step: int, interval: float, clockwise: bool) -> None:
        """
        Move the servo motor.

        Args:
            step (int): The movement step of the servo motor. A larger value results in faster movement.
            interval (float): The interval until the servo motor moves to the next step. A larger value results in a more jerky movement.
            clockwise (bool): True for clockwise movement, False for counterclockwise.
        """
        self._logger.debug(
            "Move servo motor in step:%d, interval:%.3f, %s",
            step,
            interval,
            "clockwise" if clockwise else "counterclockwise",
        )

        self._step = step
        self._interval = interval
        self._clockwise = clockwise

        self._running_event.set()

    def initial(self) -> None:
        """
        Move to initial position (normally 0 degrees).
        """
        self._logger.debug("Move to initial position in %d", self._initial_duty)

        self.stop()
        self._current_duty = self._initial_duty
        self._servo.hardware_PWM(self._pin, self._freq, self._initial_duty)
        time.sleep(0.1)

    def stop(self) -> None:
        """
        Stop the servo motor.
        """
        self._logger.debug("Stop servo motor.")

        self._running_event.clear()

    def quit(self) -> None:
        """
        Quit ThreadedServo.
        """
        self._logger.info("Start closing %s.", self._name)

        self.stop()
        self._exit = True
        self._running_event.set()
        self._servo_thread.join()
        self.initial()

        self._logger.info("End closing %s.", self._name)


class Motor(NamedClass):
    """
    A class for controlling the motor.

    Methods:
        move(dutycycle: float, forward: bool = True) -> None:
            Move the motor forward or backward until stop() is called.

        stop() -> None:
            Stop the motor.

        quit() -> None:
            Quit Motor.
    """

    def __init__(
        self,
        forward_pin: int,
        backward_pin: int,
        max_dutycycle: int = 1000,
        name: Optional[str] = None,
    ) -> None:
        """
        Initializes Motor.

        Args:
            forward_pin (int): The pin number that outputs PWM.
            backward_pin (int): The pin number that outputs PWM.
            max_dutycycle (int, optional): Range of PWM dutycycle.
            name (str, optional): Name of instance. If not set, the class name will be used.
        """
        if name is None:
            super().__init__(self.__class__.__name__)
        else:
            super().__init__(name)

        self._logger = getLogger(self._name)

        self._logger.info("Start initializing %s.", self._name)

        self._forward_pin = forward_pin
        self._backward_pin = backward_pin
        self._max_dutycycle = max_dutycycle

        self._motor = pigpiohelper.get_instance()
        self._motor.set_PWM_range(self._forward_pin, self._max_dutycycle)
        self._motor.set_mode(self._forward_pin, pigpio.OUTPUT)
        self._motor.set_PWM_range(self._backward_pin, self._max_dutycycle)
        self._motor.set_mode(self._backward_pin, pigpio.OUTPUT)

        self.stop()

        self._logger.debug("Forward pin:%d", self._forward_pin)
        self._logger.debug("Backward pin:%d", self._backward_pin)
        self._logger.debug("Max dutycycle:%d", self._max_dutycycle)

        self._logger.info("End initializing %s.", self._name)

    def move(self, dutycycle: float, forward: bool = True) -> None:
        """
        Move the motor.

        Args:
            dutycycle (float): Parcentage of dutycycle (from 0 to 1).
            forward (bool): True for forward movement, False for backward.
        """
        dutycycle_ = int(self._max_dutycycle * dutycycle)

        if dutycycle_ > self._max_dutycycle:
            dutycycle_ = self._max_dutycycle

        self._logger.debug(
            "Move motor to %s in %d",
            "foward" if forward else "backward",
            dutycycle_,
        )

        if forward:
            self._motor.set_PWM_dutycycle(self._backward_pin, 0)
            self._motor.set_PWM_dutycycle(self._forward_pin, dutycycle_)
        else:
            self._motor.set_PWM_dutycycle(self._forward_pin, 0)
            self._motor.set_PWM_dutycycle(self._backward_pin, dutycycle_)

    def stop(self) -> None:
        """
        Stop the motor.
        """
        self._logger.debug("Stop motor.")

        self._motor.set_PWM_dutycycle(self._forward_pin, 0)
        self._motor.set_PWM_dutycycle(self._backward_pin, 0)

    def quit(self) -> None:
        """
        Quit Motor.
        """
        self._logger.info("Start closing %s.", self._name)

        self.stop()

        self._logger.info("End closing %s.", self._name)
