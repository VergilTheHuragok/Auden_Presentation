import os


def get_game_root():
    """Gets the path to the root folder of the game"""

    path = os.getcwd().replace("\\", "/")
    if "floobits" in path or "PycharmProjects" in path:
        # Running from interpreter
        path_parts = path.split("/")
        path = path_parts[0] + "/" + path_parts[1] + "/" + path_parts[
            2] + "/Desktop/Auden Pres"
    else:
        # Running from compiled source
        path = path[:path.rfind("/")]

    return path + "/"


def get_config_string():
    """Creates the path to the config if necessary and returns its string"""
    while True:
        try:
            config = open(get_game_root() + "config.txt", "r")
        except FileNotFoundError:
            try:
                os.mkdir(get_game_root())  # Create root folder if necessary
            except FileExistsError:
                pass
            config = open(get_game_root() + "config.txt", "w")
            config.close()
        else:
            break
    _config_string = config.read()
    config.close()
    return _config_string


def get_header_range(header, config_string=None):
    """Returns the range of the given header."""
    if isinstance(config_string, type(None)):
        config_string = get_config_string()
    start_ind = config_string.find("§" + header + "\n")
    if start_ind == -1:
        raise Exception(
            "Header: '" + header + "' not found in config to range")
    end_ind = config_string.find("§", start_ind + 1)  # Find next header ind
    if end_ind == -1:
        # No next header
        end_ind = len(config_string)  # Find end of config
    if end_ind >= 2 and config_string[end_ind - 1] == "\n" \
            and config_string[end_ind - 2] == "\n":
        end_ind -= 1  # Account for double new line char before headers

    return start_ind, end_ind


def get_subheader_range(header, subheader, config_string=None):
    """Returns the range of the given subheader"""
    if isinstance(config_string, type(None)):
        config_string = get_config_string()
    start_ind, end_ind = get_header_range(header, config_string)
    original_start_ind = start_ind
    section = config_string[start_ind:end_ind]  # Header range

    start_ind = section.find("#" + subheader + "\n")
    if start_ind == -1:
        raise Exception("Subheader: '" + subheader + "' not found under "
                                                     "header: '" + header
                        + "' to search")
    end_ind1 = section.find("#", start_ind + 1)  # Find next sub ind
    end_ind2 = section.find("§", start_ind)  # Find next header ind
    if end_ind1 == -1 and end_ind2 == -1:
        end_ind = len(section)  # Find end of config
    else:
        # Choose the closest end index that is not -1
        end_ind = min(filter(lambda x: x != -1, [end_ind1, end_ind2]))

    return start_ind + original_start_ind, end_ind + original_start_ind


def get_key_range(header, subheader, key, config_string=None):
    """Returns the range from the start of the key given to the end of its
    value
    """
    if isinstance(config_string, type(None)):
        config_string = get_config_string()
    start_ind, end_ind = get_subheader_range(header, subheader, config_string)
    original_start_ind = start_ind
    section = config_string[start_ind:end_ind]  # Subheader range

    start_ind = section.find(key + " = ")
    if start_ind == -1:
        raise Exception("Key: '" + key + "' not found under subheader: '"
                        + subheader + "' under header: '" + header
                        + "' to search")
    end_ind = section.find("\n", start_ind)  # Find value end
    if end_ind == -1:
        # Could not find end of value
        end_ind = len(section)  # Find end of config

    return start_ind + original_start_ind, end_ind + original_start_ind


def get_ind(header, subheader, key, default_val="No Value Given"):
    """Returns the index range of a value in the config and adds any missing
    values if default is given
    """
    added_value = False
    config_string = get_config_string()
    has_default = default_val != "No Value Given"
    if has_default:
        if isinstance(default_val, str):
            default_val = "'" + default_val + "'"
        else:
            default_val = str(default_val)

    if "§" + header + "\n" not in config_string:
        # Could not find header
        if has_default:
            if len(config_string) > 0:
                config_string += "\n"
            config_string += "§" + header + "\n"
        else:
            raise Exception("Could not find header: '"
                            + header + "' and no value was given to input")
    # Header has been found or created
    start_ind, end_ind = get_header_range(header, config_string)
    if config_string.find("#" + subheader + "\n", start_ind, end_ind) == -1:
        # Could not find subheader
        if has_default:
            config_parts = [config_string[:end_ind], config_string[end_ind:]]
            config_string = config_parts[
                                0] + "#" + subheader + "\n" + config_parts[1]
        else:
            raise Exception("Could not find subheader: '"
                            + subheader + "' under header: '" + header
                            + "' and no value was given to input")
    # Subheader has been found or created
    start_ind, end_ind = get_subheader_range(header, subheader, config_string)
    key_ind = config_string.find(key + " = ", start_ind, end_ind)
    if key_ind == -1:
        # Could not find key
        if has_default:
            config_parts = [config_string[:end_ind], config_string[end_ind:]]
            config_string = \
                config_parts[
                    0] + key + " = " + default_val + "\n" + config_parts[1]
            added_value = True
        else:
            raise Exception("Could not find key: '"
                            + key + "' under subheader: '" + subheader
                            + "' under header: '" + header
                            + "'and no value was given to input")
    # Key found
    start_ind, end_ind = get_key_range(header, subheader, key, config_string)

    config = open(get_game_root() + "config.txt", "w")
    config.write(config_string)
    config.close()

    return start_ind + len(key) + len(" = "), end_ind, added_value


