import os
import discord
from discord.utils import get
from discord.ext import commands, voice_recv
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


if __name__ == '__main__':
    # load settings
    server_settings = PersistentUtility.load_data_from_file(
        filename='server_settings', on_empty=dict())

    # init discord bot with intents
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(intents=intents, command_prefix='!')

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')
        print('connected to the following guilds: {0}'.format(client.guilds))

        # check if server settings exist for all joined guilds
        for guild in client.guilds:
            if guild.id not in server_settings:
                server_settings[guild.id] = ServerSetting(guild.id)

        # save server settings, in case new settings were added above
        PersistentUtility.save_data_to_file(
            filename='server_settings', data=server_settings)

    @client.event
    async def on_message(message):
        # ignore message from itself
        if message.author.id == client.user.id:
            return

        # ai / gpt talk
        if not message.content.startswith(client.command_prefix) and message.channel.id in server_settings[message.guild.id].ai_channels:
            response = ai.response_from_text(
                message.content, conversation_id=message.channel.id)  # possible synchroneous blocking call? idk how discord handle this
            await message.channel.send(response)

        # process command
        await client.process_commands(message)
        await message.add_reaction('✅')

    @client.command()
    async def say(ctx, *, args):
        args = args.replace('@', '')
        await ctx.send(args)

    # join a voice channel the user is in
    @client.command()
    async def join(ctx):
        channel = ctx.author.voice.channel
        if channel == None:
            await ctx.send('You are not in a voice channel')
            return
        await channel.connect()

    # play youtube audio
    @client.command()
    async def play(ctx, link=None):
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

    async def check_valid_ai_text_channel(ctx, channel_id):
        # no channel id provided, use current channel
        if channel_id == None:
            channel_id = ctx.channel.id
        # channel mentioned, get raw id
        elif channel_id.startswith('<#'):
            channel_id = channel_id[2:-1]

        # convert to text channel
        try:
            channel = await commands.TextChannelConverter().convert(ctx, str(channel_id))
        except commands.ChannelNotFound:
            channel = None

        if channel is None:
            await ctx.send('Invalid channel')
        elif channel.guild.id != ctx.guild.id:
            await ctx.send('Channel is in a different server')

        return channel

    @client.command()
    async def die(ctx):
        # save server settings
        PersistentUtility.save_data_to_file(
            filename='server_settings', data=server_settings)
        print(
            f'{PrintColor.OKBLUE}Saved data{PrintColor.ENDC}')

        await ctx.bot.close()

    @client.command()
    async def test(ctx):
        def callback(member, packet):
            print(member, packet)
        vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        vc.listen(voice_recv.BasicSink(callback))

    @client.command()
    async def stop(ctx):
        ctx.voice_client.stop_listening()
        await ctx.voice_client.disconnect()

    @discord.app_commands.context_menu()
    async def react(interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_message('Very cool message!', ephemeral=True)

    client.run(TOKEN)
