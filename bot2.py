import discord
from discord.ext import commands
from discord import app_commands, Webhook

import random
import os
import time
import datetime
import asyncio

import aiohttp

import re
import sys
import traceback

from tex.processcsv import *
from tex.googleapif import *

from difflib import SequenceMatcher

import textounicode.convert

import references.references


PARAMS = {}

f = open("params/params", "r", encoding="utf-8")
for l in f.readlines():
    if l.replace("\n","") != "":
        li = l.replace("\n","").split("=")
        k = li[0]
        v = "=".join(li[1:])
        try:
            PARAMS[k] = int(v)
        except ValueError:
            try:
                PARAMS[k] = float(v)
            except ValueError:
                PARAMS[k] = v
f.close()


def simplify_role_name(r):
    return unidecode(r.split("/")[0].replace(" ", "").replace(".","").lower()).replace("*","")

CITOYENS_NAME = PARAMS["CITOYENS_NAME"]
NORMALIENS_NAME = PARAMS["NORMALIENS_NAME"]
TOURISTES_NAME = PARAMS["TOURISTES_NAME"]
POLICIERS_NAME = PARAMS["POLICIERS_NAME"]
COMMISSAIRE_NAME = PARAMS["COMMISSAIRE_NAME"]
PROCUREUR_NAME = PARAMS["PROCUREUR_NAME"]
CONSEILLER_CONST_NAME = PARAMS["CONSEILLER_CONST_NAME"]
CONSEILLER_PERM_NAME = PARAMS["CONSEILLER_PERM_NAME"]

ADMINISTRATOR_RIGHTS = ([PARAMS[n] for n in PARAMS["ADMINISTRATOR_RIGHTS"].split(",")] if PARAMS["ADMINISTRATOR_RIGHTS"] != "" else [])
VOTE_RIGHTS = ([PARAMS[n] for n in PARAMS["VOTE_RIGHTS"].split(",")] if PARAMS["VOTE_RIGHTS"] != "" else [])
DICO_RIGHTS = ([PARAMS[n] for n in PARAMS["DICO_RIGHTS"].split(",")] if PARAMS["DICO_RIGHTS"] != "" else [])
REFS_RIGHTS = ([PARAMS[n] for n in PARAMS["REFS_RIGHTS"].split(",")] if PARAMS["REFS_RIGHTS"] != "" else [])

ANCIENNETE = PARAMS["ANCIENNETE"]
NUMBER_OF_POLLS_ANCIEN = PARAMS["NUMBER_OF_POLLS_ANCIEN"]
LIMIT_NUMBER_OF_POLLS = PARAMS["LIMIT_NUMBER_OF_POLLS"]

AVENT_FREQUENCY = PARAMS["AVENT_FREQUENCY"]
AVENT_CHANNEL = PARAMS["AVENT_CHANNEL"]
AVENT_TITLE = PARAMS["AVENT_TITLE"]

VOTES_NAME = PARAMS["VOTES_NAME"]

COMMAND_PREFIX = PARAMS["COMMAND_PREFIX"]
BOT_NAME = PARAMS["BOT_NAME"]

ERROR_RIGHTS_MESSAGE = PARAMS["ERROR_RIGHTS_MESSAGE"]
ERROR_MESSAGE = PARAMS["ERROR_MESSAGE"]
ERROR_BOT_DISABLED_MESSAGE = PARAMS["ERROR_BOT_DISABLED_MESSAGE"]

VALIDATION_EMOJI = PARAMS["VALIDATION_EMOJI"]
ERROR_EMOJI = PARAMS["ERROR_EMOJI"]
DICO_EMOJI = PARAMS["DICO_EMOJI"]

PROPORTION_LOI = PARAMS["PROPORTION_LOI"]
PROPORTION_REVISION = PARAMS["PROPORTION_REVISION"]

DUREE_VOTES = PARAMS["DUREE_VOTES"]

PING_FIN_LOI = PARAMS["PING_FIN_LOI"]

REGEX_DI = PARAMS["REGEX_DI"]
REGEX_CRI = PARAMS["REGEX_CRI"]
FREQUENCY_DI = PARAMS["DI_FREQUENCY"]
FREQ_SELF_RESP = PARAMS["FREQ_SELF_RESP"]

COMPLIMENT_FREQ=PARAMS["COMPLIMENT_FREQUENCY"]
ID_HUGO=PARAMS["ID_HUGO"]
ID_LOUIS=PARAMS["ID_LOUIS"]

DISABLE_CATEGORIES = PARAMS["DISABLE_CATEGORIES"].split(",")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

intents.reactions = True
intents.guilds = True

ioloenabled = True
selfresponse = False

running_locally = False
is_local = False

bot_disabled = False
replacing_tags = True

if os.path.exists("params/local.txt"):
    f = open("params/local.txt","r")
    if f.read() == "1":
        is_local = True
        print("Running locally")
    f.close()


"""flog = open(".log","w", encoding="utf-8")
flog.write("")
flog.close()"""


lettre_frer = {}
lettre_erfr = {}
f = open("params/ernestchars", "r", encoding="utf-8")
for l in f.readlines():
    fr, er = l.replace("\n","").split(" ")
    lettre_frer[fr] = er
    lettre_erfr[er] = fr

f.close()

lettre_frer[" "] = " "
lettre_erfr[" "] = " "


def load_letter_size():
    global LETTER_SIZE_BOLD, LETTER_SIZE_REGULAR
    bold_f = "fonts/gg_bold_size.txt"
    semibold_f = "fonts/gg_semibold_size.txt"
    regular_f = "fonts/gg_regular_size.txt"
    f = open(bold_f, "r", encoding="utf-8")
    for l in f.readlines():
        s = l.split(" ")
        if len(s) == 3:
            LETTER_SIZE_BOLD[" "] = float(s[2])
        else:
            k, v = s
            LETTER_SIZE_BOLD[k] = float(v)
    f.close()
    f = open(semibold_f, "r", encoding="utf-8")
    for l in f.readlines():
        s = l.split(" ")
        if len(s) == 3:
            LETTER_SIZE_SEMIBOLD[" "] = float(s[2])
        else:
            k, v = s
            LETTER_SIZE_SEMIBOLD[k] = float(v)
    f.close()
    f = open(regular_f, "r", encoding="utf-8")
    for l in f.readlines():
        s = l.split(" ")
        if len(s) == 3:
            LETTER_SIZE_REGULAR[" "] = float(s[2])
        else:
            k, v = s
            LETTER_SIZE_REGULAR[k] = float(v)
    f.close()

LETTER_SIZE_BOLD = {}
LETTER_SIZE_SEMIBOLD = {}
LETTER_SIZE_REGULAR = {}

load_letter_size()

PB_EMOJIS = {}

class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        pass

    async def send_command_help(self, command):
        pass

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=CustomHelpCommand())

def log_save(m):
    with open(".log", "r", encoding="utf-8") as f:
        nb_lines = sum(1 for _ in f)
    
    if nb_lines < 600:
        with open(".log", "a", encoding="utf-8") as flog:
            flog.write(m+"\n")

    else:
        with open(".log","r", encoding="utf-8") as flog:
            lines = flog.readlines()[:500]
        with open(".log","w", encoding="utf-8") as flog:
            for l in lines:
                flog.write(l)
            flog.write(m+"\n")
    print(m)

def get_emoji(name: str) -> discord.PartialEmoji | None:
    l = {}
    for guild in bot.guilds:
        emoji = discord.utils.get(guild.emojis, name=name)
        l[guild.id] = emoji
    return l

def load_emojis():
    global PB_EMOJIS
    f = open("params/emojis.txt", "r", encoding="utf-8")
    l = f.read().split("\n")
    f.close()
    for v in l:
        if v.replace(" ", "") != "":
            emoji_g = get_emoji(v)
            for g in emoji_g:
                if emoji_g[g] is not None:
                    PB_EMOJIS[v] = "<:"+v+":"+str(emoji_g[g].id)+">"
                else:
                    pass

load_emojis()

def save_polls(polls, path="votes/polls.csv"):
    if polls:
        txt = []
        keys = list(polls[0].keys())
        keys.remove("citoyens")
        txt.append(";".join(keys))
        for poll in polls:
            l = []
            for k in keys:
                if k != "votes":
                    v = poll[k]
                    if type(v) in [int, float]:
                        gv = str(v)
                    elif type(v) == str:
                        gv = "\""+v.replace(";", "{\\pointvirgule}").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")+"\""
                    else:
                        raise Exception(f"Error while saving {path}, type {type(v)} not implemented.")
                    l.append(gv)
                else:
                    votes = []
                    for c in poll["citoyens"]:
                        if str(c) in poll["votes"]:
                            votes.append(str(c)+":"+poll["votes"][str(c)])
                        else:
                            votes.append(str(c))
                    l.append(",".join(votes))
            txt.append(";".join(l))
        f = open(path, "w", encoding="utf-8")
        f.write("\n".join(txt))
        f.close()
    else:
        f = open(path, "w", encoding="utf-8")
        f.write()
        f.close()

def load_polls(path="votes/polls.csv"):
    try:
        f = open(path, "r", encoding="utf-8")
        keys = []
        polls = []
        lines = f.read().split("\n")
        f.close()
        if lines:
            for i, l in enumerate(lines):
                if i == 0:
                    keys = l.split(";")
                else:
                    poll = {}
                    if l == "":continue
                    values = l.split(";")
                    if len(values) != len(keys):
                        raise Exception(f"Error while scanning {path} {values} {keys}")
                    for j in range(len(keys)):
                        if keys[j] == "votes":
                            votesl = values[j].split(",")
                            votes = {}
                            citoyens = []
                            for v in votesl:
                                if v != "":
                                    c = v.split(":")
                                    if len(c) == 2:
                                        votes[c[0]] = c[1]
                                    citoyens.append(int(c[0]))
                            poll["votes"] = votes
                            poll["citoyens"] = citoyens
                        else:
                            if values[j][0] == "\"" and values[j][-1] == "\"":
                                poll[keys[j]] = values[j][1:-1].replace("{\\pointvirgule}", ";").replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
                            else:
                                try:
                                    v = int(values[j])
                                except ValueError:
                                    try:
                                        v = float(values[j])
                                    except ValueError:
                                        raise Exception(f"Unrecognized type for \"{values[j]}\"")
                                poll[keys[j]] = v
                    polls.append(poll)
        return polls
    except FileNotFoundError:
        return []

