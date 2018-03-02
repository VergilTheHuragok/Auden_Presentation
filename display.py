import pygame

from configs import get_value, add_from_dict, get_config_dict, add_value
from default_configs import fonts as default_fonts

fonts = {}
break_chars = get_value("DISPLAY", "Text", "break-chars",
                        r"-.!?+=_,:;()[]{}`~@\\$%^&*|<>")
default_color = get_value("DISPLAY", "Textboxes", "color", (255, 255, 255))
default_border_size = get_value("DISPLAY", "Textboxes", "border-size", -1)
default_scroll_amount = get_value("DISPLAY", "Textboxes", "scroll-amount", .5)
default_zoom_scale = get_value("DISPLAY", "Textboxes", "zoom-scale", 1)
min_font_size = get_value("DISPLAY", "Text", "min-font-size", 3)
max_font_size = get_value("DISPLAY", "Text", "max-font-size", 500)


def reload_fonts():
    """Pulls the latest fonts from the config"""
    global fonts
    fonts = {}


def get_font_dict(font_name, font_resize=0):
    """Updates font dict to include font object and returns dict"""
    global fonts

    actual_size = None

    if isinstance(font_name, type(None)):
        font_name = "default"
    if font_name not in fonts:
        # Update fonts if not in list
        add_from_dict(
            default_fonts)  # Update config to include all default fonts
        fonts = get_config_dict()[
            "FONTS"]  # Update fonts list to include conf fonts
        if font_name not in fonts:
            # Font missing from default)_fonts/config
            raise Exception("Font: '" + font_name + "' not found in fonts list")
    # font_name is in fonts
    if "font object" not in fonts[font_name] or font_resize != 0:
        # Need to add pygame font object to font's dict.
        # has not been created yet

        # Get/add each necessary variable to fonts dict
        if "bold" not in fonts[font_name]:
            fonts[font_name]["bold"] = False
        font_bold = fonts[font_name]["bold"]

        if "italic" not in fonts[font_name]:
            fonts[font_name]["italic"] = False
        font_italic = fonts[font_name]["italic"]

        if "size" not in fonts[font_name]:
            fonts[font_name]["size"] = fonts["Default"]["size"]
        font_size = fonts[font_name]["size"]

        if "color" not in fonts[font_name]:
            fonts[font_name]["color"] = fonts["Default"]["color"]

        if "highlight color" not in fonts[font_name]:
            fonts[font_name]["highlight color"] = None

        try:
            # Create the font
            new_font_size = font_size + int(font_resize)
            actual_size = min(max(new_font_size, min_font_size), max_font_size)
            font = pygame.font.SysFont(fonts[font_name]["name"], actual_size,
                                       font_bold,
                                       font_italic)
        except OSError:
            if font_name == "Default":
                raise Exception("Default font could not be loaded. "
                                "Change in config.")
            # Font is not default, use default instead
            print("Could not load font: '" + font_name + ",' using Default "
                                                         "font instead.")
            font, actual_size = get_font_dict("Default")
            font = font["font object"]
        fonts[font_name]["font object"] = font

    return fonts[font_name], actual_size


