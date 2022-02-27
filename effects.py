import time
import neopixel
import RPi.GPIO as GPIO
import random
import numpy as np
import json
import board
from subprocess import call

BLUE = [0, 0, 255]
RED = [255, 0, 0]
WHITE = [255, 255, 255]
OFF = [0, 0, 0]


def change_brightness(color: tuple, brightness: float = 1.0):
    return tuple(round(brightness * c) for c in color)


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)


class Ledstrip:
    def __init__(self):
        with open('config.json', 'r') as file:
            config_json = json.load(file)
        self.pixel_pin = board.D18
        self.n_pixels = config_json['main']["pixel_number"]
        self.ORDER = config_json['main']["pixel_order"]
        self.power_pin = config_json['main']["power_supply_pin"]
        self.colors_list = config_json['lighting']["colors"]
        self.walls_list = config_json['lighting']["wall_division"]
        self.default_effects_settings = config_json['lighting']["effects"]
        self.pixels = neopixel.NeoPixel(self.pixel_pin, self.n_pixels, auto_write=False, pixel_order=self.ORDER,
                                        brightness=1.0)
        self.wall_settings = {k: [[0,0,0], 1.0] for k in self.walls_list.keys()}

    def power_switch(self, value='OFF'):
        GPIO.setup(self.power_pin, GPIO.OUT)
        if value == 'OFF':
            GPIO.output(self.power_pin, GPIO.LOW)
        else:
            GPIO.output(self.power_pin, GPIO.HIGH)

    def set_off(self):
        global OFF
        self.pixels.fill(OFF)
        self.pixels.show()
    
    def set_white(self):
        global WHITE
        self.pixels.fill(WHITE)
        self.pixels.show()
        
    def set_global_brightness(self, brightness: float = 1.0):
        self.pixels.brightness = brightness

    def controller_shutdown(self):
        self.power_switch('OFF')
        GPIO.cleanup()
        call("sudo poweroff", shell=True)

    def random_color(self, prv_color: tuple = OFF):
        color = [0, 0, 0]
        if random.randint(1, 100) <= 40:
            rgb = [0, 1, 2]
            pos = random.choice(rgb)
            rgb.remove(pos)
            c1 = random.randint(0, 255)
            color[pos] = c1
            pos = random.choice(rgb)
            rgb.remove(pos)
            c2 = random.randint(0, 255 - c1)
            color[pos] = c2
            c3 = 255 - c1 - c2
            color[rgb[0]] = c3
        else:
            color = random.choice(list(self.colors_list.values()))
            while color == prv_color or color == [0,0,0]:
                color = random.choice(list(self.colors_list.values()))
        return color

    def set_color_wall(self, color: list, wall: tuple, brightness=1.0):
        if not isinstance(color, (tuple,list)):
            return TypeError(str(color))
        color = change_brightness(color, brightness)
        for i in range(min(wall), max(wall) + 1):
            self.pixels[i] = color
        self.pixels.show()

    def rainbow_cycle(self, speed: float = 0.01, direction: str = 'right', brightness: float = 1.0):
        self.set_off()
        self.set_global_brightness(brightness)
        if direction == 'right':
            while True:
                for j in range(255):
                    for i in range(self.n_pixels):
                        pixel_index = (i * 256 // self.n_pixels) + j
                        self.pixels[i] = wheel(pixel_index & 255)
                    self.pixels.show()
                    time.sleep(speed)
        elif direction == 'left':
            while True:
                for j in range(255):
                    for i in range(self.n_pixels - 1, -1, -1):
                        pixel_index = (i * 256 // self.n_pixels) + j
                        self.pixels[i] = wheel(pixel_index & 255)
                    self.pixels.show()
                    time.sleep(speed)

    def train(self, background_col: tuple = OFF, train_color: tuple = WHITE, train_speed: float = 0.5,
              train_size: int = 1, background_brightness: float = 1.0, train_brightness: float = 1.0):
        # efekt pociagu
        self.set_global_brightness(1.0)
        background_col = change_brightness(background_col, background_brightness)
        train_color = change_brightness(train_color, train_brightness)
        self.pixels.fill(background_col)
        while True:
            for i in range(train_size, self.n_pixels):
                if i < self.n_pixels - 1:
                    for j in range(i - train_size, i + 1):
                        self.pixels[j] = train_color
                    self.pixels.show()
                    time.sleep(train_speed)
                    self.pixels[i - train_size] = background_col
                    self.pixels.show()
                else:
                    for j in range(self.n_pixels - train_size, self.n_pixels):
                        self.pixels[j] = train_color
                    self.pixels.show()
                    time.sleep(train_speed)
                    self.pixels[self.n_pixels - train_size - 1] = background_col
                    self.pixels.show()
                    for j in range(0, train_size):
                        for k in range(0, j + 1):
                            self.pixels[k] = train_color
                        self.pixels.show()
                        time.sleep(train_speed)
                        self.pixels[self.n_pixels - train_size + j] = background_col
                        self.pixels.show()

    def akuku(self, color_1=RED, color_2=BLUE, dimmer_speed: float = 1.0, max_level: float = 1.0,
              min_level: float = 0.0):
        self.set_global_brightness(1.0)
        self.set_off()
        n = 0
        while True:
            if n == 0:
                self.pixels.fill(color_1)
                n += 1
            else:
                self.pixels.fill(color_2)
                n -= 1
            for i in range(round(100 * min_level), round(101 * max_level)):
                self.pixels.brightness = i / 100
                self.pixels.show()
                time.sleep(dimmer_speed / 100)
            for i in range(round(101 * max_level), round(100 * min_level), -1):
                self.pixels.brightness = i / 100
                self.pixels.show()
                time.sleep(dimmer_speed / 100)

    def random_spot(self, nspot, color=WHITE, background_col=OFF):
        pixel_id = [random.randint(0, self.n_pixels - 1) for _ in range(nspot)]
        pixel_id = set(pixel_id)
        if len(pixel_id) != nspot:
            while len(pixel_id) != nspot:
                pixel_id.add(random.randint(0, self.n_pixels - 1))
        self.pixels.fill(background_col)
        for i in pixel_id:
            self.pixels[i] = color
        self.pixels.show()

    def alter_light(self, color_1=RED, color_2=BLUE, speed=1.0, size=1, color_func=None):
        self.pixels.fill(OFF)
        while True:
            if isinstance(color_func, type(lambda x: x)):
                color_1 = color_func()
                color_2 = color_func()
            for i in range(0, self.n_pixels - 1, size * 2):
                for j in range(i, i + size):
                    self.pixels[j] = color_1
            self.pixels.show()
            time.sleep(speed)
            self.pixels.fill(OFF)
            for i in range(size, self.n_pixels - 1, size * 2):
                for j in range(i, i + size):
                    self.pixels[j] = color_2
            self.pixels.show()
            time.sleep(speed)
            self.pixels.fill(OFF)

    def strobe(self, speed=0.1, color=WHITE):
        while True:
            self.pixels.fill(color)
            self.pixels.show()
            time.sleep(speed)
            self.pixels.fill(OFF)
            self.pixels.show()
            time.sleep(speed)

    def asteroid(self, color=WHITE, size=10, background_color=OFF, speed=0.5):
        multiplier = list(np.linspace(1, 0, size))
        self.pixels.fill(OFF)
        for i in range(0, size):
            for j in range(i, -1, -1):
                self.pixels[j] = change_brightness(color, multiplier[size - 1 - j])
            self.pixels.show()
            time.sleep(speed)
        while True:
            for i in range(size, self.n_pixels):
                if i < self.n_pixels - 1:
                    for j in range(i - size, i + 1):
                        self.pixels[j] = change_brightness(color, multiplier[i - j - 1])
                    self.pixels.show()
                    time.sleep(speed)
                    self.pixels[i - size] = background_color
                    self.pixels.show()
                else:
                    for j in range(self.n_pixels - size, self.n_pixels):
                        self.pixels[j] = change_brightness(color, multiplier[self.n_pixels - j - 1])
                    self.pixels.show()
                    time.sleep(speed)
                    self.pixels[self.n_pixels - size - 1] = background_color
                    self.pixels.show()
                    for j in range(0, size):
                        for k in range(j, -1, -1):
                            self.pixels[k] = change_brightness(color, multiplier[j - k])
                        for k in range(self.n_pixels - 1, self.n_pixels - size + j):
                            self.pixels[k] = change_brightness(color, multiplier[j - k])
                        self.pixels.show()
                        time.sleep(speed)
                        self.pixels[self.n_pixels - size + j] = background_color
                        self.pixels.show()

    def ping_pong(self, color_1=BLUE, color_2=RED, background_color=OFF, speed=0.002):
        self.pixels.fill(background_color)
        while True:
            for i in range(0, self.n_pixels):
                self.pixels[i] = color_1
                self.pixels.show()
                time.sleep(speed)
            for i in range(0, self.n_pixels):
                self.pixels[i] = background_color
                self.pixels.show()
                time.sleep(speed)
            for i in range(self.n_pixels - 1, -1, -1):
                self.pixels[i] = color_2
                self.pixels.show()
                time.sleep(speed)
            for i in range(self.n_pixels - 1, -1, -1):
                self.pixels[i] = background_color
                self.pixels.show()
                time.sleep(speed)


if __name__ == "__main__":
    print(change_brightness([255, 234, 293], 0.67))
    # ls_test = Ledstrip()
    # print(ls_test.walls_list)
    # ls_test.random_color()
    # ls_test.set_color_wall(ls_test.colors_list['BLUE'], ls_test.walls_list['2'])
