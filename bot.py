import discord
from discord.ext import commands
from discord import app_commands

import datetime
import time
import re
import asyncio
import os
import sys
import traceback

from tex.processcsv import *
from tex.googleapif import *

from difflib import SequenceMatcher


CITOYENS_NAME = "Citoyen"       # Noms exacts des rôles dans Discord
NORMALIENS_NAME = "Normalien"
TOURISTES_NAME = "Touriste"
POLICIERS_NAME = "Policier"
COMMISSAIRE_NAME = "Commissaire"
PROCUREUR_NAME = "Procureur"
CONSEILLER_CONST_NAME = "Conseiller constitutionnel"
CONSEILLER_PERM_NAME = "Conseiller permanent"

ADMINISTRATOR_RIGHTS = [CONSEILLER_CONST_NAME, POLICIERS_NAME, CONSEILLER_PERM_NAME, COMMISSAIRE_NAME] # les roles qui ont des droits spéciaux
DICO_RIGHTS = ADMINISTRATOR_RIGHTS # les roles qui ont des droits spéciaux

ANCIENNETE = 5                  # ancienneté requise pour être ancien citoyen (en jours)
NUMBER_OF_POLLS_ANCIEN = 3      # nombre de sondages à avoir répondu pour être ancien
LIMIT_NUMBER_OF_POLLS = 10      # nombre des derniers votes pris en comptes

VOTES_NAME = "votes"            # nom exact du canal des votes

COMMAND_PREFIX = "/"
BOT_NAME = "Ernestomôch"

ERROR_RIGHTS_MESSAGE = "Désolé, vous ne disposez pas des droits pour effectuer cette commande"
ERROR_MESSAGE = "Une erreur s'est produite, veuillez nous en excuser."
ERROR_BOT_DISABLED_MESSAGE = "Désolé, le bot est actuellement désactivé."

VALIDATION_EMOJI = ":white_check_mark:"
ERROR_EMOJI = ":no_entry_sign:"
DICO_EMOJI = ":book:"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

intents.reactions = True
intents.guilds = True


ioloenabled = False

class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        pass

    async def send_command_help(self, command):
        pass

flog = open(".log","w", encoding="utf-8")
flog.write("")
flog.close()

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=CustomHelpCommand())

def log_save(m):
    flog = open(".log","a", encoding="utf-8")
    flog.write(m+"\n")
    flog.close()
    print(m)

@bot.event
async def on_ready():
    await bot.tree.sync()
    for guild in bot.guilds:
        await guild.me.edit(nick=BOT_NAME)
    
    log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] OK: {bot.user} connecté à {';'.join([str(guild.id)+'#'+guild.name for guild in bot.guilds])}")
    
@bot.event
async def on_message(msg):
    if not msg.author.bot:
        if ioloenabled:
            if re.search(r"(.*)(^|\s|\_|\*)(([i][oo0][l][oô])|([i][ooô̥]))($|\s|\_|\*)(.*)",msg.content.lower()):
                await msg.channel.send("iolô !")
            elif re.search(r"(.*)(^|\s|\_|\*)(([ııi][oo0o][lʟ̥ʟʟʟ̥ʟ][oô̥ô̥ô])|([ıi][oo0ô̥ô̥ô]))($|\s|\_|\*)(.*)",msg.content.lower()):
                await msg.channel.send("ıoʟ̥ô !")
            if re.search(r"(.*)(^|\s|'|:|,|\(|\_|\*)(ernestom[oô]ch|\<@1435667613865742406\>|cꞁ̊ᒉcc̥⟊oᒐôʃ)($|\s|,|:|\)|\_|\*)(.*)", msg.content.lower()):
                await msg.channel.send("C'est moi !")
        await bot.process_commands(msg)


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
    log_save(f"[{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {interaction.guild.id if interaction.guild else 'DM'} ERREUR: {error} dans {last_frame.filename} ligne {last_frame.lineno} | Auteur: {interaction.user} | Serveur: {interaction.guild.name if interaction.guild else 'DM'} | Canal: {interaction.channel.name if interaction.guild else 'DM'} | Commande: {interaction.command.name}")

