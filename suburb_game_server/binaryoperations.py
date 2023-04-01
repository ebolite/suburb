import random

bintable = { # key: input value: output
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "A": 10,
    "B": 11,
    "C": 12,
    "D": 13,
    "E": 14,
    "F": 15,
    "G": 16,
    "H": 17,
    "I": 18,
    "J": 19,
    "K": 20,
    "L": 21,
    "M": 22,
    "N": 23,
    "O": 24,
    "P": 25,
    "Q": 26,
    "R": 27,
    "S": 28,
    "T": 29,
    "U": 30,
    "V": 31,
    "W": 32,
    "X": 33,
    "Y": 34,
    "Z": 35,
    "a": 36,
    "b": 37,
    "c": 38,
    "d": 39,
    "e": 40,
    "f": 41,
    "g": 42,
    "h": 43,
    "i": 44,
    "j": 45,
    "k": 46,
    "l": 47,
    "m": 48,
    "n": 49,
    "o": 50,
    "p": 51,
    "q": 52,
    "r": 53,
    "s": 54,
    "t": 55,
    "u": 56,
    "v": 57,
    "w": 58,
    "x": 59,
    "y": 60,
    "z": 61,
    "?": 62,
    "!": 63,
    }

reversebintable = {value : key for (key, value) in bintable.items()}

def convertto6b(int):
    return(f"{int:06b}")

def stringtobin(code):
    out = ""
    for letter in code:
        out += str(convertto6b(bintable[letter]))
    return out

def bintostring(binary): #bin as string
    code = ""
    letters = []
    for index in range(0, len(binary), 6):
        letters.append(binary[index: index+6])
    for letter in letters:
        num = int(letter, 2) # convert to number
        code += reversebintable[num] # add from reverse binary table
    return code

def bitand(bin1, bin2): # codes as binary string
    final = ""
    for index, digit in enumerate(bin1):
        if digit == "1" and bin2[index] == "1":
            final += "1"
        else:
            final += "0"
    return final

def bitor(bin1, bin2): # codes as binary string
    final = ""
    for index, digit in enumerate(bin1):
        if digit == "1" or bin2[index] == "1":
            final += "1"
        else:
            final += "0"
    return final

def codeand(code1: str, code2: str): # codes as code string
    bin1 = stringtobin(code1)
    bin2 = stringtobin(code2)
    finalbin = bitand(bin1, bin2)
    final = bintostring(finalbin)
    return final

def codeor(code1: str, code2: str): # codes as code string
    bin1 = stringtobin(code1)
    bin2 = stringtobin(code2)
    finalbin = bitor(bin1, bin2)
    final = bintostring(finalbin)
    return final

def is_valid_code(code) -> bool:
    if len(code) != 8: return False
    validated_code = "".join([char for char in code if char in bintable])
    if code != validated_code: return False
    return True

def random_valid_code() -> str:
    code = []
    for i in range(8):
        code.append(random.choice(list(bintable.keys())))
    return "".join(code)