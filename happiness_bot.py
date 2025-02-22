from dotenv import load_dotenv
import os

# Laad de variabelen uit het .env-bestand
load_dotenv()

import discord
from discord import app_commands
from flask import Flask, request, jsonify
import requests
import threading

# --- Algemene functies ---


# Functie om een celebration op te halen van de API
def get_random_celebration():
    url = "https://prbztfoixpktyel-timcassauwers.adb.eu-frankfurt-1.oraclecloudapps.com/ords/guerrilla/guerrilla/celebrate/random"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Controleer op fouten
        data = response.json()

        # Haal de eerste celebration, description en image uit de lijst
        if data.get('items') and len(data['items']) > 0:
            celebration = data['items'][0]['celebration']
            description = data['items'][0]['description']
            image_url = data['items'][0]['image']  # Haal de image URL op
            return celebration, description, image_url
        else:
            return "Geen celebration gevonden", "Probeer het later opnieuw!", None
    except requests.exceptions.RequestException as e:
        print(f"Fout bij het ophalen van de celebration: {e}")
        return "Kon geen celebration ophalen", "Probeer het later opnieuw!", None


# --- Discord Bot ---

# Vervang dit met je eigen Discord bot-token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Maak een Discord-client aan met intents
intents = discord.Intents.default()
discord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_client)


# Functie om een celebration-bericht te sturen in Discord
async def send_discord_celebration(interaction):
    celebration, description, image_url = get_random_celebration()
    embed = discord.Embed(title=f"🎉 **{celebration}** 🎉",
                          description=description,
                          color=discord.Color.gold())
    if image_url:
        embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)


# Event wanneer de Discord bot online komt
@discord_client.event
async def on_ready():
    print(f'Discord bot is ingelogd als {discord_client.user}')
    await tree.sync()


# Slash command voor /celebrate in Discord
@tree.command(name="celebrate", description="Start een celebration!")
async def discord_celebrate_command(interaction):
    await send_discord_celebration(interaction)


# --- Slack Bot ---

# Flask-app voor Slack
slack_app = Flask(__name__)


# Route om Slack Slash Commands af te handelen
@slack_app.route('/slack/celebrate', methods=['POST'])
def slack_celebrate():
    celebration, description, image_url = get_random_celebration()
    message = {
        "response_type":
        "in_channel",  # Bericht is zichtbaar voor iedereen
        "blocks": [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🎉 *{celebration}* 🎉\n{description}"
            }
        }]
    }
    if image_url:
        message['blocks'].append({
            "type": "image",
            "image_url": image_url,
            "alt_text": celebration
        })
    return jsonify(message)


# --- Start de bots ---


def run_flask():
    slack_app.run(port=3000)


if __name__ == '__main__':
    # Start de Flask-server voor Slack in een aparte thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start de Discord bot
    discord_client.run(DISCORD_TOKEN)
