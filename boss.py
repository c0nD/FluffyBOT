# boss.py
import attr, math

def get_hp(level: int = 1, lookforward: int = 150): #Extremely accurate to level 512
    levels = []
    for lvl in range(lookforward):
        lvl += level - 1
        if lvl == 0:
            hp = 0
        elif lvl < 10+1: #1-9
            hp = -875*lvl**8/9 + 10510*lvl**7/3 - 477820*lvl**6/9 + 439110*lvl**5 - 19518625*lvl**4/9 + 19735240*lvl**3/3 - 96754280*lvl**2/9 + 40013320*lvl/3 + 1013600
        elif lvl < 20+1:
            lvl -= 9
            hp = -23945*lvl**9/324 + 10550*lvl**8/3 - 3857015*lvl**7/54 + 7287980*lvl**6/9 - 607387235*lvl**5/108 + 222180350*lvl**4/9 - 5511190465*lvl**3/81 + 1013238020*lvl**2/9 - 872805200*lvl/9 + 141159200
        elif lvl < 30+1:
            lvl -= 19
            hp = 8125*lvl**9/108 - 33100*lvl**8/9 + 1381795*lvl**7/18 - 8044540*lvl**6/9 + 229140415*lvl**5/36 - 257202400*lvl**4/9 + 2168904245*lvl**3/27 - 135038440*lvl**2 + 124485560*lvl + 96331200
        else:
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
