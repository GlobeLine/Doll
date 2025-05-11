import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
import threading
import asyncio
from tinydb import TinyDB, Query

# Initialisation DB
db = TinyDB("stats.json")
Stats = Query()

# Fonctions de stats (remplacent l'ancien système fichier)
def get_stats(user_id):
    result = db.get(Stats.user_id == user_id)
    return result if result else {"solo": 0, "duo": 0, "km": 0, "vehicle_preference": "Aucun"}

def set_stats(user_id, solo, duo, km, vehicle_preference):
    if db.contains(Stats.user_id == user_id):
        db.update({
            "solo": solo,
            "duo": duo,
            "km": km,
            "vehicle_preference": vehicle_preference
        }, Stats.user_id == user_id)
    else:
        db.insert({
            "user_id": user_id,
            "solo": solo,
            "duo": duo,
            "km": km,
            "vehicle_preference": vehicle_preference
        })

# Intents Discord
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Flask pour Render
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

async def start_bot():
    TOKEN = os.environ['NKSV2']
    await bot.start(TOKEN)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")

# 📊 /stats command
@bot.tree.command(name="stats", description="Afficher les statistiques d'un chauffeur.")
@app_commands.describe(membre="Le membre dont afficher les statistiques.")
async def stats_command(interaction: discord.Interaction, membre: discord.Member = None):
    membre = membre or interaction.user
    user_id = str(membre.id)

    try:
        data = get_stats(user_id)
        if not data or all(val == 0 or val == "Aucun" for val in data.values()):
            await interaction.response.send_message(f"❌ je suis dsl mais {membre.display_name} sert à rien 😢.", ephemeral=True)
            return

        embed = discord.Embed(title=f"🪪 carte conducteur de {membre.display_name}", color=0xF1E0C6)
        embed.set_thumbnail(url=membre.avatar.url)
        embed.add_field(name="🏆 Victoires Solo", value=data.get("solo", 0), inline=False)
        embed.add_field(name="🤝 Victoires Duo", value=data.get("duo", 0), inline=False)
        embed.add_field(name="🛣️ Kilomètres Parcourus (réél)", value=f"{data.get('km', 0)} km", inline=False)
        embed.add_field(name="🚛 Véhicule Préféré", value=data.get("vehicle_preference", "Aucun"), inline=False)
        embed.set_footer(text="Dollyprane Transport")

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        print(f"Erreur dans la commande stats : {e}")
        await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)

# ⚙️ /setstats command
@bot.tree.command(name="setstats", description="Modifier les stats d’un chauffeur (Admin only).")
@app_commands.describe(
    membre="Le membre à modifier",
    solo="Victoires en solo",
    duo="Victoires en duo",
    km="Kilomètres parcourus",
    vehicle_preference="Véhicule préféré"
)
async def setstats_command(
    interaction: discord.Interaction,
    membre: discord.Member,
    solo: int,
    duo: int,
    km: int,
    vehicle_preference: str
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ ohhhh, touche pas à ça attention hein.😫", ephemeral=True)
        return

    try:
        user_id = str(membre.id)
        set_stats(user_id, solo, duo, km, vehicle_preference)
        await interaction.response.send_message(f"✅ Statistiques de {membre.display_name} mises à jour.")
    except Exception as e:
        print(f"Erreur dans la commande setstats : {e}")
        await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)

# 👫 /equipe command
@bot.tree.command(name="equipe", description="Affiche les équipes du Challenge Duo (admin only).")
@app_commands.checks.has_permissions(administrator=True)
async def equipe(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="📢 Équipes aléatoires du Challenge Duo 🛣️",
            color=0xF1E0C6,
            description="""🎲 Le tirage au sort est terminé !

━━━━━━━━━━━━━━━━━━
👥 Équipe 1 :
🧑‍🤝‍🧑 Blue_Labelrun & AyZou 
━━━━━━━━━━━━━━━━━━ 
👥 Équipe 2 :
🧑‍🤝‍🧑 Antoine & galaxiew
━━━━━━━━━━━━━━━━━━
👥 Équipe 3 :
🧑‍🤝‍🧑 Roni & Allan
━━━━━━━━━━━━━━━━━━
👥 Équipe 4 :
🧑‍🤝‍🧑 inconnukoro & chaokopops
━━━━━━━━━━━━━━━━━━
👥 Équipe 5 :
🧑‍🤝‍🧑 SKOLY & Xenox
━━━━━━━━━━━━━━━━━━

📅 Bonne chance à toutes les équipes pour les 2 prochaines semaines !
🚛 Que la meilleure équipe gagne !
"""
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Erreur dans la commande equipe : {e}")
        await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)

@equipe.error
async def equipe_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ ohhhh, touche pas à ça attention hein.😫", ephemeral=True)

# Flask sur thread à part
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Lancement bot
asyncio.run(start_bot())
