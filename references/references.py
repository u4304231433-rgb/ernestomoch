from thefuzz import fuzz
import re

FILE = "references.txt"

SEUIL = 80

f = open(FILE, "r", encoding="utf-8")
c = f.read()
f.close()

lines = c.split("\n")
refs = []
for l in lines[2:]:
    refs.append(l.split(":")[1])

def second(x):
    return -x[1]

def scoring(txt):
    answ = []
    for ref in refs:
        for replique in ref.split("/"):
            r = fuzz.ratio(replique, txt)
            score = r*0.75
            if len(replique) >= 2  and replique[0] == "(" and replique[-1] == ")":
                # ref mineure
                score = r*0.5
            if len(replique) >= 0:
                s = re.findall("\\+\\+(.*?)\\+\\+",replique)
                for res in s:
                    score += fuzz.ratio(res, txt)*10/len(replique)*0.5
            answ.append((replique,score))
    answ.sort(key=second)
    return answ[:3]

print(scoring("veau"))
