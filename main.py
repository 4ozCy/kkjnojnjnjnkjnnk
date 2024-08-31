import sqlite3
import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
client = commands.Bot(command_prefix='', intents=intents)

conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
                  user_id TEXT,
                  guild_id TEXT,
                  warnings INTEGER)''')

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await member.kick(reason=reason)
        await interaction.response.send_message(f'{member.mention} has been kicked for: {reason}', ephemeral=True)

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await member.ban(reason=reason)
        await interaction.response.send_message(f'{member.mention} has been banned for: {reason}', ephemeral=True)

    @app_commands.command(name="mute", description="Mute a user in the server")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)
        await member.add_roles(mute_role, reason=reason)
        await interaction.response.send_message(f'{member.mention} has been muted for: {reason}', ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute a user in the server")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
        await member.remove_roles(mute_role)
        await interaction.response.send_message(f'{member.mention} has been unmuted', ephemeral=True)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        cursor.execute('SELECT warnings FROM warnings WHERE user_id = ? AND guild_id = ?', (str(member.id), str(interaction.guild.id)))
        row = cursor.fetchone()
        if row:
            warnings = row[0] + 1
            cursor.execute('UPDATE warnings SET warnings = ? WHERE user_id = ? AND guild_id = ?', (warnings, str(member.id), str(interaction.guild.id)))
        else:
            warnings = 1
            cursor.execute('INSERT INTO warnings (user_id, guild_id, warnings) VALUES (?, ?, ?)', (str(member.id), str(interaction.guild.id), warnings))
        conn.commit()
        await interaction.response.send_message(f'{member.mention} has been warned for {reason}. Total warnings: {warnings}', ephemeral=True)

    @app_commands.command(name="warnings", description="Check a user's warning count")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        cursor.execute('SELECT warnings FROM warnings WHERE user_id = ? AND guild_id = ?', (str(member.id), str(interaction.guild.id)))
        row = cursor.fetchone()
        warnings = row[0] if row else 0
        await interaction.response.send_message(f'{member.mention} has {warnings} warning(s).', ephemeral=True)

    @app_commands.command(name="change-status", description="Change the bot status (Dev only)")
    async def change_status(self, interaction: discord.Interaction, activity: str, activity_type: str, status: str):
        dev_id = 1107744228773220473
        if interaction.user.id != dev_id:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return
        activity_type_map = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
        }
        status_type_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }
        await self.bot.change_presence(
            activity=discord.Activity(type=activity_type_map[activity_type.lower()], name=activity),
            status=status_type_map[status.lower()],
        )
        await interaction.response.send_message(f'Bot status updated to: {activity_type.capitalize()} {activity} ({status})', ephemeral=True)

@client.event
async def on_ready():
    await client.tree.sync()
    print(f'Logged in as {client.user}')

client.add_cog(Moderation(client))

client.run(os.getenv('TOKEN'))
