import constants as c
import yaml
from image_manager import ImageManager

class Ingredient:

    ingredient_dict = {}

    def __init__(self, name, flavor_profile):
        Ingredient.load_spices_from_yaml()
        self.name = name
        self.flavors = flavor_profile

    def get_flavor(self, key):
        return self.flavors[key]

    def flavor_iter(self):
        for flavor in c.FLAVORS:
            if flavor in self.flavors:
                yield flavor, self.flavors[flavor]

    @staticmethod
    def primary_flavor(key):
        primary = 999
        max = 34
        for flavor in c.FLAVORS:
            if Ingredient.ingredient_dict[key]["flavors"][flavor] > max:
                max = Ingredient.ingredient_dict[key]["flavors"][flavor]
                primary = flavor
        return primary

    @staticmethod
    def primary_flavor_intensity(key):
        primary = Ingredient.primary_flavor(key)
        return Ingredient.ingredient_dict[key]["flavors"][primary]

    @staticmethod
    def load_spices_from_yaml():
        if not Ingredient.ingredient_dict:
            Ingredient.load_ingredient_dict()

    @staticmethod
    def from_key(name):
        Ingredient.load_spices_from_yaml()
        return Ingredient(name, Ingredient.ingredient_dict[name]["flavors"])

    @staticmethod
    def load_ingredient_dict():
        with open("assets/yaml/ingredients.yaml") as f:
            raw = f.read()
        Ingredient.ingredient_dict = yaml.safe_load(raw)
        Ingredient.normalize_ingredient_flavors()

    @staticmethod
    def normalize_ingredient_flavors():
        # Make them add to 100
        for key in Ingredient.ingredient_dict:
            flavors = Ingredient.ingredient_dict[key]["flavors"]
            for flavor in c.FLAVORS:
                if flavor not in flavors:
                    flavors[flavor] = 0
            for fkey in flavors:
                flavors[fkey] += 100
            total = 0
            for flavor in c.FLAVORS:
                total += flavors[flavor]
            for flavor in c.FLAVORS:
                flavors[flavor] *= 100/total


    @staticmethod
    def get_surf(key):
        Ingredient.load_spices_from_yaml()
        if (not key in Ingredient.ingredient_dict) or (not "image" in Ingredient.ingredient_dict[key]):
            return ImageManager.load("pyracy/TestSprite.png")
        return ImageManager.load(Ingredient.ingredient_dict[key]["image"])