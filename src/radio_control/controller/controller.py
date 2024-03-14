import os

# For using pygame without screen
os.environ["SDL_VIDEODRIVER"] = "dummy"
# Hide pygame prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import threading
from logging import getLogger
from typing import Optional

import pygame

from baseclass import NamedClass
from controller.analogaxis import AnalogAxisConverterFactory
from controller.controllerdata import (
    ControllerInput,
    ControllerData,
    ControllerEventType,
    ControllerDataQueue,
)
from controller.controllerdefs import ControllerType


class Controller(NamedClass):
    """
    A class for capturing controller input.

    Attributes:
        data (ControllerDataQueue): Controller event and input data.

    Methods:
        connect_controller() -> None:
            Try connecting controller.

        run() -> None:
            Run main program.

        quit() -> None:
            Quit Controller.
    """

    def __init__(
        self,
        controller_type: ControllerType,
        connection_timeout: float = 30,
        name: Optional[str] = None,
    ) -> None:
        """
        Initializes Controller.

        Args:
            type (ControllerType): Type of controller.
            connection_timeout (float, optional): The time, in seconds, to wait for the controller to connect.
                Specify the duration in seconds; set to 0.0 for an infinite wait.
                The default is 30.0 seconds.
            name (str, optional): Name of instance. If not set, the class name will be used.
        """
        if name is None:
            super().__init__(self.__class__.__name__)
        else:
            super().__init__(name)

        self._logger = getLogger(self._name)

        self._logger.info("Start initializing %s.", self._name)

        self._controller_type = controller_type

        pygame.init()

        self._set_allowed_target_event()

        self._controller: pygame.joystick.JoystickType = None

        self._connection_timeout = connection_timeout
        self._controller_connected = False

        self.data = ControllerDataQueue()
        self._controller_data = ControllerData()

        self._axis_converter = AnalogAxisConverterFactory.get_converter(controller_type)

        self._running = False

        self._running_event = threading.Event()
        self._running_event.clear()
        self._controller_capture_thread = threading.Thread(
            name=f"{self._name}CapturingThread", target=self._run
        )

        self._logger.info("End initializing %s.", self._name)

    def _set_allowed_target_event(self) -> None:
        pygame.event.set_allowed(None)
        pygame.event.set_allowed(
            [
                pygame.JOYAXISMOTION,
                pygame.JOYHATMOTION,
                pygame.JOYBUTTONUP,
                pygame.JOYBUTTONDOWN,
                pygame.JOYDEVICEREMOVED,
            ]
        )

    def _try_connect_controller(self) -> bool:
        try:
            for i in range(pygame.joystick.get_count()):
                joy = pygame.joystick.Joystick(i)
                self._logger.debug(f"Detected controller: {joy.get_name()}")

                if joy.get_name() == self._controller_type.value:
                    self._controller = joy
                    self._controller.init()
                    self._controller_connected = True
                    self.data.put(ControllerData(ControllerEventType.Connected))
                    self._logger.info("Controller connected.")
                    return True

            return False

        except pygame.error:
            self._controller_connected = False
            return False

    def _search_controller(self, exit) -> None:
        self._logger.info("Searching controller.")

        pygame.event.clear()
        pygame.event.set_allowed(None)
        pygame.event.set_allowed(pygame.JOYDEVICEADDED)

        while True:
            if exit():
                break

            event = pygame.event.wait()

            if event.type == pygame.JOYDEVICEADDED:
                if self._try_connect_controller():
                    self._set_allowed_target_event()

                    if self._running:
                        self._running_event.set()

                    break

            continue

    def _reconnect_controller(self) -> None:
        exit = False
        th_connection = threading.Thread(
            name="SearchingControllerThread",
            target=self._search_controller,
            kwargs={
                "exit": lambda: exit,
            },
        )
        th_connection.start()
        # Wait `_connection_timeout` seconds
        th_connection.join(
            self._connection_timeout if self._connection_timeout > 0 else None
        )

        if th_connection.is_alive():
            exit = True

        if not self._controller_connected:
            self._logger.error("Controller is not detected.")
            self.quit()

    def _get_controller_input(self) -> str:
        input = self._controller_data.controller_input
        msg = "\n"

        for i in range(len(input.buttons)):
            msg += f"    {f'Button {i:>2}':<10}: {input.buttons[i]}\n"

        for i in range(len(input.hats)):
            hat = input.hats[i]
            msg += f"    {f'Hat {i} X':<10}: {hat[0]}\n"
            msg += f"    {f'Hat {i} Y':<10}: {hat[1]}\n"

        for i in range(len(input.axes)):
            axis = input.axes[i]
            msg += f"    {f'Axis {i}':<10}: {axis.value:.3f}, {axis.positive}\n"

        return msg.rstrip()

    def _run(self) -> None:
        current_input = ControllerInput()

        while True:
            self._running_event.wait()

            event = pygame.event.wait()

            if event.type == pygame.QUIT:
                break

            if not self._controller_connected:
                continue

            if (
                event.type == pygame.JOYDEVICEREMOVED
                and event.instance_id == self._controller.get_instance_id()
            ):
                self._controller_connected = False
                self.data.clear()
                self._controller_data.event = ControllerEventType.Disconnected
                self._controller_data.controller_input.reset()
                current_input.reset()
                self.data.put(self._controller_data)
                self._logger.warn("Controller disconnected.")
                self._running_event.clear()
                self._reconnect_controller()
                continue

            current_input.reset()

            for i in range(self._controller.get_numaxes()):
                axis = self._controller.get_axis(i)
                current_input.axes.append(self._axis_converter.convert(i, axis))

            for i in range(self._controller.get_numbuttons()):
                button = self._controller.get_button(i)
                current_input.buttons.append(button)

            for i in range(self._controller.get_numhats()):
                hat = self._controller.get_hat(i)
                current_input.hats.append(hat)

            if self._controller_data.controller_input == current_input:
                continue

            self._controller_data.event = ControllerEventType.InputChanged
            self._controller_data.controller_input.copy(current_input)

            self._logger.debug("Controller input:%s", self._get_controller_input())

            self.data.put(self._controller_data)

    def connect(self) -> None:
        """
        Connect to controller.
        """
        self._logger.info("Try connecting controller.")

        if not self._try_connect_controller():
            self._reconnect_controller()

    def run(self) -> None:
        """
        Run capturing controller input program
        """
        if self._running:
            return

        self._logger.info("Run capturing controller input.")

        self._running = True
        self._running_event.set()
        self._controller_capture_thread.start()

    def quit(self) -> None:
        """
        Quit Controller.
        """
        self._logger.info("Start closing %s.", self._name)

        self.data.clear()

        if self._running:
            pygame.event.set_allowed(None)
            pygame.event.set_allowed(pygame.QUIT)

            pygame.event.clear()
            quit_event = pygame.event.Event(pygame.QUIT, {})
            pygame.event.post(quit_event)

            self._running_event.set()
            self._controller_capture_thread.join()

        self.data.put(ControllerData(ControllerEventType.Quit))

        pygame.quit()

        self._logger.info("End closing %s.", self._name)
