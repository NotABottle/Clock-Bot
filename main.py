import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
import datetime
import webserver

load_dotenv()
DISCORD_TOKEN=os.environ["discordkey"]
CLOCKED_IN_ROLE = "Clocked In"
CLOCKED_OUT_ROLE = "Clocked Out"
ADMIN_ROLE = "Admin"
ENTRY_REQUEST_CHANNEL = "entry-requests"
GUILD_ID = 1445493059021308079


# handler = logging.FileHandler(filename = "discord.log", encoding= "utf-8", mode = "w")
handler = logging.StreamHandler()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix = "!", intents = intents)

@tasks.loop(time = datetime.time(hour = 7))
async def daily_task():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return
    
    clockedIn = discord.utils.get(guild.roles, name = CLOCKED_IN_ROLE)
    clockedOut = discord.utils.get(guild.roles, name = CLOCKED_OUT_ROLE)

    for member in guild.members:
        if member.get_role(clockedIn.id):
            await member.add_roles(clockedOut)
            await member.remove_roles(clockedIn)

@bot.event
async def on_ready():
    bot.add_view(MyView())

    guild = bot.get_guild(GUILD_ID)
    if guild:
        await guild.chunk()

    if not daily_task.is_running():
        daily_task.start()

    print(f"Logged in as {bot.user}")

@bot.command()
@commands.has_role(ADMIN_ROLE)
async def button(ctx):
    await ctx.message.delete()
    view = MyView()
    await ctx.send("", view = view)
    pass

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)

    @discord.ui.button(label = "Clock In",
                       style = discord.ButtonStyle.green,
                       custom_id = "check_in_button")
    async def clock_in_button(self,
                     interaction: discord.Interaction,
                     button: discord.ui.Button):
        #Clock in logic
        clockedIn = discord.utils.get(interaction.guild.roles, name = CLOCKED_IN_ROLE)
        clockedOut = discord.utils.get(interaction.guild.roles, name = CLOCKED_OUT_ROLE)

        if interaction.user.get_role(clockedIn.id):
            await interaction.response.send_message(f"{interaction.user.mention} - You're already clocked in!", ephemeral = True)
        else:
            if clockedIn and clockedOut:
                await interaction.user.add_roles(clockedIn)
                await interaction.user.remove_roles(clockedOut)
                await interaction.response.send_message(f"{interaction.user.mention} - You have now clocked in!", ephemeral = True)

    @discord.ui.button(label = "Clock Out",
                       style = discord.ButtonStyle.red,
                       custom_id = "check_out_button")
    async def clock_out_button(self,
                               interaction: discord.Interaction,
                               button: discord.ui.Button):
        #Clock out logic
        clockedIn = discord.utils.get(interaction.guild.roles, name = CLOCKED_IN_ROLE)
        clockedOut = discord.utils.get(interaction.guild.roles, name = CLOCKED_OUT_ROLE)

        if interaction.user.get_role(clockedOut.id):
            await interaction.response.send_message(f"{interaction.user.mention} - You're already clocked out!", ephemeral = True)
        else:
            if clockedIn and clockedOut:
                await interaction.user.add_roles(clockedOut)
                await interaction.user.remove_roles(clockedIn)
                await interaction.response.send_message(f"{interaction.user.mention} - You have now clocked out!", ephemeral = True)

    @discord.ui.button(label = "Request Entry",
                       style = discord.ButtonStyle.blurple,
                       custom_id = "request_entry_button")
    async def request_entry_button(self,
                                   interaction: discord.Interaction,
                                   button: discord.ui.Button):
        #Request entry logic
        clockedIn = discord.utils.get(interaction.guild.roles, name = CLOCKED_IN_ROLE)
        entryRequest = discord.utils.get(interaction.guild.text_channels, name = ENTRY_REQUEST_CHANNEL)

        if entryRequest is None:
            print("No channel found")

        if(len(clockedIn.members) == 0):
            await interaction.response.send_message(f"It seems nobody is clocked in!", ephemeral = True)
            return
        else:
            #Ping the role
            await entryRequest.send(f"{clockedIn.mention} - {interaction.user.display_name} has requested access to the building.")

            #Send them a dm
            for member in interaction.guild.members:
                if member.get_role(clockedIn.id):
                    await member.send(f"Hey {member.mention}! {interaction.user.display_name} has requested access to the building. If you're available, please let them know in #entry-requests")
                    pass

# webserver.keep_alive()
bot.run(DISCORD_TOKEN, log_handler = handler, log_level = logging.DEBUG)

