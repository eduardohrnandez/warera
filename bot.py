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

# --- SERVIDOR WEB (Para que Render no lo apague) ---
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
# ¡Aquí está el nuevo enlace directo al motor del juego!
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
    inicio = time.time() # Empezamos a contar los milisegundos
    try:
        async with aiohttp.ClientSession() as session:
            # Le damos máximo 5 segundos para responder. Si tarda más, está colapsado.
            async with session.get(URL_A_MONITOREAR, headers=CABECERAS, timeout=5) as response:
                fin = time.time() 
                ping_ms = int((fin - inicio) * 1000) 
                
                # Si responde con un código menor a 500, el motor está vivo y procesando.
                if response.status < 500:
                    return {"estado": "online", "ping": ping_ms}
                else:
                    return {"estado": "caido", "ping": ping_ms}
    except: 
        # Si la conexión falla por completo o da Timeout
        return {"estado": "caido", "ping": 0}

# --- GENERADOR DE RESPUESTAS VISUALES ---
def generar_embed_estado(resultado):
    hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
    
    if resultado["estado"] == "online":
        if resultado["ping"] < 800: # Rápido (Menos de 0.8s)
            embed = discord.Embed(
                title="🔎 Resultado de la Revisión",
                description=f"**¡El servidor está ONLINE y estable! ✅**\n⚡ Velocidad de respuesta: `{resultado['ping']} ms`",
                color=discord.Color.green()
            )
        else: # Lento / Pegado (Más de 0.8s)
            embed = discord.Embed(
                title="⚠️ Servidor Lento / Pegado",
                description=f"**El servidor responde, pero está sufriendo lag 🟡**\n🐌 Velocidad de respuesta: `{resultado['ping']} ms` (Muy alto)",
                color=discord.Color.orange()
            )
    else: # Caído o colapsado
        embed = discord.Embed(
            title="🛑 Servidor Caído",
            description="**El servidor de War Era no responde o está CAÍDO ❌**",
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

# --- REPORTE AUTOMÁTICO ---
@tasks.loop(hours=1)
async def reporte_por_hora():
    canal = bot.get_channel(CANAL_ID)
    if canal:
        resultado = await revisar_servidor()
        embed = generar_embed_estado(resultado)
        embed.title = "⏱️ Reporte Automático de la Hora" 
        await canal.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} operando en la nube con medidor de Ping y API directa')

mantener_vivo()
bot.run(TOKEN)
