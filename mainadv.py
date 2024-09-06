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
        self.last_used = {}
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

"""
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
"""
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

#co-pilot
from PIL import Image
conversation_history = {}  # Keyed by user ID
current_topic = {}  # Keyed by channel ID
import PyPDF2
import moviepy.editor as mp
import speech_recognition as sr

# ... (import genai, conversation_history, current_topic) ...

@bot.tree.command(name="co-pilot", description="Generates creative text or descriptions using Jamx Co-Pilot")
async def copilot(interaction: discord.Interaction, prompt: str, file: discord.Attachment = None):
    await interaction.response.defer()

    user_id = interaction.user.id
    channel_id = interaction.channel.id

    def process_text(text):
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        channel_topic = current_topic.get(channel_id, None)
        user_history = conversation_history.get(user_id, [channel_topic])


        promptx = f"{prompt}\nPrevious conversation: {', '.join(user_history)}\nCurrent topic: {channel_topic} Personality: Jamx Co-Pilot. Act like a CO-Pilot for discord, This Co-Pilot was made by @hubCode"
        response = model.generate_content([promptx, text])
        return response.text

    if file:
        filename = f"temp_file.{file.filename.split('.')[-1]}"
        await file.save(filename)

        try:
            if file.content_type.startswith('image/'):
                with Image.open(filename) as img:
                    description = process_text(img)
                    embed = discord.Embed(
                        title=prompt + " | Jamx Co-Pilot",
                        description=description,
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_image(url=file.url)
                    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
                    await interaction.followup.send(embed=embed)

            elif file.content_type == 'application/pdf':
                # Process PDF
                try:
                    with open(filename, 'rb') as pdf_file:
                        reader = PyPDF2.PdfReader(pdf_file)
                        text = ""
                        for page_num in range(len(reader.pages)):
                            page = reader.pages[page_num]
                            text += page.extract_text()
                    summary = process_text(text)
                    embed = discord.Embed(
                        title=prompt + " | Jamx Co-Pilot",
                        description=summary,
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
                    await interaction.followup.send(embed=embed)
                except Exception as e:
                    await interaction.followup.send(f"Error processing PDF: {e}")

            elif file.content_type.startswith('video/'):
                # Process video (extract audio, convert to text)
                try:
                    video = mp.VideoFileClip(filename)
                    audio = video.audio
                    audio_file = "temp_audio.wav"
                    audio.write_audiofile(audio_file)
                    video.close()  # Close the video clip

                    recognizer = sr.Recognizer()
                    with sr.AudioFile(audio_file) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data)
                    summary = process_text(text)
                    embed = discord.Embed(
                        title=prompt + " | Jamx Co-Pilot",
                        description=summary,
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
                    await interaction.followup.send(embed=embed)
                except Exception as e:
                    await interaction.followup.send(f"Error processing video: {e}")

            elif file.content_type.startswith('audio/'):
                # Process audio
                try:
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(filename) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data)
                    summary = process_text(text)
                    embed = discord.Embed(
                        title=prompt + " | Jamx Co-Pilot",
                        description=summary,
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
                    await interaction.followup.send(embed=embed)
                except Exception as e:
                    await interaction.followup.send(f"Error processing audio: {e}")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

        finally:
            # Clean up temporary files
            if os.path.exists(filename):
                os.remove(filename)
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")
    else:
        # Process text directly from the prompt
        response = process_text(prompt)
        embed = discord.Embed(
            title=prompt + " | Jamx Co-Pilot",
            description=response,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed)
#jamx boxs
import pytz
# Defining the roles and their chances
roles = {
    "mini": [
        {"chance": 0.01, "name": "VJ BLUE", "role_id": 1258252567050321981},
        {"chance": 0.01, "name": "Dairy Blue", "role_id": 1258252377891409940},
        {"chance": 0.01, "name": "Cabbage Green", "role_id": 1258252147733172278},
        {"chance": 0.01, "name": "Nach Blue", "role_id": 1258251538795597927},
        {"chance": 0.01, "name": "Chandy Red", "role_id": 1258251661760008233},
        {"chance": 0.02, "name": "Black", "role_id": 1258251204333408257},
        {"chance": 0.02, "name": "Mint", "role_id": 1258249610678505552},
        {"chance": 0.02, "name": "Gold", "role_id": 1258249269606088815},
        {"chance": 0.02, "name": "Lime", "role_id": 1258248831842127893},
        {"chance": 0.1, "name": "Lavender", "role_id": 1258209072717627453},
        {"chance": 0.1, "name": "Pinkish Red", "role_id": 1258248343172419706},
        {"chance": 0.1, "name": "Lemon Yellow", "role_id": 1258247640009670727},
        {"chance": 0.1, "name": "Light Red", "role_id": 1258247221703348224},
        {"chance": 0.1, "name": "Dark Pink", "role_id": 1258208512950145095},
        {"chance": 0.1, "name": "Pale Orange", "role_id": 1245457565148647476}
    ],
    "box": [
        {"chance": 0.01, "name": "VJ BLUE", "role_id": 1258252567050321981},
        {"chance": 0.01, "name": "Dairy Blue", "role_id": 1258252377891409940},
        {"chance": 0.01, "name": "Cabbage Green", "role_id": 1258252147733172278},
        {"chance": 0.01, "name": "Nach Blue", "role_id": 1258251538795597927},
        {"chance": 0.01, "name": "Chandy Red", "role_id": 1258251661760008233},
        {"chance": 0.02, "name": "Black", "role_id": 1258251204333408257},
        {"chance": 0.02, "name": "Mint", "role_id": 1258249610678505552},
        {"chance": 0.02, "name": "Gold", "role_id": 1258249269606088815},
        {"chance": 0.02, "name": "Lime", "role_id": 1258248831842127893},
        {"chance": 0.1, "name": "Lavender", "role_id": 1258209072717627453},
        {"chance": 0.1, "name": "Pinkish Red", "role_id": 1258248343172419706},
        {"chance": 0.1, "name": "Lemon Yellow", "role_id": 1258247640009670727},
        {"chance": 0.1, "name": "Light Red", "role_id": 1258247221703348224},
        {"chance": 0.1, "name": "Dark Pink", "role_id": 1258208512950145095},
        {"chance": 0.1, "name": "Pale Orange", "role_id": 1245457565148647476}
    ],
    "legendary": [
        {"chance": 0.01, "name": "VJ BLUE", "role_id": 1258252567050321981},
        {"chance": 0.01, "name": "Dairy Blue", "role_id": 1258252377891409940},
        {"chance": 0.01, "name": "Cabbage Green", "role_id": 1258252147733172278},
        {"chance": 0.01, "name": "Nach Blue", "role_id": 1258251538795597927},
        {"chance": 0.01, "name": "Chandy Red", "role_id": 1258251661760008233},
        {"chance": 0.02, "name": "Black", "role_id": 1258251204333408257},
        {"chance": 0.02, "name": "Mint", "role_id": 1258249610678505552},
        {"chance": 0.02, "name": "Gold", "role_id": 1258249269606088815},
        {"chance": 0.02, "name": "Lime", "role_id": 1258248831842127893},
        {"chance": 0.1, "name": "Lavender", "role_id": 1258209072717627453},
        {"chance": 0.1, "name": "Pinkish Red", "role_id": 1258248343172419706},
        {"chance": 0.1, "name": "Lemon Yellow", "role_id": 1258247640009670727},
        {"chance": 0.1, "name": "Light Red", "role_id": 1258247221703348224},
        {"chance": 0.1, "name": "Dark Pink", "role_id": 1258208512950145095},
        {"chance": 0.1, "name": "Pale Orange", "role_id": 1245457565148647476}
    ]
}
# Cooldown durations (in seconds)
EASY_COOLDOWN_DURATION = 3600
COOLDOWN_DURATION = 7200
HARDCORE_COOLDOWN_DURATION = 14400


# Function to get a random role based on weight
def get_random_role(box_type):
    total_weight = sum(role["chance"] for role in roles[box_type])
    random_choice = random.uniform(0, total_weight)
    current = 0
    for role in roles[box_type]:
        current += role["chance"]
        if current >= random_choice:
            return role
    return None


# Function to award a role to a user
async def award_role(interaction, role):
    bot_member = interaction.guild.get_member(interaction.client.user.id)
    if role and not (role.permissions.administrator or role.permissions.manage_guild):
        if role.position < bot_member.top_role.position:
            await interaction.user.add_roles(role)
            return f"Congratulations! You've been awarded the **{role.name}** role!"
        else:
            return "I cannot assign this role because it is higher than my highest role in the hierarchy."
    else:
        return "Role not found or unauthorized."


# Command for jam-box
@bot.tree.command(name="jam-box", description="Bringing back the old jam boxes")
@app_commands.choices(box_type=[
    app_commands.Choice(name="Mini", value="mini"),
    # Add more choices if you have more box types
])
async def jamxbox(interaction: discord.Interaction, box_type: app_commands.Choice[str]):
    cooldown_mapping = {
        "mini": EASY_COOLDOWN_DURATION,
        # Add more cooldowns for other box types if necessary
    }
    cooldown = cooldown_mapping[box_type.value]
    last_used = bot.last_used.get(interaction.user.id)
    now = datetime.datetime.now(datetime.timezone.utc)

    if last_used and (now - last_used).total_seconds() < cooldown:
        remaining_time = cooldown - (now - last_used).total_seconds()
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        await interaction.response.send_message(
            f"Please wait {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds before using this command again.")
        return

    bot.last_used[interaction.user.id] = now

    final_role = get_random_role(box_type.value)
    if final_role:
        guild_role = discord.utils.get(interaction.guild.roles, id=final_role['role_id'])

        # Prepare a list of roles to display (6 random roles including the final role)
        possible_roles = random.sample(roles[box_type.value], k=5)  # Get 5 random roles
        possible_roles.append(final_role)  # Add the final role to the list
        random.shuffle(possible_roles)  # Shuffle the list to randomize display order

        embed = discord.Embed(
            title=f"{box_type.name.capitalize()} Rewards 🎉",
            description="Here are the roles you might get:",
            color=0x00ffff
        )

        for role in possible_roles:
            embed.add_field(name=role["name"], value=f"<@&{role['role_id']}>", inline=True)

        # Wait for a moment before revealing the final role
        await interaction.response.send_message(embed=embed)
        await interaction.channel.send("Drumroll, please... 🥁")
        await asyncio.sleep(2)  # Wait for 2 seconds to build suspense

        # Reveal the final awarded role
        final_response = await award_role(interaction, guild_role)
        await interaction.channel.send(final_response)
    else:
        await interaction.response.send_message("Unfortunately, you did not receive any role. Better luck next time!")


#jamx tokens
import os
import asyncio
import csv

import aiofiles
import random
import json
from datetime import datetime, timedelta
class JamTokens:
    def __init__(self, bot):
        self.bot = bot
        self.salaries_file = "jam_salaries.json"
        self.products_file = "jam_products.json"
        self.balances_file = "jam_balances.json"  # File for user balances
        self.load_data()

    def load_data(self):
        self.salaries = self.load_json(self.salaries_file)
        self.products = self.load_json(self.products_file)
        self.balances = self.load_json(self.balances_file)

    def load_json(self, file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_data(self):
        self.save_json(self.salaries_file, self.salaries)
        self.save_json(self.products_file, self.products)
        self.save_json(self.balances_file, self.balances)

    def save_json(self, file_path, data):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    def generate_id(self):
        while True:
            id = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
            if id not in self.salaries and id not in self.products:
                return id

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        else:
            await ctx.send(f"An error occurred: {error}")

    # Helper function to get user's balance
    def get_user_balance(self, user_id, guild_id):
        user_id = str(user_id)
        guild_id = str(guild_id)
        if guild_id not in self.balances:
            self.balances[guild_id] = {}
        if user_id not in self.balances[guild_id]:
            self.balances[guild_id][user_id] = 0
        return self.balances[guild_id][user_id]

    # Helper function to update user's balance
    def update_user_balance(self, user_id, guild_id, amount_change):
        balance = self.get_user_balance(user_id, guild_id)
        new_balance = balance + amount_change
        self.balances[str(guild_id)][str(user_id)] = new_balance
        self.save_data()

jam_tokens = JamTokens(bot)


# ... (jam_salary, jam_product_add, list_products, list_salaries,
#      change_salary, change_product_remove, change_product commands) ...

@bot.tree.command(name="jam-salary", description="Set up or create a role with a Jam Token salary.")
@commands.has_permissions(administrator=True)
async def jam_salary(interaction: discord.Interaction,
                     create_role: str = None,
                     existing_role: discord.Role = None,
                     salary: int = None):
    if not (create_role or existing_role) or not salary:
        return await interaction.response.send_message("Please provide either a role to create, an existing role, and a salary.")

    guild_id = str(interaction.guild.id)
    if guild_id not in jam_tokens.salaries:
        jam_tokens.salaries[guild_id] = {}

    if create_role:
        try:
            new_role = await interaction.guild.create_role(name=create_role)
            role_id = str(new_role.id)
            await interaction.response.send_message(f"Role '{create_role}' created successfully!")
        except discord.Forbidden:
            return await interaction.response.send_message("I don't have permission to create roles.")
    else:
        role_id = str(existing_role.id)

    salary_id = jam_tokens.generate_id()
    jam_tokens.salaries[guild_id][salary_id] = {
        "role_id": role_id,
        "salary": salary
    }
    jam_tokens.save_data()

    await interaction.followup.send_message(f"Salary of {salary} Jam Tokens set for role <@&{role_id}> with ID: {salary_id}")


@bot.tree.command(name="jam-product-add", description="Add a product to the Jam Token store.")
async def jam_product_add(interaction: discord.Interaction,
                         name: str,
                         details: str,
                         cost: int,
                         subscription: str = None,
                         if_bought_mention: discord.Member = None,
                         existing_role: discord.Role = None):  # Optional role
    guild_id = str(interaction.guild.id)
    if guild_id not in jam_tokens.products:
        jam_tokens.products[guild_id] = {}

    product_id = jam_tokens.generate_id()
    jam_tokens.products[guild_id][product_id] = {
        "name": name,
        "details": details,
        "cost": cost,
        "subscription": subscription,
        "if_bought_mention": if_bought_mention.id if if_bought_mention else None,
        "existing_role": existing_role.id if existing_role else None  # Store role ID
    }
    jam_tokens.save_data()

    await interaction.response.send_message(f"Product '{name}' added with ID: {product_id}")

@bot.tree.command(name="list-products", description="List all products in the Jam Token store.")
async def list_products(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id in jam_tokens.products:
        products = jam_tokens.products[guild_id]
        if products:
            embed = discord.Embed(title="Jam Token Products", color=discord.Color.green())
            for product_id, product_data in products.items():
                embed.add_field(
                    name=f"ID: {product_id}",
                    value=f"**Name:** {product_data['name']}\n"
                          f"**Details:** {product_data['details']}\n"
                          f"**Cost:** {product_data['cost']} Jam Tokens\n"
                          f"**Subscription:** {product_data['subscription'] if product_data['subscription'] else 'N/A'}\n"
                          f"**Mention on Buy:** <@!{product_data['if_bought_mention']}>" if product_data['if_bought_mention'] else "N/A",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("There are no products in the store yet.")
    else:
        await interaction.response.send_message("There are no products in the store yet.")


@bot.tree.command(name="list-salaries", description="List all salary setups.")
async def list_salaries(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id in jam_tokens.salaries:
        salaries = jam_tokens.salaries[guild_id]
        if salaries:
            embed = discord.Embed(title="Jam Token Salaries", color=discord.Color.blue())
            for salary_id, salary_data in salaries.items():
                role_id = salary_data["role_id"]
                salary = salary_data["salary"]
                embed.add_field(
                    name=f"ID: {salary_id}",
                    value=f"**Role:** <@&{role_id}>\n"
                          f"**Salary:** {salary} Jam Tokens per month",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("There are no salaries set up yet.")
    else:
        await interaction.response.send_message("There are no salaries set up yet.")


@bot.tree.command(name="change-salary", description="Change the salary for a specific role.")
@commands.has_permissions(administrator=True)
async def change_salary(interaction: discord.Interaction, id: str, salary: int):
    guild_id = str(interaction.guild.id)
    if guild_id in jam_tokens.salaries:
        if id in jam_tokens.salaries[guild_id]:
            jam_tokens.salaries[guild_id][id]["salary"] = salary
            jam_tokens.save_data()
            await interaction.response.send_message(f"Salary for ID {id} updated to {salary} Jam Tokens.")
        else:
            await interaction.response.send_message(f"Salary ID {id} not found.")
    else:
        await interaction.response.send_message("There are no salaries set up yet.")


@bot.tree.command(name="change-product-remove", description="Remove a product from the store.")
@commands.has_permissions(administrator=True)
async def change_product_remove(interaction: discord.Interaction, id: str):
    guild_id = str(interaction.guild.id)
    if guild_id in jam_tokens.products:
        if id in jam_tokens.products[guild_id]:
            del jam_tokens.products[guild_id][id]
            jam_tokens.save_data()
            await interaction.response.send_message(f"Product with ID {id} has been removed.")
        else:
            await interaction.response.send_message(f"Product ID {id} not found.")
    else:
        await interaction.response.send_message("There are no products in the store yet.")


@bot.tree.command(name="change-product", description="Change details of an existing product.")
@commands.has_permissions(administrator=True)
async def change_product(interaction: discord.Interaction, id: str, name: str = None, details: str = None,
                         cost: int = None, subscription: str = None, if_bought_mention: discord.Member = None):
    guild_id = str(interaction.guild.id)
    if guild_id in jam_tokens.products:
        if id in jam_tokens.products[guild_id]:
            product = jam_tokens.products[guild_id][id]
            if name:
                product["name"] = name
            if details:
                product["details"] = details
            if cost:
                product["cost"] = cost
            if subscription is not None:  # Allow setting subscription to None
                product["subscription"] = subscription
            if if_bought_mention:
                product["if_bought_mention"] = if_bought_mention.id

            jam_tokens.save_data()
            await interaction.response.send_message(f"Product with ID {id} has been updated.")
        else:
            await interaction.response.send_message(f"Product ID {id} not found.")
    else:
        await interaction.response.send_message("There are no products in the store yet.")


@bot.tree.command(name="buy", description="Buy a product from the Jam Token store.")
async def buy(interaction: discord.Interaction, product_id: str):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    if guild_id not in jam_tokens.products or product_id not in jam_tokens.products[guild_id]:
        return await interaction.response.send_message("Invalid product ID.")

    product = jam_tokens.products[guild_id][product_id]
    cost = product['cost']
    user_balance = jam_tokens.get_user_balance(user_id, guild_id)

    if user_balance < cost:
        return await interaction.response.send_message("You don't have enough Jam Tokens to buy this product.")

    view = discord.ui.View()

    async def buy_button_callback(interaction):
        jam_tokens.update_user_balance(user_id, guild_id, -cost)
        await interaction.response.send_message(f"You bought {product['name']} for {cost} Jam Tokens!")

        # Role handling (if applicable)
        if "existing_role" in product and product["existing_role"]:
            role = interaction.guild.get_role(int(product["existing_role"]))
            if role:
                await interaction.user.add_roles(role)

    async def balance_button_callback(interaction):
        balance = jam_tokens.get_user_balance(user_id, guild_id)
        await interaction.response.send_message(f"Your balance: {balance} Jam Tokens")

    buy_button = discord.ui.Button(label="Buy", style=discord.ButtonStyle.green)
    buy_button.callback = buy_button_callback
    view.add_item(buy_button)

    balance_button = discord.ui.Button(label="See Balance", style=discord.ButtonStyle.blurple)
    balance_button.callback = balance_button_callback
    view.add_item(balance_button)

    embed = discord.Embed(
        title=f"Buy {product['name']}",
        description=f"**Details:** {product['details']}\n"
                    f"**Price:** {cost} Jam Tokens\n"
                    f"**Subscription:** {product['subscription'] if product['subscription'] else 'N/A'}\n"
                    f"**Your Balance:** {user_balance} Jam Tokens",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="balance", description="Check your Jam Token balance.")
async def balance(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    balance = jam_tokens.get_user_balance(user_id, guild_id)
    await interaction.response.send_message(f"Your balance: {balance} Jam Tokens")


@bot.tree.command(name="person-salary-editor", description="Override your current role salary.")
@commands.has_permissions(administrator=True)
async def person_salary_editor(interaction: discord.Interaction, member: discord.Member, salary: int):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)

    jam_tokens.update_user_balance(user_id, guild_id, salary)  # Directly set the salary
    await interaction.response.send_message(f"{member.mention}'s salary has been set to {salary} Jam Tokens per month.")


# Replace with your bot token
bot.run("")
