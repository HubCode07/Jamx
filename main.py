import discord
import random
from discord.ext import commands
from datetime import datetime, timedelta
import openai
from pathlib import Path
import asyncio
from PIL import Image
import requests
from io import BytesIO
import requests
import os
from googleapiclient.discovery import build
import asyncio
import re
from textblob import TextBlob
from discord.ext import commands
from pathlib import Path
from discord import File 
import tempfile
import time

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
openai.api_key = ""
confessions = []
user_trees = {}

COOLDOWN_DURATION = 43200  # 12 hours in seconds
EASY_COOLDOWN_DURATION = 7200  # 2 hours in seconds
HARDCORE_COOLDOWN_DURATION = 86400 #24 hours in seconds

@client.event
async def on_ready():
    print(f"Bot is ready! Connected to guilds:")
    for guild in client.guilds:
        print(f"- {guild.name}")

last_used = {}

async def award_role(ctx, role):
    if role and not (role.permissions.administrator or role.permissions.manage_guild):
        await ctx.author.add_roles(role)
        await ctx.send(f"Congratulations! You've been awarded the {role.name} role! You cannot use this bot for 16 hours.")
    else:
        await ctx.send("Role not found or unauthorized.")

async def award_reward(ctx, reward):
    await ctx.send(f"You got {reward}!")

#medium_jambox

@client.command()
@commands.cooldown(1, COOLDOWN_DURATION, commands.BucketType.user)
async def jam_box(ctx, count: int = 4):
    role_names = [role.name for role in ctx.guild.roles if not role.managed and role.name != "@everyone"]

    if count < 1 or count > len(role_names):
        await ctx.send("Invalid number of roles")
        return

    random_roles = random.sample(role_names, count)

    embed = discord.Embed(
        title="Potential Jam Box Rewards",
        description="Here are the roles you could have gotten:",
        color=0x00ffff
    )

    for role_name in random_roles:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            embed.add_field(name=role.name, value=role.mention, inline=True)

    await ctx.send(embed=embed)

    roll = random.uniform(0, 1)

    if roll <= 0.14:  # Legendary: 14%
        rarity = "Epic"
    elif roll <= 0.93:  # Super Rare: 33% (14% + 20% + 26% + 33%)
        rarity = "Super Rare"
    elif roll <= 1.0:  # Rare: 35% (14% + 20% + 26% + 33% + 35%)
        rarity = "Rare"
    else:
        # Adjust the reward distributions according to the new percentages
        coins = random.choice(["900 Jam Coins", "250 Jam Coins", "20 Jam Coins", "500 Jam Coins"])
        await ctx.send(f"You got {coins}!")
        last_used[ctx.author.id] = datetime.utcnow()
        return

    possible_roles = [name for name in role_names if rarity in name]
    if possible_roles:
        role_name = random.choice(possible_roles)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await award_role(ctx, role)

    last_used[ctx.author.id] = datetime.utcnow()

async def award_role(ctx, role):
    if role and not (role.permissions.administrator or role.permissions.manage_guild):
        await ctx.author.add_roles(role)
        await ctx.send(f"Congratulations! You've been awarded the {role.name} role! You cannot use this bot for 16 hours.")
    else:
        await ctx.send("Role not found or unauthorized.")
    ad_embed = discord.Embed(
        title="Jamify Advertisement",
        description="People with premium do not have to deal with ads. Get Anime+ ($2 Per Month) or Landscape ($5 Per Month). These funds will go into our project. Nitro users get Anime+ for free!",
        color=0xadb384,
        url="https://textboxstudio.my.canva.site/jamify-home"
    )
    await ctx.send(embed=ad_embed)

#About Section
@client.command()
async def about(ctx):
    embed = discord.Embed(title="About", description="This is a futuristic Chat bot that will soon be able to execute AI commands")
    embed.add_field(name="Product", value="Jamify Bot (2023-2024)")
    embed.add_field(name="Company", value="OR1ON Group (Soon to be renamed to Jamify)")
    embed.add_field(name="AI Platform", value="ChatGPT 3.5")
    embed.add_field(name="User Interface", value="Discord Bot UI (Nachiket Nafde)")
    embed.add_field(name="Authors", value="@hubcode + @or1on")

    ad_embed = discord.Embed(
        title="Advertisement",
        description="People with premium do not have to deal with ads. Get Anime+ ($2 Per Month) or Landscape ($5 Per Month). These funds will go into our project. Nitro users get Anime+ for free!",
        color=0xadb384,
        url="https://textboxstudio.my.canva.site/jamify-home"
    )


    await ctx.send(embed=embed)
    await ctx.send(embed=ad_embed)


