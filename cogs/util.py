import discord
from discord.ext import commands
from classes.error_handler import *
from roblox_data.helpers import *
from utils import emojis, checks
from utils.logger import *


class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # Runs an SQL query from a message
    @commands.command()
    @checks.is_owner()
    async def sql(self, ctx, message: str):
        result = await self.bot.data_manager.safe_execute_query(message)
        output = ""
        if (result):
            for row in result:
                for item in row:
                    output += str(item) + " "
        else:
            output = "Nothing to send"
        await ctx.send(f"{emojis.mantis} Results: {output}")


    # Displays current tickets in cache
    @commands.command()
    @checks.is_owner()
    async def tickets(self, ctx):
        tickets = await self.bot.data_manager.get_all_channel_ids()
        message = "**Tickets**\n"
        if len(tickets) != 0:
            for key in tickets:
                message += f"<#{key}> {key}\n"
            await ctx.send(f"{message}")
        else:
            await ctx.send("No tickets found!")


    # Displays current messages in cache
    @commands.command()
    @checks.is_owner()
    async def messages(self, ctx):
        output = "**Messages**\n"
        messages = await self.bot.data_manager.get_all_ticket_messages()
        if len(messages) != 0:
            for message in messages:
                output += f"**Ticket Message:**\n- Redis Key Message ID: {message['messageID']}\n- Modmail Message ID: {message['modmail_messageID']}\n- Channel ID: {message['channelID']}\n- Author ID: {message['authorID']}\n- Date: {message['date']}\n- Type: {message['type']}\n"
            await ctx.send(output)
        else:
            await ctx.send("No ticket messages found!")

    
    # Deletes one ticket
    @commands.command()
    @checks.is_owner()
    async def del_ticket(self, ctx, channel: int):
        await self.bot.data_manager.remove_ticket(channel)
        await ctx.send(f"Deleted ticket channel {channel}")


    # Empties tickets cache
    @commands.command()
    @checks.is_owner()
    async def empty_tickets(self, ctx):
        await self.bot.data_manager.empty_tickets()
        await ctx.send("Emptied tickets cache")


    # Empties messages cache
    @commands.command()
    @checks.is_owner()
    async def empty_messages(self, ctx):
        await self.bot.data_manager.empty_messages()
        await ctx.send("Emptied messages cache")


    # Flushes ticket messages to SQL
    @commands.command()
    @checks.is_owner()
    async def flush(self, ctx):
        await self.bot.data_manager.flush_messages()
        await ctx.send("Emptied messages cache")

    
    # Example error
    @commands.command()
    async def error(self, ctx):
        raise BotError("Example of an error occurring")


    # Ping for latency
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"{emojis.mantis} pong! {round(self.bot.latency * 1000,2)} ms")


async def setup(bot):
    await bot.add_cog(Util(bot))
