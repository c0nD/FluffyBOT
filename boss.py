# boss.py
import attr, cattrs, json


@attr.define
class Boss:
    name: str
    level: int
    guild: str
    hp: int = 0
    hp_list: list = []
    hits: list = []

    def __attrs_post_init__(self):
        # Boss HP at each level : index = level
        self.hits = []
        self.hp_list = [0, 100, 1000, 10000, 100000, 1000000]
        self.hp = self.hp_list[self.level]

    def set_hp(self, hp):
        self.hp = hp

    def take_damage(self, damage, user):
        self.hp -= damage
        self.hits.append(Hit(damage, user))

    def killed(self):
        self.level += 1
        self.hp = self.hp_list[self.level]

    def overkill_damage(self, damage):
        self.hp -= damage


@attr.define
class Hit:
    damage: int
    user_id: int


@attr.define
class Guild:
    users: dict = {}
    bosses = list = []
