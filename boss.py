# boss.py
import attr, math

def get_hp(level: int = 1, lookforward: int = 150): #Extremely accurate to level 512
    levels = [0, 8400000, 13692000, 21246400, 31393600, 44172800, 59192000, 75549600, 91834400,
                        102300800, 108528000, 111781600, 115136000, 118591200, 122147200, 125809600,
                        129584000, 132176800, 134820000, 137519200, 140268800, 143074400, 145936000,
                        148853600, 151832800, 154868000, 157964800, 160333600, 162736000, 165177600,
                        167652800, 172720800, 177945600, 183327200, 188865600, 194572000, 200452000]
    for lvl in range(len(levels),lookforward):
        hp = round(12253.654 * 1.030225 ** lvl) * 5600
        levels.append(math.ceil(hp))
    return levels

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
    hit_history: list = []
    queue: list = []
    queue_front: int = None


    def __attrs_post_init__(self):
        # Boss HP at each level : index = level
        self.hits = []
        self.hp_list = get_hp(level=1,lookforward=200) # If you run out of levels, just increase lookforward.
        self.hp = self.hp_list[self.level]
        self.current_users_hit = []
        self.queue = []
        is_done = True
        
    def set_hp(self, hp):
        self.hp = hp

    def take_damage(self, damage, user, used_ticket, split, boss_level):
        self.hp -= damage
        self.hits.append(Hit(damage, user, used_ticket, split, boss_level))

    def killed(self):
        self.level += 1
        self.hp = self.hp_list[self.level]
        self.current_users_hit.clear()

    def overkill_damage(self, damage):
        self.hp -= damage

    def undo(self):
        for i in range(self.hit_history[-1]):
            hit = self.hits[-1]
            if hit.boss_level == self.level:
                self.hp += hit.damage
            else:
                self.hp = hit.damage
                self.level = hit.boss_level
            self.hits.pop(-1)
        self.hit_history.pop(-1)


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
    
    def admin_set_level(self, level):
        self.level = level
        self.hp = self.hp_list[self.level]
        self.current_users_hit.clear()
    
    def admin_set_hp(self, hp):
        self.hp = hp 

    def admin_undo(self):
        for i in range(self.hit_history[-1]):
            hit = self.hits[-1]
            if hit.boss_level == self.level:
                self.hp += hit.damage
            else:
                self.hp = hit.damage
                self.level = hit.boss_level
            self.hits.pop(-1)
        self.hit_history.pop(-1)

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
    bosses: list = []
