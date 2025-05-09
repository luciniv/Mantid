import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from classes.error_handler import *
from classes.embeds import *
from utils import checks
from utils.logger import *


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # OVERFLOW system
    # @commands.Cog.listener()
    # async def on_guild_channel_create(self, channel):
    #     if (isinstance(channel, discord.TextChannel)):
    #         guild = channel.guild
    #         category = channel.category
    #         new_category = None
    #         overflow_cats = []

    #         # Gets all monitored channels / categories for the guild
    #         search_monitor = [
    #             (channelID) for guildID, channelID, monitorType 
    #             in self.bot.data_manager.monitored_channels
    #             if (guildID == guild.id)]
            
    #         # Guild has no monitored channels
    #         if (len(search_monitor) == 0):
    #             return 
            
    #         # Category is monitored
    #         if category.id in search_monitor:
    #             for cat_channel in category.channels:

    #                 # Category contains modmail channel
    #                 if cat_channel.id in search_monitor:
    #                     if (len(category.channels) >= 45):
                            
    #                         await asyncio.sleep(2)
    #                         print("overflow sql update")
    #                         # Mark channel (ticket) as overflow
    #                         ticket_id = await self.bot.data_manager.get_ticket(channel.id)
    #                         if ticket_id is not None:
    #                             print("got message id")
    #                             query = f"""
    #                                 UPDATE tickets 
    #                                 SET tickets.overflow = 'true'
    #                                 WHERE tickets.messageID = {ticket_id};
    #                                 """
    #                             await self.bot.data_manager.execute_query(query, False)
    #                             print("added to db")
                            
    #                         # Scan for pre-exisitng non-full overflow categories
    #                         categories = guild.categories
    #                         for cat in categories:
    #                             if (((cat.name).split())[0] == "Overflow"):
    #                                 overflow_cats.append(cat)
        
    #                         # Create OVERFLOW 1 category after MODMAIL, move channel there
    #                         if (len(overflow_cats) == 0):
    #                             index = guild.categories.index(category) + 1
    #                             new_category = await guild.create_category(name="Overflow 1", 
    #                                                                     overwrites=category.overwrites,
    #                                                                     position=index)
    #                             await channel.edit(category=new_category)
    #                             await self.bot.data_manager.add_monitor(guild.id, new_category.id, "Overflow category")
    #                             return      
                    
    #                         else:
    #                             cat_id = 1
    #                             for cat in overflow_cats:
    #                                 if (cat_id == int(((cat.name).split())[1])):
    #                                     # if category has space, insert
    #                                     if (len(cat.channels) < 50):
    #                                         await channel.edit(category=cat)
    #                                         return
    #                                     else:
    #                                         cat_id += 1
    #                                 else:
    #                                     # create new category, since there was a gap
    #                                     index = guild.categories.index(cat) - 1
    #                                     new_category = await guild.create_category(name=f"Overflow {cat_id}", 
    #                                                                         overwrites=category.overwrites,
    #                                                                         position=index)
    #                                     await channel.edit(category=new_category)
    #                                     await self.bot.data_manager.add_monitor(guild.id, new_category.id, "Overflow category")
    #                                     return
                                    
    #                             # create new category, since there were no open categories
    #                             index = guild.categories.index(overflow_cats[-1]) + 1
    #                             new_category = await guild.create_category(name=f"Overflow {cat_id}", 
    #                                                                     overwrites=category.overwrites,
    #                                                                     position=index)
    #                             await channel.edit(category=new_category)
    #                             await self.bot.data_manager.add_monitor(guild.id, new_category.id, "Overflow category")

    #                     else:
    #                         # modmail cat isnt full yet
    #                         return
                    

    # Catch deleted overflow categories        
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if (isinstance(channel, discord.TextChannel)):
            if channel.id in self.bot.channel_status.last_update_times:
                del self.bot.channel_status.last_update_times[channel.id]  # Remove the entry from the dictionary
                logger.debug(f"Removed last update time for channel {channel.id}")

        if (isinstance(channel, discord.CategoryChannel)):
            guild = channel.guild

            search_monitor = [
                (channelID) for guildID, channelID, monitorType 
                in self.bot.data_manager.monitored_channels
                if (channelID == channel.id)]
            
            search_categories = [
                (categoryID) for guildID, categoryID, type 
                in self.bot.data_manager.category_types
                if (categoryID == channel.id)]
            
            if (len(search_monitor) != 0):
                await self.bot.data_manager.remove_monitor(channel.id)
                print(f"removed {channel.name} from monitor")

            if (len(search_categories) != 0):
                query = f"""
                    DELETE FROM category_types WHERE 
                    category_types.categoryID = {channel.id};
                    """
                await self.bot.data_manager.execute_query(query, False)
                await self.bot.data_manager.update_cache(2)
                print(f"removed {channel.name} from category types")


    # TYPING system
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if (isinstance(before, discord.TextChannel)):

            if before.category_id != after.category_id:
                ticket_id = await self.bot.data_manager.get_ticket(before.id)
                print("channel changed categories")

                if ticket_id is not None:
                    print("channel is a ticket channel")
                    search_categories = [
                        (type) for guildID, categoryID, type 
                        in self.bot.data_manager.category_types
                        if (categoryID == after.category_id)]
                    
                    if (len(search_categories) != 0):
                        print("channel moved to typed category")
                        query = f"""
                            UPDATE tickets 
                            SET tickets.type = {search_categories[0]}
                            WHERE tickets.messageID = {ticket_id};
                            """
                        await self.bot.data_manager.execute_query(query, False)
                        print(f"updated type in db to {search_categories[0]}")


async def setup(bot):
    await bot.add_cog(Events(bot))
