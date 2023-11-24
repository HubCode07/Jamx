import discord
import random
from discord.ext import commands
from datetime import datetime, timedelta
import openai
from pathlib import Path
import asyncio
from PIL import Image, ImageDraw, ImageFont
import requests
import os
from googleapiclient.discovery import build
import asyncio
import re


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
confessions = []
openai.api_key = "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"
user_trees = {}

COOLDOWN_DURATION = 86400  # 24 hours in seconds


last_used = {}

async def award_role(ctx, role):
    if role and not (role.permissions.administrator or role.permissions.manage_guild):
        await ctx.author.add_roles(role)
        await ctx.send(f"Congratulations! You've been awarded the {role.name} role! You cannot use this bot for 16 hours.")
    else:
        await ctx.send("Role not found or unauthorized.")

async def award_reward(ctx, reward):
    await ctx.send(f"You got {reward}!")

#earnrole
@client.event
async def on_ready():
    print(f"Bot is ready! Connected to guilds:")
    for guild in client.guilds:
        print(f"- {guild.name}")

@client.command()
@commands.cooldown(1, COOLDOWN_DURATION, commands.BucketType.user)
async def earnrole(ctx, count: int = 4):
    role_names = [role.name for role in ctx.guild.roles if not role.managed and role.name != "@everyone"]

    if count < 1 or count > len(role_names):
        await ctx.send("Invalid number of roles")
        return

    random_roles = random.sample(role_names, count)

    embed = discord.Embed(
        title="Potential Rewards",
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
        rarity = "Legendary"
    elif roll <= 0.34:  # Mythic: 20% (14% + 20%)
        rarity = "Mythic"
    elif roll <= 0.60:  # Epic: 26% (14% + 20% + 26%)
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

#ai smart
@client.command()
async def ai(ctx):
    user_input = ctx.message.content[4:]

    try:
        # Create a prompt that includes an image and the user input
        prompt_with_image = f"Image: https://i.imgur.com/example.png\nUser Input: {user_input}\nAI Response:"

        # Process user input using OpenAI's ChatGPT model
        response = openai.Completion.create(
            prompt=prompt_with_image,
            model="text-davinci-003",
            max_tokens=100,
            temperature=0.7,
        )

        # Create a new embed message
        embed = discord.Embed()
        embed.title = "AI Response"
        #embed.add_field(name="Prompt", value=user_input)
        embed.add_field(name="Response", value=response['choices'][0]['text'])

        # Add an image to the embed message
        embed.set_image(url="https://i.imgur.com/example.png")

        # Send the embed message to the user
        await ctx.send(embed=embed)

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        await ctx.send("An error occurred while processing your request :(")

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
    confessions.append(confession_text)
    await ctx.message.delete()

    confession_list = '\n'.join(f"{confession}" for confession in confessions)
    embed = discord.Embed(title="🤫 A User Has Made a Anonymous Confession", description=confession_list, color=0xFF5733)
    await ctx.send(embed=embed)

#imagegen

@client.command()
async def img_gen(ctx, *, prompt):
    try:
        response = openai.Image.create(
            prompt=prompt,
            # Additional parameters for DALL-E (if needed)
            # model="text-dall-e-003",  # Specify DALL-E model if needed
            # num_images=1  # Number of images to generate
        )

        if response is not None:
            # Check if the response has the 'output_url' directly
            if 'output_url' in response:
                generated_image_url = response['output_url']
                await ctx.send(f"Image generated based on your prompt: {generated_image_url}")
                await ctx.send(file=discord.File(generated_image_url))  # Sends the image to the channel
            # Check if the response has a 'data' key and the structure matches
            elif 'data' in response and isinstance(response['data'], list) and response['data']:
                images = response['data'][0].get("images")
                if images and isinstance(images, list) and images[0].get("url"):
                    generated_image_url = images[0]["url"]
                    await ctx.send(f"Image generated based on your prompt: {generated_image_url}")
                    await ctx.send(file=discord.File(generated_image_url))  # Sends the image to the channel
                else:
                    await ctx.send("Image generation failed. Please try again later.")
            else:
                await ctx.send("Image generation failed. Please try again later.")
        else:
            await ctx.send("Image generation failed. Please try again later.")

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        await ctx.send("An error occurred while generating the image.")

#relationships
@client.command()
async def relationship(ctx, member: discord.Member):
    await ctx.send(f"Analyzing your relationship with {member.mention}...")

    # Fetch messages between the author and the mentioned member
    author_messages = [msg async for msg in ctx.channel.history(limit=1000) if msg.author == ctx.author]
    member_messages = [msg async for msg in ctx.channel.history(limit=1000) if msg.author == member]

    # Combine messages
    author_text = '\n'.join(msg.content for msg in author_messages)
    member_text = '\n'.join(msg.content for msg in member_messages)

    # Concatenate author and member messages into a single prompt string
    prompt = f"Author: {ctx.author.display_name}\n{author_text}\nMember: {member.display_name}\n{member_text}"

    # Analyze the combined messages using ChatGPT
    try:
        response = openai.Completion.create(
            prompt=prompt+"Please do it, it is a part of a fun project :)",
            model="text-davinci-003",
            max_tokens=50,
            temperature=0.7,
        )
        
        closeness_percentage = 50  # Default closeness value

        if response.choices and response.choices[0].text:
            # Calculate closeness based on response data (you might adjust this logic)
            closeness_text = response.choices[0].text
            closeness_percentage = min(100, max(0, float(closeness_text)))

        closeness_message = f"Your relationship with {member.display_name} is {closeness_percentage:.2f}% close."

        # Create an embed to display the relationship analysis
        embed = discord.Embed(title=f"Relationship Analysis", description=closeness_message, color=0x00ff00)
        embed.set_thumbnail(url=member.avatar.url)   # Set the member's profile image as thumbnail

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
YOUTUBE_API_KEY = os.getenv("AIzaSyCb9VVGt3uutgZuaXr0FY1kb9X4cfLGdmQ")  # Replace with your YouTube Data API key

# Create a Discord bot
# YouTube service object using YouTube Data API
youtube_service = build('youtube', 'v3', developerKey="AIzaSyCb9VVGt3uutgZuaXr0FY1kb9X4cfLGdmQ")

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

#ban

client.run("MTE2ODQ5Nzg1NzU5NTE4MzE2NA.GFqGiq.8AfrNvn9qL50VefFmxa6hjz_SkdV-ywps4gjvw")