async def recover_polls():
    polls = load_polls()
    for poll in polls:
        if poll["closed"] != 1:
            channel = bot.get_channel(poll["channel_id"])
            if not channel:
                continue
            try:
                message = await channel.fetch_message(poll["message_id"])
                view = PollView(question=poll["question"], guild_id=poll["guild_id"], \
                                channel_id=poll["channel_id"], \
                                author_id=poll["author_id"], \
                                message_id=poll["message_id"], \
                                proportion=poll["proportion"], \
                                existing_votes=poll["votes"], \
                                timestamp=poll["timestamp"], \
                                duration=poll["duration"], \
                                vote_type=poll["type"], \
                                citoyens=poll["citoyens"], \
                                poll_id=poll["poll_id"])
                view.message = message
                asyncio.create_task(view.wait_end())
                embed = view.get_embed()
                await message.edit(embed=embed, view=view)
            except Exception as e:
                log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] ERROR: impossible de reprendre le vote #{poll['poll_id']} \"{poll['question']}\" suite à l'erreur : {e}")
        else:
            channel = bot.get_channel(poll["channel_id"])
            if not channel:
                continue

            message = await channel.fetch_message(poll["message_id"])
            view = get_closed_view(poll)
            await message.edit(view=view)

def get_closed_view(poll):
    view = discord.ui.View(timeout=None)
    view.question = poll["question"]
    view.proportion = poll["proportion"]
    view.guild_id = poll["guild_id"]
    view.channel_id = poll["channel_id"]
    view.author_id = poll["author_id"]
    view.message_id = poll["message_id"]
    view.PB_EMOJIS = PB_EMOJIS

    view.citoyens = poll["citoyens"]

    view.poll_id = poll["poll_id"]

    view.timestamp = poll["timestamp"]
    view.duration = poll["duration"]
    view.vote_type = poll["type"]

    view.termine = poll["closed"]

    button = PollButton(label=" ", emoji="ℹ️", view=view, vote_key="i")
    button.citoyens = poll["citoyens"]
    button.proportion = poll["proportion"]

    view.oui, view.non, view.blancs = 0,0,0
    for v in poll["votes"].values():
        if v == "o":
            view.oui += 1
        elif v == "n":
            view.non += 1
        elif v == "b":
            view.blancs += 1

    view.votes = {"o": [], "n": [], "b": []}
    for k in poll["votes"]:
        view.votes[poll["votes"][k]].append(int(k))

    view.add_item(button)
    return view

@bot.event
async def on_ready():
    #await bot.tree.sync()
    """for guild in bot.guilds:
        await guild.me.edit(nick=BOT_NAME)"""
    try:
        log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] RUNNING")
        await update_specrights()
        log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] OK: {bot.user} connecté à {';'.join([str(guild.id)+'#'+guild.name for guild in bot.guilds])}")
        load_emojis()
        log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] OK: Emojis chargés")
        await recover_polls()
        log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] OK: Votes actualisés")
        await donner_signe_de_vie()
    except Exception as e:
        print_message_error(None,e)


async def donner_signe_de_vie():
    if not os.path.exists("upgrade.temp"):
        fw = open("upgrade.temp", "w", encoding="utf-8")
        fw.write("")
        fw.close()
    
    f = open("upgrade.temp","r",encoding="utf-8")
    t = f.read()
    f.close()

    if t.replace(" ", "") != "":
        try:
            channel = bot.get_channel(int(t.replace(" ", "")))
            if channel is None:
                raise ValueError()
            fw = open("upgrade.temp", "w", encoding="utf-8")
            fw.write("")
            fw.close()
            await channel.send(":white_check_mark: Le bot a bien redémarré !")
        except ValueError:
            log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] ERROR: value error in donner_signe_de_vie find channel {t.replace(' ', '')}")


# modification contextuelle par ernestomoch

def remove_code_blocks(text):
    text = re.sub(r"```.*?```", lambda m: " " * len(m.group()), text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", lambda m: " " * len(m.group()), text)
    return text

def replace_tags(text):
    tags = ["\\", "€", "£", "$"]
    tagscodes = ["\\backslashsymbol", "\\eurosymbol", "\\poundsymbol", "\\dollarsymbol"]
    for i, tag in enumerate(tags):
        text = text.replace("\\"+tag, tagscodes[i])
    transformations = {"€": ernconvert, "£": lambda x: ernconvert(x)+" ("+x+")", r"\$": textounicode.convert.convert}
    cleaned = remove_code_blocks(text)

    for transfo in transformations:
        matches = list(re.finditer(transfo+r"(.*?)"+transfo, cleaned))

        new_text = []
        last_index = 0
        for match in matches:
            start, end = match.span()
            content = match.group(1)
            replacement = transformations[transfo](content)

            # Ajouter le texte avant la balise
            new_text.append(text[last_index:start])
            # Ajouter le remplacement
            new_text.append(replacement)
            last_index = end

        new_text.append(text[last_index:])
        text = ''.join(new_text)
    return text

async def send_custom_message(channel, name, user, avatar_url, content, delete_old=None):
    async with aiohttp.ClientSession() as session:
        webhook = await channel.create_webhook(name="TempWebhook")
        if delete_old is not None:
            await delete_old.delete()

        msg = await webhook.send(
            content,
            username=name,
            avatar_url=avatar_url,
            wait=True
        )
        msg_id = msg.id
        await webhook.delete()

        def check(x, xuser):
            return x.message.channel.id == channel.id and xuser.id == user.id
        reaction = await bot.wait_for("reaction_add", check=check, timeout=None)  # Wait for a reaction
        if reaction[0].emoji == "❌":
            msg2 = await channel.fetch_message(msg_id)
            await msg2.delete()

@bot.event
async def on_message(msg):
    try:
        msgtext = msg.content
        msgchannel = msg.channel
        msgauthor = msg.author
        if bot_disabled:return
        if not (is_local or not running_locally): return
        if hasattr(msgchannel,"category") and msgchannel.category.name in DISABLE_CATEGORIES: return
        if "** ** ** **" in msg.content: return
        if ioloenabled and (random.randint(0,99) < FREQUENCY_DI or msgauthor.bot):
            global selfresponse
            if msgauthor.bot:
                if selfresponse and random.randint(0, 100) > FREQ_SELF_RESP:
                    await msgchannel.send("Bon j'en ai marre....")
                    selfresponse = False
                    return
                selfresponse = True
            else:
                selfresponse = False

            if str(ID_HUGO) in msgtext:
                await msgchannel.send("hellgo")
            
            matchs_di = re.search(REGEX_DI, msgtext)
            matchs_cri = re.search(REGEX_CRI, msgtext)
            
            if matchs_di and ((not matchs_cri) or matchs_di.start() < matchs_cri.start()):
                if matchs_di.start() == 0:
                    text = re.split(REGEX_DI, msgtext, 1)[-1].strip()

                else:
                    text = re.split(REGEX_DI, msgtext, 1)[-1].strip().split(" ")[0]

                if text:
                    await msgchannel.send(text, allowed_mentions=discord.AllowedMentions(users=False, everyone=False, roles=False, replied_user=False))
            
            elif matchs_cri:
                if matchs_cri.start() == 0:
                    text = re.split(REGEX_CRI, msgtext, 1)[-1].strip().upper() + " !!!"
                
                else:
                    text = re.split(REGEX_CRI, msgtext, 1)[-1].strip().split(" ")[0].upper() + " !!!"
                    await msgchannel.send(text, allowed_mentions=discord.AllowedMentions(users=False, everyone=False, roles=False, replied_user=False))


        if msg.author.bot:return
        if replacing_tags:
            balises = ["€","£",r"\$"]
            tomodify = False
            textcb = remove_code_blocks(msgtext)
            for balise in balises:
                if re.search(balise+r".*?"+balise,textcb) is not None:
                    tomodify = True
                    break
            if tomodify:
                await send_custom_message(
                    msg.channel,
                    name=msgauthor.display_name+" ft. "+BOT_NAME,
                    user=msgauthor,
                    avatar_url=msgauthor.display_avatar.url,
                    content=replace_tags(msgtext),
                    delete_old=msg
                )
        if ioloenabled:
            if random.randint(1,200)==42:
                await msgchannel.send("J'ai perdu...")
            if re.search(PARAMS["REGEX_QUOI"], msgtext):
                await msgchannel.send("Feur !")

            if re.search(r"(.*)(^|\s|\_|\*)(([i][oo0][l][oô])|([i][ooô̥]))($|\s|\_|\*)(.*)",msgtext.lower()):
                await msgchannel.send("iolô !")
            elif re.search(r"(.*)(^|\s|\_|\*)(([ııi][oo0o]([lʟʟʟ]|ʟ̥)([oô]|ô))|([ıiı]([oo0ô]|ô)))($|\s|\_|\*)(.*)",msgtext.lower()):
                await msgchannel.send("ıoʟ̥ô !")
            if re.search(r"(.*)(^|\s|'|:|,|\(|\_|\*)(ernesto*m[oô]*ch|\<@1435667613865742406\>|cꞁ̊ᒉcc̥⟊oᒐ(ô|ô|o)*ʃ)($|\s|,|:|\)|\_|\*)(.*)", msgtext.lower()):
                await msgchannel.send("C'est moi !")
            
            await references.references.process_message(msgtext,msgchannel)
        

        if (msgauthor.id == ID_HUGO or msg.author.id == ID_LOUIS) and random.randint(0,99) < COMPLIMENT_FREQ:
            with open("compliments.txt", "r") as file:
                list_compliments = file.readlines()
                text=f"<@{msgauthor.id}> {random.choice(list_compliments)}"
                await msgchannel.send(text)

        #await bot.process_commands(msg)
    except Exception as e:
        print_message_error(msg,e)

def get_last_user_traceback_line(tb):
    for frame in reversed(tb):
        if os.getcwd() in frame.filename:  # filtre les fichiers dans ton projet
            return frame
    return tb[-1]  # fallback : dernière ligne du traceback

@bot.event
async def on_command_error(ctx, error):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)
    if tb:
        last_frame = get_last_user_traceback_line(tb)
        filename = last_frame.filename
        lineno = last_frame.lineno
    else:
        filename = "?"
        lineno = "?"
    log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {ctx.guild.id if ctx.guild else 'DM'} ERREUR: {error} dans {filename} ligne {lineno} | Auteur: {ctx.author} | Serveur: {ctx.guild.name if ctx.guild else 'DM'} | Canal: {ctx.channel.name if ctx.guild else 'DM'} | Commande: {ctx.command}")

