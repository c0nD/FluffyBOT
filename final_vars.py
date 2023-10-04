import linecache

guild_id = int(linecache.getline('guild_id.txt', 1))
admin_roles = []
valid_channels = ["dragon","avatar","abyss"]
split_threshold = 3
max_queue_length = 2
guilds = {
    "toasted": None,
    "pearl": None,
    "burnt": None,
    "royal": None,
    "spring": None,
    "fall": None,
    "onion": None,

    "toasted_sandbox": None,
    "pearl_sandbox": None,
    "burnt_sandbox": None,
    "royal_sandbox": None,
    "spring_sandbox": None,
    "fall_sandbox": None,
    "onion_sandbox": None,

    "dev": None,
}

ping_roles = {
    "avatar": 1067512238497349753,
    "living_abyss": 1067512238497349753,
    "dragon": 1067512238497349753
}

sweeper_roles = {
    "avatar": 1067512238497349753,
    "living_abyss": 1067512238497349753,
    "dragon": 1067512238497349753
}

sweeper_requirements = {
    "onion": {
        "avatar": 100_000_000,
        "living_abyss": 135_000_000,
        "dragon": 5_000_000
    },
    "fall": {
        "avatar": 100_000_000,
        "living_abyss": 140_000_000,
        "dragon": 5_000_000
    },
    "spring": {
        "avatar": 85_000_000,
        "living_abyss": 140_000_000,
        "dragon": 5_000_000
    },
    "burnt": {
        "avatar": -1,
        "living_abyss": 130_000_000,
        "dragon": 5_000_000
    },
    "other": {
        "avatar": 5_000_000,
        "living_abyss": 5_000_000,
        "dragon": 5_000_000
    }
}

split_exempt = ["onion", "spring", "fall", "burnt", "toasted", "royal", "pearl", "onion_sandbox", "toasted_sandbox", 
                "pearl_sandbox", "burnt_sandbox", "royal_sandbox", "spring_sandbox", "fall_sandbox", "dev"]

# ERRORS MADE TO BE CONSTANTS
INVALID_INT_ERR = '''**ERROR: Please double check that you input a full integer value, correct number for level and hp
(will not accept comma separated numbers). 
If there is some other error: please contact a developer.**'''

INSERT_HIT_ERR = '''**ERROR: Please double check that you input the exact, correct number for level and hp
(will not accept comma separated numbers). 
If there is some other error, please contact your staff to get them to reset the boss at it's current level and hp.**'''

BOSS_SETUP_ERR = '''**ERROR: A boss has not been set up in this channel. Check /help for more information.
Please contact staff/a developer if you think this is a mistake.**'''

INVALID_GUILD_ERR = '''**ERROR: Invalid guild entered. Check /help for more information.
Please contact staff/a developer if you think this is a mistake.**'''

INVALID_BOSS_ERR = '''**ERROR: Cannot create two bosses at once, or no boss exists in this channel. 
If you want to reset the boss, please call `/delete_boss` first. Otherwise, use `/create_boss` to make a new boss.**'''

INVALID_CHANNEL_ERR = "**ERROR: Cannot create boss in this channel. Please try this command again in a valid channel.**"

INVALID_HP_ERR = "**ERROR: HP was set higher than boss level allows for. Please try again with valid HP.**"

INVALID_UNDO_ERR = "**ERROR: You can only undo the last command if you ran it.**"

INVALID_PARAM_ERR = "**ERROR: The parameter that has been entered is incorrect. Please either check the command description or /help for more information.**"
