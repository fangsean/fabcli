# -*- coding: utf-8 -*-   

import os

from yaml import load, Loader


def file_path(dir, reg):
    L = []
    for root, dirs, files in os.walk(dir):
        if "." not in os.path.basename(root):
            for file in files:
                if os.path.splitext(file)[1] == reg:
                    L.append(os.path.join(root, file))
    return L


def load_config(path):
    f = open(path, "r")
    config = load(f, Loader=Loader)
    f.close()
    return config
