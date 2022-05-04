import sys
import re

placeholder = "LoremipsumdolorsitametconsecteturadipiscingelitseddoeiusmodtemporincididuntutlaboreetdoloremagnaaliquaUtenimadminimveniamquisnostrudexercitationullamcolaborisnisiutaliquipexeacommodoconsequatDuisauteiruredolorinreprehenderitinvoluptatevelitessecillumdoloreeufugiatnullapariaturExcepteursintoccaecatcupidatatnonproidentsuntinculpaquiofficiadeseruntmollitanimidestlaborum"
placeholder_index = 0
excluded = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "every", "st", "rd", "nd", "th", "x", "w", "p"
]


def repl(match):
    m = match.group()
    if m.lower() in excluded:
        return m

    global placeholder_index
    s = placeholder_index
    e = s + len(m)
    if e >= len(placeholder):
        s = 0
        e = s + len(m)
    placeholder_index = e
    return placeholder[s:e]


with open(sys.argv[1], "r") as file:
    for line in file:
        print(re.sub(r"[a-zA-Z]+", repl, line), end="")
