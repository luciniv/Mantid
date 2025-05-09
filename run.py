import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from classes.data_manager import DataManager
from classes.channel_status import ChannelStatus
from classes.error_handler import *
from utils import emojis, checks
from utils.logger import *


bot_token = os.getenv("BOT_TOKEN")
owners = list(map(int, os.getenv("OWNERS").split(",")))

startup = True
ready = True

class Mantid(commands.Bot):
    def __init__(self):
        # guild, guild_messages, and message_content intents, plus all default intents
        intents = discord.Intents(1 | 512 | 32768)
        description = ""

        # Create bot instance with command prefix
        super().__init__(command_prefix=commands.when_mentioned_or('m!'), intents=intents, description=description, help_command=None)
        self.data_manager = DataManager(self)
        self.channel_status = ChannelStatus(self)


    # Loads cogs when bot is ready
    async def on_ready(self):
        global ready
        global startup

        logger.log("SYSTEM", "------- STARTUP INITIATED ----------------")

        logger.log("SYSTEM", "------- FETCHING DATA --------------------")
        if startup and self.data_manager.db_pool is None:
            try:
                await self.data_manager.connect_to_db()
            except Exception as e:
                ready = False
                logger.critical(f"All database re-connect attempts failed: {e}")
                await self.close()
            if self.data_manager.db_pool is not None:
                await self.data_manager.update_cache()
                await self.data_manager.connect_to_redis()
                await self.data_manager.load_status_dicts_from_redis()
                await self.data_manager.load_timers_from_redis()
                await self.data_manager.load_mods_from_redis()
                await self.channel_status.start_worker()
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for tickets!"))
                heartbeat.start()
            startup = False
        
        logger.log("SYSTEM", "------- LOADING COGS ---------------------")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                 # Attempt to load each cog, ignore if already loaded
                if (f'cogs.{filename[:-3]}') in self.extensions:
                    logger.info(f"Already loaded cog: {filename}")
                else:  
                    try:
                        await bot.load_extension(f'cogs.{filename[:-3]}')
                        logger.success(f"Loaded cog: {filename}")
                    except Exception as e:
                        ready = False
                        logger.exception(f"Failed to load {filename}: {e}")

        # Prints READY ASCII text (duh)          
        if ready:
            logger.log("NOTIF", "\n  ___   ___     _     ___   __   __"
                                "\n | _ \ | __|   /_\   |   \  \ \ / /"
                                "\n |   / | _|   / _ \  | |) |  \ V / "
                                "\n |_|_\ |___| /_/ \_\ |___/    |_|  "
                                "\n                                   ")
            logger.log("SYSTEM", f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        else:
            logger.critical("❌❌❌ Bot experienced core failures: Resolve listed errors before further use ❌❌❌")
            await super().close()


    # Shuts down database, redis, and workers before bot shutdown
    async def on_close(self):
        logger.log("SYSTEM", "------- SHUTTING DOWN --------------------")
        
        heartbeat.cancel()
        await self.channel_status.shutdown()
        await self.data_manager.save_status_dicts_to_redis()
        await self.data_manager.save_timers_to_redis()
        await self.data_manager.save_mods_to_redis()
        await self.data_manager.close_db()
        await self.data_manager.close_redis()
        await super().close()

bot = Mantid()


# Sends a small query every 10 minutes to catch inactivity disconnects
@tasks.loop(minutes=10)
async def heartbeat():
    status = await bot.data_manager.check_db_health()
    if not status:
        if bot.data_manager.db_pool is None:
            await bot.data_manager.connect_to_db()


# Save channel_status dictionaries to cache every 2 minutes
# @tasks.loop(minutes=2)
# async def autosave():
#     await bot.data_manager.save_status_dicts_to_redis()
#     await bot.data_manager.save_timers_to_redis()


# Shuts down the bot (and all workers )
@bot.command(name="shutdown", aliases=["sh"])
@checks.is_owner()
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    logger.log("SYSTEM", "------- SHUTTING DOWN --------------------")

    heartbeat.cancel()
    await bot.channel_status.shutdown()
    await bot.data_manager.save_status_dicts_to_redis()
    await bot.data_manager.save_timers_to_redis()
    await bot.data_manager.save_mods_to_redis()
    await bot.data_manager.close_db()
    await bot.data_manager.close_redis()
    await bot.close()


# Hot-reload cogs command
@bot.command(name="reload", aliases=["r"])
@checks.is_owner()
async def reload(ctx, cog: str):
    try:
        # Unload and load the cog asynchronously
        await bot.unload_extension(f'cogs.{cog}')
        await bot.load_extension(f'cogs.{cog}')
        
        await ctx.send(f"{emojis.mantis} Cog **{cog}** has been reloaded")
        logger.success(f"Reloaded cog: {cog}.py")
    except Exception as e:
        await ctx.send(f"❌ Error reloading cog **{cog}**: {e}")
        logger.error(f"Failed to reload {cog}.py: {e}")


# Sync slash commands
@bot.command(name="sync", aliases=["s"])
@checks.is_owner()
async def sync_commands(ctx):
    message = await ctx.send(f"{emojis.mantis} Syncing global tree...")
    try:
        await bot.wait_until_ready()
        synced = await bot.tree.sync()
        logger.success(f"{bot.user.name} has been synced globally, please wait for Discord's API to update")
    except Exception as e:
        await message.edit(content=f"❌ An error has occurred: {e}")
    else: 
        await message.edit(content=f"{emojis.mantis} Main tree globally synced {len(synced)} commands.") 


# Centralized prefix / hybrid error handling event
@bot.event
async def on_command_error(ctx, error):
    try:
        errorMsg = "❌ An unexpected error occurred. Please try again later"
        
        if (ctx.author.id in owners):
                errorMsg = f"❌ An unexpected error occurred: {error}"

        if isinstance(error, commands.NotOwner):
            errorMsg = "❌ Ownership error: You need ownership of Mantid to use this command"
        
        elif isinstance(error, AccessError):
            errorMsg = f"❌ Access error: {error}"

        elif isinstance(error, BotError):
            errorMsg = "❌ An error occurred. Please try again later"

            if (ctx.author.id in owners):
                errorMsg = f"❌ An error occurred: {error}"
            logger.exception(f"❌ General command error: {error}")

        elif isinstance(error, commands.CommandNotFound):
            errorMsg = "❌ This command does not exist, run /help to view available commands"
        
        else:
            logger.error(f"❌ Unexpected command error: {error}")

        errorEmbed = discord.Embed(title="",
                                description=f"{errorMsg}",
                                color=0xFF0000)
        await ctx.send(embed=errorEmbed, ephemeral=True)

    except discord.errors.NotFound:
        logger.warning("Failed to send error message: Message context no longer exists")


# Centralized application error handling event
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    try:
        errorMsg = "❌ An unexpected error occurred. Please try again later"

        if interaction.user.id in owners:
            errorMsg = f"❌ An unexpected error occurred: {error}"

        if isinstance(error, app_commands.errors.MissingPermissions):
            errorMsg = "❌ You do not have the required permissions to use this command"

        elif isinstance(error, app_commands.errors.CommandNotFound):
            errorMsg = "❌ This command does not exist, run /help to view available commands"

        elif isinstance(error, app_commands.errors.CommandOnCooldown):
            errorMsg = f"❌ This command is on cooldown. Try again in {error.retry_after:.2f} seconds"

        elif isinstance(error, commands.NotOwner):
            errorMsg = "❌ Ownership error: You need ownership of Mantid to use this command"

        elif isinstance(error, AppAccessError):
            errorMsg = f"❌ Access error: {error}"

        elif isinstance(error, BotError):
            errorMsg = "❌ An error occurred. Please try again later"

            if interaction.user.id in owners:
                errorMsg = f"❌ An error occurred: {error}"
            logger.exception(f"❌ General command error: {error}")

        else:
            logger.error(f"❌ Unexpected command error: {error}")

        errorEmbed = discord.Embed(title="", description=errorMsg, color=0xFF0000)

        # Ensure the interaction is still valid before responding
        if interaction.response.is_done():
            await interaction.followup.send(embed=errorEmbed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=errorEmbed, ephemeral=True)

    except discord.errors.NotFound:
        logger.warning("Failed to send error message: Interaction no longer exists.")

    except Exception as e:
        logger.error(f"Unexpected error in on_app_command_error: {e}")


bot.run(bot_token)
