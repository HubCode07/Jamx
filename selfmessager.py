import discord
from discord.ext import commands
import google.generativeai as genai
from PIL import Image
import os

# Replace with your Gemini API key
genai.configure(api_key='')

# Model configuration
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

# Discord bot setup
conversation_history = {}  # Keyed by user ID
current_topic = {}  # Keyed by channel ID

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print("Bot is Up and Ready!")
        await self.tree.sync()

bot = MyBot()

async def generate_response(prompt, user_id, channel_id):
    user_history = conversation_history.get(user_id, [])
    channel_topic = current_topic.get(channel_id, None)
    enhanced_prompt = f"{prompt}\nPrevious conversation: {', '.join(user_history)}\nCurrent topic: {channel_topic} Personality: Your name is Jam, you should be like a friend on discord. Not a bunch of emojis please, but use some if needed."

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    response = model.generate_content(enhanced_prompt)
    return response.text

def conversation_needs_ai(content):
    # Basic keyword check to decide if AI intervention is needed
    keywords = ['help', 'question', 'issue', 'problem', 'how', 'what', 'why', 'who', 'jamx']
    return any(keyword in content.lower() for keyword in keywords)

async def process_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions or conversation_needs_ai(message.content):
        response = await generate_response(message.content, message.author.id, message.channel.id)
        await message.reply(response)
        conversation_history.setdefault(message.author.id, []).append(message.content)
    else:
        conversation_history.setdefault(message.author.id, []).append(message.content)

    for attachment in message.attachments:
        if attachment.content_type.startswith('image/'):
            try:
                filename = f"temp_image.{attachment.filename.split('.')[-1]}"
                await attachment.save(filename)
                img = Image.open(filename)
                os.remove(filename)
            except Exception as e:
                print(f"Error processing image: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message):
    await process_message(message)

bot.run('')
