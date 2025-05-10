import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from flask import Flask
import threading
import asyncio

# ✅ Ajout de l'intention message_content
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Crée une instance Flask pour l'hébergement sur Render si nécessaire
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"

# Fonction pour démarrer Flask
def run_flask():
    port = int(os.environ.get('PORT', 5000))  # Utilisation du port défini sur Render
    app.run(host='0.0.0.0', port=port)

# Fonction pour démarrer le bot Discord
async def start_bot():
    TOKEN = os.environ['NKSV2']  # Assure-toi que cette variable est bien définie sur Render
    await bot.start(TOKEN)

# Chargement des stats
def load_stats():
    try:
        with open("stats.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Sauvegarde des stats
def save_stats(data):
    with open("stats.json", "w") as f:
        json.dump(data, f, indent=4)

stats = load_stats()

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
        if user_id not in stats:
            await interaction.response.send_message(f"❌ je suis dsl mais {membre.display_name} sert à rien 😢.", ephemeral=True)
            return

        data = stats[user_id]
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
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Une erreur est survenue en traitant la commande.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Une erreur est survenue en traitant la commande.", ephemeral=True)

# ⚙️ /setstats command (admin only)
@bot.tree.command(name="setstats", description="Modifier les stats d’un chauffeur (Admin only).")
@app_commands.describe(
    membre="Le membre à modifier",
    solo="Victoires en solo",
    duo="Victoires en duo",
    km="Kilomètres parcourus",
    vehicle_preference="Véhicule préféré"
)
async def setstats(
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
        stats[user_id] = {
            "solo": solo,
            "duo": duo,
            "km": km,
            "vehicle_preference": vehicle_preference
        }
        save_stats(stats)

        await interaction.response.send_message(f"✅ Statistiques de {membre.display_name} mises à jour.")

    except Exception as e:
        print(f"Erreur dans la commande setstats : {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Une erreur est survenue en traitant la commande.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Une erreur est survenue en traitant la commande.", ephemeral=True)

# 👫 /equipe command (admin only)
@bot.tree.command(name="equipe", description="Affiche les équipes du Challenge Duo (admin only).")
@app_commands.checks.has_permissions(administrator=True)
async def equipe(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="📢 Équipes aléatoires du Challenge Duo 🛣️",
            color=0xF1E0C6,
            description="""🎲 Le tirage au sort est terminé !
Voici les équipes tirées au sort pour ce challenge :

━━━━━━━━━━━━━━━━━━

👥 Équipe 1 :
🧑‍🤝‍🧑 Bysneaks & Roni 

━━━━━━━━━━━━━━━━━━ 

👥 Équipe 2 :
🧑‍🤝‍🧑 Xenox & Allan

━━━━━━━━━━━━━━━━━━

👥 Équipe 3 :
🧑‍🤝‍🧑 Galax & Anou

━━━━━━━━━━━━━━━━━━

📅 Bonne chance à toutes les équipes pour les 2 prochaines semaines !
🚛 Que la meilleure équipe gagne !
"""
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Erreur dans la commande equipe : {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Une erreur est survenue en traitant la commande.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Une erreur est survenue en traitant la commande.", ephemeral=True)

# Gérer erreur si non-admin
@equipe.error
async def equipe_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ ohhhh, touche pas à ça attention hein.😫", ephemeral=True)

# Démarre Flask dans un thread séparé pour ne pas bloquer l'exécution du bot
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Démarre le bot
asyncio.run(start_bot())
