import discord
from discord import Option, OptionChoice
from discord.ext import commands
import json
from datetime import datetime
import sqlite3
import random
bot = discord.Bot()

###############################################################
# CONFIG
###############################################################

with open("config.json", "r") as f:
    config = json.load(f)

coinEmoji = config["coinEmoji"]
patoID = config["patoID"]

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

###############################################################
# UTILITY
###############################################################

def current_time():
    time = datetime.now()
    return datetime.strftime(time, "%d/%m/%Y %H:%M:%S")

def log(string):
    print(f"[{current_time()}] {string}")

def changeBalance(userID, change):
    balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (str(userID),)).fetchone()

    newBalance = balance[0] + change

    cursor.execute("UPDATE users SET balance = :b WHERE id = :i", {"b": newBalance ,"i": str(userID)})
    connection.commit()

def invToList(userID):
    inventory = cursor.execute("SELECT inventory FROM users WHERE id = ?", (str(userID),)).fetchone()
    inv = inventory[0]
    if inv == None:
        return []
    else:
        return list(inv.split(","))

def ListToInv(li):
    return ",".join(li)

def modifyInv(string, userID):
    cursor.execute("UPDATE users SET inventory = :b WHERE id = :i", {"b": string ,"i": str(userID)})
    connection.commit()

###############################################################
# EVENTS
###############################################################

@bot.event
async def on_ready():
    log("Logged in.")

@bot.event
async def on_message(message):
    if message.author.bot == False and message.author.id != patoID:

        response = cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE id=?)", (str(message.author.id), ))
        userExists = response.fetchone()[0]

        if userExists == 1:
            balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (str(message.author.id),))
            balance = balance.fetchone()[0]

            newBalance = balance + config["balIncreaseOnMessage"]

            cursor.execute("UPDATE users SET balance = :b WHERE id = :i", {"b": newBalance ,"i": str(message.author.id),})
            connection.commit()

        else:
            cursor.execute("INSERT INTO users values (?, ?, ?)", (str(message.author.id), str(message.author), 10))
  

###############################################################
# COMMANDS
###############################################################

@commands.is_owner()
@bot.slash_command(name="sql")
async def sql(ctx, input:Option(str)):
    try:
        cursor.execute(input)
        connection.commit()
        await ctx.respond(f"`{input}` executed", ephemeral=True)
    except sqlite3.Error as err:
        embed = discord.Embed(title=f"Failed to execute\n{input}", description=f"```{repr(err)}```", color=discord.Colour.red())
        await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="rebríček", description="Bohatí ľudia")
async def rebricek(ctx):
    allUsers = cursor.execute("SELECT name, balance FROM users ORDER BY balance DESC")
    usersList = []

    for i in allUsers:
        usersList.append(f"{i[0]} - {i[1]}{coinEmoji}")
    usersStr = '\n'.join(usersList)

    embed = discord.Embed(title="Bohatí", description=usersStr)
    
    await ctx.respond(embed=embed)


##############
# OBCHOD
##############

obchod = bot.create_group(name="obchod")

@obchod.command(name="zoznam", description="Zoznam tovaru v obchode.")
async def obchodZoznam(ctx):
    with open("shop.json", "r") as f:
        shop = json.load(f)

    embed = discord.Embed(title="Obchod")
    for i in shop:
        embed.add_field(name=f'{i["emoji"]} {i["name"]}', value=f'{i["description"]}\n**{i["price"]}**{coinEmoji}')

    await ctx.respond(embed=embed)  


with open("shop.json", "r") as f:
    shop = json.load(f)   
tovar = []
for i in shop:
    tovar.append(OptionChoice(name=i["name"], value=i["id"]))

async def obrannyotrok(ctx):
    inventory = invToList(ctx.author.id)
    inventory.append("obrannyotrok")
    modifyInv(ListToInv(inventory), ctx.author.id)

async def patogun(ctx):
    inventory = invToList(ctx.author.id)
    inventory.append("patogun")
    modifyInv(ListToInv(inventory), ctx.author.id)

async def lottery(ctx):
    with open("config.json", "r") as f:
        config = json.load(f)

    numbers = []
    for i in range(3):
        numbers.append(random.randint(0, (len(config["lotteryIcons"]) - 1)))
    

    if numbers[0] == numbers[1] and numbers[1] == numbers[2]:
        prize = config["lotteryPrizes"][numbers[0]]
        changeBalance(ctx.author.id, prize)

    else:
        prize = 0

    emojiList = []
    
    for i in numbers:
        emojiList.append(config["lotteryIcons"][i])
    
    emojis = "".join(emojiList)


    embed = discord.Embed(title="Stierací žreb", description=emojis, color=discord.Colour.dark_gold())
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1050096025974620190/1050112834220085318/3D6E3F69-4FA6-48F5-A44A-FF8D4AD8B2A8.png")
    if prize > 0:
        embed.set_footer(text=f"Vyhral si {prize}")
    else:
        embed.set_footer(text=f"Nevyhral si.")

    await ctx.respond(embed=embed)

