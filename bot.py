import discord
from discord.ext import tasks, commands
import aiohttp
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
import os

# --- SERVIDOR WEB PARA MANTENERLO DESPIERTO EN RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "El bot de War Era está vivo y vigilando en la nube."

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def mantener_vivo():
    t = Thread(target=run_server)
    t.start()

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get(DISCORD_TOKEN)
CANAL_ID = 1369374657563721780
URL_A_MONITOREAR = 'https://app.warera.io/site.webmanifest'
CABECERAS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36'}

tz_venezuela = pytz.timezone('America/Caracas')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def revisar_servidor():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(URL_A_MONITOREAR, headers=CABECERAS, timeout=10) as response:
                return response.status == 200
    except Exception:
        return False

# --- CREACIÓN DE LOS BOTONES ---
class PanelBotones(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="SÍ (Revisar)", style=discord.ButtonStyle.success, custom_id="btn_si")
    async def boton_si(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Mostramos que el bot está "pensando"
        await interaction.response.defer() 
        
        estado = await revisar_servidor()
        hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
        
        embed = discord.Embed(
            title="🔎 Resultado de la Revisión",
            description="**¡El servidor de War Era está ONLINE! ✅**" if estado else "**El servidor de War Era está CAÍDO ❌**",
            color=discord.Color.green() if estado else discord.Color.red()
        )
        embed.set_footer(text=f"Última actualización: {hora} • Activo")
        
        # Transformamos el panel original: mostramos el resultado y quitamos los botones (view=None)
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
        
        # Editamos el panel original al instante y quitamos los botones (view=None)
        await interaction.response.edit_message(embed=embed, view=None)

# --- EVENTOS Y COMANDOS ---
@bot.event
async def on_ready():
    print(f'Bot profesional conectado en la nube como {bot.user}')
    bot.add_view(PanelBotones())
    reporte_por_hora.start()

@bot.command()
async def panel(ctx):
    """Genera el panel de control permanente con botones"""
    hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
    
    embed = discord.Embed(
        title="⚙️ STATUS SERVER - WAR ERA ⚙️",
        description="¿Deseas Revisar si está activo el server?",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Última actualización: {hora} • Activo")
    
    await ctx.send(embed=embed, view=PanelBotones())

@tasks.loop(hours=1)
async def reporte_por_hora():
    canal = bot.get_channel(CANAL_ID)
    if not canal:
        return

    estado = await revisar_servidor()
    hora = datetime.now(tz_venezuela).strftime("%I:%M %p")
    
    embed = discord.Embed(
        title="⏱️ Reporte Automático de la Hora",
        description="**✅ WAR ERA ESTÁ ONLINE ✅**" if estado else "**❌ WAR ERA ESTÁ CAÍDO ❌**",
        color=discord.Color.green() if estado else discord.Color.red()
    )
    embed.set_footer(text=f"Última actualización: {hora} • Activo")
    
    await canal.send(embed=embed)

# --- ENCENDIDO ---
mantener_vivo() # Arrancamos el servidor web falso
bot.run(TOKEN)  # Arrancamos el bot real