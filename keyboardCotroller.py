import random

def get_random_key(previous_key):
    if previous_key in ["w", "a", "s", "d"]:
        # 如果上一次的值是“w”、“a”、“s”或“d”，下一个只能是“ ”、“f”、“e”、“r”、“n”
        return random.choice(["-", "f", "e", "r", "n"])
    elif previous_key == "r":
        # 如果上一次的值是“r”，下一个可以是“w”、“a”、“s”或“d”
        return random.choice(["w", "a", "s", "d"])
    else:
        # 如果上一次是空格或其他情况，随机选择所有
        return random.choice(["w", "a", "s", "d", "-", "f", "e", "r", "n"])

def map_key(targetmap):
    if targetmap == "Shenzhen":
        key_array = ['d','n','r','w','n','n','r','-','w','n','n','n','r','s','r']
        return key_array
    elif targetmap == 2:
        return "a"
    elif targetmap == 3:
        return "s"
    elif targetmap == 4:
        return "d"
    else:
        return "n"