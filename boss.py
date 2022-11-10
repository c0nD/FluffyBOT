import attr, cattr, json


class Boss:
    def __init__(self, name, level):
        # Boss HP at each level : index = level
        hp_list = [0, 100, 1000, 10000, 100000, 1000000]
        self.hits = []
        self.name = name
        self.level = level
        self.level_hp = hp_list
        self.hp = self.level_hp[self.level]

    def set_hp(self, hp):
        self.hp = hp

    def take_damage(self, damage, user):
        self.hp -= damage
        self.hits.append(Hit(damage, user))

    def killed(self):
        self.level += 1
        self.hp = self.level_hp[self.level]

    def overkill_damage(self, damage):
        self.hp -= damage


class Hit:
    def __init__(self, damage, user):
        self.damage = damage
        self.user = user