@obchod.command(name="kúpiť", description="Nákup tovaru z obchodu.")
async def obchodKupit(ctx, tovar: Option(str, choices=tovar,required = True)):
    log(f"{ctx.author} si kúpil {tovar}")
    with open("shop.json", "r") as f:
        shop = json.load(f)   
    
    for i in shop:
        if i["id"] == tovar:
            price = i["price"]
            name = i["name"]
            break
  
    balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (str(ctx.author.id),)).fetchone()

    newBalance = balance[0] - price
    if newBalance >= 0:
        cursor.execute("UPDATE users SET balance = :b WHERE id = :i", {"b": newBalance ,"i": str(ctx.author.id)})
        connection.commit()

        embed = discord.Embed(title=f"Kúpil si si: **{name}!**", color=discord.Colour.green())
        await ctx.respond(embed=embed)
        await eval(tovar + "(ctx)")
    else:
        embed = discord.Embed(title=f"Nemáš dostatok peňazí.", color=discord.Colour.dark_red())
        await ctx.respond(embed=embed)

@bot.slash_command(name="zostatok", description="Zostatok na účte")
async def zostatok(ctx):
    balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (str(ctx.author.id),)).fetchone()

    embed = discord.Embed(title=f"Zostatok - {ctx.author}", description=f"{balance[0]}{coinEmoji}")
    
    await ctx.respond(embed=embed)  

@bot.slash_command(name="okradnúť", description="Okradnúť človeka.")
async def okradnut(ctx, cloveka: Option(discord.Member, required=True)):
    try:
        victimBalance = cursor.execute("SELECT balance FROM users WHERE id = ?", (str(cloveka.id),)).fetchone()
    except:
        ctx.respond("Tento človek nemá peňaženku.", ephemeral=True)

    if victimBalance[0] < 750:
        embed = discord.Embed(title="Oplatí sa ti tu vôbec kradnúť?", description="Tento človek je fakt chudobný.")
        await ctx.respond(embed=embed, ephemeral=True)

        return
    
    robberInv = invToList(ctx.author.id)
    victimInv = invToList(cloveka.id)

    robChances = random.randint(1,10)

    otrokAlive = True


    if "patogun" in robberInv and "obrannyotrok" in victimInv:
        if robChances >= 7: # kradez vysla
            robberyPercentage = random.randint(1,10)
        elif robChances >= 4 : # otrok neumrel
            failEmbed = discord.Embed(title=f"Obranný otrok ti zabránil okradnúť {cloveka}", description=f"Krádež ti nevyšla.", color=discord.Colour.dark_red())
            failEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1035114072179490849/1050517109626654740/F8CE3C9A-B5A9-4DC1-8877-37CA6A18296A.png")
    
            robberyPercentage = 0
        else: # otrok umrel
            failEmbed = discord.Embed(title=f"Obranný otrok ti zabránil okradnúť {cloveka}, súboj neprežil.", description=f"Krádež ti nevyšla.", color=discord.Colour.dark_red())
            failEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1035114072179490849/1050517109626654740/F8CE3C9A-B5A9-4DC1-8877-37CA6A18296A.png")
            otrokAlive = False
            robberyPercentage = 0

    elif "obrannyotrok" in victimInv:
        if robChances >= 7:
            robberyPercentage = random.randint(1,10)
        else:
            failEmbed = discord.Embed(title=f"Obranný otrok ti zabránil okradnúť {cloveka}", description=f"Krádež ti nevyšla.", color=discord.Colour.dark_red())
            failEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1035114072179490849/1050517109626654740/F8CE3C9A-B5A9-4DC1-8877-37CA6A18296A.png")
            robberyPercentage = 0
        
    elif "patogun" in robberInv:
        if robChances >= 4:
            robberyPercentage = random.randint(1,10)
        else:
            failEmbed = discord.Embed(title=f"Netrafil si.", description=f"Krádež ti nevyšla.", color=discord.Colour.dark_red())
            failEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1035114072179490849/1050517109400150129/D1985ABD-4382-4392-9E10-5DAF0B8D4BBB.png")
            robberInv.remove("patogun")
            modifyInv(ListToInv(robberInv), ctx.author.id)
            robberyPercentage = 0
    else:
        if robChances >= 6:
            robberyPercentage = random.randint(1,10)
        else:
            failEmbed = discord.Embed(title=f"Nepodarilo sa.", description=f"Krádež ti nevyšla.", color=discord.Colour.dark_red())
            robberyPercentage = 0

    if robberyPercentage <= 6:
        moneyPercentage = random.randint(10, 50)
    else:
        moneyPercentage = random.randint(51, 80)
    
    if robberyPercentage > 0:
        robbed = int(victimBalance[0] * (moneyPercentage / 100))

        changeBalance(cloveka.id, -robbed)
        changeBalance(ctx.author.id, robbed)

        embed = discord.Embed(title=f"Okradol si {cloveka}", description=f"Prišiel o {robbed} {coinEmoji}", color=discord.Colour.dark_green())
        await ctx.respond(embed=embed)

        embed = discord.Embed(title=f"Bol si okradnutý o {robbed} {coinEmoji}", color=discord.Colour.dark_red())
        await cloveka.send(embed=embed)
    else: 
        await ctx.respond(embed=failEmbed)

    if otrokAlive == False:
        victimInv.remove("obrannyotrok")
        modifyInv(ListToInv(victimInv), cloveka.id)

        embed = discord.Embed(title="Tvoj obranný otrok neprežil pokus o krádež.")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1035114072179490849/1050517109626654740/F8CE3C9A-B5A9-4DC1-8877-37CA6A18296A.png")
        await cloveka.send(embed=embed)

        robberInv.remove("patogun")
        modifyInv(ListToInv(robberInv), ctx.author.id)


bot.run(config["token"])
