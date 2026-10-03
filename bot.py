import os
import asyncio
import discord
from discord.ext import commands

# ==========================================
# BOT INITIALIZATION
# ==========================================
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is online and ready.')

# ==========================================
# 1. OUTCAST POWER: !void_eclipse @user
# ==========================================
@bot.command()
@commands.has_role("Outcast")
async def void_eclipse(ctx, target: discord.Member):
    survivor_role = discord.utils.get(ctx.guild.roles, name="Survivor")
    if survivor_role not in target.roles:
        await ctx.send("Target is immune to the Eclipse.")
        return

    await ctx.message.delete()
    await ctx.send(f"Void Eclipse initiated for {target.mention}.")

    saved_roles = [role for role in target.roles if role.name != "@everyone"]
    await target.remove_roles(*saved_roles)

    eclipse_channel = await ctx.guild.create_text_channel(
        name=f"void-{target.name}",
        overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            target: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
    )
    
    await eclipse_channel.send(f"{target.mention} has been moved to the void channel for 60 seconds.")

    await asyncio.sleep(60)
    await eclipse_channel.delete()
    await target.add_roles(*saved_roles)
    await ctx.send(f"The Eclipse has passed. {target.mention} has returned.")

# ==========================================
# 2. SURVIVOR POWER: !contagion @user
# ==========================================
infected_users = {}

@bot.command()
@commands.has_role("Survivor")
async def contagion(ctx, target: discord.Member):
    await ctx.message.delete()
    if target == ctx.author:
        return

    await ctx.send(f"Contagion status effect applied to {target.mention}.")
    infected_users[target.id] = True
    await asyncio.sleep(120)
    
    if target.id in infected_users:
        del infected_users[target.id]
        await ctx.send(f"{target.mention}'s status has returned to normal.")

# ==========================================
# 3. CHAMPION POWER: !total_silence
# ==========================================
@bot.command()
@commands.has_role("Champion")
async def total_silence(ctx):
    await ctx.message.delete()
    await ctx.send(f"Total silence initiated by the Champion.")

    locked_channels = []
    for channel in ctx.guild.text_channels:
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is not False:
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            locked_channels.append(channel)

    await asyncio.sleep(90)

    for channel in locked_channels:
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    await ctx.send("Silence period has concluded. Text channels restored.")

# ==========================================
# 4. EVENTS & ERROR HANDLING
# ==========================================
@bot.event
async def on_message(message):
    if message.author.id in infected_users and not message.content.startswith("!"):
        try:
            await message.delete()
            await message.channel.send(f"**{message.author.display_name}**: Text muted due to status effect.")
        except:
            pass
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.author.send("Access denied: Required role missing.")

# ==========================================
# 5. SAFE STARTUP EXECUTION
# ==========================================
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("ERROR: DISCORD_TOKEN environment variable is completely empty!")