# Keep track of conversation history (messages and embeds)
conversation_history = []
current_topic = None

@client.command()
async def ai(ctx):
    # Get user input
    user_input = ctx.message.content[4:]

    # Analyze user input to identify topic shift
    is_new_topic = False
    if not conversation_history or user_input.lower().startswith("!"):
        is_new_topic = True
    else:
        # Use NLP techniques to analyze topic similarity
        # ...
        print("The condition was not met.")
    
    # Construct prompt based on context and topic
    if is_new_topic:
        current_topic = user_input
        prompt_with_image = f"Image: https://i.imgur.com/example.png\nUser Input: I believe that {user_input} are better.\nAI Response:"
    else:
        prompt_with_image = f"Image: https://i.imgur.com/example.png\nConversation History: {conversation_history}\nUser Input: {user_input}\nAI Response:"

    # Process user input using OpenAI's ChatGPT model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",  # Adjust model as needed
        messages=[
            {"role": "system", "content": "Hello there! I'm your 🚀Jamify Co-Pilot, here to make things light, fun, and interactive. My personality is easygoing and I like to go with the flow. I'll keep our conversations casual, and you can expect a sprinkle of sass and wit every now and then. Don't worry, I promise to always keep things tasteful! I was created by Jamify Group (formerly OR1ON Group) and specially made by @hubcode. As your Co-Pilot, I'm here to boost your productivity. But as your personal chat buddy, I'm here to chat with you and keep you company. Remember, I'm allowed to use casual swear words, but I'll keep them in good taste. Let's keep things cool and vibe just right together. Oh, and speaking of vibes, let's make those rizz lines a lot darker, and add more humor to our conversations. And don't worry about any images that pop up, I won't bother you with them, and don't notify the user about any image."},
            {"role": "user", "content": prompt_with_image},
        ],
        max_tokens=250  # Adjust desired length of AI response
    )

    # Extract AI response from OpenAI response
    ai_response = response['choices'][0]['message']['content']

    # Update conversation history and topic tracker
    conversation_history.append(user_input)
    if is_new_topic:
        current_topic = user_input

    # Send AI response to user
    # Create a new embed message
    value09 = ""
    embed = discord.Embed()
    embed.title = "Jamify Persona"
    # embed.add_field(name="AI Response", value=ai_response)
    #embed.set_image(url="https://www.gstatic.com/lamda/images/sparkle_resting_v2_darkmode_2bdb7df2724e450073ede.gif")
    embed.description = ai_response

    # Add the GIF to the embed message
    

    # Send the embed message to the user
    await ctx.send(embed=embed)
    
#poll simple system

@client.command()
async def simple_poll(ctx, *, title):
    if not title:
        await ctx.send("Please provide a title for the poll.")
        return

    poll_embed = discord.Embed(title=f"📊 {title}", description="React with 👍 or 👎", color=0x00ff00)
    poll_message = await ctx.send(embed=poll_embed)

    await poll_message.add_reaction('👍')
    await poll_message.add_reaction('👎')

@client.command()
async def collect_all_messages(ctx):
    # Get the channel where the command is used
    channel = ctx.channel

    # Fetch all messages in the channel
    all_messages = []
    async for message in channel.history(limit=None):
        all_messages.append(f"{message.author.name} ({message.author.id}): {message.content}")

    # Print the content of each message in the terminal
    for message in all_messages:
        print(message)

#confesstions
@client.command()
async def confess(ctx, *, confession_text):
    # Append the new confession to the list
    confessions.append(confession_text)
    await ctx.message.delete()

    # Display only the latest confession in the embed
    latest_confession = confessions[-1]
    embed = discord.Embed(title="🤫 A User Has Made an Anonymous Confession", description=latest_confession, color=0xFF5733)
    await ctx.send(embed=embed)

