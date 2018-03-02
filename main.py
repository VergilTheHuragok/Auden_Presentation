import pygame
from pygame.image import load
import math
import time
import colorsys

from configs import get_game_root, get_value
from display import Textbox, Text, get_font_dict

pygame.init()

DISPLAY_FLAGS = pygame.FULLSCREEN
RESOLUTION = [1920, 1080]


class Image:

    def __init__(self, path, pins):
        self.path = path
        self.pins = pins

        self.temp_pins = None

    def pins_to_rect(self, original=False):
        x = self.pins[0] * display.get_width()
        y = self.pins[1] * display.get_height()
        if not isinstance(self.temp_pins, type(None)) and not original:
            x2 = self.temp_pins[0] * display.get_width()
            y2 = self.temp_pins[1] * display.get_height()
            # print(self.temp_pins, x2, y2)
        else:
            x2 = self.pins[2] * display.get_width()
            y2 = self.pins[3] * display.get_height()
        return [int(x), int(y), abs(int(x2 - x)), abs(int(y2 - y))]

    def get_size(self):
        return self.pins_to_rect()[2:]

    def get_pos(self):
        return self.pins_to_rect()

    def set_pos(self, point):
        width = display.get_width()
        height = display.get_height()
        self.pins[0] = point[0] / width
        self.pins[1] = point[1] / height
        self.pins[2] = (point[0] + self.pins_to_rect()[2]) / width
        self.pins[3] = (point[1] + self.pins_to_rect()[3]) / height
        print(self.pins)

    def render(self, display):
        image = load(self.path)
        image = pygame.transform.scale(image, self.get_size())  # TODO: Why does size animation start too large?
        display.blit(image, self.pins_to_rect())

    def resize(self, size, perma=False):

        rect = self.pins_to_rect(True)
        self.temp_pins = [(rect[0] + size[0]) / display.get_width(),
                          (rect[1] + size[1]) / display.get_height()]
        if perma:
            self.pins[2] = self.temp_pins[0]
            self.pins[3] = self.temp_pins[1]
            self.temp_pins = None


class Trait:

    def __init__(self, _type, trigger, name, new, speed=None, time=None,
                 accel=0):
        """:param accel: only affects speed"""
        self.type = _type
        self.name = name
        self.new = new
        self.trigger = trigger
        if not isinstance(speed, type(None)):
            self.speed = speed / 1000  # Standardize speed
        else:
            self.speed = None
        if not isinstance(time, type(None)):
            self.time = time * 1000  # Convert from seconds to millis
        else:
            self.time = None
        self.accel = accel / 1000000  # Standardize acceleration

        if isinstance(speed, type(None)) and isinstance(time, type(None)):
            raise Exception("Speed or Time must be provided")

        self.start = None

    def restart(self):
        self.start = None

    def check_triggers(self):
        for trigger in self.trigger:
            if trigger.replace("$", self.name) in triggers:
                return True
        return False

    def get_progress(self, old, image=False):
        run_time = get_time() - self.start
        if not isinstance(self.time, type(None)):
            if self.time == 0:
                percentage = 1
            else:
                percentage = run_time / self.time
        else:
            percentage = (self.speed * run_time) + (
                    .5 * self.accel * run_time ** 2)

        if percentage >= 1:
            trigger_name = self.name + "-"
            if trigger_name not in triggers:
                triggers.append(trigger_name)
            trigger_name = self.name + "+"
            if trigger_name in triggers:
                triggers.remove(trigger_name)

        if self.type == "location":
            new = self.new
            if isinstance(self.new[0], type(None)):
                new[0] = old[0]
            if isinstance(self.new[1], type(None)):
                new[1] = old[1]
            dist = get_dist(new, old)
            angle = angle_wrt_x(old, new)
            point = point_pos(old, int(dist * percentage), angle)
            point = list(int(val) for val in point)
            return point, percentage
        elif self.type == "color":
            old = to_HSL(old)
            new = to_HSL(self.new)

            difs = []
            for i in range(0, len(old)):
                difs.append(old[i] + (percentage * (new[i] - old[i])))
            return to_RGB(difs), percentage
        elif self.type == "size":
            if not image:
                return int(old + ((self.new - old) * percentage)), percentage
            nsize = [None, None]
            for i in range(0, 2):
                nsize[i] = int(old[i] + ((self.new[i] - old[i]) * percentage))
            # print(old, self.new, nsize)
            return nsize, percentage


