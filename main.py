import os
import discord
from discord import app_commands
from discord.ext import commands

# Initialize bot with required intents
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
SOUNDS_DIR = "./sounds"

# Ensure the sounds directory exists
if not os.path.exists(SOUNDS_DIR):
    os.makedirs(SOUNDS_DIR)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Ready to rock the soundboard!")

# 1. /join Command
@bot.tree.command(name="join", description="Make the bot join your voice channel")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("You need to be in a voice channel first!", ephemeral=True)
    
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()
    
    await interaction.response.send_message(f"Joined **{channel.name}**!", ephemeral=True)

# 2. /leave Command
@bot.tree.command(name="leave", description="Make the bot leave the voice channel")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Left the voice channel.", ephemeral=True)
    else:
        await interaction.response.send_message("I'm not currently in a voice channel!", ephemeral=True)

# Autocomplete helper for /playsound
async def sound_autocomplete(interaction: discord.Interaction, current: str):
    if not os.path.exists(SOUNDS_DIR):
        return []
    # Get filenames without extensions
    files = [os.path.splitext(f)[0] for f in os.listdir(SOUNDS_DIR) if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
    return [
        app_commands.Choice(name=sound, value=sound)
        for sound in files if current.lower() in sound.lower()
    ][:25] # Discord limit is 25 choices

# 3. /playsound Command
@bot.tree.command(name="playsound", description="Play a sound from the soundboard")
@app_commands.autocomplete(sound=sound_autocomplete)
async def playsound(interaction: discord.Interaction, sound: str):
    if not interaction.guild.voice_client:
        return await interaction.response.send_message("I need to be in a voice channel first! Use `/join`.", ephemeral=True)
    
    # Locate the sound file with any supported extension
    match_path = None
    for ext in ['.mp3', '.wav', '.ogg', '.m4a']:
        path = os.path.join(SOUNDS_DIR, sound + ext)
        if os.path.exists(path):
            match_path = path
            break
            
    if not match_path:
        return await interaction.response.send_message(f"Could not find sound file for: **{sound}**", ephemeral=True)
        
    vc = interaction.guild.voice_client
    if vc.is_playing():
        vc.stop()
        
    # Note: Ensure FFmpeg is installed in your hosting environment
    source = discord.FFmpegPCMAudio(match_path)
    vc.play(source)
    
    await interaction.response.send_message(f"Playing: **{sound}**", ephemeral=True)

# 4. /addsound Command (Admin Only)
@bot.tree.command(name="addsound", description="Upload a new sound to the soundboard (Admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def addsound(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
        return await interaction.response.send_message("Please upload a valid audio file (.mp3, .wav, .ogg, .m4a).", ephemeral=True)
        
    save_path = os.path.join(SOUNDS_DIR, file.filename)
    await file.save(save_path)
    
    await interaction.response.send_message(f"Successfully added **{file.filename}** to the soundboard!", ephemeral=True)

# Error handler for missing permissions on addsound
@addsound.error
async def addsound_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You do not have permission to use this command. Administrator required.", ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred while running this command.", ephemeral=True)

# Run the bot using your token from environment variables
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
