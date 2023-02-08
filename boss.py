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
    current_users_hit: list = []
    is_done: bool = False
    done_tasks: dict = {}
    queue: list = []
    last_kill_id: int = 0


    def __attrs_post_init__(self):
        # Boss HP at each level : index = level
        self.hits = []
        self.hp_list = [0, 8400000, 13692000, 21246400, 31393600, 44172800, 59192000, 75549600, 91834400,
                        102300800, 108528000, 111781600, 115136000, 118591200, 122147200, 125809600,
                        129584000, 132176800, 134820000, 137519200, 140268800, 143074400, 145936000,
                        148853600, 151832800, 154868000, 157964800, 160333600, 162736000, 165177600,
                        167652800, 172720800, 177945600, 183327200, 188865600, 194572000, 200452000,
                        206511200, 212749600, 219178400, 225803200, 232629600, 239657600, 246904000,
                        254363200, 262052000, 269970400, 278129600, 286535200, 295198400, 304124800,
                        313320000, 322789600, 332550400, 342602400, 352956800, 363624800, 374617600,
                        385935200, 397600000, 409617600, 421999200, 434750400, 447893600, 461434400,
                        475384000, 489748000, 504554400, 519803200, 535511200, 551695232, 568371968,
                        585547200, 603243200, 621476800, 640264832, 659618432, 679554432, 700095232,
                        721251968, 743052800, 765508800, 788642432, 812476032, 837032000, 862332800,
                        888395200, 915247200, 942911200, 971415200, 1000776000,
                        9999999999999, 9999999999999, 9999999999999, 9999999999999, 9999999999999,
                        9999999999999, 9999999999999, 9999999999999, 9999999999999, 9999999999999,
                        9999999999999, 9999999999999, 9999999999999, 9999999999999, 9999999999999]

        self.hp = self.hp_list[self.level]
        self.current_users_hit = []
        self.queue = []
        is_done = True

        
    def set_hp(self, hp):
        self.hp = hp

    def take_damage(self, damage, user, used_ticket, split, boss_level):
        self.hp -= damage
        self.hits.append(Hit(damage, user, used_ticket, split, boss_level))
        if self.hp == 0:
            self.last_kill_id = user
        else:
            self.last_kill_id = 0

    def killed(self):
        self.level += 1
        self.hp = self.hp_list[self.level]
        self.current_users_hit.clear()

    def overkill_damage(self, damage):
        self.hp -= damage

    def undo(self, idx):
        hit = self.hits[idx]
        if hit.boss_level == self.level:
            self.hp += hit.damage
        else:
            self.hp = hit.damage
            self.level = hit.boss_level
        self.hits.pop(idx)


    # For fixing hps
    def admin_hit(self, damage):
        self.hp -= damage

    def admin_kill(self):
        self.level += 1
        self.hp = self.hp_list[self.level]
        self.current_users_hit.clear()

    def admin_revive(self):
        self.level -= 1
        self.hp = self.hp_list[self.level]
        self.current_users_hit.clear()

    def admin_undo(self):
        hit = self.hits[-1]
        if hit.boss_level == self.level:
            self.hp += hit.damage
        else:
            self.hp = hit.damage
            self.level = hit.boss_level
        self.hits.pop(-1)

@attr.define
class Hit:
    damage: int
    user_id: int
    ticket_used: bool
    split: bool
    boss_level: int
    username: str = ''


@attr.define
class Guild:
    users: dict = {}
    bosses = list = []
