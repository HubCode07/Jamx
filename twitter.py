import discord
from discord import app_commands
import datetime
from discord.ext import commands, tasks


# Set up the Discord bot
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="!", intents=intents)


# Define the /tweet command
@bot.tree.command(name="tweet", description="Post a tweet")
@app_commands.describe(
    content="The text content of the tweet",
    image="The image to include in the tweet (optional)",
    video="The video to include in the tweet (optional)",
)
async def tweet(interaction: discord.Interaction, content: str, image: discord.Attachment = None, video: discord.Attachment = None):
    await interaction.response.defer()  # Defer the response to prevent the timeout error

    try:
        # Create the tweet embed
        tweet_embed = discord.Embed(
            title=f"{interaction.user.name}'s Tweet",
            description=content,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow(),
        )
        tweet_embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

        # Add image or video if provided
        if image:
            tweet_embed.set_image(url=image.url)
        elif video:
            tweet_embed.add_field(name="Video", value=video.url, inline=False)

        # Create the view with buttons
        view = TweetView(interaction.user)
        tweet_message = await interaction.followup.send(embed=tweet_embed, view=view)

        # Save the tweet message ID for later use
        view.tweet_message_id = tweet_message.id

    except Exception as e:
        error_embed = discord.Embed(
            title="Error",
            description=f"An error occurred while posting the tweet: {str(e)}",
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=error_embed)

# Define the tweet view and buttons
class TweetView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)  # No timeout for the buttons
        self.user = user
        self.likes = 0
        self.tweet_message_id = None

    @discord.ui.button(label="Quote", style=discord.ButtonStyle.primary)
    async def quote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the original tweet message
        tweet_message = await interaction.channel.fetch_message(self.tweet_message_id)

        # Quote the tweet and send it as a reply
        quote_embed = discord.Embed(
            title="Quote Tweet",
            description=f"Replying to {self.user.mention}'s tweet:",
            color=discord.Color.green(),
        )
        quote_embed.add_field(name="Tweet", value=tweet_message.embeds[0].description)

        await interaction.response.send_message(embed=quote_embed, mention_author=False)

    @discord.ui.button(label="Likes", style=discord.ButtonStyle.secondary)
    async def likes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the original tweet message
        tweet_message = await interaction.channel.fetch_message(self.tweet_message_id)

        # Update the number of likes and edit the tweet message
        self.likes += 1
        tweet_embed = tweet_message.embeds[0]
        tweet_embed.set_footer(text=f"Likes: {self.likes}")
        await tweet_message.edit(embed=tweet_embed, view=self)

        await interaction.response.send_message(f"{interaction.user.mention} liked the tweet!", ephemeral=True)

# Start the Discord bot
bot.run("")