def print_command_error(interaction, error):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)
    last_frame = get_last_user_traceback_line(tb)
    log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {interaction.guild.id if interaction.guild else 'DM'} ERREUR: {error} dans {last_frame.filename} ligne {last_frame.lineno} | Auteur: {interaction.user} | Serveur: {interaction.guild.name if interaction.guild else 'DM'} | Canal: {interaction.channel.name if interaction.guild else 'DM'} | Commande: {interaction.command.name if interaction.command else '?'}")


reactions_to_wait = {}

def add_reaction(msg_id, emoji, function, user_id=None):
    global reactions_to_wait
    r = {"function": function, "emoji": emoji}
    if user_id is not None:
        r["user_id"] = user_id
    if msg_id in reactions_to_wait:
        reactions_to_wait[msg_id].append(r)
    else:
        reactions_to_wait[msg_id] = [r]
    

def remove_reaction(msg_id, emoji=None):
    global reactions_to_wait
    if msg_id not in reactions_to_wait: return
    if emoji is None:
        del reactions_to_wait[msg_id]
    else:
        l2 = []
        for e in reactions_to_wait[msg_id]:
            if e["emoji"] != emoji:
                l2.append(e)
        if l2:
            reactions_to_wait[msg_id] = l2
        else:
            del reactions_to_wait[msg_id]


@bot.event
async def on_raw_reaction_add(payload):
    try:
        msg_id = payload.message_id
        if msg_id in reactions_to_wait:
            reaction_waited = reactions_to_wait[msg_id]
            for e in reaction_waited:
                if e["emoji"] != payload.emoji.name:
                    continue
                if "user_id" in e:
                    if e["user_id"] != payload.user_id:
                        continue
                await e["function"]()
    except Exception as e:
        print_message_error(None,e)

def replace_lbreaks(t):
    return t.replace('\n','\\n')

def print_message_error(msg, error):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)
    last_frame = get_last_user_traceback_line(tb)
    log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {msg.guild.id if hasattr(msg, "guild") else 'DM'} ERREUR: {error} dans {last_frame.filename} ligne {last_frame.lineno} | Auteur: {msg.author if hasattr(msg, "author") else "?"} | Serveur: {msg.guild.name if hasattr(msg, "guild") else 'DM'} | Canal: {msg.channel.name if hasattr(msg, "channel") else 'DM'} | Message: '{replace_lbreaks(msg.content) if hasattr(msg, "content") else "?"}'")


async def custom_response(inter,msg,duration=3):
    try:
        await inter.response.defer(ephemeral=True)
    except (discord.HTTPException,discord.InteractionResponded):
        pass
    message = await inter.followup.send(msg, ephemeral=True)
    await asyncio.sleep(duration)
    await message.delete()

async def validation_response(inter,msg,duration=3):
    try:
        await inter.response.defer(ephemeral=True)
    except (discord.HTTPException,discord.InteractionResponded) as e:
        print_message_error(msg,e)
    message = await inter.followup.send(VALIDATION_EMOJI+" "+msg, ephemeral=True)
    await asyncio.sleep(duration)
    await message.delete()

async def error_response(inter,msg, duration=3):
    try:
        await inter.response.defer(ephemeral=True)
    except (discord.HTTPException,discord.InteractionResponded) as e:
        print_message_error(msg,e)
    message = await inter.followup.send(ERROR_EMOJI+" "+msg, ephemeral=True)
    await asyncio.sleep(duration)
    await message.delete()


async def generate_pdf():
    process = await asyncio.create_subprocess_exec(
        "xelatex", "-synctex=1", "-interaction=nonstopmode", "-output-directory=tex", "tex/main.tex",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    

async def update_specrights():
    specrights = []
    if bot_disabled:
        specrights.append("off")
    if ioloenabled:
        specrights.append("iolô")
    if running_locally:
        specrights.append("local")
    await bot.change_presence(
        activity=discord.Game(name=", ".join(specrights)),
        status=discord.Status.online
    )


@bot.tree.command(name="bot", description="[A] Active/désactive le bot")
@app_commands.choices(state=[app_commands.Choice(name="on", value="on"),
                             app_commands.Choice(name="off", value="off"),
                             app_commands.Choice(name="switch", value="switch")])
@app_commands.describe(state="État du bot : on (activé), off (désactivé), switch (basculer on/off)")
async def botstate(inter,state : str = "switch"):
    try:
        global bot_disabled
        for right in ADMINISTRATOR_RIGHTS:
            if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                if state == "switch":
                    bot_disabled = not bot_disabled
                elif state == "on":
                    bot_disabled = False
                elif state == "off":
                    bot_disabled = True
                else:
                    await error_response(inter,ERROR_EMOJI+f" Paramètre state={state} non valide")
                await update_specrights()
                await validation_response(inter,f"Le bot est bien {'désactivé' if bot_disabled else 'activé'}")
                break
        else:
            await error_response(inter,ERROR_RIGHTS_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)
    


@bot.tree.command(name="local", description="[A] Passe en mode local (maintenance)")
@app_commands.choices(state=[app_commands.Choice(name="on", value="on"),
                             app_commands.Choice(name="off", value="off"),
                             app_commands.Choice(name="switch", value="switch")])
@app_commands.describe(state="État du bot : on (local), off (tous serveurs), switch (basculer on/off)")
async def localstate(inter,state : str = "switch"):
    try:
        if not bot_disabled:
            global running_locally
            for right in ADMINISTRATOR_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    if state == "switch":
                        running_locally = not running_locally
                    elif state == "on":
                        running_locally = True
                    elif state == "off":
                        running_locally = False
                    else:
                        await error_response(inter,ERROR_EMOJI+f" Paramètre state={state} non valide")
                    await update_specrights()
                    await validation_response(inter,f"Paramètre d'état local fixé à state={'on' if running_locally else 'off'}")
                    break
            else:
                await error_response(inter,ERROR_RIGHTS_MESSAGE)
        else:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


@bot.tree.command(description="[A] Affiche le fichier des logs")
@app_commands.describe(limit="Limite du nombre de lignes dans le fichier log, infinie par défaut.")
async def logs(inter, limit : int = 0):
    try:
        if (is_local or not running_locally) and not bot_disabled:
            for right in ADMINISTRATOR_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    try:
                        await inter.response.defer(ephemeral=True)
                    except discord.HTTPException:
                        pass
                    flog = open(".log","r",encoding="utf-8")
                    i = 0
                    lines = flog.readlines()
                    flog.close()
                    fw = open("limit.log","w")
                    fw.write("".join(lines[-limit::][::-1]))
                    fw.close()
                    file = discord.File("limit.log", filename=f".log")
                    await inter.followup.send("", file=file,ephemeral=True)
                    break
            else:
                await error_response(inter,ERROR_RIGHTS_MESSAGE)
        elif bot_disabled:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


@bot.tree.command(name="dicopdf", description="[D] Édite le dictionnaire")
async def dictionnaire(inter):
    try:
        if (is_local or not running_locally) and not bot_disabled:
            for right in DICO_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    os.environ["TEXINPUTS"] = ":./tex//:"
                    await inter.response.send_message(":arrows_counterclockwise: Edition du dictionnaire...", ephemeral=True)
                    await inter.edit_original_response(content=":arrow_down: Downloading file")
                    await download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","tex/ernestien.csv")
                    await inter.edit_original_response(content=":robot: Conversion python")
                    await processcsv()
                    await inter.edit_original_response(content=":pencil: Première compilation XeLaTex")
                    await generate_pdf()
                    await inter.edit_original_response(content=":pencil: Deuxième compilation XeLaTex")
                    await generate_pdf()
                    now = datetime.datetime.now()
                    file = discord.File("tex/main.pdf", filename=f"dico-{now.year}-{now.month}-{now.day}.pdf")
                    await inter.delete_original_response()
                    await inter.followup.send(f"Dictionnaire édité par {inter.user.mention} :", file=file, allowed_mentions=discord.AllowedMentions(users=False))
                    break
            else:
                await error_response(inter,ERROR_RIGHTS_MESSAGE)
        elif bot_disabled:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)

# DICO

def interprete_balises(text):
    text = re.sub(r"\_\_(.*?)\_\_", r"_\1_", text)
    text = re.sub(r"\#(.*?)\#", lambda x : rf"{textounicode.convert.convert(x.group(1))}", text)
    text = re.sub(r"£(.*?)£", lambda m: ernconvert(m.group(1))+" ("+m.group(1)+")", text)
    text = re.sub(r"€(.*?)€", lambda m: ernconvert(m.group(1)), text)

    return text


class DicoPaginator(discord.ui.View):
    def __init__(self, resultats, *, timeout=60, mot="", statut=True, user=""):
        super().__init__(timeout=timeout)
        self.resultats = resultats.reset_index(drop=True)
        self.index = 0
        self.mot = mot
        self.COLS = ["Francais", "Ernestien", "Etymologie"]

        self.closed = False
        self.statut = statut
        self.user = user

    def format_embed(self):
        ligne = self.resultats.iloc[self.index]
        embed = discord.Embed(
            title=f"\"{self.mot}\" — Résultat {self.index + 1} / {len(self.resultats)}",# ({ligne['pertinence']})",
            description=("" if self.statut else "Recherche de "+self.user),
            color=discord.Color.blue()
        )
        for col in self.COLS:
            val = ligne[col]
            if pd.notna(val) and str(val).strip() and str(val).lower() != "nan":  # Ignore NaN ou vide
                if col == "Ernestien":
                    tval = ernconvert(val) + " ("+val+")"
                else:
                    tval = interprete_balises(val)
                embed.add_field(name=col, value=tval, inline=False)
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = self.format_embed()
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            self.closed = True

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.closed:
            self.index = (self.index - 1) % len(self.resultats)
            await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.closed:
            self.index = (self.index + 1) % len(self.resultats)
            await self.update_message(interaction)


