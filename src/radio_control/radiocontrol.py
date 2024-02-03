from logging import getLogger, Formatter, StreamHandler, DEBUG

import pigpio
import gpio.pigpiohelper as pigpiohelper
from controller.controller import Controller, ControllerType
from controller.controllerdata import ControllerEventType
from controller.speed import Speed
from controller.xboxdefs import XboxControllerInputHelper
from gpio.led import LED
from gpio.motordriver import ThreadedServo, Motor

IS_DEBUG = False

SG90_MIN_PULSE_WIDTH = 0.5
SG90_MAX_PULSE_WIDTH = 2.4
SG90_FRAME_WIDTH = 20

SERVO_INITIAL_PULSE = 1.5

LED_PIN = 16

SERVO_STEP_SLOW = 250
SERVO_STEP_MIDDLE = 500
SERVO_STEP_HIGH = 750
SERVO_STEP_MAX = 1000

SERVO_INTERVAL = 0.025

PAN_SERVO_PIN = 13
TILT_SERVO_PIN = 12

MOTOR_DRIVER_STATE_PIN = 26

LEFT_FORWARD_PIN = 22
LEFT_BACKWARD_PIN = 24
RIGHT_FORWARD_PIN = 27
RIGHT_BACKWARD_PIN = 23

MAIN_NAME = "RadioController"
CONTROLLER_NAME = "XboxController"
PAN_SERVO_NAME = "PanServo"
TILT_SERVO_NAME = "TiltServo"
LEFT_MOTOR_NAME = "LeftMotor"
RIGHT_MOTOR_NAME = "RightMotor"
LED_NAME = "CameraLED"

# logger configs
logger = getLogger(MAIN_NAME)
formatter = Formatter(
    "%(asctime)s - %(name)s - %(funcName)s - %(threadName)s | %(levelname)s | %(message)s"
)
handler = StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)

getLogger(CONTROLLER_NAME).addHandler(handler)

getLogger(PAN_SERVO_NAME).addHandler(handler)
getLogger(TILT_SERVO_NAME).addHandler(handler)

getLogger(LEFT_MOTOR_NAME).addHandler(handler)
getLogger(RIGHT_MOTOR_NAME).addHandler(handler)

getLogger(LED_NAME).addHandler(handler)

logger.propagate = False

if IS_DEBUG:
    logger.setLevel(DEBUG)
    getLogger(CONTROLLER_NAME).setLevel(DEBUG)
    getLogger(PAN_SERVO_NAME).setLevel(DEBUG)
    getLogger(TILT_SERVO_NAME).setLevel(DEBUG)
    getLogger(LEFT_MOTOR_NAME).setLevel(DEBUG)
    getLogger(RIGHT_MOTOR_NAME).setLevel(DEBUG)
    getLogger(LED_NAME).setLevel(DEBUG)


def run_servo(servo: ThreadedServo, speed: Speed, clockwise: bool) -> None:
    if speed == Speed.Slow:
        servo.move(SERVO_STEP_SLOW, SERVO_INTERVAL, clockwise)
    elif speed == Speed.Middle:
        servo.move(SERVO_STEP_MIDDLE, SERVO_INTERVAL, clockwise)
    elif speed == Speed.High:
        servo.move(SERVO_STEP_HIGH, SERVO_INTERVAL, clockwise)
    elif speed == Speed.Max:
        servo.move(SERVO_STEP_MAX, SERVO_INTERVAL, clockwise)


def get_dutycycle(speed: Speed) -> float:
    if speed == Speed.Slow:
        return 0.25
    elif speed == Speed.Middle:
        return 0.5
    elif speed == Speed.High:
        return 0.75
    elif speed == Speed.Max:
        return 1
    else:
        return 0


def run_motor_raw(motor: Motor, dutycycle: float, forward: bool = True) -> None:
    motor.move(dutycycle, forward)


