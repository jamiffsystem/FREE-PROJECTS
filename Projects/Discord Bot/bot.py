import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

ALLOWED_CHANNEL_ID = 1390963810675851308
VIP_USERS = {1200145640022356019, 1359484898821279974}
like_request_tracker = {}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

async def call_api(region, uid):
    url = f"https://likebot-ruby.vercel.app/like?uid={uid}&server_name={region}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return "API_ERROR"
                data = await resp.json()
                return data
    except Exception:
        return "API_ERROR"

def gif_url():
    return "https://media.discordapp.net/attachments/1375872056578805771/1382338793079836763/venom_exe_exact_replace.png?ex=685556d2&is=68540552&hm=dd0332a1bd6057054dc73dd533eba7b9df1a00bd7f78830d30444ca4d4ca68ea&=&format=webp&quality=lossless&width=976&height=160"

async def send_processing_embed(interaction):
    embed = discord.Embed(
        title="Please wait...",
        description=f"<@{interaction.user.id}>, your request is being processed.",
        color=0xEFE6C6
    )
    embed.set_image(url=gif_url())
    return await interaction.followup.send(embed=embed, wait=True)

async def edit_embed_with_message(message, title, description, footer_text):
    embed = discord.Embed(
        title=title,
        description=description,
        color=0xEFE6C6
    )
    embed.set_image(url=gif_url())
    embed.set_footer(text=footer_text)
    await message.edit(embed=embed)

@tree.command(name="like", description="Send like request to the panel")
@app_commands.describe(uid="Enter the player UID", server="Select server/region")
@app_commands.choices(server=[
    app_commands.Choice(name="BD", value="BD"),
    app_commands.Choice(name="IND", value="IND"),
    # app_commands.Choice(name="SEA", value="SEA"),
    # app_commands.Choice(name="OTHER", value="OTHER")
])
async def like(interaction: discord.Interaction, uid: str, server: app_commands.Choice[str]):
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("🚫 This channel is not allowed to use this bot!", ephemeral=True)
        return

    region = server.value

    if not uid.isdigit():
        await interaction.response.send_message("❌ Invalid input! UID must be numbers.", ephemeral=True)
        return

    user_id = interaction.user.id
    await interaction.response.defer()

    message = await send_processing_embed(interaction)

    response = await call_api(region, uid)

    if response == "API_ERROR" or not isinstance(response, dict):
        await edit_embed_with_message(message,
            "Like Request Failed",
            f"<@{user_id}>, unable to complete your request right now. Please try again later.",
            "Venom Exe Bot • Request Failed"
        )
        return

    player_name = response.get('PlayerNickname', 'Unknown Player')
    likes_before = response.get('LikesbeforeCommand', '0')
    likes_after = response.get('LikesafterCommand', '0')
    likes_given = int(response.get('LikesGivenByAPI', 0))
    uid_response = response.get('UID', uid)

    if response.get("status") == 1:
        if likes_given == 0:
            await edit_embed_with_message(message,
                "Max Likes Reached",
                f"<@{user_id}>, you have already reached the daily like limit for **{player_name}** (UID: {uid_response}). No additional likes were given.",
                "Venom Exe 2.0"
            )
            return

        if user_id not in VIP_USERS:
            if like_request_tracker.get(user_id):
                await edit_embed_with_message(message,
                    "Max Likes Reached",
                    f"<@{user_id}>, you have already reached the daily like limit for **{player_name}** (UID: {uid_response}).",
                    "Venom Exe Bot • Like Limit Info"
                )
                return
            like_request_tracker[user_id] = True

        embed = discord.Embed(
            description=f"<@{user_id}>, you just sent likes to **{player_name}**\n\n**Please check the following like details:**",
            color=0xEFE6C6
        )
        embed.set_author(name="Hui hui!", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Before", value=f"{likes_before} likes", inline=True)
        embed.add_field(name="After", value=f"{likes_after} likes", inline=True)
        embed.add_field(name="Likes Given", value=f"You got {likes_given} like(s) in your id {uid_response}.", inline=False)
        embed.set_image(url=gif_url())
        embed.set_footer(text="Venom Exe 2.0")
        await message.edit(embed=embed)

    else:
        await edit_embed_with_message(message,
            "Max Likes Reached",
            f"<@{user_id}>, you have already reached the daily like limit for **{player_name}** (UID: {uid_response}).",
            "Venom Exe 2.0 Bot • Like Limit Info"
        )

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await tree.sync()
    except Exception as e:
        print(f"Error syncing commands: {e}")

bot.run(BOT_TOKEN)
