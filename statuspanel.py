import discord
from discord.ext import commands, tasks
import datetime, psutil, time

STATUS_CHANNEL_ID = 123456789012345678  # ← pon aquí el canal donde irá el panel
MESSAGE_ID_FILE = "status_message.txt"

class StatusPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.update_panel.start()

    def cog_unload(self):
        self.update_panel.cancel()

    # Guardar ID del mensaje
    def save_message_id(self, msg_id):
        with open(MESSAGE_ID_FILE, "w") as f:
            f.write(str(msg_id))

    # Cargar ID del mensaje
    def load_message_id(self):
        try:
            with open(MESSAGE_ID_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return None

    # ============================
    # TAREA AUTOMÁTICA CADA 60s
    # ============================

    @tasks.loop(seconds=60)
    async def update_panel(self):
        await self.bot.wait_until_ready()

        channel = self.bot.get_channel(STATUS_CHANNEL_ID)
        if not channel:
            return

        msg_id = self.load_message_id()
        message = None

        if msg_id:
            try:
                message = await channel.fetch_message(msg_id)
            except:
                message = None

        # ============================
        # DATOS DEL BOT
        # ============================

        ping = round(self.bot.latency * 1000)
        servers = len(self.bot.guilds)

        # Uptime
        uptime_seconds = int(time.time() - self.start_time)
        uptime = str(datetime.timedelta(seconds=uptime_seconds))

        # RAM
        ram = psutil.virtual_memory()
        ram_used = round(ram.used / (1024**3), 2)
        ram_total = round(ram.total / (1024**3), 2)

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # DISCO
        disk = psutil.disk_usage("/")
        disk_used = round(disk.used / (1024**3), 2)
        disk_total = round(disk.total / (1024**3), 2)

        now = datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")

        # ============================
        # EMBED
        # ============================

        embed = discord.Embed(
            title="<a:alarmazul:1491858094043693177> Panel de Estado del Bot",
            color=discord.Color(0x0A3D62)
        )

        embed.add_field(name="<a:flechazul:1492182951532826684> Estado", value="Online", inline=True)
        embed.add_field(name="<:wifi:1492176492753588344> Ping", value=f"{ping} ms", inline=True)
        embed.add_field(name="<:discord:1483506738954244258>Servidores", value=str(servers), inline=True)

        embed.add_field(name="<:cronometro:1492176494422659087> Uptime", value=uptime, inline=False)

        embed.add_field(name="<:nose:1491491155198607440> RAM", value=f"{ram_used} GB / {ram_total} GB", inline=True)
        embed.add_field(name="<:candado:1491537429889552514> Disco", value=f"{disk_used} GB / {disk_total} GB", inline=True)
        embed.add_field(name="<:ruedita:1491491111557140570> CPU", value=f"{cpu_percent}%", inline=True)

         
        embed.set_footer(text="ModdyBot • Panel de estado")

        # Editar mensaje existente
        if message:
            try:
                await message.edit(embed=embed)
                return
            except:
                pass

        # Crear mensaje nuevo si no existe
        new_msg = await channel.send(embed=embed)
        self.save_message_id(new_msg.id)

    @update_panel.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(StatusPanel(bot))
