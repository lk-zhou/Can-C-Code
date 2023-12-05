#!/usr/bin/python3

import os
import importlib

def check(pack_name):
    try:
        importlib.import_module(pack_name)
        return True
    except ImportError:
        return False

if check("chardet"):
    import chardet


class file_op:
    def __init__(self, file_path=None, new_file=False):
        self.file_path = file_path
        if new_file is False:
            self.file_mode = "r"
        else:
            self.file_mode = "w"
        self.file_obj = None


    def open(self, file_path=None):
        if file_path is None:
            if self.file_path is None:
                print("[Warning] file_path is None\n")
                return False
        else:
            self.file_path = file_path

        try:
            f = open(self.file_path,
                     mode=self.file_mode,
                     encoding=self.detect_encoding(self.file_path))
            self.file_obj = f
            return True
        except Exception as e:
            print("[Error] failed to open %s" % self.file_path)
            return False

    def write(self,message):
        if self.file_obj is not None:
            self.file_obj.write(message)

    def is_opened(self):
        if self.file_obj is None:
            return False
        else:
            return True

    def close(self):
        if self.file_obj is not None:
            self.file_obj.close()
            self.file_obj = None

    def readline(self):
        if self.file_obj is None:
            return None

        line = self.file_obj.readline()
        if line == "":
            return None

        return line


    def detect_encoding(self, file_path):
        try:
            with open(file_path, "rb") as f:
                det = chardet.detect(byte_str = f.read())
        except Exception as e:
            print("Failed to detect file encoding" % file_path)
            return None

        return det["encoding"]
