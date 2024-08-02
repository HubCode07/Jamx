import discord
from discord.ext import commands, tasks
import google.generativeai as genai
import PIL
import os
import colorsys
import asyncio
import csv
import time
import sqlite3
import aiofiles


from discord import app_commands
import random
from datetime import datetime, timedelta
import datetime

# Replace with your actual API key
genai.configure(api_key='')

# Conversation history and topic tracker
conversation_history = []
# Model setup
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
]



intents = discord.Intents.default()
intents.typing = False
intents.presences = False



class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print("Bot is Up and Ready!")
        await self.tree.sync()

bot = MyBot()
# Initialize SQLite database
conn = sqlite3.connect('messages.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS messages (
    user_id INTEGER,
    timestamp TEXT,
    content TEXT
)
''')
conn.commit()

async def fetch_messages(channel):
    messages = []
    last_message_id = None
    while True:
        try:
            history = channel.history(limit=100, after=last_message_id)
            async for message in history:
                messages.append(message)
                last_message_id = message.id
            if len(messages) == 0:
                break
            await asyncio.sleep(1)  # Use async sleep to avoid blocking the event loop
        except discord.Forbidden:
            print(f"Bot does not have permission to read messages in {channel.name}")
            break
        except discord.HTTPException as e:
            print(f"HTTP error fetching messages: {e}")
            break
        except Exception as e:
            print(f"Error fetching messages: {e}")
            break
    return messages

@bot.tree.command(name="gather_messages")
async def gather_messages(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message("Gathering messages...")

    try:
        guild = interaction.guild
        channels = [channel for channel in guild.text_channels if channel.permissions_for(guild.me).read_messages]

        tasks = [fetch_messages(channel) for channel in channels]
        all_messages = await asyncio.gather(*tasks)
        flattened_messages = [msg for sublist in all_messages for msg in sublist]
        user_messages = [msg for msg in flattened_messages if msg.author == user]

        # Store messages in SQLite database
        with conn:
            cursor.executemany('''
                INSERT INTO messages (user_id, timestamp, content) VALUES (?, ?, ?)
            ''', [(user.id, msg.created_at.strftime("%Y-%m-%d %H:%M:%S"), msg.content) for msg in user_messages])

        # Create CSV file
        async with aiofiles.open(f"{user.id}_messages.csv", "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["timestamp", "content"])
            await writer.writeheader()

            for message in user_messages:
                await writer.writerow({"timestamp": message.created_at.strftime("%Y-%m-%d %H:%M:%S"), "content": message.content})

        await interaction.followup.send(f"Messages from {user.name} have been saved to {user.id}_messages.csv")

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

@bot.tree.command(name="retired-co-pilot-old", description="Generates creative text based on your input. Jamx Co-Pilot w/ Gemini AI")
async def jamx(interaction: discord.Interaction, prompt: str, image: str = None):
    await interaction.response.defer()  # Defers the response to prevent the timeout error
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    promptx = f"Previous Conversation: {', '.join(conversation_history)}\n"

    response = model.generate_content(promptx)

    embed = discord.Embed(
        title= prompt + " | Jamx Co-Pilot",
        description=response.text,
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
    if image:
        embed.set_image(url=image)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="pollbasic", description="Create a poll with up to 10 options")
async def poll(interaction: discord.Interaction,
               heading: str,
               option1: str,
               option2: str,
               option3: str = None,
               option4: str = None,
               option5: str = None,
               option6: str = None,
               option7: str = None,
               option8: str = None,
               option9: str = None,
               option10: str = None):
    options = [option1, option2]
    for option in [option3, option4, option5, option6, option7, option8, option9, option10]:
        if option:
            options.append(option)

    poll_embed = discord.Embed(title=heading, color=discord.Color.blue())

    for idx, option in enumerate(options):
        poll_embed.add_field(name=f"Option {idx + 1}", value=option, inline=False)

    await interaction.response.send_message(embed=poll_embed)

    message = await interaction.original_response()
    for idx, option in enumerate(options):
        await message.add_reaction(f"{idx + 1}\u20e3")

#pollx_smart
@bot.tree.command(name="pollx", description="Create a poll with options generated by Gemini AI")
async def poll(interaction: discord.Interaction, heading: str, num_options: int = 5):
    await interaction.response.defer()  # Defer the response to prevent the timeout error
    model = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    prompt = f"Generate {num_options} options for a poll with the heading: '{heading}'"
    response = model.generate_content(prompt)

    options = response.text.strip().split("\n")

    poll_embed = discord.Embed(title=heading, color=discord.Color.blue())

    for idx, option in enumerate(options):
        poll_embed.add_field(name=f"Option {idx + 1}", value=option, inline=False)

    await interaction.followup.send(embed=poll_embed)  # Send the Embed as a followup message

    message = await interaction.original_response()
    for idx in range(len(options)):
        await message.add_reaction(f"{idx + 1}\u20e3")


import openai
openai.api_key = ""

# Define the /imagine command
@bot.tree.command(name="imagine", description="Generate images using DALL-E based on a given prompt")

async def imagine(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()  # Defer the response to prevent the timeout error

    try:
        # Generate images using DALL-E
        response = openai.Image.create(
            model="dall-e-2",
            prompt=prompt,
            n=1,  # Number of images to generate
            size="1024x1024",  # Size of the generated images
            quality="hd",

        )

        # Send the generated images to Discord
        for image_data in response['data']:
            embed = discord.Embed(title=prompt, color=discord.Color.blue())
            embed.set_image(url=image_data['url'])
            await interaction.followup.send(embed=embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="Error",
            description=f"An error occurred while generating the images: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=error_embed)
from PIL import Image

@bot.tree.command(name="retired-co-pilot-images-old", description="Generate a text description for an uploaded image: Jamx Co-Pilot w/ Gemini Images Dectection")
async def jamx_imagr(interaction: discord.Interaction, image: discord.Attachment, prompt: str = ""):
    await interaction.response.defer()  # Defer the response to prevent the timeout error

    try:
        # Download the image from the attachment and get the temporary file path
        filename = f"temp_image.{image.filename.split('.')[-1]}"  # Create a unique filename
        await image.save(filename)

        # Use Pillow to open the downloaded image
        img = Image.open(filename)

        # Use the Gemini AI image detector to generate text from the image
        model = genai.GenerativeModel(
            model_name="gemini-pro-vision",
            safety_settings=safety_settings
        )

        # Specify task type for image description
        if prompt:
            response = model.generate_content([prompt, img], stream=True)
            response.resolve()
        else:
            response = model.generate_content(img)
        image_url = image.url
        # Clean up the downloaded image (optional)
        os.remove(filename)

        # Send the generated text description to Discord
        image_description = response.text
        embed = discord.Embed(
            title="Jamx Image Detection",
            description=image_description,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="Error",
            description=f"An error occurred while generating the image description: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=error_embed)

        # Clean up the downloaded image in case of errors (optional)
        if os.path.exists(filename):
            os.remove(filename)

@bot.tree.command(name="co-pilot", description="Generates creative text or image descriptions using Jamx Co-Pilot with Gemini AI")
async def jamx(interaction: discord.Interaction, prompt: str, image: discord.Attachment = None):
    await interaction.response.defer()  # Defers the response to prevent the timeout error

    if image:
        # Image processing
        try:
            # Download the image from the attachment and get the temporary file path
            filename = f"temp_image.{image.filename.split('.')[-1]}"  # Create a unique filename
            await image.save(filename)

            # Use Pillow to open the downloaded image
            img = Image.open(filename)

            # Use the Gemini AI image detector to generate text from the image
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            response = model.generate_content([prompt, img], stream=True)
            response.resolve()

            image_description = response.text
            embed = discord.Embed(
                title=prompt + " | Jamx Co-Pilot",
                description=image_description,
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_image(url=image.url)
            await interaction.followup.send(embed=embed)

            # Clean up the downloaded image
            os.remove(filename)

        except Exception as e:
            error_embed = discord.Embed(
                title="Error",
                description=f"An error occurred while generating the image description: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed)

            # Clean up the downloaded image in case of errors
            if os.path.exists(filename):
                os.remove(filename)

    else:
        # Text processing
        model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        promptx = f"Previous Conversation: {', '.join(conversation_history), prompt ,'Use the previous conv and crruent prompt, and join them together to create a responce, remember you are Jamx Co-Pilot'}"

        response = model.generate_content(promptx)

        embed = discord.Embed(
            title=prompt + " | Jamx Co-Pilot",
            description=response.text,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)



# Replace with your bot token
bot.run("")