def add_value(header, subheader, key, value):
    """Adds or changes a value in the config"""
    indexes = get_ind(header, subheader, key, value)
    if indexes[2]:
        # Value was not in config, added value during index search
        return
    if isinstance(value, str):
        value = "'" + value + "'"
    else:
        value = str(value)
    # Key is already in config, replace value in index range with new value
    config_string = get_config_string()
    config_string = config_string[:indexes[0]] + value + config_string[
                                                         indexes[1]:]
    config = open(get_game_root() + "config.txt", "w")
    config.write(config_string)
    config.close()


def update_value(header, subheader, key, default_val):
    """Adds the given value to the config if not already present"""
    get_value(header, subheader, key, default_val)


def get_value(header, subheader, key, default_val="No Value Given"):
    """Returns the evaled value of the given config key and adds default_val if
    key not found
    """
    indexes = get_ind(header, subheader, key, default_val)
    config_string = get_config_string()
    value = config_string[indexes[0]:indexes[1]]
    return eval(value)  # TODO: Reset value if error on eval


def get_headers():
    """Returns a list of all headers in config"""
    config_string = get_config_string()
    headers = []
    i = 0
    for phrase in config_string.split("§"):
        # Add each word after a §
        if i > 0:  # Do not add phrase before first §
            headers.append(phrase[:phrase.index("\n")])
        i += 1
    return headers


def get_subheaders(header):
    """Returns a list of all headers under given header in config"""
    config_string = get_config_string()
    subheaders = []

    start_ind, end_ind = get_header_range(header)
    section = config_string[start_ind:end_ind]

    i = 0
    for phrase in section.split("#"):
        if i > 0:  # Do not add phrase before first #
            subheaders.append(phrase[:phrase.index("\n")])
        i += 1
    return subheaders


def get_keys(header, subheader):
    """Returns a list of all keys under given header and subheader in config"""
    config_string = get_config_string()
    keys = []

    start_ind, end_ind = get_subheader_range(header, subheader)
    section = config_string[start_ind:end_ind]

    for phrase in section.split("\n"):
        if " = " in phrase:  # Do not add phrase before first key
            keys.append(phrase[:phrase.index(" = ")])
    return keys


def add_from_dict(config_dict, update=True):
    """Adds all keys from a given config dictionary.
    :param update: Only add keys not already present
    """
    for header in config_dict:
        for subheader in config_dict[header]:
            for key in config_dict[header][subheader]:
                val = config_dict[header][subheader][key]
                if update:
                    update_value(header, subheader, key, val)
                else:
                    add_value(header, subheader, key, val)


def get_config_dict():
    """Returns a dictionary made from the config"""
    config_dict = {}
    for header in get_headers():
        header_dict = {}
        for subheader in get_subheaders(header):
            subheader_dict = {}
            for key in get_keys(header, subheader):
                subheader_dict[key] = get_value(header, subheader, key)
            header_dict[subheader] = subheader_dict
        config_dict[header] = header_dict
    return config_dict


def gen_random_config():
    """For testing purposes"""
    import random
    import string

    for i in range(0, random.randint(1, 3)):
        header = ''.join(random.choices(string.ascii_uppercase + string.digits,
                                        k=random.randint(1, 10)))
        for j in range(0, random.randint(1, 5)):
            subheader = ''.join(random.choices(string.ascii_letters
                                               + string.digits,
                                               k=random.randint(1, 10)))
            for k in range(0, random.randint(1, 5)):
                key = ''.join(random.choices(string.ascii_letters
                                             + string.digits,
                                             k=random.randint(1, 10)))
                for l in range(0, random.randint(1, 3)):
                    value = ''.join(
                        random.choices(string.ascii_letters + string.digits,
                                       k=random.randint(1, 10)))
                    add_value(header, subheader, key, value)


def print_config():
    """For debug purposes"""
    print(get_headers())
    for header in get_headers():
        print("    ", header, get_subheaders(header))
        for subheader in get_subheaders(header):
            print("        ", subheader, get_keys(header, subheader))
            for key in get_keys(header, subheader):
                print("            ", key, get_value(header, subheader, key))