async def validation_response(inter,msg,duration=3):
    try:
        await inter.response.defer(ephemeral=True)
    except (discord.HTTPException,discord.InteractionResponded):
        pass
    message = await inter.followup.send(VALIDATION_EMOJI+" "+msg, ephemeral=True)
    await asyncio.sleep(duration)
    await message.delete()

async def error_response(inter,msg, duration=3):
    try:
        await inter.response.defer(ephemeral=True)
    except (discord.HTTPException,discord.InteractionResponded):
        pass
    message = await inter.followup.send(ERROR_EMOJI+" "+msg, ephemeral=True)
    await asyncio.sleep(duration)
    await message.delete()


async def generate_pdf():
    process = await asyncio.create_subprocess_exec(
        "xelatex", "-synctex=1", "-interaction=nonstopmode", "main.tex",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

running_locally = False
is_local = False

bot_disabled = False

if os.path.exists("local.txt"):
    f = open("local.txt","r")
    if f.read() == "1":
        is_local = True
        print("Running locally")
    f.close()


async def update_specrights(inter):
    specrights = []
    if bot_disabled:
        specrights.append("[O]")
    if ioloenabled:
        specrights.append("[I]")
    if running_locally:
        specrights.append("[L]")
    await inter.guild.me.edit(nick=BOT_NAME+" "+" ".join(specrights))



@bot.tree.command(name="bot", description="[A] Active/désactive le bot")
@app_commands.choices(state=[app_commands.Choice(name="on", value="on"),
                             app_commands.Choice(name="off", value="off"),
                             app_commands.Choice(name="switch", value="switch")])
@app_commands.describe(state="État du bot : on (activé), off (désactivé), switch (basculer on/off)")
async def botstate(inter,state : str = "switch"):
    try:
        global bot_disabled
        for right in ADMINISTRATOR_RIGHTS:
            if right in [r.name for r in inter.user.roles]:
                if state == "switch":
                    bot_disabled = not bot_disabled
                elif state == "on":
                    bot_disabled = False
                elif state == "off":
                    bot_disabled = True
                else:
                    await error_response(inter,ERROR_EMOJI+f" Paramètre state={state} non valide")
                await update_specrights(inter)
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
                if right in [r.name for r in inter.user.roles]:
                    if state == "switch":
                        running_locally = not running_locally
                    elif state == "on":
                        running_locally = True
                    elif state == "off":
                        running_locally = False
                    else:
                        await error_response(inter,ERROR_EMOJI+f" Paramètre state={state} non valide")
                    await update_specrights(inter)
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
async def logs(inter, limit : int = None):
    try:
        if (is_local or not running_locally) and not bot_disabled:
            for right in ADMINISTRATOR_RIGHTS:
                if right in [r.name for r in inter.user.roles]:
                    try:
                        await inter.response.defer()
                    except discord.HTTPException:
                        pass
                    if limit is None:
                        f = open(".log","r")
                        f.close()
                        file = discord.File(".log", filename=".log")
                        await inter.followup.send("", file=file,ephemeral=True)
                    else:
                        flog = open(".log","r",encoding="utf-8")
                        i = 0
                        lines = flog.readlines()
                        flog.close()
                        fw = open("limit.log","w")
                        fw.write("\n".join(lines[-limit:]))
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

@bot.tree.command(name="dicopdf", description="[A] Édite le dictionnaire")
async def dictionnaire(inter):
    try:
        if (is_local or not running_locally) and not bot_disabled:
            for right in ADMINISTRATOR_RIGHTS:
                if right in [r.name for r in inter.user.roles]:
                    os.chdir("./tex/")
                    await inter.response.send_message(":arrows_counterclockwise: Edition du dictionnaire...", ephemeral=True)
                    await inter.edit_original_response(content=":arrow_down: Downloading file")
                    await download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","ernestien.csv")
                    await inter.edit_original_response(content=":robot: Conversion python")
                    await processcsv()
                    await inter.edit_original_response(content=":pencil: Première compilation XeLaTex")
                    await generate_pdf()
                    await inter.edit_original_response(content=":pencil: Deuxième compilation XeLaTex")
                    await generate_pdf()
                    now = datetime.datetime.now()
                    file = discord.File("main.pdf", filename=f"dico-{now.year}-{now.month}-{now.day}.pdf")
                    await inter.delete_original_response()
                    await inter.followup.send(f"Dictionnaire édité par {inter.user.mention} :", file=file, allowed_mentions=discord.AllowedMentions(users=False))
                    os.chdir("../")
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
    text2 = re.sub(r"\_\_(.*?)\_\_", r"_\1_", text)
    return text2


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
    return unicodedata.normalize("NFKD", str(texte)).encode("ASCII", "ignore").decode().lower()

def ernconvert(mot):
    erchars = [".",","," ",'𓆟', 'n', 'n̂', 'Ր', 'Þ', 'c', 'ĉ', 'ϕ', 'ᕋ', 'ʃ', 'ı', 'î', 'J', '¢', 'ʟ̥', 'ᒐ', 'ᒉ', 'o', 'ô', 'г̊', 'Ꞁ̊', 'c̥', '⟊', 'u', 'û', 'v̥', '∤']
    frchars = "., qaâbdeêfghiîjklmnoôprstuûvz"
    mapping = dict(zip(frchars, erchars))
    return ''.join(mapping[c] for c in mot if c in mapping)

def frconvert(mot):
    erchars = [".",","," ",'𓆟', 'n', 'n̂', 'Ր', 'Þ', 'c', 'ĉ', 'ϕ', 'ᕋ', 'ʃ', 'ı', 'î', 'J', '¢', 'ʟ̥', 'ᒐ', 'ᒉ', 'o', 'ô', 'г̊', 'Ꞁ̊', 'c̥', '⟊', 'u', 'û', 'v̥', '∤']
    frchars = "., qaâbdeêfghiîjklmnoôprstuûvz"
    mapping = dict(zip(erchars, frchars))
    return ''.join(mapping[c] for c in mot if c in mapping)

def frconvert_keep(mot):
    erchars = [".",","," ",'𓆟', 'n', 'n̂', 'Ր', 'Þ', 'c', 'ĉ', 'ϕ', 'ᕋ', 'ʃ', 'ı', 'î', 'J', '¢', 'ʟ̥', 'ᒐ', 'ᒉ', 'o', 'ô', 'г̊', 'Ꞁ̊', 'c̥', '⟊', 'u', 'û', 'v̥', '∤']
    frchars = "., qaâbdeêfghiîjklmnoôprstuûvz"
    mapping = dict(zip(erchars, frchars))
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
                        score += witherrors/5 * (3 - d1)  # bonus inversé
 
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

    # Nettoyage colonne par colonne (sans applymap)
    df_clean = df[colonnes].copy()
    for col in colonnes:
        df_clean[col] = df_clean[col].map(nettoyer_texte)

    # Calcul du score de pertinence
    scores = df_clean.apply(lambda x : score_ligne(x,mot), axis=1)
    df_resultats = df[scores >= 1][COLS].copy()
    df_resultats["pertinence"] = scores[scores >= 1]
    df_resultats = df_resultats.sort_values(by="pertinence", ascending=False)

    # Surlignage dans les colonnes ciblées
    def surligner_ernestien(val):
        val_clean = nettoyer_texte(val)
        val2 = re.sub(r"£(.*?)£", lambda m: "_"+m.group(1)+"_ ("+ernconvert(m.group(1))+")", val)
        val2 = re.sub(r"€(.*?)€", lambda m: "_"+m.group(1)+"_", val2)
        return re.sub(pattern, lambda m: f"**{val[m.start():m.end()]}**", val2, flags=re.IGNORECASE)

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
                        if right in [r.name for r in inter.user.roles]:
                            os.chdir("./tex/")
                            await download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","ernestien.csv")
                            os.chdir("../")
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
                if right in [r.name for r in inter.user.roles]:
                    await inter.response.send_message(":arrow_down: Téléchargement du dictionnaire...", ephemeral=True)
                    os.chdir("./tex/")
                    await download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","ernestien.csv")
                    os.chdir("../")
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
                        os.chdir("./tex/")
                        await ajouter_ligne_sheet(
                            spreadsheet_id="1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q",
                            range_target="Dico",
                            nouvelle_ligne=[mot_francais, mot_ernestien, mot_etymologie]
                        )
                        os.chdir("../")

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
                            content=DICO_EMOJI+f" {interaction.user.mention} a ajouté\n```{mot_francais} → {mot_ernestien}{'\n' + mot_etymologie if mot_etymologie != '' else ''}```",
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
                        os.chdir("./tex/")
                        await modifier_ligne_sheet(
                            spreadsheet_id="1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q",
                            ligne=self.linenumber,
                            range_target="Dico",
                            nouvelle_ligne=[mot_francais, mot_ernestien, mot_etymologie]
                        )
                        os.chdir("../")

                        df = pd.read_csv("tex/ernestien.csv")

                        df.at[self.linenumber, "Francais"] = mot_francais
                        df.at[self.linenumber, "Ernestien"] = mot_ernestien
                        df.at[self.linenumber, "Etymologie"] = mot_etymologie
                        df.to_csv("tex/ernestien.csv", index=False)

                        await interaction.delete_original_response()
                        await interaction.followup.send(
                            content=DICO_EMOJI+f" {interaction.user.mention} a modifié{' : '+self.francais_val+' en '+mot_francais if self.francais_val != mot_francais else ''}\n```{mot_francais} → {mot_ernestien}{'\n' + mot_etymologie if mot_etymologie != '' else ''}```",
                            allowed_mentions=discord.AllowedMentions(users=False)
                        )
                    else:
                        if self.francais_val == mot_francais:
                            os.chdir("./tex/")
                            await supprimer_ligne_sheet(
                                spreadsheet_id="1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q",
                                ligne=self.linenumber,
                                range_target="Dico"
                            )
                            os.chdir("../")
                            
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
                if right in [r.name for r in inter.user.roles]:
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
                if right in [r.name for r in inter.user.roles]:
                    if state == "switch":
                        ioloenabled = not ioloenabled
                    elif state == "on":
                        ioloenabled = True
                    elif state == "off":
                        ioloenabled = False
                    else:
                        await error_response(inter,ERROR_EMOJI+f" Paramètre state={state} non valide")
                    await update_specrights(inter)
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
                roles = [r.name for r in m.roles]
                if CITOYENS_NAME in roles:
                    citoyens.append(m.display_name)
                elif NORMALIENS_NAME in roles:
                    normaliens.append(m.display_name)
                elif TOURISTES_NAME in roles:
                    touristes.append(m.display_name)

            embed = discord.Embed(
                title=":bar_chart: Statistiques",
                description="",
                color=discord.Color.blue()
            )
            if citoyens:
                embed.add_field(name="Citoyens ("+str(len(citoyens))+")", value="- "+"\n- ".join(citoyens), inline=False)
            if normaliens:
                embed.add_field(name="Normaliens ("+str(len(normaliens))+")", value="- "+"\n- ".join(normaliens), inline=False)
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
        if (is_local or not running_locally) and not bot_disabled:
            response = inter.response
            citoyens = []
            anciens_citoyens = []

            canalvotes = discord.utils.get(inter.guild.text_channels, name=VOTES_NAME)

            voters = {}
            icompteur = 0
            async for msg in canalvotes.history():
                if msg.poll is not None:
                    for answer in msg.poll.answers:
                        async for voter in answer.voters():
                            if voter.id not in voters:
                                voters[voter.id] = 1
                            else:
                                voters[voter.id] += 1
                    icompteur += 1
                    if icompteur >= LIMIT_NUMBER_OF_POLLS:
                        break
            
            for m in inter.guild.members:
                joined = m.joined_at.timestamp()
                now = datetime.datetime.now().timestamp()
                difference = now-joined

                if m.id in voters:
                    pollsanswered = voters[m.id]
                else:
                    pollsanswered = 0

                roles = [r.name for r in m.roles]
                if CITOYENS_NAME in roles:
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

            await response.send_message(embed=embed)
        elif bot_disabled:
            await error_response(inter,ERROR_BOT_DISABLED_MESSAGE)
    except Exception as e:
        print_command_error(inter,e)
        await error_response(inter,ERROR_MESSAGE)


ftoken = open("SECRET/token_discord.txt","r")
DISCORD_TOKEN = ftoken.read()
ftoken.close()

bot.run(DISCORD_TOKEN)
