import discord
from discord import app_commands
from discord.ext import tasks, commands
import aiohttp
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
import os
import time

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot Status Online"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def mantener_vivo():
    Thread(target=run_server).start()

# --- CONFIGURACIÓN PRINCIPAL ---
TOKEN = os.environ.get('DISCORD_TOKEN')
CANAL_ID = 1369374657563721780
URL_A_MONITOREAR = 'https://api3.warera.io/trpc/map.getMapData'
CABECERAS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
tz_venezuela = pytz.timezone('America/Caracas')

# --- CLASE DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Comandos / sincronizados.")
        if not reporte_por_hora.is_running():
            reporte_por_hora.start()

bot = MyBot()

# --- FUNCIÓN DE REVISIÓN CON CRONÓMETRO ---
async def revisar_servidor():
    inicio = time.time() 
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(URL_A_MONITOREAR, headers=CABECERAS, timeout=5) as response:
                fin = time.time() 
                ping_ms = int((fin - inicio) * 1000) 
                
                if response.status < 500:
                    return {"estado": "online", "ping": ping_ms}
                else:
                    return {"estado": "caido", "ping": ping_ms}
    except: 
        return {"estado": "caido", "ping": 0}

# --- NUEVO RADAR DE LAG (Calibrado) ---
def generar_embed_estado(resultado):
    hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
    
    if resultado["estado"] == "online":
        ping = resultado["ping"]
        
        if ping < 1000: 
            embed = discord.Embed(
                title="🔎 Resultado de la Revisión",
                description=f"**¡El servidor está ONLINE y estable! ✅**\n⚡ Velocidad de respuesta: `{ping} ms`",
                color=discord.Color.green()
            )
        elif ping < 2000: 
            embed = discord.Embed(
                title="⚠️ Servidor Inestable",
                description=f"**El servidor responde, pero con algo de lag 🟡**\n🐢 Velocidad de respuesta: `{ping} ms` (Inestable)",
                color=discord.Color.yellow()
            )
        else: 
            embed = discord.Embed(
                title="⚠️ Servidor Lento / Pegado",
                description=f"**El servidor responde, pero está sufriendo MUCHO lag 🟠**\n🐌 Velocidad de respuesta: `{ping} ms` (Injugable)",
                color=discord.Color.orange()
            )
    else: 
        embed = discord.Embed(
            title="🛑 Servidor Caído",
            description="**El motor de War Era no responde o está CAÍDO ❌**",
            color=discord.Color.red()
        )
        
    embed.set_footer(text=f"Última actualización: {hora} • Activo")
    return embed

# --- PANEL DE BOTONES INTERACTIVOS ---
class PanelBotones(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="SÍ (Revisar)", style=discord.ButtonStyle.success, custom_id="btn_si")
    async def boton_si(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        resultado = await revisar_servidor()
        embed = generar_embed_estado(resultado)
        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="NO", style=discord.ButtonStyle.danger, custom_id="btn_no")
    async def boton_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
        embed = discord.Embed(
            title="🛑 Revisión Cancelada",
            description="**Decidiste no revisar esta vez.**\n¡A seguir farmeando!",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Última actualización: {hora} • Activo")
        await interaction.response.edit_message(embed=embed, view=None)

# --- COMANDO SLASH /STATUS ---
@bot.tree.command(name="status", description="Muestra el panel de control para revisar el servidor de War Era")
async def status(interaction: discord.Interaction):
    hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
    embed = discord.Embed(
        title="⚙️ STATUS SERVER - WAR ERA ⚙️",
        description="¿Deseas Revisar si está activo el server?",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Última actualización: {hora} • Activo")
    await interaction.response.send_message(embed=embed, view=PanelBotones())

# --- REPORTE AUTOMÁTICO (AHORA INMORTAL) ---
@tasks.loop(hours=1)
async def reporte_por_hora():
    try: # El escudo anti-crasheo
        canal = bot.get_channel(CANAL_ID)
        if canal:
            resultado = await revisar_servidor()
            embed = generar_embed_estado(resultado)
            embed.title = "⏱️ Reporte Automático de la Hora" 
            await canal.send(embed=embed)
    except Exception as e:
        print(f"Error detectado y bloqueado en el reporte automático: {e}")

@reporte_por_hora.before_loop
async def esperar_conexion():
    # Obligamos al bot a esperar a estar 100% online antes de empezar a contar la hora
    await bot.wait_until_ready() 

@bot.event
async def on_ready():
    print(f'Bot {bot.user} operando. Loop automático protegido.')

mantener_vivo()
bot.run(TOKEN)