class ScreenObject:

    def __init__(self, item, traits=None):
        self.item = item
        self.original_location = item.get_pos()
        self.traits = traits
        if isinstance(traits, type(None)):
            self.traits = []

    def animate(self):

        is_image = isinstance(self.item, Image)

        if isinstance(self.original_location, type(None)):
            self.original_location = self.item.get_pos()
        for trait in self.traits:
            trigger_name = trait.name + "-"
            if trigger_name in triggers:
                triggers.remove(trigger_name)
                trait.restart()
            if trait.check_triggers():

                # Start animation
                trigger_name = trait.name + "+"
                if trigger_name not in triggers:
                    triggers.append(trigger_name)
                # Remove animation end
                trigger_name = trait.name + "-"
                if trigger_name in triggers:
                    triggers.remove(trigger_name)

                if isinstance(trait.start, type(None)):
                    trait.start = get_time()
                if trait.type == "location":
                    point, percent = trait.get_progress(
                        self.original_location[:2], is_image)
                    self.item.set_pos(point)
                elif trait.type == "color":
                    color, percent = trait.get_progress(self.item.get_color(),
                                                        is_image)
                    self.item.set_color(color, percent >= 1)
                elif trait.type == "size":
                    if isinstance(self.item, Textbox):
                        font_name = self.item.lines[0][0].font_name
                        for text in self.item.whole_text_list:
                            if "size" in text.animations:
                                font_name = text.font_name
                                break
                        font_dict, actual_size = get_font_dict(font_name)
                        old_size = font_dict["size"]
                        size, percent = trait.get_progress(old_size, is_image)
                        self.item.resize(size, percent >= 1)
                    else:
                        size, percent = trait.get_progress(
                            self.original_location[2:], is_image)
                        self.item.resize(size, percent >= 1)


display = pygame.display.set_mode(RESOLUTION, DISPLAY_FLAGS)

BACKGROUND_COLOR = get_value("DISPLAY", "Background", "color", (0, 151, 167))

current_slide = 0
click_num = 0

triggers = ["start"]

rainbow_ani = [Trait("color",
                     ["start", "rainbow end-", "$+"],
                     "rainbow start",
                     (244, 66, 66), time=1),
               Trait("color", ["rainbow start-", "$+"],
                     "rainbow end",
                     (66, 244, 244), time=1),
               Trait("size",
                     ["start", "size end-", "$+"],
                     "size start",
                     30, time=1),
               Trait("size", ["size start-", "$+"],
                     "size end",
                     50, time=1)]

slides = [
    {"objects": [
        ScreenObject(
            Textbox(-1, .1, 0, 1,
                    [Text("Wystan Hugh Auden", "title")]),
            [Trait("location", ["start", "$+"],
                   "title slide", [100, None], time=1)]),
        ScreenObject(
            Textbox(-1, .2, 0, 1,
                    [Text("1907 - 1973", "subheader", animations=["color"])]),
            [Trait("location", ["click 1", "$+"],
                   "subheader slide", [1000, None], time=1)]),
        ScreenObject(Image(get_game_root() + "auden.jpg", [-1, .3, -.5, .8]),
                     [Trait("location", ["subheader slide-", "$+"],
                            "image slide", [300, None], time=0),
                      Trait("size", ["click 2", "$+"],
                            "image size", [200, 200], time=3)
                      ]
                     ),
        # ScreenObject(
        #     Textbox(.05, .05, 1, 1,
        #             [Text("TEST"), Text("test", "rainbow", animations=["color", "size"]), Text("TEST"), ]),
        #     rainbow_ani,
        # ),
    ]}
]


