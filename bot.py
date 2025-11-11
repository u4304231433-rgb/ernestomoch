import discord
from discord.ext import commands
from discord import app_commands

import datetime
import re
import asyncio
import os
import sys
import traceback

from tex.processcsv import *
from tex.googleapif import *


CITOYENS_NAME = "Citoyen"       # Noms exacts des rôles dans Discord
NORMALIENS_NAME = "Normalien"
TOURISTES_NAME = "Touriste"
POLICIERS_NAME = "Policier"
COMMISSAIRE_NAME = "Commissaire"
PROCUREUR_NAME = "Procureur"
CONSEILLER_CONST_NAME = "Conseiller constitutionnel"
CONSEILLER_PERM_NAME = "Conseiller permanent"

ADMINISTRATOR_RIGHTS = [CONSEILLER_CONST_NAME, POLICIERS_NAME, CONSEILLER_PERM_NAME, COMMISSAIRE_NAME] # les roles qui ont des droits spéciaux

ANCIENNETE = 0.001                  # ancienneté requise pour être ancien citoyen (en jours)
NUMBER_OF_POLLS_ANCIEN = 1      # nombre de sondages à avoir répondu pour être ancien

VOTES_NAME = "votes"            # nom exact du canal des votes

COMMAND_PREFIX = "/"
BOT_NAME = "Ernestomôch"

ERROR_RIGHTS_MESSAGE = "Désolé, vous ne disposez pas des droits pour effectuer cette commande."
ERROR_MESSAGE = "Une erreur s'est produite, veuillez nous en excuser."
ERROR_BOT_DISABLED_MESSAGE = "Désolé, le bot est actuellement désactivé."

VALIDATION_EMOJI = ":white_check_mark:"
ERROR_EMOJI = ":no_entry_sign:"

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

async def validation_response(inter,msg):
    try:
        await inter.response.defer(ephemeral=True)
    except (discord.HTTPException,discord.InteractionResponded):
        pass
    message = await inter.followup.send(VALIDATION_EMOJI+" "+msg, ephemeral=True)
    await asyncio.sleep(3)
    await message.delete()

async def error_response(inter,msg):
    try:
        await inter.response.defer(ephemeral=True)
    except (discord.HTTPException,discord.InteractionResponded):
        pass
    message = await inter.followup.send(ERROR_EMOJI+" "+msg, ephemeral=True)
    await asyncio.sleep(3)
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
        specrights.append("[D]")
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

@bot.tree.command(description="[A] Édite le dictionnaire")
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
                    await inter.followup.send("", file=file)
                    os.chdir("../")
                    break
            else:
                await error_response(inter,ERROR_RIGHTS_MESSAGE)
        elif bot_disabled:
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
            async for msg in canalvotes.history():
                if msg.poll is not None:
                    for answer in msg.poll.answers:
                        async for voter in answer.voters():
                            if voter.id not in voters:
                                voters[voter.id] = 1
                            else:
                                voters[voter.id] += 1
            
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



