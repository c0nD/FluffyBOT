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
    current_users_hit = []

    def __attrs_post_init__(self):
        # Boss HP at each level : index = level
        self.hits = []
        self.hp_list = [8400000, 13692000, 21246400, 31393600, 44172800, 59192000, 75549600, 91834400,
                        102300800, 108528000, 111781600, 115136000, 118591200, 122147200, 125809600,
                        129584000, 132176800, 134820000, 137519200, 140268800, 143074400, 145936000,
                        148853600, 151832800, 154868000, 157964800, 160333600, 162736000, 165177600,
                        167652800, 172720800, 177945600, 183327200, 188865600, 194572000, 200452000,
                        206511200, 212749600, 219178400, 225803200, 232629600, 239657600, 246904000,
                        254363200, 262052000, 269970400, 278129600, 286535200, 295198400, 304124800,
                        313320000, 322789600, 332550400, 342602400, 352956800, 363624800, 374617600,
                        385935200, 397600000, 409617600, 421999200, 434750400, 447896300, 461434400,
                        475384000, 489748000, 504554400, 519803200, 535511200, 551695232, 568371968,
                        585547200, 603243200, 621476800, 640264832, 659618432, 679554432, 700095232]

        self.hp = self.hp_list[self.level]

    def set_hp(self, hp):
        self.hp = hp

    def take_damage(self, damage, user, used_ticket, split):
        self.hp -= damage
        self.hits.append(Hit(damage, user, used_ticket, split))

    def killed(self):
        self.level += 1
        self.hp = self.hp_list[self.level]
        self.current_users_hit.clear()

    def overkill_damage(self, damage):
        self.hp -= damage


@attr.define
class Hit:
    damage: int
    user_id: int
    ticket_used: bool
    split: bool
    username: str = ''


@attr.define
class Guild:
    users: dict = {}
    bosses = list = []
