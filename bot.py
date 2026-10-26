import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from commands.recycle import handle_recycle_command

load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="recycle", description="辨識垃圾/回收物照片的材質與回收標誌")
@app_commands.describe(photo="要辨識的照片")
async def recycle(interaction: discord.Interaction, photo: discord.Attachment | None = None):
    await interaction.response.defer()
    reply = await handle_recycle_command(photo)
    await interaction.followup.send(reply)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


if __name__ == "__main__":
    token = os.environ["DISCORD_TOKEN"]
    client.run(token)
