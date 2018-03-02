import base64

import jsonpickle

from cryptography.fernet import Fernet


key = b'\xdb3\x06ht\xd5_\x98\x0c\xee\x100{\xcf=\xe6\x07G|hl\x1bq\x15ah\xdf\xc1|5\xf4\xc0'
key = base64.urlsafe_b64encode(key)


def decrypt(bytes_message):
    """Takes an encrypted bytes object and returns a decrypted one"""
    cipher = Fernet(key)
    return cipher.decrypt(bytes_message)


def encrypt(message):
    """Takes a decrypted string and returns an encrypted bytes object"""
    cipher = Fernet(key)
    return cipher.encrypt(bytes(message, "utf8"))


def encode(obj):
    """Encodes an object as a string"""
    return jsonpickle.encode(obj)


def decode(obj):
    """Decodes a string into an object"""
    return jsonpickle.decode(obj)


def encrypt_obj_to_file(obj, path):
    """Writes an object to a file and obfuscates"""
    obj = encode(obj)
    obj = encrypt(obj)

    file = open(path, "wb")
    file.write(obj)
    file.close()


def decrypt_obj_from_file(path):
    """Reads an an obfuscated object from a file"""
    file = open(path, "rb")
    obj = file.read()
    file.close()

    obj = decrypt(obj)
    obj = decode(obj)

    return obj