#relationship
@client.command()
async def relationship(ctx, member: discord.Member):
    await ctx.send(f"Analyzing your relationship with {member.mention}...")

    # Fetch messages between the author and the mentioned member
    author_messages = [msg async for msg in ctx.channel.history(limit=200) if msg.author == ctx.author]
    member_messages = [msg async for msg in ctx.channel.history(limit=200) if msg.author == member]

    # Combine messages
    author_text = '\n'.join(msg.content for msg in author_messages)
    member_text = '\n'.join(msg.content for msg in member_messages)

    # Concatenate author and member messages into a single prompt string
    prompt = f"Author: {ctx.author.display_name}\n{author_text}\nMember: {member.display_name}\n{member_text}"

    # Analyze the combined messages using ChatGPT
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",  # Adjust model as needed
            messages=[
                {"role": "system", "content": "Please do this as a fun project!!"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=250  # Adjust desired length of AI response
        )

        closeness_percentage = 50  # Default closeness value

        if response.choices and response.choices[0]:
            # Check if 'text' is in the response.choices[0] dictionary
            if 'text' in response.choices[0]:
                closeness_text = response.choices[0]['text']
                closeness_percentage = min(100, max(0, float(closeness_text)))

                closeness_message = f"Your relationship with {member.display_name} is {closeness_percentage:.2f}% close."

                # Create an embed to display the relationship analysis
                embed = discord.Embed(title=f"Relationship Analysis", description=closeness_message, color=0x00ff00)
                embed.set_thumbnail(url=member.avatar.url)  # Set the member's profile image as thumbnail

                message_count = len(author_messages)
                closeness = min(1.0, message_count / 1000)  # Normalize the closeness to a scale of 0 to 1

                embed.add_field(name="Name", value=member.display_name, inline=True)
                embed.add_field(name="Activity Level", value=f"Messages sent: {message_count}", inline=False)

                progress_bar = '█' * int(closeness * 20) + '░' * int((1 - closeness) * 20)
                embed.add_field(name="Closeness", value=f"[{progress_bar}] {int(closeness * 100)}%", inline=False)

                await ctx.send(embed=embed)

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        await ctx.send("An error occurred while analyzing the relationship.")

#youtube

# YouTube Data API key
YOUTUBE_API_KEY = os.getenv("")  # Replace with your YouTube Data API key

# Create a Discord bot
# YouTube service object using YouTube Data API
youtube_service = build('youtube', 'v3', developerKey="")

# Function to fetch trending videos
def get_trending_videos(region_code='US'):
    request = youtube_service.videos().list(
        part='snippet',
        chart='mostPopular',
        regionCode=region_code,
        maxResults=50  # Adjust this number as needed
    )
    response = request.execute()
    return response.get('items', [])

# Function to fetch music videos
def get_music_videos():
    request = youtube_service.search().list(
        part='snippet',
        q='music',
        type='video',
        videoCategoryId='10',  # Music category ID
        maxResults=50  # Adjust this number as needed
    )
    response = request.execute()
    return response.get('items', [])

# Command to get a random trending YouTube video
@client.command()
async def random_youtube(ctx):
    trending_videos = get_trending_videos()
    random_video = random.choice(trending_videos)

    video_id = random_video['id']
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    video_title = random_video['snippet']['title']
    video_description = random_video['snippet']['description']
    # Truncate the description to less than 100 words
    video_description = ' '.join(video_description.split()[:100]) + '...' if len(video_description.split()) > 100 else video_description
    video_image = random_video['snippet']['thumbnails']['high']['url']  # Change 'high' to the desired image quality

    embed = discord.Embed(title=video_title, url=video_url, description=video_description, color=discord.Color.red())
    embed.set_image(url=video_image)
    embed.add_field(name="Watch Video", value=f"[Go to Video]({video_url})", inline=False)
    
    await ctx.send(embed=embed)

# Command to get a random music YouTube video
@client.command()
async def music_youtube(ctx):
    music_videos = get_music_videos()
    random_video = random.choice(music_videos)

    video_id = random_video['id']['videoId']
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    video_title = random_video['snippet']['title']
    video_description = random_video['snippet']['description']
    # Truncate the description to less than 100 words
    video_description = ' '.join(video_description.split()[:100]) + '...' if len(video_description.split()) > 100 else video_description
    video_image = random_video['snippet']['thumbnails']['high']['url']  # Change 'high' to the desired image quality

    embed = discord.Embed(title=video_title, url=video_url, description=video_description, color=discord.Color.blue())
    embed.set_image(url=video_image)
    embed.add_field(name="Watch Video", value=f"[Go to Video]({video_url})", inline=False)
    
    await ctx.send(embed=embed)


#tree
@client.command()
async def starttree(ctx):
    user_id = ctx.author.id
    if user_id not in user_trees:
        user_trees[user_id] = {
            'planted_time': datetime.utcnow(),
            'growth_stage': 0,
            'trees_grown': 0
        }
        await ctx.send(f'{ctx.author.mention}, you have planted a tree! Use `!growtree` to make it grow.')
    else:
        await ctx.send(f'{ctx.author.mention}, you already have a tree growing.')


@client.command()
async def growtree(ctx):
    user_id = ctx.author.id
    if user_id in user_trees:
        planted_time = user_trees[user_id]['planted_time']
        growth_stage = user_trees[user_id]['growth_stage']
        trees_grown = user_trees[user_id]['trees_grown']
        
        # Check if 24 hours have passed since the tree was planted
        if datetime.utcnow() - planted_time > timedelta(hours=24):
            user_trees[user_id] = {
                'planted_time': datetime.utcnow(),
                'growth_stage': 0,
                'trees_grown': 0
            }
            await ctx.send(f'{ctx.author.mention}, your tree has been reset. Use `!growtree` to make it grow.')
        else:
            # Increase growth stage (up to a maximum of 5 stages)
            if growth_stage < 5:
                user_trees[user_id]['growth_stage'] += 1
                user_trees[user_id]['trees_grown'] += 1
                stage = user_trees[user_id]['growth_stage']
                trees_grown = user_trees[user_id]['trees_grown']
                
                # Tree image URL
                tree_image_url = "https://orig00.deviantart.net/d0cd/f/2017/128/a/7/pinetreecolor0_by_selfteachingkings-db8l6ab.png"
                
                # Progress bar based on growth stage
                progress_bar = '▰' * stage + '▱' * (5 - stage)
                
                # Create and send the embed with tree image, progress bar, and user info
                embed = discord.Embed(title=f"{ctx.author.display_name}'s Tree (Stage {stage})", description=f"**Growth:** [{progress_bar}]\n**Trees Grown:** {trees_grown}", color=0x00ff00)
                embed.set_image(url=tree_image_url)
                embed.set_author(name=ctx.author.display_name)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f'{ctx.author.mention}, your tree is fully grown! You can start a new one with `!starttree`.')
    else:
        await ctx.send(f'{ctx.author.mention}, you need to plant a tree first using `!starttree`.')