def get_clicks():
    """Finds the greatest needed click on the slide"""
    clicks = 0
    for obj in slides[current_slide]["objects"]:
        for trait in obj.traits:
            for trig in trait.trigger:
                if trig.startswith("click"):
                    _click_num = int(trig.replace("click ", ""))
                    if _click_num > clicks:
                        clicks = _click_num
    return clicks


def get_time():
    return time.time() * 1000


def to_HSL(ocolor):
    color = [(float)(ocolor[0]) / 255, (float)(ocolor[1]) / 255,
             (float)(ocolor[2]) / 255]
    color = colorsys.rgb_to_hls(color[0], color[1], color[2])
    ncolor = list(x for x in color)
    if len(ocolor) >= 4:
        ncolor.append(ocolor[3])
    return ncolor


def to_RGB(ocolor):
    ncolor = colorsys.hls_to_rgb(ocolor[0], ocolor[1], ocolor[2])
    ncolor = [(float)(ncolor[0]) * 255, (float)(ncolor[1]) * 255,
              (float)(ncolor[2]) * 255]
    if len(ocolor) >= 4:
        ncolor.append(ocolor[3])
    return ncolor


def get_dist(point1, point2):
    return math.sqrt(
        (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def angle_wrt_x(point1, point2):
    """Modified from here:
    https://stackoverflow.com/a/13544022
    """
    ax, ay = point1
    bx, by = point2
    return math.degrees(math.atan2(by - ay, bx - ax))


def point_pos(point, d, theta):
    """Found here:
    https://stackoverflow.com/a/23280722
    """
    x0 = point[0]
    y0 = point[1]
    theta_rad = math.pi / 2 - math.radians(theta)
    return x0 + d * math.sin(theta_rad), y0 + d * math.cos(theta_rad)


def get_boxes():
    """Get boxes on current slide"""
    return [obj.item for obj in slides[current_slide]["objects"] if
            isinstance(obj.item, Textbox)]


def get_images():
    """Get images on current slide"""
    return [obj.item for obj in slides[current_slide]["objects"] if
            isinstance(obj.item, Image)]


def get_items():
    """Get boxes and images on slide"""
    return get_boxes() + get_images()


def next_slide():
    global current_slide, click_num, triggers, quit
    if len(slides) > current_slide + 1:
        current_slide += 1
        click_num = 0
        triggers = ["start"]
    else:
        quit = True


quit = False
while not quit:
    display.fill(BACKGROUND_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit = True
        elif event.type == pygame.VIDEORESIZE:
            width, height = event.dict["size"]
            display = pygame.display.set_mode([width, height],
                                              DISPLAY_FLAGS)
        elif event.type == pygame.KEYDOWN:
            if event.dict["key"] == pygame.K_ESCAPE:
                quit = True
                break
            next_slide()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            click_num += 1
            triggers.append("click " + str(click_num))
            if click_num > get_clicks():
                next_slide()
                continue
        else:
            for box in get_boxes():
                box.handle_event(event, display)

    for box in get_items():
        box.render(display)

    for obj in slides[current_slide]["objects"]:
        obj.animate()
        # for trait in obj.traits:
        #     if trait.type == "location":
        #         print(trait.new)
        #         pygame.draw.circle(display, (255, 0, 0), trait.new[:2], 10)
        #         pygame.draw.circle(display, (0, 255, 0), obj.item.get_pos()[:2], 10)
        #         pygame.draw.circle(display, (255, 255, 0), obj.original_location[:2], 10)
    if "start" in triggers:
        triggers.remove("start")
    for trigger in triggers:
        if trigger.startswith("click"):
            triggers.remove(trigger)

    pygame.display.flip()

pygame.quit()
