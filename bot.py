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

# Global State Tracking Dictionaries
infected_users = {}
shielded_users = {} 

# ==========================================
# 1. OUTCAST POWER: !void_eclipse @user
# ==========================================
@bot.command()
@commands.has_role("Outcast")
@commands.cooldown(1, 1800, commands.BucketType.user) # ⏳ 30-minute cooldown
async def void_eclipse(ctx, target: discord.Member):
    survivor_role = discord.utils.get(ctx.guild.roles, name="Survivor")
    if survivor_role not in target.roles:
        await ctx.send("Target is immune to the Eclipse.")
        return

    # 🛡️ INTEGRATED NEW SHIELD CHECK (Fails if shielded)
    if target.id in shielded_users:
        await ctx.send(f"🛡️ **Eclipse Failed!** {target.mention} is currently protected by a Survivor's Shield.")
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
@bot.command()
@commands.has_role("Survivor")
@commands.cooldown(1, 1200, commands.BucketType.user) # ⏳ 20-minute cooldown
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
@commands.cooldown(1, 86400, commands.BucketType.guild) # ⏳ 24-hour global cooldown
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
# 🚀 NEW EXPANDED FACTION COMMANDS
# ==========================================

@bot.command()
@commands.has_role("Outcast")
@commands.cooldown(1, 300, commands.BucketType.user) # ⏳ 5-minute cooldown
async def unveil(ctx):
    """🔮 Tactical Power: Exposes everyone currently suffering from Contagion."""
    try: await ctx.message.delete()
    except: pass
    if not infected_users:
        await ctx.send("🔮 *The Outcast peers into the fog... No active infections found.*")
        return
    mentions = [f"<@{user_id}>" for user_id in infected_users.keys()]
    await ctx.send(f"👁️ **The Outcast unveils the plagues:** {', '.join(mentions)} are currently infected!")

@bot.command()
@commands.has_role("Survivor")
@commands.cooldown(1, 600, commands.BucketType.user) # ⏳ 10-minute cooldown
async def shield(ctx, target: discord.Member):
    """🛡️ Defensive Power: Protects a teammate from the Void Eclipse for 5 minutes."""
    try: await ctx.message.delete()
    except: pass
    shielded_users[target.id] = True
    await ctx.send(f"🛡️ {ctx.author.mention} applied a **Void Shield** to {target.mention} for 5 minutes!")
    await asyncio.sleep(300)
    if target.id in shielded_users:
        del shielded_users[target.id]
        await ctx.send(f"🍃 {target.mention}'s Void Shield has expired.")

@bot.command()
@commands.has_role("Champion")
@commands.cooldown(1, 300, commands.BucketType.user) # ⏳ 5-minute cooldown
async def dispel(ctx, target: discord.Member):
    """🏆 Defensive Power: Instantly removes a text Contagion from a user."""
    try: await ctx.message.delete()
    except: pass
    if target.id in infected_users:
        del infected_users[target.id]
        await ctx.send(f"✨ **The Champion has spoken!** {target.mention} has been cleansed of Contagion.")
    else:
        await ctx.send(f"❌ {target.mention} is not currently infected.")

@bot.command(name="factions")
async def factions_help(ctx):
    """📜 Public Power: Displays an on-demand game guide card."""
    try: await ctx.message.delete()
    except: pass
    
    embed = discord.Embed(
        title="⚔️ FACTION WARFARE PROTOCOL ⚔️", 
        description="Every faction holds one offensive mastery and one strategic counter-play utility.",
        color=discord.Color.from_rgb(114, 137, 218)
    )
    
    embed.add_field(
        name="🔥 OFFENSIVE ABILITIES", 
        value=(
            "**🏆 Champion:** `!total_silence`\n*Mutes all channels for 90s (24h cd)*\n\n"
            "**☣️ Survivor:** `!contagion @user`\n*Deletes target text for 120s (20m cd)*\n\n"
            "**🔮 Outcast:** `!void_eclipse @user`\n*Strips and isolates target for 60s (30m cd)*"
        ), 
        inline=True
    )
    
    embed.add_field(
        name="🛡️ COUNTER-PLAY ACTIONS", 
        value=(
            "**✨ Dispel:** `!dispel @user`\n*Instantly purges contagion (5m cd)*\n\n"
            "**🛡️ Shield:** `!shield @user`\n*Blocks void eclipse for 5 mins (10m cd)*\n\n"
            "**👁️ Unveil:** `!unveil`\n*Reveals active infected list (5m cd)*"
        ), 
        inline=True
    )
    
    embed.set_footer(text="System active across our 4 text channels. Administrator targets remain completely immune.")
    await ctx.send(embed=embed)

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
    if isinstance(error, commands.CommandOnCooldown):
        try: await ctx.message.delete()
        except: pass
        minutes = int(error.retry_after // 60)
        seconds = int(error.retry_after % 60)
        if minutes > 0:
            await ctx.author.send(f"⏳ **Ability Recharging:** You must wait `{minutes}m {seconds}s` before using `!{ctx.command.name}` again.")
        else:
            await ctx.author.send(f"⏳ **Ability Recharging:** You must wait `{seconds}s` before using `!{ctx.command.name}` again.")
        return

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