def distance_approx(a, b):
    return int((1 - SequenceMatcher(None, a, b).ratio()) * max(len(a), len(b)))

def nettoyer_texte(texte):
    if pd.isna(texte):
        return ""
    return unidecode(str(texte)).encode("ASCII", "ignore").decode().lower()


def ernconvert(mot):
    mapping = lettre_frer
    return ''.join(mapping[c.lower()] for c in mot if c.lower() in mapping)

def frconvert(mot):
    mapping = lettre_erfr
    return ''.join(mapping[c] for c in mot if c in mapping)

def frconvert_keep(mot):
    mapping = lettre_erfr
    return ''.join(mapping[c] if c in mapping else c for c in mot)

def score_ligne(ligne,mot):
    mot_clean = nettoyer_texte(mot)
    pattern = rf"\b{re.escape(mot_clean)}\b"
    
    score = 0
    for col, val in zip(ligne.index, ligne):
        if not isinstance(val, str):
            continue

        # Pondération par colonne
        if col in ["Francais", "Ernestien"]:
            exact, regex, witherrors, partial = 100, 50, 5, 10
        else:  # Etymologie ou autre
            exact, regex, witherrors, partial = 30, 15, 2, 1

        # Matching
        if val == mot_clean:
            score += exact
        elif re.search(pattern, val):
            score += regex                
        elif mot_clean in val:
            score += partial
        else:
            # Fuzzy match: distance ≤ 2
            if col in ["Francais", "Ernestien"]:
                for word in frconvert_keep(nettoyer_texte(val)).split():
                    d1 = distance_approx(word, mot_clean)
                    if d1 <= 2:
                        score += witherrors/5 * (3 - d1)
    return score

def cherche_dico(mot, sens="*"):
    df = pd.read_csv("tex/ernestien.csv", encoding="utf-8")
    mot_clean = nettoyer_texte(mot)
    mot_clean_ern = frconvert_keep(mot_clean)
    pattern = rf"\b{re.escape(mot_clean)}\b|\b{re.escape(mot_clean_ern)}\b"

    COLS = ["Francais", "Ernestien", "Etymologie"]

    if sens == "fe":
        colonnes = ["Francais"]
    elif sens == "ef":
        colonnes = ["Ernestien"]
    else:
        colonnes = df.columns.tolist()

    df_clean = df[colonnes].copy()
    for col in colonnes:
        df_clean[col] = df_clean[col].map(nettoyer_texte)

    scores = df_clean.apply(lambda x : score_ligne(x,mot), axis=1)
    df_resultats = df[scores >= 1][COLS].copy()
    df_resultats["pertinence"] = scores[scores >= 1]
    df_resultats = df_resultats.sort_values(by="pertinence", ascending=False)

    def surligner_ernestien(val):
        val_clean = nettoyer_texte(val)
        return re.sub(pattern, lambda m: f"**{val[m.start():m.end()]}**", val, flags=re.IGNORECASE)

    for col in COLS:
        df_resultats[col] = df_resultats[col].apply(lambda val: surligner_ernestien(str(val)))

    return df_resultats


@bot.tree.command(name="dico", description="Recherche dans le dictionnaire")
@app_commands.describe(mot="Mot recherché")
@app_commands.choices(sens=[app_commands.Choice(name="fe", value="fe"),
                             app_commands.Choice(name="ef", value="ef"),
                             app_commands.Choice(name="*", value="*")])
@app_commands.describe(sens="Sens de traduction : fe (fr -> er), ef (er -> fr), * (par défaut : les deux)")
@app_commands.choices(statut=[app_commands.Choice(name="Privé", value=1),
                             app_commands.Choice(name="Publique", value=0)])
@app_commands.describe(statut="Statut de la réponse (Privée (défaut)/Publique) les réponses privées sont temporaires.")
@app_commands.describe(update="[D] Actualiser le dictionnaire ? (Oui/Non)")
@app_commands.choices(update=[app_commands.Choice(name="Oui", value=1),
                             app_commands.Choice(name="Non", value=0)])
async def dico(inter, mot : str, sens : str = "*", statut : int = 1, update : int = 0):
    try:
        if not bot_disabled:
            if sens in ["fe","ef","*"]:
                await inter.response.send_message(":arrows_counterclockwise: Recherche...",ephemeral=True)
                if update == 1:
                    for right in DICO_RIGHTS:
                        if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                            await download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","tex/ernestien.csv")
                            break
                    else:
                        await error_response(inter,ERROR_RIGHTS_MESSAGE+" (actualiser le dictionnaire). La recherche s'effectuera sur la dernière version actualisée.", duration=8)
                result = cherche_dico(mot,sens)
                await inter.delete_original_response()
                if result.empty:
                    await inter.followup.send(content=":grey_question: Aucun résultat...", ephemeral=True)
                else:
                    view = DicoPaginator(result, mot=mot, statut=bool(statut), user=inter.user.mention)
                    embed = view.format_embed()
                    await inter.followup.send(embed=embed,view=view,ephemeral=bool(statut), allowed_mentions=discord.AllowedMentions(users=False))
            else:
                await error_response(inter,ERROR_EMOJI+f" Paramètre {sens} non valide.")
        else:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


@bot.tree.command(description="[D] Actualise le dictionnaire")
async def dicoupdate(inter):
    try:
        if not bot_disabled:
            for right in DICO_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    await inter.response.send_message(":arrow_down: Téléchargement du dictionnaire...", ephemeral=True)
                    await download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","tex/ernestien.csv")
                    await inter.delete_original_response()
                    await inter.followup.send(content=DICO_EMOJI+f" {inter.user.mention} a actualisé le dictionnaire", allowed_mentions=discord.AllowedMentions(users=False))
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)    


class FormulaireModal(discord.ui.Modal):
    def __init__(self, mode, francais="", ernestien="", etymologie="", warning="", linenumber=None):
        if warning != "":
            super().__init__(title=(warning[:42]+"..." if len(warning) > 45 else warning))
        else:
            super().__init__(title=(f"Édition de \"{francais}\"" if mode == "edit" else "Ajouter un mot au dictionnaire"))
        self.mode = mode
        self.linenumber = linenumber
        self.francais_val = francais
        self.francais = discord.ui.TextInput(
            label="Français",
            placeholder="ex: poisson",
            default=francais[:200],
            required=True,
            max_length=200
        )

        self.ernestien = discord.ui.TextInput(
            label="Ernestien",
            placeholder="ex: ernêst",
            default=ernestien[:200],
            required=False,
            max_length=200
        )

        self.etymologie = discord.ui.TextInput(
            label="Étymologie (facultatif)",
            style=discord.TextStyle.paragraph,
            default=etymologie[:600],
            required=False,
            max_length=600
        )
        
        self.add_item(self.francais)
        self.add_item(self.ernestien)
        self.add_item(self.etymologie)


    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message("En cours...", ephemeral=True)
            mot_francais = self.francais.value
            mot_ernestien = self.ernestien.value
            mot_etymologie = self.etymologie.value

            try:
                if self.mode == "add":
                    if mot_ernestien != "":
                        await ajouter_ligne_sheet(
                            spreadsheet_id="1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q",
                            range_target="Dico",
                            nouvelle_ligne=[mot_francais, mot_ernestien, mot_etymologie]
                        )

                        df = pd.read_csv("tex/ernestien.csv")

                        nouvelleligne = {
                            "Francais": mot_francais,
                            "Ernestien": mot_ernestien,
                            "Etymologie": mot_etymologie
                        }
                        df = pd.concat([df, pd.DataFrame([nouvelleligne])], ignore_index=True)
                        df.to_csv("tex/ernestien.csv", index=False)

                        await interaction.delete_original_response()
                        await interaction.followup.send(
                            content=DICO_EMOJI+f" {interaction.user.mention} a ajouté\n```{mot_francais} → {ernconvert(mot_ernestien)} ({mot_ernestien})"+('\n' + mot_etymologie if mot_etymologie != '' else '')+"```",
                            allowed_mentions=discord.AllowedMentions(users=False)
                        )
                    else:
                        message = await interaction.edit_original_response(
                            content=f":warning: Vous devez obligatoirement entrer une nouvelle traduction"
                        )
                        await asyncio.sleep(5)
                        await message.delete()

                elif self.mode == "edit":
                    if mot_ernestien != "":
                        await modifier_ligne_sheet(
                            spreadsheet_id="1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q",
                            ligne=self.linenumber,
                            range_target="Dico",
                            nouvelle_ligne=[mot_francais, mot_ernestien, mot_etymologie]
                        )

                        df = pd.read_csv("tex/ernestien.csv")

                        df.at[self.linenumber, "Francais"] = mot_francais
                        df.at[self.linenumber, "Ernestien"] = mot_ernestien
                        df.at[self.linenumber, "Etymologie"] = mot_etymologie
                        df.to_csv("tex/ernestien.csv", index=False)

                        await interaction.delete_original_response()
                        await interaction.followup.send(
                            content=DICO_EMOJI+f" {interaction.user.mention} a modifié{' : '+self.francais_val+' en '+mot_francais if self.francais_val != mot_francais else ''}\n```{mot_francais} → {ernconvert(mot_ernestien)} ({mot_ernestien})"+('\n' + mot_etymologie if mot_etymologie != '' else '')+"```",
                            allowed_mentions=discord.AllowedMentions(users=False)
                        )
                    else:
                        if self.francais_val == mot_francais:
                            await supprimer_ligne_sheet(
                                spreadsheet_id="1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q",
                                ligne=self.linenumber,
                                range_target="Dico"
                            )
                            
                            df = pd.read_csv("tex/ernestien.csv")
                            df = df.drop(index=self.linenumber).reset_index(drop=True)
                            df.to_csv("tex/ernestien.csv", index=False)

                            await interaction.delete_original_response()
                            await interaction.followup.send(
                                content=DICO_EMOJI+f" {interaction.user.mention} a supprimé le mot \"{self.francais_val}\"",
                                allowed_mentions=discord.AllowedMentions(users=False)
                            )
                        else:
                            message = await interaction.edit_original_response(
                                content=f":warning: Vous ne pouvez supprimer un autre mot (\"{mot_francais}\") que celui entré dans la commande `/dicochange` (\"{self.francais_val}\")."
                            )
                            await asyncio.sleep(5)
                            await message.delete()

            except FileNotFoundError:
                message = await interaction.edit_original_response(
                    content=ERROR_EMOJI+f" Une erreur s'est produite. Essayez d'actualiser le dictionnaire en amont avec la commande `/dicoupdate`."
                )
                await asyncio.sleep(5)
                await message.delete()
        except Exception as e:
            print_command_error(interaction,e)
            await error_response(interaction,ERROR_MESSAGE)    