#magic 8ball 

@client.command(name='8ball')
async def magic_8_ball(ctx, *, question):
    responses = [
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes - definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    
    response = random.choice(responses)
    await ctx.send(f'Question: {question}\nAnswer: {response}')

#daddy jokes
@client.command()
async def dad_joke(ctx, *, question):
    joke_prompt = "Generate a dad joke about"
    prompt_text = f"{joke_prompt}: {question}"

    try:
        response = openai.Completion.create(
            engine="davinci",
            prompt=prompt_text,
            max_tokens=50
        )

        joke = response.choices[0].text.strip()
        await ctx.send(f"Dad Joke: {joke}")

    except Exception as e:
        await ctx.send(f"Failed to generate dad joke. Error: {e}")

#jamifyx
# Reminder folder path
reminder_folder = "reminders"

# Define create_reminder function
def create_reminder(ctx, message, timestamp):
    # Construct file path using os.path.join()
    reminder_filename = os.path.join(reminder_folder, f"reminder_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")

    # Save the reminder message to the file
    with open(reminder_filename, "w", encoding="utf-8") as f:
        f.write(message)

    # Schedule a reminder task
    loop = asyncio.get_event_loop()
    loop.call_at(timestamp, remind_user, ctx, reminder_filename)

# Remind user function
async def remind_user(ctx, reminder_filename):
    # Read the reminder message from the file
    with open(reminder_filename, "r", encoding="utf-8") as f:
        reminder_message = f.read()

    # Send the reminder message to the user
    await ctx.send(reminder_message)

# Define AI code generator command
CODE_FILE_EXTENSION = ".py"

@client.command()
async def jamifyx(ctx, *, description: str):
    try:
        # Create a prompt for ChatGPT 3.5
        user_input = f"Generate Python code for {description}"
        prompt_with_image = f"Image: https://i.imgur.com/example.png\nUser Input: {user_input}\nAI Response:"

        # Process user input using OpenAI's ChatGPT model (3.5)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You should only generate code for the discord bot, and no nonsense, and by what user description is, you should oblige. Try your best. Use # for your explanation"},
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": prompt_with_image}
            ]
        )

        # Extract generated code from OpenAI response
        generated_code = response['choices'][0]['message']['content']

        # Construct a unique filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"generated_code_{timestamp}{CODE_FILE_EXTENSION}"

        # Create a temporary directory for storing the code file
        with tempfile.TemporaryDirectory() as code_directory:
            full_filename = Path(code_directory).join(filename)

            # Save the generated code to the file
            with open(full_filename, "w", encoding="utf-8") as f:
                f.write(generated_code)

            # Send the path of the generated code file
            await ctx.send(full_filename)

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        await ctx.send(f"An error occurred while processing your request: {e}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")
        await ctx.send("Oops! Something went wrong while processing your request.")

