import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from classes.error_handler import *
from classes.paginator import *
from utils import emojis, checks
from utils.logger import *


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # Send embed of help guide + server commands
    @commands.hybrid_command(name="help", description="Display Mantid's bio, setup guide, and all commands")
    @checks.has_access()
    async def help(self, ctx):
        pages = []
        bot_user = self.bot.user
        helpEmbed = discord.Embed(title=f"Mantid Help Menu {emojis.mantis}", 
                                        description=f"Mantid is a complimentary analytics bot to Modmail (with the long-term"
                                         " goal of replicating and enhancing Modmail's functionality). Use the buttons below"
                                         " to naviagte through Mantid's help pages.\n\nTo setup Mantid, run `/setup`"
                                         " \n**Move to the next page for Mantid's setup guide --> (WIP)**\n\n**TIP:** Use `/edit_monitor`"
                                         " to add additional Modmail ticket categories for the bot to monitor. Ticket categories"
                                         " generated by Mantid are automatically added (and removed) from the monitor."
                                         " \n\n**Contact <@429711831695753237> for support & suggestions**", 
                                        color=0x3ad407)
        helpEmbed.set_thumbnail(url=bot_user.avatar.url)
        pages.append(helpEmbed)

        for cog_name in self.bot.cogs:
            if cog_name in ["Admin", "Util", "Analytics"]:
                continue

            cog = self.bot.get_cog(cog_name)
            cog_commands = cog.get_commands()
            if len(cog_commands) == 0:
                continue

            page = discord.Embed(title=f"{cog_name} Commands",
                                 description="",
                                 color=0x3ad407)
            page.set_author(name=f"Mantid Help Menu")
            page.set_thumbnail(url=bot_user.avatar.url)

            for command in cog_commands:
                page.add_field(name=f"/{command.name}", 
                                value=command.description, 
                                inline=False)
            pages.append(page)

        for page in range(len(pages)):
            pages[page].set_footer(text=f"Use the buttons below to navigate (Page {page + 1}/{len(pages)})")

        # Create an instance of the pagination view
        view = Paginator(pages)
        view.message = await ctx.send(embed=pages[0], view=view)


    @commands.hybrid_command(name="setup", description="Setup the bot (with steps)")
    @checks.has_access()
    async def setup(self, ctx):
        guild = ctx.guild
        time_now = datetime.now()
        format_time = time_now.strftime("Today at %-I:%M %p")
        bot_user = self.bot.user
           
        setupEmbed = discord.Embed(title=f"Bot Setup {emojis.mantis} ", 
                                description="Run this command to setup or refresh Mantid's monitored channels\n\n"
                                            "To properly record data on Modmail, Mantid requires channel monitors"
                                            " for the #modmail-log channel and any categories used to store Modmail" 
                                            " tickets. Channel monitors are set automatically upon running the"
                                            " command `/setup` or when Mantid generates a category to handle ticket"
                                            " overflow.\n\n- Use the `/edit_monitor` command and select **add** to"
                                            " assign Mantid additional ticket categories to monitor after setup\n"
                                            "- View current monitored channels and categories with `/show`, then select"
                                            " **monitored channels**\n- If Mantid incorrectly adds or is missing a"
                                            " channel in the monitor, use `/edit_monitor` with **add** or **remove**"
                                            f" as needed\n\n**Confirm correct setup by identifying a {emojis.mantis}"
                                            " reaction underneath all new entries in #modmail-log. If this reaction"
                                            " fails to appear, run `/setup` again or contact <@429711831695753237>.\n\n**", 
                                color=0x3ad407)
        setupEmbed.add_field(name="Setup Output:", value=f"", inline=False)
        setupEmbed.set_footer(text=f"Mantid · {format_time}", icon_url=bot_user.avatar.url)

        for channel in guild.channels:
            if (isinstance(channel, discord.DMChannel)):
                pass

            if (isinstance(channel, discord.TextChannel)):
                if (channel.name == "modmail-log"):
                    search_monitor = [
                        (channelID) for guildID, channelID, monitorType 
                        in self.bot.data_manager.monitored_channels if channelID == channel.id]
                    if (len(search_monitor) != 0):
                        setupEmbed.add_field(name="", 
                                            value=f"{emojis.mantis} <#{channel.id}> is already set as this server's **Modmail log**", 
                                            inline=False)
                    else:
                        query = f"""
                            INSERT INTO channel_monitor VALUES 
                            ({guild.id}, 
                            {channel.id}, 
                            'Modmail log');
                            """
                        await self.bot.data_manager.execute_query(query, False)
                        await self.bot.data_manager.update_cache(1)
                        setupEmbed.add_field(name="", 
                                            value=f"{emojis.mantis} Set <#{channel.id}> as this server's **Modmail log**", 
                                            inline=False)
                elif ((channel.name)[-2:] == "-0"):
                    # Modmail format ticket channel (ensure the MODMAIL category check doesnt catch here)
                    this_category = channel.category
                    if ((this_category.name).casefold() == "modmail"):
                        pass
                    else:
                        search_monitor = [
                            (channelID) for guildID, channelID, monitorType 
                            in self.bot.data_manager.monitored_channels if channelID == this_category.id]
                        if (len(search_monitor) != 0):
                            setupEmbed.add_field(name="", 
                                                value=f"{emojis.mantis} **<#{this_category.id}>** is already set as a **Tickets Category**", 
                                                inline=False)
                        else:
                            query = f"""
                                INSERT INTO channel_monitor VALUES 
                                ({guild.id}, 
                                {this_category.id}, 
                                'Tickets category');
                                """
                            await self.bot.data_manager.execute_query(query, False)
                            await self.bot.data_manager.update_cache(1)
                            setupEmbed.add_field(name="", 
                                                value=f"{emojis.mantis} Set **<#{this_category.id}>** as a **Tickets Category**", 
                                                inline=False)

            if (isinstance(channel, discord.CategoryChannel)):
                if ((channel.name).casefold() == "modmail"):
                    search_monitor = [
                        (channelID) for guildID, channelID, monitorType 
                        in self.bot.data_manager.monitored_channels if channelID == channel.id]
                    if (len(search_monitor) != 0):
                        setupEmbed.add_field(name="", 
                                            value=f"{emojis.mantis} **<#{channel.id}>** is already set as a **Tickets Category**", 
                                            inline=False)
                    else:
                        query = f"""
                            INSERT INTO channel_monitor VALUES 
                            ({guild.id}, 
                            {channel.id}, 
                            'Tickets category');
                            """
                        await self.bot.data_manager.execute_query(query, False)
                        await self.bot.data_manager.update_cache(1)
                        setupEmbed.add_field(name="", 
                                            value=f"{emojis.mantis} Set **<#{channel.id}>** as a **Tickets Category**", 
                                            inline=False)
        await ctx.send(embed=setupEmbed)


    @commands.hybrid_command(name="show", description="List this server's role permissions or monitored channels and categories")
    @checks.has_access()
    @app_commands.describe(selection="Select list to show (server role permissions or monitored channels)")
    @app_commands.choices(selection=[
        app_commands.Choice(name="role permissions", value="role permissions"),
        app_commands.Choice(name="monitored channels", value="monitored channels")])
    async def show(self, ctx, selection: discord.app_commands.Choice[str]):
        try:
            choice = selection.value
            this_guildID = ctx.guild.id
            guildName = (self.bot.get_guild(this_guildID)).name
            time_now = datetime.now()
            format_time = time_now.strftime("Today at %-I:%M %p")
            bot_user = self.bot.user

            if (choice == "role permissions"):
                search_access = [
                    (roleID, permLevel) for guildID, roleID, permLevel 
                    in self.bot.data_manager.access_roles if guildID == this_guildID]
                permsEmbed = discord.Embed(title=f"Server Role Permissions {emojis.mantis} ", 
                                        description=f"Roles with access to Mantid in: **{guildName}** ({this_guildID})", 
                                        color=0x3ad407)
                permsEmbed.set_footer(text=f"Mantid · {format_time}", icon_url=bot_user.avatar.url)
                search_access[20]
                if not search_access:
                    permsEmbed.description=""
                    permsEmbed.color=0xFF0000
                    permsEmbed.add_field(name="", 
                                        value="No permissions set, run **/edit permissions** to add one", 
                                        inline=False)
                else:
                    for row in search_access:
                        permsEmbed.add_field(name="", 
                                            value=f"<@&{row[0]}> - **{row[1]}**", 
                                            inline=False)
                
                await ctx.send(embed=permsEmbed)
            
            if (choice == "monitored channels"):
                search_monitor = [
                    (channelID, monitorType) for guildID, channelID, monitorType 
                    in self.bot.data_manager.monitored_channels if guildID == this_guildID]
                monitorEmbed = discord.Embed(title=f"Server Monitored Channels {emojis.mantis} ", 
                                            description=f"Channels monitored in: **{guildName}** ({this_guildID})", 
                                            color=0x3ad407)
                monitorEmbed.set_footer(text=f"Mantid · {format_time}", icon_url=bot_user.avatar.url)
                
                if not search_monitor:
                    monitorEmbed.description=""
                    monitorEmbed.color=0xFF0000
                    monitorEmbed.add_field(name="", 
                                        value="No channels set, run **/edit monitor** to add one", 
                                        inline=False)
                else:
                    for row in search_monitor:
                        monitorEmbed.add_field(name="", 
                                            value=f"<#{row[0]}> - **{row[1]}**", 
                                            inline=False)
                
                await ctx.send(embed=monitorEmbed)

        except Exception as e:
                raise BotError(f"/show sent an error: {e}")


    @commands.hybrid_command(name="edit_permissions", description="Add or remove roles that can use Mantid in this"
                                                                  " server (toggles the Bot Admin permission)")
    @checks.has_access()
    @app_commands.describe(action="Desired edit action. Use 'add' to grant permissions and 'remove' to delete them")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove")])
    @app_commands.describe(role="Selected role")
    async def edit_permissions(self, ctx, action: discord.app_commands.Choice[str], role: discord.Role):
        this_guildID = ctx.guild.id
        choice = action.value
        this_roleID = role.id
        time_now = datetime.now()
        format_time = time_now.strftime("Today at %-I:%M %p")
        bot_user = self.bot.user

        editEmbed = discord.Embed(title=f"Edit Results {emojis.mantis}", 
                                  description="", 
                                  color=0x3ad407)
        editEmbed.set_footer(text=f"Mantid · {format_time}", icon_url=bot_user.avatar.url)

        # check if access is already given, if not add it
        if (choice == "add"):
            search_access = [
                (roleID, permLevel) for guildID, roleID, permLevel 
                in self.bot.data_manager.access_roles if (roleID == this_roleID)]
            if (search_access):
                perm = search_access[0][1]
                editEmbed.description=f"Unable to add permissions, <@&{this_roleID}> already has **{perm}**"
                editEmbed.color=0xFF0000
            else:
                query = f"""
                    INSERT INTO permissions VALUES 
                    ({this_guildID}, 
                    {this_roleID}, 
                    'Bot Admin');
                    """
                await self.bot.data_manager.execute_query(query, False)
                await self.bot.data_manager.update_cache(0)
                editEmbed.description=f"Added **Bot Admin** permissions to <@&{this_roleID}>"

        # check if user has access, if not do nothing
        if (choice == "remove"):
            search_access = [
                roleID for guildID, roleID, permLevel 
                in self.bot.data_manager.access_roles if (roleID == this_roleID)]
            if (search_access):
                query = f"""
                    DELETE FROM permissions WHERE 
                    (permissions.roleID = {this_roleID});
                    """
                await self.bot.data_manager.execute_query(query, False)
                await self.bot.data_manager.update_cache(0)
                editEmbed.description=f"Removed **Bot Admin** permissions from <@&{this_roleID}>"
            else:
                editEmbed.description=f"Unable to remove permissions, <@&{this_roleID}> does not have access"
                editEmbed.color=0xFF0000

        await ctx.send(embed=editEmbed)


    @commands.hybrid_command(name="edit_monitor", description="Add or remove monitored modmail-log"
                                                              " channels and tickets categories in this server")
    @checks.has_access()
    @app_commands.describe(action="Desired edit action. Use 'add' to add channels / categories and 'remove' to remove them")
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove")])
    @app_commands.describe(channel="Modmail channel")
    @app_commands.describe(category="Tickets category")
    async def edit_monitor(self, ctx, action: discord.app_commands.Choice[str], 
                           channel: discord.TextChannel = None, 
                           category: discord.CategoryChannel = None):
        this_guildID = ctx.guild.id
        choice = action.value
        this_channelID = None
        this_categoryID = None
        time_now = datetime.now()
        format_time = time_now.strftime("Today at %-I:%M %p")
        bot_user = self.bot.user

        if channel is None and category is None:
            errorEmbed = discord.Embed(title=f"", 
                                       description="❌ You must provide at least a channel or category", 
                                       color=0xFF0000)
            errorEmbed.set_footer(text=f"Mantid · {format_time}", icon_url=bot_user.avatar.url)

            await ctx.send(embed=errorEmbed, ephemeral=True)
            return

        if channel is not None:
            this_channelID = channel.id
        if category is not None:
            this_categoryID = category.id

        editEmbed = discord.Embed(title=f"Edit Results {emojis.mantis}", 
                                  description="", 
                                  color=0x3ad407)
        editEmbed.set_footer(text=f"Mantid · {format_time}", icon_url=bot_user.avatar.url)

        # check if channel / category is already added or not
        if (choice == "add"):
            if (this_channelID is not None):
                search_monitor = [
                    (channelID) for guildID, channelID, monitorType 
                    in self.bot.data_manager.monitored_channels if (guildID == this_guildID and monitorType == "Modmail log")]
                if (search_monitor):
                    if (search_monitor[0] == this_channelID):
                        editEmbed.description=f"Unable to add channel, <#{this_channelID}> is already set as **Modmail log**"
                        editEmbed.color=0xFF0000
                    elif (search_monitor[0] != this_channelID):
                        editEmbed.description=(f"Unable to add channel, <#{search_monitor[0]}> is already set as this server's"
                                              " **Modmail log** \n\n(run **/edit monitor remove channel** to remove this set"
                                              " channel before attempting to add a new one)")
                        editEmbed.color=0xFF0000
                else:
                    query = f"""
                        INSERT INTO channel_monitor VALUES 
                        ({this_guildID}, 
                        {this_channelID}, 
                        'Modmail log');
                        """
                    await self.bot.data_manager.execute_query(query, False)
                    await self.bot.data_manager.update_cache(1)
                    # await 
                    editEmbed.description=f"Set <#{this_channelID}> as **Modmail log** channel"
                await ctx.send(embed=editEmbed)

            if (this_categoryID is not None):
                search_monitor = [
                    (channelID) for guildID, channelID, monitorType 
                    in self.bot.data_manager.monitored_channels if (channelID == this_categoryID and monitorType == "Tickets category")]
                if (search_monitor):
                    editEmbed.description=f"Unable to add category, __{this_categoryID}__ is already set as a **Tickets category**"
                    editEmbed.color=0xFF0000
                else:
                    query = f"""
                        INSERT INTO channel_monitor VALUES 
                        ({this_guildID}, 
                        {this_categoryID}, 
                        'Tickets category');
                        """
                    await self.bot.data_manager.execute_query(query, False)
                    await self.bot.data_manager.update_cache(1)
                    editEmbed.description=f"Set __{this_categoryID}__ as a **Tickets category**"
                await ctx.send(embed=editEmbed)

        # check if channel / category is already removed or not
        if (choice == "remove"):
            if (this_channelID is not None):
                search_monitor = [
                    (channelID) for guildID, channelID, monitorType 
                    in self.bot.data_manager.monitored_channels if (channelID == this_channelID and monitorType == "Modmail log")]
                if (search_monitor):
                    query = f"""
                        DELETE FROM channel_monitor WHERE 
                        ((channel_monitor.channelID = {this_channelID}) AND 
                        (channel_monitor.monitorType = 'Modmail log'));
                        """
                    await self.bot.data_manager.execute_query(query, False)
                    await self.bot.data_manager.update_cache(1)
                    editEmbed.description=f"Removed **Modmail log** status from <#{this_channelID}>"
                else:
                    editEmbed.description=f"Unable to remove channel, <#{this_channelID}> is not a **Modmail log** channel"
                    editEmbed.color=0xFF0000
                await ctx.send(embed=editEmbed)

            if (this_categoryID is not None):
                search_monitor = [
                    (channelID) for guildID, channelID, monitorType 
                    in self.bot.data_manager.monitored_channels if (channelID == this_categoryID and monitorType == "Tickets category")]
                if (search_monitor):
                    query = f"""
                        DELETE FROM channel_monitor WHERE 
                        ((channel_monitor.channelID = {this_categoryID}) AND 
                        (channel_monitor.monitorType = 'Tickets category'));
                        """
                    await self.bot.data_manager.execute_query(query, False)
                    await self.bot.data_manager.update_cache(1)
                    editEmbed.description=f"Removed **Tickets category** status from <#{this_categoryID}>"
                else:
                    editEmbed.description=f"Unable to remove category, <#{this_categoryID}> is not a **Tickets category**"
                    editEmbed.color=0xFF0000
                await ctx.send(embed=editEmbed)


async def setup(bot):
    await bot.add_cog(Main(bot))