@bot.tree.command(description="[D] Modifie le dictionnaire")
@app_commands.choices(action=[app_commands.Choice(name="add", value="add"),
                             app_commands.Choice(name="edit", value="edit"),
                             app_commands.Choice(name="auto", value="auto")])
@app_commands.describe(action="Action effectuée : add (ajout d'un mot en français), edit (édition d'un mot), auto (automatique)")
@app_commands.describe(mot="Mot à ajouter")
@app_commands.choices(langue=[app_commands.Choice(name="fr", value="fe"),
                             app_commands.Choice(name="er", value="ef")])
@app_commands.describe(langue="Langue du mot ajouté : fr (français, par défaut), er (ernestien)")
async def dicochange(inter, mot : str, action : str = "auto", langue : str = "fe"):
    try:
        if not bot_disabled:
            for right in DICO_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    t = time.time()
                    actiont = ""
                    df = pd.read_csv("tex/ernestien.csv", encoding="utf-8")
                    corresp = {"fe": "Francais", "ef": "Ernestien"}
                    warning = ""
                    for linedico, motdico in enumerate(df[corresp[langue]]):
                        if mot.lower() == motdico.lower():
                            if action == "edit" or action == "auto":
                                actiont = "edit"
                            elif action == "add":
                                await error_response(inter, f"Le mot \"{mot}\" à ajouter existe déjà dans le dictionnaire. Ne voulez-vous pas plutôt le modifier ?", duration=6)
                            break
                    else:
                        if action == "add":
                            actiont = "add"
                        else:
                            recherche = cherche_dico(mot, langue)
                            if list(recherche.iloc) and recherche.iloc[0]["pertinence"] >= 10:
                                if action == "auto":
                                    actiont = "add"
                                    warning = f"⚠️ \"{recherche.iloc[0][corresp[langue]]}\" déjà dans le dico !"
                                elif action == "edit":
                                    await error_response(inter, f"Le mot à éditer n'existe pas. Ne vouliez-vous pas plutôt modifier \"{recherche.iloc[0][corresp[langue]]}\" ?", duration=6)
                            else:
                                if action == "edit":
                                    await error_response(inter, "Le mot à éditer n'existe pas.")
                                elif action == "auto":
                                    actiont = "add"
                    
                    if actiont == "":
                        pass#await error_response(inter, "Une erreur est survenue. Nous vous prions de nous en excuser.")
                    elif actiont == "add":
                        await inter.response.send_modal(FormulaireModal(francais=str(mot), warning=warning, mode="add"))
                    elif actiont == "edit":
                        await inter.response.send_modal(FormulaireModal(francais=str(mot), ernestien=str(df["Ernestien"][linedico]), etymologie=(str(df["Etymologie"][linedico]) if str(df["Etymologie"][linedico]) != "nan" else ""), mode="edit", linenumber=linedico))
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
        else:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


@bot.tree.command(name="iolo", description="[A] Active/désactive la réponse automatique aux \"iô\" ou \"iolô\"")
@app_commands.choices(state=[app_commands.Choice(name="on", value="on"),
                             app_commands.Choice(name="off", value="off"),
                             app_commands.Choice(name="switch", value="switch")])
@app_commands.describe(state="Réactions du bot : on (répond), off (muet), switch (basculer on/off)")
async def iolostate(inter, state : str = "switch"):
    try:
        if not bot_disabled:
            global ioloenabled
            for right in ADMINISTRATOR_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    if state == "switch":
                        ioloenabled = not ioloenabled
                    elif state == "on":
                        ioloenabled = True
                    elif state == "off":
                        ioloenabled = False
                    else:
                        await error_response(inter,ERROR_EMOJI+f" Paramètre state={state} non valide")
                    await update_specrights()
                    await validation_response(inter,f"Iolô {'activé' if ioloenabled else 'désactivé'}")
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
        else:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)

@bot.tree.command(description="Affiche les statistiques du serveur")
async def statistiques(inter):
    try:
        if (is_local or not running_locally) and not bot_disabled:
            response = inter.response
            citoyens = []
            normaliens = []
            touristes = []
            for m in inter.guild.members:
                roles = [simplify_role_name(r.name) for r in m.roles]
                if simplify_role_name(CITOYENS_NAME) in roles:
                    citoyens.append(m.display_name)
                elif simplify_role_name(NORMALIENS_NAME) in roles:
                    normaliens.append(m.display_name)
                elif simplify_role_name(TOURISTES_NAME) in roles:
                    touristes.append(m.display_name)

            embed = discord.Embed(
                title=":bar_chart: Statistiques",
                description="",
                color=discord.Color.blue()
            )
            if citoyens:
                embed.add_field(name="Citoyens ("+str(len(citoyens))+")", value="- "+"\n- ".join(citoyens), inline=False)
            if normaliens:
                embed.add_field(name="Normaliens touristes ("+str(len(normaliens))+")", value="- "+"\n- ".join(normaliens), inline=False)
            if touristes:
                embed.add_field(name="Touristes ("+str(len(touristes))+")", value="- "+"\n- ".join(touristes), inline=False)

            embed.timestamp = inter.created_at

            await response.send_message(embed=embed)
        elif bot_disabled:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


@bot.tree.command(description="Affiche la liste des citoyens et anciens citoyens")
async def citoyens(inter):
    try:
        if not (is_local or not running_locally): return
        if not bot_disabled:
            await inter.response.defer()

            citoyens = []
            anciens_citoyens = []

            canalvotes = discord.utils.get(inter.guild.text_channels, name=VOTES_NAME)

            voters = {}
            icompteur = 0

            guild_id = inter.guild.id
            polls = load_polls()
            for poll in polls:
                if poll["channel_id"] == guild_id:
                    if icompteur >= LIMIT_NUMBER_OF_POLLS:
                        break
                    for k in poll["votes"]:
                        if int(k) not in voters:
                            voters[int(k)] = 1
                        else:
                            voters[int(k)] += 1
                    icompteur += 1
            
            async for msg in canalvotes.history():
                if msg.poll is not None:
                    if icompteur >= LIMIT_NUMBER_OF_POLLS:
                        break
                    for answer in msg.poll.answers:
                        async for voter in answer.voters():
                            if voter.id not in voters:
                                voters[voter.id] = 1
                            else:
                                voters[voter.id] += 1
                    icompteur += 1
            
            for m in inter.guild.members:
                joined = m.joined_at.timestamp()
                now = datetime.datetime.now().timestamp()
                difference = now-joined

                if m.id in voters:
                    pollsanswered = voters[m.id]
                else:
                    pollsanswered = 0

                roles = [simplify_role_name(r.name) for r in m.roles]
                if simplify_role_name(CITOYENS_NAME) in roles:
                    if difference >= ANCIENNETE*24*3600 and pollsanswered >= NUMBER_OF_POLLS_ANCIEN:
                        anciens_citoyens.append(m.display_name)
                    else:
                        citoyens.append(m.display_name)
            
            embed = discord.Embed(
                title=":ballot_box: Citoyenneté",
                description="",
                color=discord.Color.blue()
            )
            if anciens_citoyens:
                embed.add_field(name="Anciens citoyens ("+str(len(anciens_citoyens))+")", value="- "+"\n- ".join(anciens_citoyens), \
                            inline=False)
            if citoyens:
                embed.add_field(name="Citoyens ("+str(len(citoyens))+")", value="- "+"\n- ".join(citoyens), \
                            inline=False)
            embed.timestamp = inter.created_at

            await inter.followup.send(embed=embed)
        elif bot_disabled:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


