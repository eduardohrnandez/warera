import discord
from discord import app_commands
from discord.ext import tasks, commands
import aiohttp
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
import os

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot Online"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def mantener_vivo():
    Thread(target=run_server).start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('DISCORD_TOKEN')
CANAL_ID = 1369374657563721780
URL_A_MONITOREAR = 'https://app.warera.io/site.webmanifest'
CABECERAS = {'User-Agent': 'Mozilla/5.0'}
tz_venezuela = pytz.timezone('America/Caracas')

# --- CLASE DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sincroniza los comandos / con Discord
        await self.tree.sync()
        print("Comandos sincronizados.")
        if not reporte_por_hora.is_running():
            reporte_por_hora.start()

bot = MyBot()

async def revisar_servidor():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(URL_A_MONITOREAR, headers=CABECERAS, timeout=10) as response:
                return response.status == 200
    except: return False

# --- PANEL CON AMBOS BOTONES ---
class PanelBotones(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="SÍ", style=discord.ButtonStyle.success, custom_id="btn_si")
    async def boton_si(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        estado = await revisar_servidor()
        hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
        embed = discord.Embed(
            title="🔎 Resultado de la Revisión",
            description="**¡El servidor de War Era está ONLINE! ✅**" if estado else "**El servidor de War Era está CAÍDO ❌**",
            color=discord.Color.green() if estado else discord.Color.red()
        )
        embed.set_footer(text=f"Última actualización: {hora} • Activo")
        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="NO", style=discord.ButtonStyle.danger, custom_id="btn_no")
    async def boton_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
        embed = discord.Embed(
            title="🛑 Revisión Cancelada",
            description="**Decidiste no revisar esta vez.**\n¡A seguir farmeando!",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Última actualización: {hora} • Activo")
        await interaction.response.edit_message(embed=embed, view=None)

# --- COMANDO SLASH /STATUS ---
@bot.tree.command(name="status", description="Muestra el panel para revisar el servidor de War Era")
async def status(interaction: discord.Interaction):
    hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
    embed = discord.Embed(
        title="⚙️ STATUS SERVER - WAR ERA ⚙️",
        description="¿Deseas Revisar si está activo el server?",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Última actualización: {hora} • Activo")
    await interaction.response.send_message(embed=embed, view=PanelBotones())

@tasks.loop(hours=1)
async def reporte_por_hora():
    canal = bot.get_channel(CANAL_ID)
    if canal:
        estado = await revisar_servidor()
        hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
        embed = discord.Embed(
            title="⏱️ Reporte Automático de la Hora",
            description="**✅ WAR ERA ESTÁ ONLINE ✅**" if estado else "**❌ WAR ERA ESTÁ CAÍDO ❌**",
            color=discord.Color.green() if estado else discord.Color.red()
        )
        embed.set_footer(text=f"Última actualización: {hora} • Activo")
        await canal.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} operando en la nube con Slash Commands')

mantener_vivo()
bot.run(TOKEN)