def run_motor(motor: Motor, speed: Speed, forward: bool = True) -> None:
    dutycycle = get_dutycycle(speed)
    run_motor_raw(motor, dutycycle, forward)


def main():
    logger.info("Start initializing.")

    controller = Controller(controller_type=ControllerType.Xbox, name=CONTROLLER_NAME)

    led = LED(LED_PIN, LED_NAME)

    pan_servo = ThreadedServo(
        PAN_SERVO_PIN,
        SG90_MIN_PULSE_WIDTH,
        SG90_MAX_PULSE_WIDTH,
        SG90_FRAME_WIDTH,
        SERVO_INITIAL_PULSE,
        name=PAN_SERVO_NAME,
    )
    tilt_servo = ThreadedServo(
        TILT_SERVO_PIN,
        SG90_MIN_PULSE_WIDTH,
        SG90_MAX_PULSE_WIDTH,
        SG90_FRAME_WIDTH,
        SERVO_INITIAL_PULSE,
        name=TILT_SERVO_NAME,
    )

    left_motor = Motor(LEFT_FORWARD_PIN, LEFT_BACKWARD_PIN, name=LEFT_MOTOR_NAME)
    right_motor = Motor(RIGHT_FORWARD_PIN, RIGHT_BACKWARD_PIN, name=RIGHT_MOTOR_NAME)

    pi = pigpiohelper.get_instance()
    pi.set_mode(MOTOR_DRIVER_STATE_PIN, pigpio.INPUT)
    pi.set_pull_up_down(MOTOR_DRIVER_STATE_PIN, pigpio.PUD_DOWN)

    logger.info("End initializing.")

    try:
        controller.connect()

        # Wait for the controller to be connected before calling controller.run().
        while True:
            state = controller.data.get()

            if state.event == ControllerEventType.Connected:
                break

            if state.event == ControllerEventType.Quit:
                raise Exception("Faild to connect controller.")

        controller.run()

        logger.info("Start main loop of radio control.")
        while True:
            state = controller.data.get()

            if state.event == ControllerEventType.Quit:
                break

            if state.event == ControllerEventType.Disconnected:
                pan_servo.stop()
                tilt_servo.stop()
                left_motor.stop()
                right_motor.stop()

            if state.event != ControllerEventType.InputChanged:
                continue

            input = state.controller_input

            # LED lighting
            if XboxControllerInputHelper.HatX(input) > 0:
                # LED on if Hat Right is pushed.
                led.on()
            elif XboxControllerInputHelper.HatX(input) < 0:
                # LED off if Hat Left is pushed.
                led.off()

            if XboxControllerInputHelper.HatY(input) > 0:
                # Increment brightness of LED if Hat Up is pushed.
                led.increment_brightness()
            elif XboxControllerInputHelper.HatY(input) < 0:
                # Decrement brightness of LED if Had Down is pushed.
                led.decrement_brightness()

            # Control camera servo
            if XboxControllerInputHelper.StickRightX(input).value == 0:
                # Stop servo if Right Stick's X axis is neutral position.
                pan_servo.stop()
            else:
                # Run the servo clockwise or counterclockwise based on the tilt direction of the Left Stick's X axis.
                speed = Speed(XboxControllerInputHelper.StickRightX(input).value)
                clockwise = XboxControllerInputHelper.StickRightX(input).positive
                run_servo(pan_servo, speed, not clockwise)

            if XboxControllerInputHelper.StickRightY(input).value == 0:
                # Stop servo if Right Stick's Y axis is neutral position.
                tilt_servo.stop()
            else:
                # Run the servo clockwise or counterclockwise based on the tilt direction of the Left Stick's Y axis.
                speed = Speed(XboxControllerInputHelper.StickRightY(input).value)
                clockwise = XboxControllerInputHelper.StickRightY(input).positive
                run_servo(tilt_servo, speed, clockwise)

            if XboxControllerInputHelper.ButtonStickRight(input):
                # Move to initial position if Right Stick is pushed.
                pan_servo.initial()
                tilt_servo.initial()

            # Check motor driver chip's state
            if pi.read(MOTOR_DRIVER_STATE_PIN):
                logger.warn("Motor driver chip down. Waiting restart.")
                continue

            # Spin turn
            if (
                XboxControllerInputHelper.TriggerLeft(input).value != 0
                and XboxControllerInputHelper.TriggerRight(input).value == 0
            ):
                # Spin turn to left if only Trigger Left is pushed.
                speed = Speed(XboxControllerInputHelper.TriggerLeft(input).value)
                run_motor(left_motor, speed, False)
                run_motor(right_motor, speed)
                continue
            elif (
                XboxControllerInputHelper.TriggerLeft(input).value == 0
                and XboxControllerInputHelper.TriggerRight(input).value != 0
            ):
                # Spin turn to right if only Trigger Right is pushed.
                speed = Speed(XboxControllerInputHelper.TriggerRight(input).value)
                run_motor(left_motor, speed)
                run_motor(right_motor, speed, False)
                continue

            # Running motor
            if (
                XboxControllerInputHelper.StickLeftY(input).value == 0
                and XboxControllerInputHelper.StickLeftX(input).value == 0
            ):
                # Stop motor if Left Stick is neutral position.
                left_motor.stop()
                right_motor.stop()
            elif (
                XboxControllerInputHelper.StickLeftY(input).value != 0
                and XboxControllerInputHelper.StickLeftX(input).value == 0
            ):
                # Run forward or backward if Left Stick is tilted only Y axis.
                speed = Speed(XboxControllerInputHelper.StickLeftY(input).value)
                forward = not XboxControllerInputHelper.StickLeftY(input).positive
                run_motor(left_motor, speed, forward)
                run_motor(right_motor, speed, forward)
            elif (
                XboxControllerInputHelper.StickLeftY(input).value == 0
                and XboxControllerInputHelper.StickLeftX(input).value != 0
            ):
                # Turn left or right if Left Stick is tilted only X axis.
                speed = Speed(XboxControllerInputHelper.StickLeftX(input).value)
                if XboxControllerInputHelper.StickLeftX(input).positive:
                    right_motor.stop()
                    run_motor(left_motor, speed)
                else:
                    left_motor.stop()
                    run_motor(right_motor, speed)
            else:
                # Turn left or right
                #
                # ex) Turn left ->
                # RUNNING SPEED is based on Left Stick's Y axis value.
                # Right motor runs at RUNNING SPEED.
                # Left motor's speed is (RUNNING SPEED - Left Stick's X axis value * 0.15).
                # So, left motor runs 15-60% slower than RUNNING SPEED (slowest is 0).
                speed = Speed(XboxControllerInputHelper.StickLeftY(input).value)
                dutycycle = get_dutycycle(speed) - (
                    0.15 * XboxControllerInputHelper.StickLeftX(input).value
                )
                forward = not XboxControllerInputHelper.StickLeftY(input).positive

                if dutycycle < 0:
                    dutycycle = 0

                if XboxControllerInputHelper.StickLeftX(input).positive:
                    run_motor(left_motor, speed, forward)
                    run_motor_raw(right_motor, dutycycle, forward)
                else:
                    run_motor(right_motor, speed, forward)
                    run_motor_raw(left_motor, dutycycle, forward)

            if (
                XboxControllerInputHelper.ButtonBack(input)
                and XboxControllerInputHelper.ButtonStart(input)
            ):
                # Quit when Back button and Start button pushed.
                logger.info("End main loop of radio control.")
                break

    except Exception as e:
        logger.exception(e)

    finally:
        controller.quit()
        pan_servo.quit()
        tilt_servo.quit()
        left_motor.quit()
        right_motor.quit()
        led.quit()

        logger.info("End program.")


if __name__ == "__main__":
    main()