class PollView(discord.ui.View):
    def __init__(self, question, guild_id, channel_id, author_id, message_id=None, existing_votes=None, proportion=0.5, vote_type=None, timestamp=None, duration=None, citoyens=None, ern=False, poll_id=None, closed=False):
        super().__init__(timeout=None)
        self.question = question
        self.proportion = proportion
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.author_id = author_id
        self.message_id = message_id
        self.PB_EMOJIS = PB_EMOJIS

        self.citoyens = citoyens

        self.poll_id = poll_id

        self.timestamp = timestamp
        self.duration = duration
        self.vote_type = vote_type

        self.ern = ern

        self.termine = closed

        self.options = {
            "o": {
                "text": "Oui",
                "ernestien": "chlorên",
                "emoji": self.PB_EMOJIS["yes_check_mark"]
                },
            "b": {
                "text": "Blanc",
                "ernestien": "ketvôg",
                "emoji": "🏳️"
                },
            "n": {
                "text": "Non",
                "ernestien": "rôz",
                "emoji": self.PB_EMOJIS["no_x_mark"]
                }
            }
        self.votes = {opt: [] for opt in self.options}

        if existing_votes is None:
            self.oui, self.non, self.blancs = 0,0,0
        else:
            self.oui, self.non, self.blancs = 0,0,0
            for v in existing_votes.values():
                if v == "o":
                    self.oui += 1
                elif v == "n":
                    self.non += 1
                elif v == "b":
                    self.blancs += 1
                
        if existing_votes:
            for uid, opt in existing_votes.items():
                self.votes[opt].append(int(uid))
        for opt in self.options.keys():
            self.add_item(PollButton(label=(self.options[opt]["text"] if not self.ern else ernconvert(self.options[opt]["ernestien"])), emoji=self.options[opt]["emoji"], view=self, vote_key=opt))
        self.add_item(PollButton(label=" ", emoji="ℹ️", view=self, vote_key="i"))
        
    def get_results(self):
        return "\n".join(
            f"**{opt}** — {len(voters)} vote(s)" for opt, voters in self.votes.items()
        )
            
    def get_progressbar(self, pb_width=11):
        proportion = self.proportion
        b_s_number = int(proportion*pb_width)
        b_s_numberhalf = int(2*proportion*pb_width)/2

        side_spaces = ""
        
        """en pratique, je n'ai pas programmé le cas
        où la limite est au bord pour les votes non vides... inutiles ici"""
        
        if self.oui + self.non == 0:
            pb = side_spaces
            if b_s_number >= 1:
                pb += self.PB_EMOJIS["progressbar_left_e"]
            else:
                pb += self.PB_EMOJIS["progressbar_left_e_l"]
            pb += (b_s_number-1)*self.PB_EMOJIS["progressbar_middle_e"]
            if b_s_number <= pb_width-2 and b_s_number >= 1:
                pb += self.PB_EMOJIS["progressbar_middle_e_l"]
            pb += (pb_width-b_s_number-2)*self.PB_EMOJIS["progressbar_middle_e"]
            if b_s_number <= pb_width-2:
                pb += self.PB_EMOJIS["progressbar_right_e"]
            else:
                pb += self.PB_EMOJIS["progressbar_right_e_l"]
            return pb
        else:
            propoui = self.oui/(self.oui+self.non)
            oui_number = int(pb_width*propoui)
            oui_numberhalf = int(2*pb_width*propoui)/2
            first_col = "progressbar_left_o"
            if self.oui == 0:
                first_col = "progressbar_left_n"
            if oui_numberhalf <= b_s_number:
                pb = side_spaces+self.PB_EMOJIS[first_col]
                pb += (oui_number-1)*self.PB_EMOJIS["progressbar_middle_o"]
                if oui_numberhalf < b_s_number and oui_number>=1:
                    if oui_numberhalf*2 % 2 == 1:
                        pb += self.PB_EMOJIS["progressbar_middle_on"]
                    else:
                        pb += self.PB_EMOJIS["progressbar_middle_n"]
                pb += (b_s_number-oui_number-1)*self.PB_EMOJIS["progressbar_middle_n"]
                pb += self.PB_EMOJIS["progressbar_middle_n_l"]
                pb += (pb_width-b_s_number-2)*self.PB_EMOJIS["progressbar_middle_n"]
                pb += self.PB_EMOJIS["progressbar_right_n"]
            elif oui_numberhalf == b_s_number+0.5:
                pb = side_spaces+self.PB_EMOJIS[first_col]
                pb += (oui_number-1)*self.PB_EMOJIS["progressbar_middle_o"]
                pb += self.PB_EMOJIS["progressbar_middle_on_l"]
                pb += (pb_width-b_s_number-2)*self.PB_EMOJIS["progressbar_middle_n"]
                pb += self.PB_EMOJIS["progressbar_right_n"]
            elif oui_numberhalf <= pb_width-0.5:
                pb = side_spaces+self.PB_EMOJIS["progressbar_left_o"]
                pb += (b_s_number-1)*self.PB_EMOJIS["progressbar_middle_o"]
                if propoui > proportion:
                    pb += self.PB_EMOJIS["progressbar_middle_o_l"]
                else:
                    pb += self.PB_EMOJIS["progressbar_middle_on_l"]
                pb += (oui_number-b_s_number-1)*self.PB_EMOJIS["progressbar_middle_o"]
                if oui_number <= pb_width-2:
                    if oui_numberhalf*2 % 2 == 1:
                        pb += self.PB_EMOJIS["progressbar_middle_on"]
                    else:
                        pb += self.PB_EMOJIS["progressbar_middle_n"]
                pb += (pb_width-oui_number-2)*self.PB_EMOJIS["progressbar_middle_n"]
                pb += self.PB_EMOJIS["progressbar_right_n"]
            else:
                pb = side_spaces+self.PB_EMOJIS["progressbar_left_o"]
                pb += (b_s_number-1)*self.PB_EMOJIS["progressbar_middle_o"]
                pb += self.PB_EMOJIS["progressbar_middle_o_l"]
                pb += (pb_width-b_s_number-2)*self.PB_EMOJIS["progressbar_middle_o"]
                pb += self.PB_EMOJIS["progressbar_right_o"]
            pb += side_spaces
            return pb

    def get_actual_max(self):
        citoyens_number = len(self.citoyens)
        if citoyens_number > 0:
            prop = (int(citoyens_number*self.proportion)+1)
            adv_oui = self.oui/prop
            if citoyens_number == prop:
                adv_non = 1
            else:
                adv_non = self.non/(citoyens_number - prop)
            if adv_non == 0 and adv_oui == 0:
                return "b"
            elif adv_oui > adv_non:
                return "o"
            else:
                return "n"
        else:
            return "b"

    def get_advancement(self):
        citoyens_number = len(self.citoyens) - self.blancs
        if citoyens_number > 0:
            prop = (int(citoyens_number*self.proportion)+1)
            adv_oui = self.oui/prop
            if citoyens_number == prop:
                adv_non = 1
            else:
                adv_non = self.non/(citoyens_number - prop)
            if self.proportion == 0:
                return self.PB_EMOJIS["load_100_o"]
            elif self.proportion == 1:
                return self.PB_EMOJIS["load_100_n"]
            if adv_oui > adv_non:
                if adv_oui >= 1:
                    return self.PB_EMOJIS["load_100_o"]
                else:
                    if int(adv_oui*10)*10 > 0:
                        return self.PB_EMOJIS["load_"+str(int(adv_oui*10)*10)+"_o"]
                    else:
                        return self.PB_EMOJIS["load_0"]
            else:
                if adv_non >= 1:
                    return self.PB_EMOJIS["load_100_n"]
                else:
                    if int(adv_non*10)*10 > 0:
                        return self.PB_EMOJIS["load_"+str(int(adv_non*10)*10)+"_n"]
                    else:
                        return self.PB_EMOJIS["load_0"]
        else:
            return self.PB_EMOJIS["load_0"]


    def cut_text(self,text,max_width=18):
        lettersizes = LETTER_SIZE_BOLD
        ntext = []
        wspace = lettersizes[" "]
        actualw = 0
        actualligne = []
        for mot in text.split(" "):
            w = sum([lettersizes[l] if l in lettersizes else 0.5 for l in mot])
            if w+wspace + actualw <= max_width:
                actualligne.append(mot)
                actualw += w+wspace
            else:
                if actualligne != []:
                    ntext.append(" ".join(actualligne))
                    actualligne = [mot]
                    actualw = w
        if actualligne:
            ntext.append(" ".join(actualligne))
        return "\n".join(ntext)
        
        
    def get_embed(self, ended=False):
        pb = ">\u200B<".join(self.get_progressbar().split("><"))
        results = []
        w=0
        emptyem = self.PB_EMOJIS["empty"]
        if self.oui != 0:
            results.append(f"**O** {self.oui}")
        if self.non != 0:
            results.append(f"**N** {self.non}")
        if self.blancs != 0:
            results.append(f"**B** {self.blancs}")
        w = 7-2*len(results)
        if self.oui+self.non > 0:
            prop = self.oui/(self.oui+self.non)
            proportions = "\u00A0"+(str(round(prop*100))+"%" if prop < 1 else " ")+2*emptyem+" "
        else:
            proportions = 3*emptyem
            prop = 1

        if not ended:
            color = discord.Color.red()
        else:
            m = self.get_actual_max()
            if m == "o":
                color = discord.Color.yellow()
                
            elif m == "n":
                color = discord.Color.dark_purple()
            elif m == "b":
                color = discord.Color.light_gray()
            else:
                color = discord.Color.red()
            
        embed = discord.Embed(
            title=f"**{self.cut_text(self.question)}**",
            description=self.PB_EMOJIS["empty"]+"\n",
            color=color
        )
        embed.add_field(name="", value=self.PB_EMOJIS["empty"]*(1 if prop < 1 else 2)+pb+proportions, inline=True)
        if not ended:
            txt = self.get_advancement()
        else:
            if m == "b":
                txt = self.PB_EMOJIS["load_0"]
            else:
                txt = self.PB_EMOJIS["load_100_"+m]
        txt += emptyem
        txt += (w//2)*emptyem+(" ○ ".join(results) if self.oui+self.non+self.blancs>0 else "")+(w-w//2)*emptyem
        txt += " "+1*self.PB_EMOJIS["empty"]
        if not ended:
            txt += "<t:"+str(self.timestamp+self.duration)+":R>"
        else:
            txt += "**Terminé**"
        embed.add_field(name=emptyem, value=txt, inline=False)
        return embed

    async def send(self, inter):
        embed = self.get_embed()
        channel = inter.channel
        msg = await channel.send(embed=embed, view=self)
        await validation_response(inter, "Le vote a bien été initié !")
        return msg

    def save(self, msg_id):
        self.message_id = msg_id
        polls = load_polls()
        if polls:
            poll_id = max(poll["poll_id"] for poll in polls)+1
        else:
            poll_id = 1
        self.poll_id = poll_id
        polls.append({"poll_id": poll_id, "message_id": msg_id, "question": self.question, "proportion": self.proportion, "type": self.vote_type, "author_id": self.author_id, "channel_id": self.channel_id, "guild_id": self.guild_id, "timestamp": int(self.timestamp), "duration": self.duration, "vote_type": self.vote_type, "closed": 0, "votes":{}, "citoyens": self.citoyens})
        save_polls(polls)
        return poll_id

    async def wait_end(self):
        delay = self.timestamp+self.duration-time.time()
        if delay > 0:
            await asyncio.sleep(delay)
        self.termine = True
        polls = load_polls()
        for i in range(len(polls)):
            if self.poll_id == polls[i]["poll_id"]:
                polls[i]["closed"] = 1
                break
        save_polls(polls)
        channel = bot.get_channel(self.channel_id)
        message = await channel.fetch_message(self.message_id)
        embed = self.get_embed(True)
        view = get_closed_view(polls[i])
        await message.edit(embed=embed, view=view)
        await self.send_compterendu()

    async def send_compterendu(self):
        channel = bot.get_channel(self.channel_id)
        if self.non+self.oui == 0:
            txt = "En l'absence de votants, la proposition est **rejetée**."
            txtvotants = ""
            color = discord.Color.dark_purple()
        else:
            txtvotants = f"Votants : {self.oui+self.non+self.blancs}, Majorité : {int(self.proportion*(self.oui+self.non))+1}, Votes blanc : {self.blancs}, Pour : {self.oui}, Contre : {self.non}\n"
            prop = self.oui/(self.non+self.oui)
            if prop>self.proportion:
                txt = "En conséquence, la proposition est **adoptée**."
                color = discord.Color.yellow()
            else:

                txt = "En conséquence, la proposition est **rejetée**."
                color = discord.Color.dark_purple()
        link = f"https://discord.com/channels/{self.guild_id}/{self.channel_id}/{self.message_id}"
        embed = discord.Embed(
            title=f"",
            description=f"Le vote de {'loi' if self.vote_type == 'l' else 'révision constitutionnelle'} {link} : _\"{self.question}\"_ est clos.\n"+txtvotants+"\n"+txt,
            color=color
        )
        #roletoping = discord.utils.get(channel.guild.roles,name=PING_FIN_LOI)
        await channel.send(PING_FIN_LOI, embed=embed)


class PollButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str, view: PollView, vote_key: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji)
        self.poll_view = view
        self.vote_key = vote_key

    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user.id in self.poll_view.citoyens and self.vote_key != "i":
                if not self.poll_view.termine:
                    log_save("1")

                    user_id = interaction.user.id
                    # Anti-vote multiple
                    change_vote = False
                    initial_vote = None
                    for k in self.poll_view.votes:
                        voters = self.poll_view.votes[k]
                        if user_id in voters:
                            change_vote = True
                            initial_vote = k
                            voters.remove(user_id)
                            if k == "o":
                                self.poll_view.oui -= 1
                            elif k == "n":
                                self.poll_view.non -= 1
                            elif k == "b":
                                self.poll_view.blancs -= 1

                    if self.vote_key == "o":
                        self.poll_view.oui += 1
                    elif self.vote_key == "n":
                        self.poll_view.non += 1
                    elif self.vote_key == "b":
                        self.poll_view.blancs += 1
                    
                    self.poll_view.votes[self.vote_key].append(user_id)

                    polls = load_polls()
                    for poll in polls:
                        if poll["message_id"] == interaction.message.id:
                            poll["votes"][str(user_id)] = self.vote_key
                            break
                    save_polls(polls)

                    embed = self.poll_view.get_embed()
                    await interaction.response.edit_message(
                        embed=embed,
                        view=self.poll_view
                    )
                    vote = self.view.options[self.vote_key]
                    if not change_vote:
                        await custom_response(interaction, f"{vote['emoji']} Vote \"{vote['text']} / {ernconvert(vote['ernestien'])}\" enregistré.", duration=20)
                    else:
                        ivote = self.view.options[initial_vote]
                        await custom_response(interaction, f"{vote['emoji']} Vote \"{ivote['text']}\" changé en \"{vote['text']} / {ernconvert(vote['ernestien'])}\".", duration=20)
                else:
                    log_save("2")
                    await error_response(interaction, "Désolé, ce vote est clos...", duration=5)
            elif self.vote_key == "i":
                embed = await self.get_embed_infos(interaction)
                await interaction.response.send_message(embed=embed, ephemeral=True, allowed_mentions=discord.AllowedMentions(users=False))
            else:
                log_save("4")
                await error_response(interaction, f"Désolé, vous ne pouvez voter que si vous étiez citoyen au début du vote. {self.poll_view.citoyens}", duration=20)
        except Exception as e:
            print_command_error(interaction, e)
            await error_response(interaction,ERROR_MESSAGE)

    
    async def get_embed_infos(self, inter):
        citoyens_number = len(self.poll_view.citoyens) - self.poll_view.blancs
        prop = (int(citoyens_number*self.poll_view.proportion)+1)
        adv_oui = self.poll_view.oui/prop
        if citoyens_number == prop:
            adv_non = 1
        else:
            adv_non = self.poll_view.non/(citoyens_number - prop)
        
        if adv_non == 0 and adv_oui == 0:
            m = "b"
        elif adv_oui > adv_non:
            m = "o"
        else:
            m = "n"
        
        if m == "o":
            color = discord.Color.yellow()
        elif m == "n":
            color = discord.Color.dark_purple()
        elif m == "b":
            color = discord.Color.light_gray()
        else:
            color = discord.Color.red()

        link = f"https://discord.com/channels/{self.poll_view.guild_id}/{self.poll_view.channel_id}/{self.poll_view.message_id}"

        embed = discord.Embed(
            title=f"**{self.poll_view.question}** {link}",
            description="",
            color=color
        )
        guild = inter.message.guild
        author = guild.get_member(self.poll_view.author_id)
        user_id = inter.user.id
        if user_id in self.poll_view.votes["o"]:
            vote_tag = "o"
        elif user_id in self.poll_view.votes["n"]:
            vote_tag = "n"
        elif user_id in self.poll_view.votes["b"]:
            vote_tag = "b"
        else:
            vote_tag = None

        if vote_tag:
            mon_vote = self.poll_view.options[vote_tag]["emoji"]+" "+self.poll_view.options[vote_tag]["text"] + " / " + ernconvert(self.poll_view.options[vote_tag]["ernestien"])
            embed.add_field(name="**Mon vote**", value=mon_vote, inline=False)

        votetypetxt = {"l": "Loi", "r": "Révision constitutionnelle"}
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="**Type**", value=votetypetxt[self.poll_view.vote_type], inline=True)
        embed.add_field(name="**Statut**", value=(f"clôt <t:{self.poll_view.timestamp+self.poll_view.duration}:R>" if self.poll_view.termine == 0 else "Terminé"), inline=True)


        empty = self.poll_view.PB_EMOJIS["empty"]

        embed.add_field(name="", value=f"**Votes** - {self.poll_view.oui+self.poll_view.non+self.poll_view.blancs}", inline=False)
        if self.poll_view.oui:
            ouis = []
            for id_ in self.poll_view.votes["o"]:
                try:
                    mem = await inter.guild.fetch_member(id_)
                    ouis.append(mem.mention)
                except discord.errors.NotFound:
                    ouis.append(str(id_))
            embed.add_field(name=f"**Oui** - {len(ouis)}", value="- "+("\n- ").join(ouis), inline=True)

        if self.poll_view.non:
            nons = []
            for id_ in self.poll_view.votes["n"]:
                try:
                    mem = await inter.guild.fetch_member(id_)
                    nons.append(mem.mention)
                except discord.errors.NotFound:
                    nons.append(str(id_))
            embed.add_field(name=f"**Non** - {len(nons)}", value="- "+("\n- ").join(nons), inline=True)

        if self.poll_view.blancs:
            blancs = []
            for id_ in self.poll_view.votes["b"]:
                try:
                    mem = await inter.guild.fetch_member(id_)
                    blancs.append(mem.mention)
                except discord.errors.NotFound:
                    blancs.append(str(id_))
            embed.add_field(name=f"**Blanc** - {len(blancs)}", value="- "+("\n- ").join(blancs), inline=True)
        
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="", value=author.mention+empty+f"#{self.poll_view.poll_id}")
        return embed

