def health_calc(damage, channel_name):
    # replace later from json specific to each guild
    RVD_health = [0, 1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000]
    AOD_health = [0, 1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000]
    RVD_health = [0, 1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000]

    # Parsing damage incase people fuckup the format...
    if (damage[damage.length() - 1].toLower() == 'm'):
        return "test successful"

    invalid_chars = ['.', '']