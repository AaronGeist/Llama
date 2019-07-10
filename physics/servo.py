import RPi.GPIO as GPIO
import time

from core.cache import Cache


class Servo:
    hPin = None
    vPin = None

    H_DB_KEY = "horizontal_duty_cycle"
    V_DB_KEY = "vertical_duty_cycle"

    @staticmethod
    def initialize():
        if Servo.hPin is None and Servo.vPin is None:
            if Cache().get(Servo.H_DB_KEY) is None:
                Cache().set(Servo.H_DB_KEY, 7.5)
            if Cache().get(Servo.V_DB_KEY) is None:
                Cache().set(Servo.V_DB_KEY, 7.5)

            try:
                # horizontal servo
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(17, GPIO.OUT, initial=False)
                Servo.hPin = GPIO.PWM(17, 50)  # 50HZ
                Servo.hPin.start(0)
            except Exception as e:
                print(e)


            # vertical servo
            GPIO.setup(19, GPIO.OUT, initial=False)
            Servo.vPin = GPIO.PWM(19, 50)  # 50HZ
            Servo.vPin.start(0)

    @staticmethod
    def control(vDelta=0.0, hDelta=0.0):
        Servo.initialize()
        if vDelta != 0:
            duty_cycle = float(Cache().get(Servo.V_DB_KEY))
            duty_cycle += vDelta
            if duty_cycle < 2.5 or duty_cycle > 12.5:
                return
            print(duty_cycle)
            Cache().set(Servo.V_DB_KEY, duty_cycle)
            Servo.vPin.ChangeDutyCycle(duty_cycle)
            time.sleep(0.02)
            Servo.vPin.ChangeDutyCycle(0)
            time.sleep(0.2)

        if hDelta != 0:
            duty_cycle = float(Cache().get(Servo.H_DB_KEY))
            duty_cycle += hDelta
            if duty_cycle < 2.5 or duty_cycle > 12.5:
                return
            print(duty_cycle)
            Cache().set(Servo.H_DB_KEY, duty_cycle)
            Servo.hPin.ChangeDutyCycle(duty_cycle)
            time.sleep(0.02)
            Servo.hPin.ChangeDutyCycle(0)
            time.sleep(0.2)

    @staticmethod
    def left():
        Servo.control(hDelta=-0.25)

    @staticmethod
    def right():
        Servo.control(hDelta=0.25)

    @staticmethod
    def up():
        Servo.control(vDelta=0.25)

    @staticmethod
    def down():
        Servo.control(vDelta=-0.25)


if __name__ == "__main__":
    Servo.left()
    Servo.left()
    Servo.left()
    Servo.left()
    Servo.left()
    Servo.right()
    Servo.right()
    Servo.right()
    Servo.right()
    Servo.right()