class ConfirmView(discord.ui.View):
    def __init__(self, inter, i, msg_id, channel_id, visible, poll_id):
        super().__init__(timeout=None)
        self.inter = inter
        self.i = i
        self.msg_id = msg_id
        self.channel_id = channel_id
        self.visible = visible
        self.poll_id = poll_id

    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.danger, custom_id="confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.visible == 0:
            channel = bot.get_channel(self.channel_id)
            message = await channel.fetch_message(self.msg_id)
            await message.delete()
        polls = load_polls()
        polls2 = polls[:self.i]+polls[self.i+1:]
        save_polls(polls2)
        await self.inter.delete_original_response()
        log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {self.inter.guild.id if self.inter.guild else 'DM'} DELETE: vote \"{polls[self.i]['question']}\" #{self.poll_id} | Auteur: {self.inter.user} | Serveur: {self.inter.guild.name if self.inter.guild else 'DM'} | Canal: {self.inter.channel.name if self.inter.guild else 'DM'} | Commande: {self.inter.command.name}")
        await custom_response(interaction, "✅ Suppression confirmée")

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.secondary, custom_id="cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.inter.delete_original_response()


@bot.tree.command(description="[C] Actualise les interfaces des votes en cas de problème.")
async def votesupdate(inter):
    await inter.response.defer(ephemeral=True)
    await recover_polls()
    await validation_response(inter, "Votes actualisés !")


@bot.tree.command(description="[C] Supprime un vote.")
@app_commands.describe(identifiant="Identifiant du vote")
@app_commands.describe(visible="Garder le vote sur le serveur ?")
@app_commands.choices(visible=[app_commands.Choice(name="Oui", value=1),
                             app_commands.Choice(name="Non", value=0)])
async def deletevote(inter, identifiant: int, visible : int = 0):
    try:
        if not (is_local or not running_locally): return

        if not bot_disabled:
            for right in VOTE_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    polls = load_polls()
                    for i, poll in enumerate(polls):
                        if poll["poll_id"] == identifiant:
                            if poll["guild_id"] == inter.guild.id:
                                if poll["channel_id"] == inter.channel.id:
                                    if visible == 0 or poll["closed"] == 1:
                                        link = f"https://discord.com/channels/{poll['guild_id']}/{poll['channel_id']}/{poll['message_id']}"
                                        embed = discord.Embed(
                                            title="⚠️ Confirmation requise",
                                            description=f"Êtes-vous sûr.e de vouloir **supprimer** de façon **définitive** ce vote : \"{poll['question']}\" : {link} ?",
                                            color=discord.Color.red()
                                        )
                                        view = ConfirmView(inter, i, poll["message_id"], poll["channel_id"], visible, poll_id=identifiant)
                                        await inter.response.send_message(embed=embed, view=view, ephemeral=True)
                                    else:
                                        await error_response(inter, "Désolé, vous ne pouvez supprimer ce vote de façon invisible car il est toujours actif.\nSi vous souhaitez le supprimer tout de même, exécutez `deletevote` en supprimant également le message associé (visible=Non).", duration=10)
                                else:
                                    await error_response(inter, "Désolé, vous devez supprimer ce vote depuis le canal dans lequel vous l'avez initié.")
                            else:
                                await error_response(inter, "Désolé, vous ne pouvez pas supprimer ce vote.")
                            break
                    else:
                        await error_response(inter, "Désolé, cet identifiant n'est associé à aucun vote.")
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
        elif bot_disabled:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)



