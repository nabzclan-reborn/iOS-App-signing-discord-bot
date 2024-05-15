import discord
import requests
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Replace these with your actual tokens
NABZLINKS_TOKEN = "Nabzlinks token here"
API_ARIES_TOKEN = "API Aries token here"
DISCORD_TOKEN = "discord token here"

# URLs
SHORTEN_API_URL = "https://nabz.link/api"
SIGNING_API_URL = "https://api.api-aries.online/v1/cococloud/app-signer"
CERT_STATUS_URL = "https://api.cococloud-signing.online/cert-status/api"

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command(name='sign')
async def sign_app(ctx):
    if not ctx.message.attachments:
        await ctx.send("Please attach an IPA file. - [YouTube Tutorial](https://m.youtube.com/watch?v=Tdt13UOX3xI&feature=youtu.be)")
        return

    process_embed = discord.Embed(title="Signing App", description="Signing the app. Please wait...")
    process_message = await ctx.send(embed=process_embed)

    attachment_url = ctx.message.attachments[0].url

    # Shorten the URL
    try:
        params = {
            "api": NABZLINKS_TOKEN,
            "url": attachment_url,
            "type": 0
        }
        shorten_response = requests.get(SHORTEN_API_URL, params=params)
        shorten_response.raise_for_status()
        shortened_url = shorten_response.json().get("shortenedUrl")
        if not shortened_url:
            await process_message.edit(content="Error shortening the URL. Please try again.")
            return

        api_url = f"{SIGNING_API_URL}?app={shortened_url}"
        process_embed.title = "Shortened URL"
        process_embed.description = "URL has been shortened successfully. Please wait..."
        await process_message.edit(embed=process_embed)
    except requests.exceptions.RequestException as e:
        print(f"Error shortening URL: {e}")
        await process_message.edit(content="Error shortening the URL. Please try again.")
        return

    headers = {"APITOKEN": API_ARIES_TOKEN}

    # Request app signing
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        json_response = response.json()

        bundle_id = json_response.get("bundle_id", "N/A")
        plist_url = json_response.get("plist_url", "N/A")

        # Get certificate status
        try:
            cert_status_response = requests.get(CERT_STATUS_URL, headers=headers)
            cert_status_response.raise_for_status()
            cert_status_json = cert_status_response.json()
            certificate_status = cert_status_json.get("CertificateStatus", "N/A")
            certificate_name = cert_status_json.get("CertificateName", "N/A")

            if certificate_status == 'Signed':
                certificate_status = 'Signed 🟢'
            elif certificate_status == 'Revoked':
                certificate_status = 'Revoked 🔴'
        except requests.exceptions.RequestException as e:
            print(f"Error getting certificate status: {e}")
            certificate_status = 'Unknown'
            certificate_name = 'Unknown'

        process_embed.title = "App Signing Information"
        process_embed.description = "The app has been successfully signed:"
        process_embed.add_field(name="Certificate Name:", value=certificate_name, inline=False)
        process_embed.add_field(name="Status:", value=certificate_status, inline=False)
        process_embed.add_field(name="Bundle ID:", value=bundle_id, inline=False)
        process_embed.add_field(name="Signed IPA File:", value=f"[Download File]({shortened_url})", inline=False)
        process_embed.add_field(name="Install on device:", value=f"[Install](http://api.cococloud-signing.online/files/enterprise/install-plist.php?app={plist_url})", inline=False)
        await process_message.edit(embed=process_embed)

    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        await process_message.edit(content="Error signing the app. Please try again.")

bot.run(DISCORD_TOKEN)
