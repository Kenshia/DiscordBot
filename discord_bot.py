import os
import discord
from discord.utils import get
from discord.ext import commands
# from discord.ext import voice_recv
from dotenv import load_dotenv
import asyncio
import yt_dlp
import ai_module as ai
from utility import PersistentUtility, PrintColor

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# youtube dl requires ffmpeg, use youtube_dl at your own risk
FFMPEG_PATH = os.getenv('FFMPEG_PATH')


class ServerSetting:
    def __init__(self, server_id):
        self.server_id = server_id
        self.ai_channels = []
        self.talk_channel = None | int
        self.play_queue = []
        self.playing = None | str


if __name__ == '__main__':
    ACTIVE = False

    # load settings
    server_settings = PersistentUtility.load_data_from_file(
        filename='server_settings', on_empty=dict())

    # init discord bot with intents
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(intents=intents, command_prefix='!')

    @client.event
    async def on_ready():
        global ACTIVE
        ACTIVE = True

        print(f'{client.user} has connected to Discord!')
        print('connected to the following guilds: {0}'.format(client.guilds))

        # check if server settings exist for all joined guilds
        for guild in client.guilds:
            if guild.id not in server_settings:
                server_settings[guild.id] = ServerSetting(guild.id)
            server_settings[guild.id].talk_channel = None

        # save server settings, in case new settings were added above
        PersistentUtility.save_data_to_file(
            filename='server_settings', data=server_settings)

    @client.event
    async def on_message(message):
        # ignore message from itself
        if message.author.id == client.user.id:
            return

        # message is not a command
        if not message.content.startswith(client.command_prefix):
            # in normal chat channel
            if message.channel.id in server_settings[message.guild.id].ai_channels:
                response = ai.response_from_text(
                    message.content, conversation_id=message.channel.id)
                await message.channel.send(response)
            # in talk channel
            if message.channel.id == server_settings[message.guild.id].talk_channel:
                response = ai.response_from_text(
                    message.content, conversation_id=message.channel.id)
                await message.channel.send(response)
                voice_data = ai.get_voice_from_text(response)

                # send voice data to voice channel
                vc = get(client.voice_clients, guild=message.guild)
                await send_audio_data(audio_data=voice_data, vc=vc)
        else:
            await client.process_commands(message)

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

        filename = link.split('/')[-1]
        if filename.startswith('watch?'):
            filename = filename[8:]
            filename = filename[:filename.index('&')]

        vc = get(client.voice_clients, guild=ctx.guild)
        if vc is None:
            await channel.connect()
            vc = get(client.voice_clients, guild=ctx.guild)

        ydl = yt_dlp.YoutubeDL(
            {'format': 'bestaudio', 'noplaylist': 'True', 'outtmpl': f'Data/Youtube/{filename}',
             #  'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
             })

        if os.path.exists(f'Data/Youtube/{filename}'):
            await ctx.send(f'{filename} in storage')
        else:
            await ctx.send(f'{filename} downloading')
            await asyncio.get_event_loop().run_in_executor(None, ydl.download, [link])
            await ctx.send(f'{filename} downloaded')

        audio = discord.FFmpegPCMAudio(
            executable=FFMPEG_PATH, source=f'Data/Youtube/{filename}')

        server_settings[ctx.guild.id].play_queue.append((audio, filename))

        if vc.is_playing():
            return
        while len(server_settings[ctx.guild.id].play_queue) > 0:
            audio, filename = server_settings[ctx.guild.id].play_queue.pop(0)
            server_settings[ctx.guild.id].playing = filename
            vc.play(audio)
            await ctx.send(f'playing: {filename}')
            while vc.is_playing():
                await asyncio.sleep(1)

        server_settings[ctx.guild.id].playing = None
        await vc.disconnect()

    @client.command()
    async def skip(ctx):
        vc = get(client.voice_clients, guild=ctx.guild)
        if vc is None:
            await ctx.send('not in a voice channel')
        elif vc.is_playing():
            vc.stop()
        else:
            await ctx.send('nothing is playing')

    @client.command()
    async def queue(ctx):
        result = f'Playing: {server_settings[ctx.guild.id].playing}\n'
        for i, (audio, filename) in enumerate(server_settings[ctx.guild.id].play_queue):
            result += f'{i}: {filename}\n'
        await ctx.send(result)

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
        elif isinstance(channel_id, str) and channel_id.startswith('<#'):
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
        global ACTIVE
        ACTIVE = False

        for guild_id in server_settings:
            server_settings[guild_id].talk_channel = None
            server_settings[guild_id].playing = None

        # save server settings
        PersistentUtility.save_data_to_file(
            filename='server_settings', data=server_settings)
        print(
            f'{PrintColor.OKBLUE}Saved data{PrintColor.ENDC}')

        await ctx.bot.close()

    # abandoned voice listening packet, received packet is in proprietary format?
    # @client.command()
    # async def listen(ctx):
    #     recognizer = ai.VoiceRecognizerThread()

    #     def callback(user, packet: voice_recv.rtp.RTPPacket):
    #         recognizer.incoming_packet(packet)

    #         print(packet)
    #         print(packet.header)
    #         print(packet.decrypted_data)
    #         print(packet.extension)
    #         print(packet.extension_data)
    #         print()

    #         # audio callback
    #         # vc: discord.voice_client = get(
    #         #     client.voice_clients, guild=ctx.guild)
    #         # vc.send_audio_packet(packet.decrypted_data, encode=False)

    #     vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
    #     vc.listen(voice_recv.BasicSink(callback))

    async def send_audio_data(audio_data, vc: discord.voice_client):
        encoder = discord.opus.Encoder()
        frame_size = 960*4

        while len(audio_data) % frame_size != 0:
            audio_data += b'\x00'

        for i in range(0, len(audio_data), frame_size):
            chunk = audio_data[i:i+frame_size]
            encoded_chunk = encoder.encode(chunk, int(frame_size/4))
            vc.send_audio_packet(encoded_chunk, encode=False)
            await asyncio.sleep(20/1000)

    @client.command()
    async def stop(ctx):
        vc: discord.voice_client = get(client.voice_clients, guild=ctx.guild)
        await vc.disconnect()

        server_settings[ctx.guild.id].playing = None

        if server_settings[ctx.guild.id].talk_channel is not None:
            ai.memory.remove_history(
                server_settings[ctx.guild.id].talk_channel)
        server_settings[ctx.guild.id].talk_channel = None

    @client.command()
    async def talk(ctx):
        try:
            channel = await commands.VoiceChannelConverter().convert(ctx, str(ctx.channel.id))
        except commands.ChannelNotFound:
            channel = None

        if channel is None:
            await ctx.send('Not in a voice channel')
            return

        vc = await ctx.author.voice.channel.connect()
        server_settings[ctx.guild.id].talk_channel = ctx.channel.id

    client.run(TOKEN)
    # client.run(os.getenv('DISCORD_TOKEN2'))