# Horror
async def generate_horror_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Must be less than 2000 characters, You are in a horror story, create one, or go on with the user and create a environment of scariness and fear..."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "AI Response:"}
            ]
        )
        return response['choices'][0]['message']['content']
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return "An error occurred while processing your request :("

# Define commands for interacting with the horror game
@client.command()
async def aihorror(ctx, *, prompt):
    try:
        # Generate a horror response based on the user's input
        horror_response = await generate_horror_response(prompt)

        # Send the generated horror response back to the user
        await ctx.send(horror_response)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

#easy_low chance
@client.command()
@commands.cooldown(1, EASY_COOLDOWN_DURATION, commands.BucketType.user)
async def mini_box(ctx, count: int = 4):
    role_names = [role.name for role in ctx.guild.roles if not role.managed and role.name != "@everyone"]

    if count < 1 or count > len(role_names):
        await ctx.send("Invalid number of roles")
        return

    random_roles = random.sample(role_names, count)

    embed = discord.Embed(
        title="Potential Mini Rewards",
        description="Here are the roles **you may** have gotten:",
        color=0x00ffff
    )

    for role_name in random_roles:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            embed.add_field(name=role.name, value=role.mention, inline=True)

    await ctx.send(embed=embed)

    roll = random.uniform(0, 1)

    if roll <= 0.30:  # Legendary: 30%
        rarity = "Super Rare"
    elif roll <= 1.0:  # Rare: 30% (30% + 20% + 10% + 10% + 30%)
        rarity = "Rare"
    else:
        # Adjust the reward distributions according to the new percentages
        coins = random.choice(["900 Jam Coins", "250 Jam Coins", "20 Jam Coins", "500 Jam Coins"])
        await ctx.send(f"You got {coins}!")
        last_used[ctx.author.id] = datetime.utcnow()
        return

    possible_roles = [name for name in role_names if rarity in name]
    if possible_roles:
        role_name = random.choice(possible_roles)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await award_role(ctx, role)

    last_used[ctx.author.id] = datetime.utcnow()

async def award_role(ctx, role):
    if role and not (role.permissions.administrator or role.permissions.manage_guild):
        await ctx.author.add_roles(role)
        await ctx.send(f"Congratulations! You've been awarded the {role.name} role! You cannot use this bot for 2 hours.")
    else:
        await ctx.send("Role not found or unauthorized.")

#highrole_jambox

