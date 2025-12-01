from thefuzz import fuzz
import re
from discord import File


def load_references():
    f = open(FILE, "r", encoding="utf-8")
    c = f.read()
    f.close()

    lines = c.split("\n")
    refs = []
    for l in lines[2:]:
        if l.replace(" ", "") != "":
            ls = l.split(":")
            gif = None
            if len(ls) == 3:
                gif = ls[2]
            refs.append({"tag": ls[0], "text": ls[1], "gif": gif})
    return refs

def save_references(refs):
    fo = open(FILE, "r", encoding="utf-8")
    text = fo.read()
    fo.close()
    t = "\n".join(text[:2])+"\n"
    t += "\n".join([ref["tag"]+":"+ref["text"]+(":"+ref["gif"] if ref["gif"] is not None else "" for ref in refs)])
    f = open(FILE, "w", encoding="utf-8")
    f.write(t)
    f.close()

def second(x):
    return x[1]

def search_in(txt,replique2, skip=False):
    replique = re.sub("\\((.*?)\\)","",replique2)
    if not skip:
        score = fuzz.ratio(replique.replace("+",""), txt.replace("+",""))
    else:
        score = 0
    if len(replique) >= 0:
        s = re.findall("\\+\\+(.*?)\\+\\+", replique)
        for res in s:
            score += fuzz.ratio(res.replace("+",""), txt.replace("+",""))**1.5/10
    if len(replique) >= 0:
        s = re.findall("\\+(.*?)\\+",replique.replace("++",""))
        for res in s:
            score += fuzz.ratio(res.replace("+",""), txt.replace("+",""))**1.5/20
    return score

def argmax(l,key=lambda x: x):
    m = key(l[0])
    im = 0
    for i in range(1,len(l)):
        c = key(l[i])
        if c > m:
            im = i
            m = c
    return im
    

def scoring(txt):
    if txt.replace("+","") != "":
        answ = []
        for i_ref, ref in enumerate(refs):
            for i_repl, replique in enumerate(ref["text"].split("/")):
                for i_mom, mom in enumerate(replique.split(";")):
                    if mom.replace("(","").replace(")","") != "":
                        score = search_in(txt,mom)+search_in(mom,txt,True)*2
                        answ.append((mom,score, i_ref,i_repl,i_mom))
        im = argmax(answ,key=second)
        return answ[im]
    else:
        return None


def get_real_next(l,i):
    for j in range(i+1,len(l)):
        if l[j] == "":
            return None # le dialogue est break par un //
        elif re.sub("\\((.*?)\\)", "", l[j]).replace(" ", "").replace(";", "").replace("+", "") != "":
            return l[j]
    return None # on est arrivé au bord

def reform_text(t):
    return re.sub("\\((.*?)\\)", "", t).replace("+","").replace("{\\pointvirgule}",";").replace("{\\deuxpoints}", ":").replace("{\\gauchepar}","(").replace("{\\droitepar}",")")


SEUIL = 100
SEUIL_FOLLOW = 140

if __name__ != "__main__":
    FILE = "references/references.txt"
    refs = load_references()

    async def process_message(txt, channel):
        first = scoring(txt)
        if first is not None:
            (mom,score, i_ref,i_repl,i_mom) = first
            if score >= SEUIL:
                if score >= SEUIL_FOLLOW:
                    x = refs[i_ref]["text"].split("/")
                    x0 = x[i_repl]
                    if get_real_next(x0.split(";"),i_mom) is not None:
                        await channel.send(reform_text(get_real_next(x0.split(";"),i_mom)))
                        #print(reform_text(get_real_next(x0.split(";"),i_mom)))
                    elif get_real_next(x,i_repl) is not None:
                        await channel.send(reform_text(get_real_next(x,i_repl).split(";")[0]))
                        #print(reform_text(get_real_next(x,i_repl).split(";")[0]))
                else:
                    # la ref est pas très précise mais ernestomoch renvoie
                    await channel.send(reform_text(refs[i_ref]["text"].split("/")[i_repl].replace(";"," ")))
                    #print(reform_text(refs[i_ref]["text"].split("/")[i_repl].replace(";"," ")))
                if refs[i_ref]["gif"] is not None:
                    await channel.send(file=File(f"references/gifs/{refs[i_ref]['gif']}_{refs[i_ref]['tag']}.gif"))
                    #print("gif", refs[i_ref]["gif"])

else:
    FILE = "references.txt"
    refs = load_references()
    while True:
        t = input("> ")
        first = scoring(t)
        if first is not None:
            (mom,score, i_ref,i_repl,i_mom) = first
            print(f"[{score} ({i_ref},{i_repl},{i_mom})]", mom)
            if score >= SEUIL:
                print(f"[{score} ({i_ref},{i_repl},{i_mom})]", mom)
                if refs[i_ref]["gif"] is not None:
                    print("gif", refs[i_ref]["gif"])
                elif score >= SEUIL_FOLLOW:
                    x = refs[i_ref]["text"].split("/")
                    x0 = x[i_repl]
                    if get_real_next(x0.split(";"),i_mom) is not None:
                        print(reform_text(get_real_next(x0.split(";"),i_mom)))
                    elif get_real_next(x,i_repl) is not None:
                        print(reform_text(get_real_next(x,i_repl).split(";")[0]))
                else:
                    # la ref est pas très précise mais ernestomoch renvoie
                    print(reform_text(refs[i_ref]["text"].split("/")[i_repl].replace(";"," ")))