class Text(object):
    """Stores variables and methods for displaying pygame text"""

    def __init__(self, text="\n", font_name=None, hover_text_list=None,
                 animations=None):
        self.text = text
        self.whole = text
        self.font_name = font_name
        self.hover_text_list = hover_text_list
        self.pos = None
        self.label = None
        self.width = None
        self.height = None

        self.color_override = None
        self.font_resize = 0

        self.animations = animations
        if isinstance(animations, type(None)):
            self.animations = []

    def set_color(self, color, perma=False):
        if perma:
            fonts[self.font_name]["color"] = color
        self.color_override = color
        self.label = None

    def resize(self, size, perma=False):
        font_dict, actual_size = get_font_dict(self.font_name)
        old_size = font_dict["size"]
        self.font_resize = size - old_size
        self.label = None
        if perma:
            fonts[self.font_name]["size"] = size

    def get_color(self):
        font_dict, actual_size = get_font_dict(self.font_name)
        return font_dict["color"]

    def get_text(self):
        return self.text

    def copy(self, text=None):
        """Returns a copy of the text object with new text"""
        if isinstance(text, type(None)):
            text = self.text
        new_text = Text(text, self.font_name, self.hover_text_list)
        new_text.whole = self.whole
        new_text.animations = self.animations
        new_text.font_resize = self.font_resize
        new_text.color_override = self.color_override
        return new_text

    def break_line(self, remaining_width, font_resize=0):
        """Breaks into two texts where overflows remaining_width"""
        word = ""
        dash = ""
        for char in self.text:
            word += char
            if self.copy(word).get_dimensions(font_resize)[0] > remaining_width:
                if len(word) >= 3 and word[-3] != " ":
                    dash = "-"
                    word = word[:-2]
                else:
                    word = word[:-1]
                break
        word2 = self.text[len(word):]
        return self.copy(word + dash), self.copy(word2)

    def break_chars(self, break_char="\n"):
        """Breaks text into separate words at break_char"""
        words = []
        word = ""
        i = 0
        for char in self.text:
            i += 1
            word += char
            if char == break_char or len(self.text) == i:
                words.append(self.copy(word))
                word = ""
        return words

    def get_dimensions(self, font_resize=0):
        """Returns dimensions of text, generates new dimensions if necessary"""
        if isinstance(self.width, type(None)):
            font, actual_size = get_font_dict(self.font_name, font_resize)
            font = font["font object"]
            self.width, self.height = font.size(self.text)
        return self.width, self.height

    def get_label(self, font_resize=0):
        """Generates if necessary and returns a label

        :param font_resize: amount to resize fonts by for zooming
        """
        actual_size = None

        if isinstance(self.label, type(None)) or font_resize != 0:
            font_dict, actual_size = get_font_dict(self.font_name, font_resize)
            font = font_dict["font object"]
            color = font_dict["color"]
            if not isinstance(self.color_override, type(None)):
                color = self.color_override
            self.label = font.render(self.text.strip().replace("\n", ""), 1,
                                     color, font_dict["highlight color"])
        return self.label, actual_size

    def clear_for_pickle(self):
        """Clears the label in order to not mess with the pickling process"""
        self.label = None

    def render(self, display, pos, font_resize):
        """Renders text to given display"""
        self.pos = pos
        _font_resize = font_resize
        if self.font_resize != 0:
            _font_resize = self.font_resize
        label, actual_size = self.get_label(_font_resize)
        display.blit(label, pos)
        return actual_size

    def is_hovered(self, mouse_pos):
        """Checks whether text is being hovered"""
        if isinstance(self.pos, type(None)):
            print("Warning: Text not yet rendered when click attempted")
            # TODO: Does this ever occur and is it a problem?
            return False
        width, height = self.get_dimensions()
        if self.pos[0] <= mouse_pos[0] <= self.pos[0] + width:
            if self.pos[1] <= mouse_pos[1] <= self.pos[1] + height:
                return True
        return False

    def get_hover_text(self):
        return self.hover_text_list


