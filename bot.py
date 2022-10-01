import discord
import os
import json
from datetime import datetime
import re
import database as db


intents = discord.Intents.all()
bot = discord.Client(intents=intents)

fp = open("./data/userrolemapping.json", "r")
userRoleMapping = json.load(fp=fp)

eventRoleMapping = {
  "Valorant" : 1018184079092482142,
  "NFS" : 1018184145777741847,
  "PARTICIPANT" : 1018184021873803264
}

conn = db.get_connection()


@bot.event
async def on_ready():
  log = open("./data/logs.txt", "a")
  log.write(f"[{datetime.now()}] [bot] : Bot logged in\n")
  log.close()


async def add_role_member(message: discord.message.Message, log):
  guild = bot.get_guild(message.guild.id)
  user = guild.get_member(message.author.id)

  log.write(
    f"[{datetime.now()}] : [{user.name}] \t{message.content} is a PSG Student\n"
  )

  if message.content.upper() in userRoleMapping.keys():

    nickname = f'{userRoleMapping[message.content.upper()]["name"]}'
    if userRoleMapping[message.content.upper()]["event"] != "":
      nickname += " | " + userRoleMapping[message.content.upper()]["event"].replace(" - Nfs","").replace(" - Valorant","").replace(" - Poster Presentation","").replace(" - Paper Presentation","")

    await user.edit(nick=nickname)
    log.write(
      f"[{datetime.now()}] : [{user.name}] \t User Nickname changed from '{user.display_name}' to {nickname}\n"
    )

    await user.edit(roles=[])
    roles = [
      discord.utils.get(guild.roles, id=role_id)
      for role_id in userRoleMapping[message.content.upper()]["roles"]
    ]
    await user.add_roles(*roles,
                         reason=f"Role [{roles}] assigned upon on request")

    log.write(
      f"[{datetime.now()}] : [{user.name}] \t{message.content} added roles {roles}\n"
    )

  else:

    await user.send(
      "Your request cannot be processed. Please contact your Event Coordinator or Admin to gain access"
    )
    log.write(
      f"[{datetime.now()}] : [{user.name}] \t{message.content} Not available in database\n"
    )


async def add_role_participant(message: discord.message.Message, log):

  events = db.get_user_events(message.content, conn)
  guild = bot.get_guild(message.guild.id)
  user = guild.get_member(message.author.id)

  if events:
    roles = [discord.utils.get(guild.roles, id=eventRoleMapping["PARTICIPANT"])]
    if ("laststand-valorant" in events) or "laststand-nfs" in events:
      log.write(
        f"[{datetime.now()}] : [{user.name}] \t`{message.content}` is a Registered Participant\n"
      )

      if "laststand-valorant" in events:
        roles.append(discord.utils.get(guild.roles, id=eventRoleMapping["VALORANT"]))
      if "laststand-nfs" in events:
        roles.append(discord.utils.get(guild.roles, id=eventRoleMapping["NFS"]))

      nickname = db.get_user_name(message.content, conn).title()
      await user.edit(nick=nickname)
      log.write(
        f"[{datetime.now()}] : [{user.name}] \t User Nickname changed from '{user.display_name}' to {nickname}\n"
      )

      await user.add_roles(*roles,
                          reason=f"Role [{roles}] assigned upon on request")
      log.write(
        f"[{datetime.now()}] : [{user.name}] \t{message.content} added roles {roles}\n"
      )
    else:
      nickname = db.get_user_name(message.content, conn).title()
      await user.edit(nick=nickname)
      log.write(
        f"[{datetime.now()}] : [{user.name}] \t User Nickname changed from '{user.display_name}' to {nickname}\n"
      )
      await user.add_roles(*roles,
                          reason=f"Role [{roles}] assigned upon on request")
      log.write(
        f"[{datetime.now()}] : [{user.name}] \t{message.content} added roles {roles}\n"
      )
      log.write(
      f"[{datetime.now()}] : [{user.name}] \t`{message.content}` has Not a Registered for LastStand\n"
      )
      await user.send(
        "Oh oohh!, it seems like you haven't registered for the event Last Stand, Login 2022. Please Register through our website and try again later! If this continues, please contact Server Admin\n\n Website : https://www.psglogin.in\n\nIf you have registered for other events from Login 2022 please join our **Login 2022 Discord Server** at https://discord.com/invite/RTrVjqMYF8"
      )
  else:
    log.write(
      f"[{datetime.now()}] : [{user.name}] \t`{message.content}` is a Not a Registered Participant\n"
    )
    await user.send(
      "Oh oohh!, it seems like you haven't registered for Login 2022. Please Register through our website and try again later! If this continues, please contact Server Admin\n\n Website : https://www.psglogin.in"
    )


@bot.event
async def on_message(message: discord.message.Message):

  log = open("./data/logs.txt", "a")
  if message.author == bot.user:
    return

  if message.content == "pinglogin":
    await message.channel.send("ping success!")

  if message.content == "dumpautologs":
    await message.channel.send(file=discord.File("./data/logs.txt"))
    log.write(
      f"[{datetime.now()}] : [{ message.author.name}] requested log file.\n"
    )

  if message.content.startswith("dumpautologs -t"):
    count = int(message.content.split(" ")[2])
    log_file = open("./data/logs.txt")
    logs = [log for log in log_file]
    send_logs = "```\n" + "\n".join(logs[-count:]) + "\n```"
    await message.channel.send(send_logs)

  if message.channel.id == int(os.environ["CHANNEL_ID"]):
    await message.delete()
    log.write(
      f"[{datetime.now()}] : [{bot.get_user(message.author.id).name}] \tMessage Deleted `{message.content}`\n"
    )
    if re.match(r"\d{2}\w{2}\d+", message.content.upper()):
      await add_role_member(message=message, log=log)
    elif re.match(r".*@\w+\.+\w+", message.content):
      await add_role_participant(message=message, log=log)
    else:
      pass
  log.close()


if __name__ == "__main__":
  # server.start()
  bot.run(os.environ["BOT_TOKEN"])
