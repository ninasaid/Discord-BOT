from discord.ext import commands
import discord
import asyncio
import random
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen
import json


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(
    command_prefix="!",  # Change to your desired prefix
    case_insensitive=True,  # Commands aren't case-sensitive
    intents=intents,  # Set up basic permissions
)

bot.author_id = 1166785082250494093  # Change to your Discord ID

# Dictionary to keep track of users' message counts
message_counts = {}

# Dictionary to track when warnings have been sent to users
warning_sent = {}

# Custom message for flood (de)activation confirmation
flood_status_message = "Moderation workflow has been {status}."

# Define bot.flood_detection as a global variable
bot.flood_detection = False

# Dictionary to store active polls and their timers
active_polls = {}

@bot.event
async def on_ready():  # When the bot is ready
    print("I'm in")
    print(bot.user)  # Prints the bot's username and identifier

@bot.command()
async def pong(ctx):
    await ctx.send('pong')

# ... (rest of your commands)

@bot.command()
async def flood(ctx, action=None):
    if action is None:
        await ctx.send("Please provide an action. Use '!flood activate' or '!flood deactivate'.")
        return

    action = action.lower()
    if action not in ("activate", "deactivate"):
        await ctx.send("Invalid action. Use '!flood activate' or '!flood deactivate'.")
        return

    if action == "activate":
        bot.flood_detection = True
        await ctx.send(flood_status_message.format(status="activated"))
        await ctx.send("Flood detection is now active. The bot will monitor message activity.")
        bot.loop.create_task(monitor_flood(ctx))

    if action == "deactivate":
        bot.flood_detection = False
        await ctx.send(flood_status_message.format(status="deactivated"))
        await ctx.send("Flood detection is now deactivated.")

# Function to update message counts and check for excessive messages
async def monitor_flood(ctx):
    while bot.flood_detection:
        threshold = 5  # Lower threshold to 5 messages per minute
        time_frame = 1  # Time frame in minutes (adjust as needed)

        # Make both start_time and last_message_time offset-aware
        start_time = datetime.now(timezone.utc) - timedelta(minutes=time_frame)

        for user in list(message_counts.keys()):
            if message_counts[user]['last_message_time'] < start_time:
                message_counts.pop(user)
                warning_sent.pop(user)

            if message_counts[user]['message_count'] >= threshold:
                member = ctx.guild.get_member(user)
                if member and user not in warning_sent:
                    await ctx.send(f"{member.mention}, please slow down on messages!")
                    warning_sent[user] = True

            message_counts.pop(user)

        await asyncio.sleep(60)

@bot.event
async def on_message(message):
    if message.author.id in message_counts:
        message_counts[message.author.id]['message_count'] += 1
        message_counts[message.author.id]['last_message_time'] = datetime.now(timezone.utc)
    else:
        message_counts[message.author.id] = {
            'message_count': 1,
            'last_message_time': datetime.now(timezone.utc),
        }

    if bot.flood_detection:
        threshold = 5  # Adjust the threshold as needed
        if message_counts[message.author.id]['message_count'] >= threshold and message.author.id not in warning_sent:
            await message.channel.send(f"{message.author.mention}, please slow down on messages!")
            warning_sent[message.author.id] = True

    await bot.process_commands(message)


@bot.command()
async def xkcd(ctx):
    try:
        # Get a random comic number by following the redirection
        random_comic_url = "https://c.xkcd.com/random/comic/"
        response = urlopen(random_comic_url)
        random_comic_num = int(response.url.split("/")[-2])  # Extract the comic number

        # Construct the image URL for the random comic
        xkcd_url = f"https://xkcd.com/{random_comic_num}/info.0.json"
        response = urlopen(xkcd_url)
        data = response.read().decode("utf-8")

        img_url = json.loads(data)["img"]

        await ctx.send(f"{img_url}")
    except Exception as e:
        await ctx.send("Error fetching XKCD comic")

@bot.command()
async def poll(ctx, *, question=None):
    if not question:
        await ctx.send("You should write a question. Example: `!poll Should we get burgers?`")
        return

    if ctx.channel.id in active_polls:
        active_polls[ctx.channel.id].append(await create_poll(ctx, question))
    else:
        active_polls[ctx.channel.id] = [await create_poll(ctx, question)]

async def create_poll(ctx, question):
    mention = "@here"
    poll_message = await ctx.send(f"{mention}\n\n**Poll:** {question}\n\nReact with :thumbsup: or :thumbsdown.")

    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

    return poll_message

# Schedule the result posting and message deletion
async def schedule_poll_result(ctx, poll_message):
    await asyncio.sleep(60)  # Set the time limit for the poll (in seconds)
    if not poll_message.reactions:
        return

    await post_poll_result(ctx, poll_message)
    await poll_message.delete()

async def post_poll_result(ctx, poll_message):
    thumbs_up = 0
    thumbs_down = 0
    for reaction in poll_message.reactions:
        if str(reaction.emoji) == "👍":
            thumbs_up = reaction.count - 1
        elif str(reaction.emoji) == "👎":
            thumbs_down = reaction.count - 1

    await ctx.send(f"**Poll Result:**\n\n**Question:** {poll_message.content}\n\n**Yes (👍):** {thumbs_up}\n**No (👎):** {thumbs_down}")

token = "MTE2Njc4NTQ3NjE5NjMwNjk5NA.GyN1Pc.pAL7nz-ICP2QgpiAdbVEVemvUa0SS4gHjvmLZY"
bot.run(token)  # Starts the bot