import pandas as pd
import re
from unidecode import unidecode

def erreorder(t):
    replacements = str.maketrans({"c": "",
                                  "ô": "a",
                                  "o": "a",
                                  "e": "b",
                                  "ê": "b",
                                  "î": "c",
                                  "i": "c",
                                  "a": "d",
                                  "â": "d",
                                  "u": "e",
                                  "û": "e",
                                  "b": "f",
                                  "j": "g",
                                  "n": "h",
                                  "m": "i",
                                  "h": "j",
                                  "d": "k",
                                  "k": "l",
                                  "f": "m",
                                  "t": "n",
                                  "z": "o",
                                  "p": "p",
                                  "r": "q",
                                  "g": "r",
                                  "s": "s",
                                  "l": "t",
                                  "v": "u"})
    return t.translate(replacements)

def fr(x):
    return unidecode(x.lower().replace("œ","oe"))

def er(x):
    if len(x.split(","))<=2:
        return ""
    else:
        return erreorder(unidecode(x.split(",")[1].lower()))+","+erreorder(unidecode(x.split(",")[0].lower()))

def balisage(t):
    l = t.split("\n")
    l2 = []
    for line in l:
        ls = line.split(",")
        ls2 = []
        for e in ls:
            x=re.sub(r"\€(.*?)\€", r"\\begin{ernestienenv}\1\\end{ernestienenv}", e)
            x=re.sub(r"\£(.*?)\£", r"\\begin{ernestientrad}\1\\end{ernestientrad}", x)
            x=re.sub(r"\_\_(.*?)\_\_", r"\\emph{\1}", x)
            x=re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", x)
            x=re.sub(r"\#(.*?)\#", r"$\1$", x)
            ls2.append(x)
        l2.append(",".join(ls2))
    return "\n".join(l2)


async def processcsv():
    # Lire le fichier CSV en respectant les guillemets
    df = pd.read_csv("tex/ernestien.csv", quotechar='"', sep=',', skip_blank_lines=True)

    # Remplacer les virgules dans toutes les cellules
    df = df.map(lambda x: x.replace(',', '{|comma}') if isinstance(x, str) else x)

    # Sauvegarder le fichier modifié
    df.to_csv("tex/ernestien_comma.csv", index=False, quotechar='"')

    f = open("tex/ernestien_comma.csv","rb")
    r = f.read().replace(b"\n,,\r\n",b"\n").replace(b"\x90",b"").decode(errors="replace").replace("·",".")
    f.close()

    l = r.split("\n")

    lfr = [l[0]]+sorted(l[1:],key=fr)
    rfr = "\n".join(lfr)
    ler = [l[0]]+sorted(l[1:],key=er)
    rer = "\n".join(ler)


    rfrform = rfr.replace("\"\"","''") \
             .replace("\"","") \
             .replace("''","\"") \
             .replace("ref ", "ref. ") \
             .replace("(nom)","(n.)") \
             .replace("(adjectif)","(adj.)") \
             .replace("(adverbe)","(adv.)") \
             .replace("\\","{\\backslash}") \
             .replace("$","").replace("œ","oe")

    rerform = rer.replace("\"\"","''") \
             .replace("\"","") \
             .replace("''","\"") \
             .replace("ref ", "ref. ") \
             .replace("(nom)","(n.)") \
             .replace("(adjectif)","(adj.)") \
             .replace("(adverbe)","(adv.)") \
             .replace("\\","{\\backslash}") \
             .replace("$","").replace("œ","oe")

    rfrform = balisage(rfrform).replace("_","").replace("{|comma}","{\\comma}").encode(errors="replace")
    rerform = balisage(rerform).replace("_","").replace("{|comma}","{\\comma}").encode(errors="replace")

    f2 = open("tex/frer.csv","wb")
    f2.write(rfrform)
    f2.close()

    f3 = open("tex/erfr.csv","wb")
    f3.write(rerform)
    f3.close()


if __name__ == "__main__":
    processcsv()
