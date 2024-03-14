from logging import getLogger
from typing import Optional

import pigpio

import gpio.pigpiohelper as pigpiohelper
from baseclass import NamedClass


class LED(NamedClass):
    """
    A class of controlling the LED.

    Methods:
        on() -> None:
            Turn on the LED with the brightness when it was turned off.
            If the brightness is 0 (due to decrement_brightness()), turn on the LED with maximum brightness.

        off() -> None:
            Turn off the LED.

        increment_brightness() -> None:
            Increment the brightness of the LED.

        decrement_brightness() -> None:
            Decrement the brightness of the LED.

        quit() -> None:
            Quit LED.
    """

    def __init__(self, led_pin: int, name: Optional[str] = None) -> None:
        """
        Initializes LED.

        Args:
            led_pin (int): The pin number that outputs PWM.
            name (str, optional): Name of instance. If not set, the class name will be used.
        """
        if name is None:
            super().__init__(self.__class__.__name__)
        else:
            super().__init__(name)

        self._logger = getLogger(self._name)

        self._logger.info("Start initializing %s.", self._name)

        self._led_pin: int = led_pin
        self.PWM_RANGE: int = 1000
        self.BRIGHTNESS_STEP: float = 0.1

        self._current_duty: float = 1

        self._led = pigpiohelper.get_instance()
        self._led.set_mode(led_pin, pigpio.OUTPUT)
        self._led.set_PWM_range(led_pin, self.PWM_RANGE)

        self._logger.info("End initializing %s.", self._name)

    def _set_led(self, dutycycle: int) -> None:
        self._led.set_PWM_dutycycle(self._led_pin, dutycycle)

    def on(self) -> None:
        """
        Turn on the LED.
        """
        if self._current_duty == 0:
            self._current_duty = 1

        dutycycle = int(self._current_duty * self.PWM_RANGE)

        self._logger.debug("Turn on LED by %d", dutycycle)

        self._set_led(dutycycle)

    def off(self) -> None:
        """
        Turn off the LED.
        """
        self._set_led(0)

    def increment_brightness(self) -> None:
        """
        Increment the brightness of the LED.
        """
        self._current_duty += self.BRIGHTNESS_STEP

        if self._current_duty > 1:
            self._current_duty = 1

        dutycycle = int(self._current_duty * self.PWM_RANGE)

        self._logger.debug("Increment dutycycle to %d", dutycycle)

        self._set_led(dutycycle)

    def decrement_brightness(self) -> None:
        """
        Increment the brightness of the LED.
        """
        self._current_duty -= self.BRIGHTNESS_STEP

        if self._current_duty < 0:
            self._current_duty = 0

        dutycycle = int(self._current_duty * self.PWM_RANGE)

        self._logger.debug("Decrement dutycycle to %d", dutycycle)

        self._set_led(dutycycle)

    def quit(self) -> None:
        """
        Quit LED.
        """
        self._logger.info("Start closing %s.", self._name)

        self.off()

        self._logger.info("Start closing %s.", self._name)