def get_current_citoyens(inter):
    citoyensl = []
    for m in inter.guild.members:
        roles = [simplify_role_name(r.name) for r in m.roles]
        if simplify_role_name(CITOYENS_NAME) in roles:
            citoyensl.append(m.id)
    return citoyensl


@bot.tree.command(description="[C] Initie un vote.")
@app_commands.describe(question="Question à voter (loi par défaut)")
@app_commands.choices(vote=[app_commands.Choice(name="Loi", value="l"),
                             app_commands.Choice(name="Révision constitutionnelle", value="r")])
@app_commands.describe(vote="Type de vote")
async def vote(inter, question: str, vote: str = "l"):
    try:
        await inter.response.defer(ephemeral=True)
        if not (is_local or not running_locally): return

        if not bot_disabled:
            for right in VOTE_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    if inter.channel.name == VOTES_NAME:
                        if vote == "l":
                            proportion = PROPORTION_LOI
                        elif vote == "r":
                            proportion = PROPORTION_REVISION
                        else:
                            raise Exception(f"Le type de vote {vote} n'existe pas")
                        citoyensl = get_current_citoyens(inter)
                        poll = PollView(question, guild_id=inter.guild.id, author_id=inter.user.id, \
                                        channel_id=inter.channel.id, \
                                        proportion=proportion, \
                                        vote_type=vote,
                                        timestamp=int(time.time()), duration=DUREE_VOTES*24*3600, \
                                        citoyens=citoyensl)
                        msg = await poll.send(inter)
                        poll_id = poll.save(msg.id)
                        log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {inter.guild.id if inter.guild else 'DM'} ADD: vote \"{question}\" #{poll_id} | Auteur: {inter.user} | Serveur: {inter.guild.name if inter.guild else 'DM'} | Canal: {inter.channel.name if inter.guild else 'DM'} | Commande: {inter.command.name}")
                        asyncio.create_task(poll.wait_end())
                    else:
                        await error_response(inter, f"Désolé, vous ne pouvez initier de vote que dans le salon \"{VOTES_NAME}\" prévu à cet effet.")
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
        elif bot_disabled:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


@bot.tree.command(description="[A] Recharger les émojis (en cas de problème)")
async def emojisupdate(inter):
    try:
        if not (is_local or not running_locally): return

        if not bot_disabled:
            global ioloenabled
            for right in ADMINISTRATOR_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    load_emojis()
                    await validation_response(inter,f"Émojis actualisés...")
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
        else:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)

class FormulaireModal2(discord.ui.Modal):
    def __init__(self, reftag="", reftext=""):
        super().__init__(title="")
        self.inp1 = discord.ui.TextInput(
            label="Français",
            placeholder="ex: poisson",
            default=reftag[:200],
            required=True,
            max_length=200 
        )

        self.inp2 = discord.ui.TextInput(
            label="Étymologie (facultatif)",
            style=discord.TextStyle.paragraph,
            default=reftext[:600],
            required=False,
            max_length=600
        )
        
        self.add_item(self.inp1)
        self.add_item(self.inp2)


    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message("En cours...", ephemeral=True)
            mot_francais = self.inp1.value
            mot_ernestien = self.inp2.value

            try:
                pass
            except FileNotFoundError:
                message = await interaction.edit_original_response(
                    content=ERROR_EMOJI+f" Une erreur s'est produite. Essayez d'actualiser le dictionnaire en amont avec la commande `/dicoupdate`."
                )
                await asyncio.sleep(5)
                await message.delete()
        except Exception as e:
            print_command_error(interaction,e)
            await error_response(interaction,ERROR_MESSAGE)


@bot.tree.command(description="[R] Ajoute ou modifie une référence.")
@app_commands.describe(texte="La référence à ajoutée, formatée. Lire la doc. avant (`/referencedoc`).")
@app_commands.describe(action="Action à effectuer : \"add\" pour ajouter, \"edit\" pour éditer, \"auto\" automatique (par défaut), \"forced add\" pour un ajout forcé.")
@app_commands.choices(action=[app_commands.Choice(name="edit", value="edit"),
                             app_commands.Choice(name="add", value="add"),
                             app_commands.Choice(name="forced add", value="forced add"),
                              app_commands.Choice(name="auto", value="auto")])
async def reference(inter, texte : str, action : str = "auto"):
    try:
        if not (is_local or not running_locally): return

        if not bot_disabled:
            for right in REFS_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    (mom,score, i_ref,i_repl,i_mom) = references.references.scoring(texte)
                    refs = references.references.load_references()

                    if score >= references.references.SEUIL:
                        if action == "auto":
                            #modif
                            await inter.response.send_modal(FormulaireModal2())
                        elif action == "add":
                            await error_response(inter,f"Désolé, une référence similaire existe déjà : \"{mom}\" ({refs[i_ref]}). Si vous voulez l'éditer, renseignez `action=edit`. Si vous voulez ajouter une réf similaire malgré tout `action=force add`.")
                        elif action == "edit":
                            #modif
                            await inter.response.send_modal(FormulaireModal2())
                    else:
                        pass
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
        else:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)
    

class FormulaireModalAvent(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Case")
        self.inp1 = discord.ui.TextInput(
            label="Jour",
            placeholder="1-24",
            default=str(datetime.datetime.today().day),
            required=True,
            max_length=200 
        )

        self.inp2 = discord.ui.TextInput(
            label="Corps",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=600
        )
        
        self.add_item(self.inp1)
        self.add_item(self.inp2)


    async def on_submit(self, interaction: discord.Interaction):
        try:
            try:
                daynumber = int(self.inp1.value)
            except ValueError:
                await error_response(interaction, "Veuillez entrer un jour valide (entier, dans la plage 1-24).")
                return
            if daynumber >= 1 and daynumber <= 24:
                channel = discord.utils.get(bot.get_all_channels(), name=AVENT_CHANNEL)
                embed = discord.Embed(
                    title=AVENT_TITLE,
                    description="",
                    color=discord.Color.red()
                )
                #embed.add_field(name="", value="", inline=True)
                #embed.add_field(name="", value=replace_tags(self.inp2.value), inline=True)
                paysage = await self.get_paysage()
                for e in paysage.split("\n"):
                    embed.add_field(name="", value=e, inline=False)
                
                #embed.add_field(name="", value="", inline=True)

                fl = f'fonts/avent/{daynumber}.png'
                file = discord.File(fl, filename=f"{daynumber}.png")
                embed.set_thumbnail(url=f"attachment://{daynumber}.png")

                await interaction.response.send_message(embed=embed, file=file)
                msg = await interaction.original_response()
                await msg.add_reaction("🙉")
                await msg.add_reaction("❄️")

                user_id = interaction.user.id
                msg_id = msg.id
                        
                add_reaction(msg_id, "❌", lambda: self.delete, user_id=user_id)

                add_reaction(msg_id, "🙉", self.open_calendrier)
                add_reaction(msg_id, "❄️", self.faire_neiger)

        except Exception as e:
            print_command_error(interaction,e)
            await error_response(interaction,ERROR_MESSAGE)
    
    async def get_paysage(self):
        proportion_star = 0.3
        proportion_sapin = 0.3
        width = 9
        height = 6
        t = ""
        i0 = random.randint(0,3)
        if i0 == 3:
            i0 = 1
        j0 = random.randint(1,width-1)
        for i in range(height-1):
            for j in range(width):
                if i0 == i and j0 == j:
                    t += PB_EMOJIS["lune"]
                else:
                    t += PB_EMOJIS["empty"]
            t += "\n"
        for j in range(width):
            if random.random() <= proportion_sapin:
                t += PB_EMOJIS["sapin"]
            else:
                t += PB_EMOJIS["empty"]
        return t

    async def balancer_la_neige(self):
        proportion_star = 0.3
        proportion_sapin = 0.3
        width = 9
        height = 6
        t = ""
        for i in range(height-1):
            for j in range(width):
                m = 1
                if i == 0 or j == 0 or i == height-2 or j == width-1:
                    m = 0.5
                if random.random() <= proportion_star*m:
                    t += PB_EMOJIS["neige"]
                else:
                    t += PB_EMOJIS["empty"]
            t += "\n"
        return t


    async def delete(self):
        log_save("delete calendrier")
    
    async def open_calendrier(self):
        log_save("open_calendrier")
        embed = discord.Embed(
            title=AVENT_TITLE,
            description="",
            color=discord.Color.red()
        )
        #embed.add_field(name="", value="", inline=True)
        embed.add_field(name="", value=replace_tags(self.inp2.value), inline=True)

    async def faire_neiger(self):
        pass


@bot.tree.command(description="[L] Affiche le calendrier de l'avent.")
async def avent(inter):
    try:
        if not (is_local or not running_locally): return

        if not bot_disabled:
            for right in DICO_RIGHTS:
                if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                    if datetime.datetime.today().month == 12 and datetime.datetime.today().day >= 1 and datetime.datetime.today().day <= 24:
                        if inter.channel.name == AVENT_CHANNEL:
                            await inter.response.send_modal(FormulaireModalAvent())
                        else:
                            await error_response(inter, f"Désolé, allez dans \"{AVENT_CHANNEL}\"...")
                    else:
                        await error_response(inter, "Désolé, ça n'est pas le moment...")
                    break
            else:
                await error_response(inter, ERROR_RIGHTS_MESSAGE)
        else:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


@bot.tree.command(description="[A] Met à jour ernestomôch et le redémarre")
async def upgradebot(inter):
    if not bot_disabled:
        for right in ADMINISTRATOR_RIGHTS:
            if simplify_role_name(right) in [simplify_role_name(r.name) for r in inter.user.roles]:
                f = open("upgrade.temp", "w", encoding="utf-8")
                f.write(str(inter.channel.id))
                f.close()
                try:
                    await validation_response(inter, "Redémarrage")
                except Exception as e:
                    print_command_error(inter,e)
                os.system("./update.sh &")
                await bot.close()
                break
        else:
            await error_response(inter, ERROR_RIGHTS_MESSAGE)
    else:
        await error_response(inter, ERROR_BOT_DISABLED_MESSAGE)
    


ftoken = open("SECRET/token_discord.txt","r")
DISCORD_TOKEN = ftoken.read()
ftoken.close()

bot.run(DISCORD_TOKEN)