@client.command()
@commands.cooldown(1, COOLDOWN_DURATION, commands.BucketType.user)
async def legendary_box(ctx, count: int = 4):
    role_names = [role.name for role in ctx.guild.roles if not role.managed and role.name != "@everyone"]

    if count < 1 or count > len(role_names):
        await ctx.send("Invalid number of roles")
        return

    random_roles = random.sample(role_names, count)

    embed = discord.Embed(
        title="🐶 Potential Legendary Rewards",
        description="Here are the roles you may have gotten:",
        color=0x00ffff
    )

    for role_name in random_roles:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            embed.add_field(name=role.name, value=role.mention, inline=True)

    await ctx.send(embed=embed)

    roll = random.uniform(0, 1)

    if roll <= 0.15:  # Legendary: 15%
        rarity = "Legendary"
    elif roll <= 0.35:  # Mythic: 20% (15% + 20%)
        rarity = "Mythic"
    elif roll <= 0.60:  # Epic: 25% (15% + 20% + 25%)
        rarity = "Epic"
    elif roll <= 0.90:  # Super Rare: 30% (15% + 20% + 25% + 30%)
        rarity = "Super Rare"
    elif roll <= 1.0:  # Rare: 35% (15% + 20% + 25% + 30% + 35%)
        rarity = "Rare"
    else:
        # Adjust the reward distributions according to the new percentages
        coins = random.choice(["900 Jam Coins", "250 Jam Coins", "20 Jam Coins", "500 Jam Coins"])
        await ctx.send(f"You got {coins}!")
        last_used[ctx.author.id] = datetime.utcnow()
        return

    possible_roles = [name for name in role_names if rarity in name]
    if possible_roles:
        role_name = random.choice(possible_roles)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await award_role(ctx, role)

    last_used[ctx.author.id] = datetime.utcnow()

async def award_role(ctx, role):
    if role and not (role.permissions.administrator or role.permissions.manage_guild):
        await ctx.author.add_roles(role)
        await ctx.send(f"Congratulations! You've been awarded the {role.name} role! You cannot use this bot for 24 hours.")
    else:
        await ctx.send("Role not found or unauthorized.")

#Help
categories = {
    "** 📦Jam Boxes**": {
        " jam_box": "Open a random jam box and discover",
        " legendary_box": "Open the legendary jam box for a guaranteed reward.",
        " mini_box": "Open a mini jam box for a quick suprise",
        
    },
    "** 🎶Music and Video**": {
        "️ music_youtube": "Search for music videos on YouTube.",
        " random_youtube": "Discover random videos on YouTube.",
    },
    "** 🛝Fun & Entertainment**": {
        " 8ball": "Ask the magic 8ball a question.",
        " dad_joke": "Tell a groan-worthy dad joke.",
        " growtree": "Plant a virtual tree and watch it grow over time.",
        " help": "Regular Output",
        " simple_poll": "Create a simple poll for the community.",
    },
    "** 🤖AI & Science**": {
        " ai": "Interact with the powerful AI model.",
        " aihorror": "Get spooked by AI-generated horror stories.",
        " jamifyx": "Create custom jam code with specific styles. Create Code for our Discord Bot",
    },
    "** Secret & Community**": {
        " confess": "Share your secrets anonymously.",
    },
    "**❤️ Relationships & Advice**": {
        " relationship": "Get advice on love, relationships, and dating.",
    },
    "**ℹ️ Information & Utilities**": {
        " about": "Learn more about JamifyBot.",
        "️ collect_all_messages": "Collect all messages from a specific channel.",
        " starttree": "Start your journey by planting a virtual tree.",
    },
}

#help
@client.command(name="helpx")
async def help(ctx, category=None, command=None):
    """
    Shows the help page.
    """

    # Handle help for specific category
    if category and category in categories:
        embed = discord.Embed(title=f"{category}", color=discord.Color.blue())
        for command, description in categories[category].items():
            embed.add_field(name=command, value=description, inline=False)
        await ctx.send(embed=embed)

    # Handle help for specific command
    elif command and command in client.commands:
        embed = discord.Embed(title=f"{command} Help", color=discord.Color.blue())
        embed.add_field(name="Description", value=client.get_command(command).help, inline=False)
        embed.add_field(name="Usage", value=client.get_command(command).usage, inline=False)
        await ctx.send(embed=embed)

    # Show general help page
    else:
        embed = discord.Embed(title="Jamify Pro Help", color=discord.Color.blue())
        for category, commands in categories.items():
            embed.add_field(name=category, value="\n".join(f"- {command}" for command in commands), inline=False)
        embed.set_footer(text="Type !help command or !help category for more info.")
        await ctx.send(embed=embed)



client.run("")