class Textbox:

    def __init__(self, x_pin, y_pin, x2_pin, y2_pin, text_list=None, name=None,
                 color=None, border_size=None, scroll_amount=None,
                 zoom_scale=None, allow_zoom=False):
        self.name = name
        self.x_pin = x_pin
        self.y_pin = y_pin
        self.x2_pin = x2_pin
        self.y2_pin = y2_pin

        self.color = color
        if isinstance(color, type(None)):
            self.color = default_color
        self.border_size = border_size
        if isinstance(border_size, type(None)):
            self.border_size = default_border_size
        self.scroll_amount = scroll_amount  # Number of lines to scroll
        if isinstance(scroll_amount, type(None)):
            self.scroll_amount = default_scroll_amount
        self.zoom_scale = zoom_scale  # Multiply zoom amount by this
        if isinstance(zoom_scale, type(None)):
            self.zoom_scale = default_zoom_scale

        self.text_list = []
        self.whole_text_list = []
        if not isinstance(text_list, type(None)):
            self.add_text_list(text_list)
        self.lines = []
        self.line_num = 0  # Current line scroll is on
        self.current_scroll = 0
        # ^ Must reach 1/self.scroll_amount if self.scroll_amount < 0 to scroll

        self.width = None
        self.height = None
        self.screen_width = None
        self.screen_height = None

        self.font_resize = 0
        self.zoom_amount = 0

        self.zoom_switch = None
        self.zoom_limit = None

        self.allow_zoom = allow_zoom

        self.rect = None

        # TODO: Allow saving of multiple self.lines for easily redisplaying tooltips?

    def get_all_contained_texts(self):
        texts = []
        texts += self.text_list
        texts += self.whole_text_list
        for line in self.lines:
            texts += line
        return texts

    def get_color(self):
        for text in self.whole_text_list:
            if "color" in text.animations:
                return text.get_color()
        return self.whole_text_list[0].get_color()

    def set_color(self, color, perma=False):
        for text in self.get_all_contained_texts():
            if "color" in text.animations:
                text.set_color(color, perma)

    def resize(self, size, perma=False):
        for text in self.get_all_contained_texts():
            if "size" in text.animations:
                text.resize(size, perma)
        self.rewrap()

    def get_pos(self):
        if isinstance(self.rect, type(None)):
            return None
        return list(int(val) for val in self.rect)

    def set_pos(self, point):
        """Moves upper left corner to point"""
        self.x_pin = point[0] / self.screen_width
        self.y_pin = point[1] / self.screen_height
        self.x2_pin = (point[0] + self.rect[1]) / self.screen_width
        self.y2_pin = (point[1] + self.rect[3]) / self.screen_height

    def within_bounds(self, pos, display):
        width = display.get_width()
        height = display.get_height()
        bounds = [int(self.x_pin * width),
                  int(self.y_pin * height),
                  int(self.x2_pin * width),
                  int(self.y2_pin * height)]

        if bounds[2] >= pos[0] >= bounds[0]:
            if bounds[3] >= pos[1] >= bounds[1]:
                return True
        return False

    def handle_event(self, event, display):
        cursor_pos = pygame.mouse.get_pos()
        if self.within_bounds(cursor_pos, display):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    # Scroll down in box
                    self.scroll(False)
                elif event.button == 5:
                    # Scroll up in box
                    self.scroll()

    def scroll(self, up=True):
        # Allow for scroll amounts of less than zero which scroll every interval
        ctrl_held = pygame.key.get_mods() & pygame.KMOD_CTRL
        if ctrl_held and self.allow_zoom:
            if not up:
                if self.zoom_limit != 1:
                    # Zoom instead of scroll
                    if self.zoom_limit == -1:
                        self.zoom_limit = None
                    if self.zoom_switch == -1:
                        self.zoom_amount = 0
                    self.zoom_switch = 1
                    if self.zoom_amount == 0:
                        self.zoom_amount = self.zoom_scale
                    self.zoom_amount *= self.zoom_scale
                    self.zoom_amount *= self.zoom_scale
                    self.font_resize += self.zoom_amount
                    self.rewrap()
            else:
                if self.zoom_limit != -1:
                    if self.zoom_limit == 1:
                        self.zoom_limit = None
                    if self.zoom_switch == 1:
                        self.zoom_amount = 0
                    self.zoom_switch = -1
                    if self.zoom_amount == 0:
                        self.zoom_amount = self.zoom_scale
                    self.zoom_amount *= self.zoom_scale
                    self.font_resize -= self.zoom_amount
                    self.rewrap()
        else:
            scroll_int = 0
            scroll_amount = self.scroll_amount
            if self.scroll_amount < 1:
                scroll_int = 1 / self.scroll_amount
                scroll_amount = 1
            self.current_scroll += 1
            if self.current_scroll >= scroll_int:
                self.current_scroll = 0
                if not up:
                    self.line_num -= int(scroll_amount)
                else:
                    self.line_num += int(scroll_amount)
                self.check_scroll()

    def add_text_list(self, text_list):
        self.text_list += text_list
        self.whole_text_list += text_list

    def get_dimensions(self):
        if isinstance(self.width, type(None)):
            raise Exception("Access to dimensions attempted before rendering "
                            "for textbox: '" + self.name + "'.")
        return self.width, self.height

    def update_dimensions(self, display):
        # Update dimensions if necessary
        width = display.get_width()
        height = display.get_height()
        changed = False
        if width != self.screen_width:
            # Width has been changed
            self.screen_width = width
            self.width = (self.x2_pin * width) - (self.x_pin * width)
            changed = True
        if height != self.screen_height:
            # Width has been changed
            self.screen_height = height
            self.height = (self.y2_pin * height) - (self.y_pin * height)
            changed = True
        if changed:
            self.rewrap()

    def render(self, display):
        self.update_dimensions(display)  # Will always rewrap on first render
        self.wrap()

        x = self.x_pin * display.get_width()
        y = self.y_pin * display.get_height()
        x2 = self.x2_pin * display.get_width()
        y2 = self.y2_pin * display.get_height()
        rect = [x, y, x2 - x, y2 - y]

        self.rect = rect

        pygame.draw.rect(display, self.color, rect, self.border_size)
        self.check_scroll()

        _y = y
        for line in self.lines[self.line_num:]:
            line_height = self.get_line_dimensions(line)[1]
            if _y + line_height > y2:
                break
            else:
                _x = x
                for word in line:
                    word_size = word.render(display, (_x, _y), self.font_resize)
                    if not isinstance(word_size, type(None)):
                        if word_size == max_font_size:
                            self.zoom_limit = 1
                        elif word_size == min_font_size:
                            self.zoom_limit = -1
                    _x += word.get_dimensions(self.font_resize)[0]
            _y += line_height
        if not isinstance(self.zoom_limit, type(None)):
            self.zoom_amount = 0

    def get_line_dimensions(self, line=None):
        if isinstance(line, type(None)):
            line = self.lines[0]
        height = 0
        width = 0
        for word in line:
            height = max(height, word.get_dimensions(self.font_resize)[1])
            width += word.get_dimensions(self.font_resize)[0]
        return width, height

    def check_scroll(self):
        if self.line_num >= len(self.lines):
            self.line_num = len(self.lines) - 1
        if self.line_num < 0:
            self.line_num = 0

    def rewrap(self):
        """Rewraps all lines in the event of a resolution change."""
        self.lines = []
        self.text_list = self.whole_text_list[:]
        self.wrap()

    def check_line_can_fit(self, text):
        """Checks whether given text can fit in last line"""
        if len(self.lines[-1]) > 0 and self.lines[-1][-1].get_text().endswith(
                "\n"):
            return False  # Last line ended with new line char
        width = 0
        for _text in self.lines[-1]:
            width += _text.get_dimensions(self.font_resize)[0]
        if width + text.get_dimensions(self.font_resize)[0] <= \
                self.get_dimensions()[0]:
            return True
        return False

    def wrap(self):
        """Wraps all text left in text_list, does not affect previous lines
        except where new text fits on last line.
        """
        break_char_ind = 0
        while len(self.text_list) > 0:
            text = self.text_list.pop(0)  # Get first text in queue
            words = text.break_chars()  # Break at newlines
            while len(words) > 0:
                word = words[0]

                # Add initial line
                if len(self.lines) == 0:
                    self.lines.append([])
                    continue

                # Check if fits on previous line
                elif self.check_line_can_fit(word):
                    # It fits, don't continue
                    self.lines[-1].append(word)

                # Try breaking at spaces
                elif " " in word.get_text()[1:-1]:
                    # Test whether space is within word (not at ends)
                    words.pop(0)
                    for w in word.break_chars(" ")[::-1]:
                        words.insert(0, w)
                    continue

                # Try making new line
                elif len(self.lines[-1]) > 0:
                    self.lines.append([])
                    continue

                # Try breaking at break chars
                elif break_char_ind < len(break_chars):
                    break_char = break_chars[break_char_ind]
                    if break_char in word.get_text()[1:-1]:
                        # Test whether char is within word (not at ends)
                        words.pop(0)
                        for w in word.break_chars(break_char)[::-1]:
                            words.insert(0, w)
                    break_char_ind += 1
                    continue

                # Try breaking at char closest to edge
                else:
                    char_width = word.copy("W").get_dimensions(
                        self.font_resize)[0]

                    if char_width <= self.width:
                        # Single char can fit on screen
                        if len(self.lines[-1]) == 0 and len(self.lines) > 1:
                            # Remove previously added empty line
                            self.lines.pop()
                        previous_width = self.get_line_dimensions(self.lines[
                                                                      -1])[0]
                        char_line_width = previous_width + char_width
                        can_fit_char = char_line_width < self.width
                        previous_line_exists = len(self.lines[-1]) > 0
                        previous_newline = False
                        if previous_line_exists:
                            previous_newline = self.lines[-1][-1].get_text(). \
                                endswith("\n")
                        if previous_line_exists and can_fit_char \
                                and not previous_newline:
                            # Previous line has room for chars,
                            # not newline char
                            words.pop(0)
                            for w in word.break_line(
                                    self.width - previous_width,
                                    self.font_resize)[::-1]:
                                words.insert(0, w)
                            continue
                        else:
                            self.lines.append([])
                            words.pop(0)
                            for w in word.break_line(self.width,
                                                     self.font_resize)[::-1]:
                                words.insert(0, w)
                            continue
                    else:
                        # Skip word, font too large
                        pass

                # TODO: Wrap at wrap points

                # Word was added, did not continue
                break_char_ind = 0
                words.pop(0)
                if word.get_text().endswith("\n"):
                    self.lines.append([])
