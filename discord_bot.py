import os
import discord
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
import youtube_dl
import ai_module as ai
from utility import PersistentUtility, PrintColor

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FFMPEG = os.getenv('FFMPEG_PATH')


class ServerSetting:
    def __init__(self, server_id):
        self.server_id = server_id
        self.ai_channels = []
        self.queue = []


def temporary_save():
    PersistentUtility.save_data_to_file(
        filename='server_settings', data=server_settings)
    print(f'{PrintColor.OKBLUE}Saved data, change saving behavior later..{PrintColor.ENDC}')


if __name__ == '__main__':
    server_settings = PersistentUtility.load_data_from_file(
        filename='server_settings', on_empty=dict())

    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(intents=intents, command_prefix='!')

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')
        print('connected to the following guilds: {0}'.format(client.guilds))

        for guild in client.guilds:
            if guild.id not in server_settings:
                server_settings[guild.id] = ServerSetting(guild.id)

        PersistentUtility.save_data_to_file(
            filename='server_settings', data=server_settings)

    @client.event
    async def on_message(message):
        if message.author.id == client.user.id:
            return

        if not message.content.startswith(client.command_prefix) and message.channel.id in server_settings[message.guild.id].ai_channels:
            response = ai.response_from_text(
                message.content, conversation_id=message.channel.id)  # possible synchroneous blocking call? idk how discord handle this
            await message.channel.send(response)

        await client.process_commands(message)
        await message.add_reaction('✅')

    @client.command()
    async def say(ctx, *, args):
        args = args.replace('@', '')
        await ctx.send(args)

    @client.command()
    async def join(ctx):
        channel = ctx.author.voice.channel
        if channel == None:
            await ctx.send('You are not in a voice channel')
            return
        await channel.connect()

    @client.command()
    async def play(ctx, link=None):
        if (link == 'force'):
            channel = ctx.author.voice.channel
            vc = get(client.voice_clients, guild=ctx.guild)
            audio = discord.FFmpegPCMAudio(
                executable=FFMPEG, source='ydl_output')
            vc.play(audio)
            return

        channel = ctx.author.voice.channel
        if channel == None:
            await ctx.send('You are not in a voice channel')
            return
        elif link == None:
            await ctx.send('No link provided')
            return
        vc = get(client.voice_clients, guild=ctx.guild)

        ydl = youtube_dl.YoutubeDL(
            {'format': 'bestaudio', 'noplaylist': 'True', 'outtmpl': 'ydl_output',
             #  'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
             })
        ydl.download([link])
        audio = discord.FFmpegPCMAudio(
            executable=FFMPEG, source='ydl_output')
        vc.play(audio)
        os.remove('ydl_output')

    @client.command()
    async def remove_history(ctx, channel_id=None):
        channel = await check_valid_ai_text_channel(ctx, channel_id)
        ai.memory.remove_history(channel.id)
        await ctx.send(f'<#{channel.id}> history removed')

    @client.command()
    async def add_ai_channel(ctx, channel_id=None):
        channel = await check_valid_ai_text_channel(ctx, channel_id)
        if channel is None:
            return
        elif channel.id in server_settings[ctx.guild.id].ai_channels:
            await ctx.send(f'<#{channel.id}> already added')
            return

        server_settings[ctx.guild.id].ai_channels.append(channel.id)
        await ctx.send(f'<#{channel.id}> added')
        temporary_save()

    @client.command()
    async def remove_ai_channel(ctx, channel_id=None):
        channel = await check_valid_ai_text_channel(ctx, channel_id)
        if channel is None:
            return
        elif channel.id not in server_settings[ctx.guild.id].ai_channels:
            await ctx.send(f'<#{channel.id}> is not in the list')
            return

        server_settings[ctx.guild.id].ai_channels.remove(channel.id)
        await ctx.send(f'<#{channel.id}> removed')
        temporary_save()

    async def check_valid_ai_text_channel(ctx, channel_id):
        if channel_id == None:
            channel_id = ctx.channel.id
        elif channel_id.startswith('<#'):
            channel_id = channel_id[2:-1]

        try:
            channel = await commands.TextChannelConverter().convert(ctx, str(channel_id))
        except commands.ChannelNotFound:
            channel = None

        if channel is None:
            await ctx.send('Invalid channel')
        elif channel.guild.id != ctx.guild.id:
            await ctx.send('Channel is in a different server')

        return channel

    @discord.app_commands.context_menu()
    async def react(interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_message('Very cool message!', ephemeral=True)

    client.run(TOKEN)
