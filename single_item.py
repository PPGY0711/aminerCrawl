# -*- encoding=utf-8 -*-
import json


class Author(object):
    def __init__(self, name, img, citation, paper_list, theme):
        self.name = name
        self.img = img
        self.citaion = citation
        self.paper_list = paper_list
        self.theme = theme

    def print_to_json(self):
        info = {"name": self.name, "img_src": self.img, "citation": self.citaion, "paper_list": self.paper_list}
        return info
