import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime
from config import *

# ============================
# CONFIGURACIÓN DEL BOT
# ============================

intents = discord.Intents.all()
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

# ============================
# SISTEMA DE BACKUPS GLOBAL
# ============================

class BackupSystem:
    def __init__(self):
        self.backups = self.load_backups()

    def load_backups(self):
        try:
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_backups(self):
        with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.backups, f, indent=2, ensure_ascii=False)

    async def create_backup(self, guild):
        backup_data = {
            'guild_id': str(guild.id),
            'guild_name': guild.name,
            'created_at': datetime.now().isoformat(),
            'channels': [],
            'categories': [],
            'roles': [],
            'emojis': [],
            'guild_settings': {
                'verification_level': str(guild.verification_level),
                'default_notifications': str(guild.default_notifications),
                'explicit_content_filter': str(guild.explicit_content_filter),
                'afk_timeout': guild.afk_timeout,
                'afk_channel': str(guild.afk_channel.id) if guild.afk_channel else None,
                'system_channel': str(guild.system_channel.id) if guild.system_channel else None,
                'rules_channel': str(guild.rules_channel.id) if guild.rules_channel else None,
                'public_updates_channel': str(guild.public_updates_channel.id) if guild.public_updates_channel else None
            }
        }

        # Roles
        for role in guild.roles:
            if role.name != '@everyone':
                backup_data['roles'].append({
                    'id': str(role.id),
                    'name': role.name,
                    'permissions': role.permissions.value,
                    'color': role.color.value,
                    'hoist': role.hoist,
                    'mentionable': role.mentionable,
                    'position': role.position
                })

        # Categorías
        for category in guild.categories:
            category_data = {
                'id': str(category.id),
                'name': category.name,
                'position': category.position,
                'overwrites': []
            }
            for target, overwrite in category.overwrites.items():
                category_data['overwrites'].append({
                    'id': str(target.id),
                    'type': 'role' if isinstance(target, discord.Role) else 'member',
                    'allow': overwrite.pair()[0].value,
                    'deny': overwrite.pair()[1].value
                })
            backup_data['categories'].append(category_data)

        # Canales
        for channel in guild.channels:
            if not isinstance(channel, discord.CategoryChannel):
                channel_data = {
                    'id': str(channel.id),
                    'name': channel.name,
                    'type': 'text' if isinstance(channel, discord.TextChannel) else 'voice',
                    'position': channel.position,
                    'category_id': str(channel.category.id) if channel.category else None,
                    'overwrites': []
                }

                if isinstance(channel, discord.TextChannel):
                    channel_data.update({
                        'topic': channel.topic,
                        'slowmode_delay': channel.slowmode_delay,
                        'nsfw': channel.nsfw
                    })
                elif isinstance(channel, discord.VoiceChannel):
                    channel_data.update({
                        'bitrate': channel.bitrate,
                        'user_limit': channel.user_limit
                    })

                for target, overwrite in channel.overwrites.items():
                    channel_data['overwrites'].append({
                        'id': str(target.id),
                        'type': 'role' if isinstance(target, discord.Role) else 'member',
                        'allow': overwrite.pair()[0].value,
                        'deny': overwrite.pair()[1].value
                    })

                backup_data['channels'].append(channel_data)

        # Emojis
        for emoji in guild.emojis:
            backup_data['emojis'].append({
                'id': str(emoji.id),
                'name': emoji.name,
                'animated': emoji.animated,
                'url': str(emoji.url)
            })

        return backup_data


backup_system = BackupSystem()

# ============================
# EVENTO ON_READY
# ============================

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} está conectado y listo!')
    bot.start_time = datetime.now()

    cogs_to_load = [
        'cogs.backup_commands',
        'cogs.moderation_commands',
        'cogs.utility_commands',
        'cogs.admin_commands',
        'cogs.server_management',
        'cogs.user_management',
        'cogs.help_commands',
        'cogs.id',
        'cogs.guia',
        'cogs.copy',
        'cogs.blacklist',
        'cogs.antiflood',
        'cogs.status',
        'cogs.antiraid',
        'cogs.administ',
        'cogs.bienvenidas',
        'cogs.antibots',
        'cogs.Rename',
        'cogs.stats',
        'cogs.antialts',
        'cogs.antihacks'
    ]

    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            print(f'✅ Cog {cog} cargado exitosamente')
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f'❌ Error cargando {cog}: {e}')

    await asyncio.sleep(3)
    try:
        synced = await bot.tree.sync()
        print(f'🔄 Sincronizados {len(synced)} comandos slash')
    except Exception as e:
        print(f'❌ Error al sincronizar comandos: {e}')

# ============================
# MODO MANTENIMIENTO
# ============================

async def check_maintenance():
    try:
        with open('maintenance.json', 'r') as f:
            data = json.load(f)
            return data.get('enabled', False), data.get('message', 'Bot en mantenimiento')
    except FileNotFoundError:
        return False, ""

@bot.tree.interaction_check
async def global_interaction_check(interaction: discord.Interaction):
    is_maintenance, maintenance_msg = await check_maintenance()
    if is_maintenance and interaction.user.id not in ADMIN_IDS:
        embed = discord.Embed(
            title="🔧 Modo Mantenimiento",
            description=f"```\n{maintenance_msg}\n```\nEl bot está temporalmente fuera de servicio.",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="⏰ Disponibilidad",
            value="Todos los comandos están deshabilitados durante el mantenimiento.",
            inline=False
        )
        embed.set_footer(text="Solo los administradores del bot pueden usar comandos en este momento")

        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass
        return False

    return True

# ============================
# MANEJO GLOBAL DE ERRORES
# ============================

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    embed = discord.Embed(
        title="❌ Error en el Comando",
        description="Ha ocurrido un error al ejecutar el comando.",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )

    if isinstance(error, discord.app_commands.CheckFailure):
        embed.description = "No tienes permisos para usar este comando."
    elif isinstance(error, discord.app_commands.CommandOnCooldown):
        embed.description = f"Comando en cooldown. Inténtalo en {error.retry_after:.1f} segundos."
    else:
        embed.description = f"```\n{str(error)[:1900]}\n```"

    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)
    except:
        pass

# ============================
# EVENTOS JOIN / LEAVE
# ============================

@bot.event
async def on_guild_join(guild):
    embed = discord.Embed(
        title="🎉 ¡Gracias por Invitarme!",
        description=f"He sido añadido a **{guild.name}**",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )

    embed.add_field(name="🚀 Comenzar", value="Usa `/help` para ver todos los comandos disponibles.", inline=True)
    embed.add_field(name="💾 Backups", value="Usa `/createbackup` para crear tu primer backup.", inline=True)
    embed.add_field(name="🛡️ Moderación", value="Configura permisos para usar comandos de moderación.", inline=True)
    embed.add_field(name="❓Tienes Dudas", value="Accede a nuestro panel web https://antiraidextreme.vercel.app/", inline=True)
    embed.add_field(name="📊 Estadísticas", value=f"• **Servidores:** {len(bot.guilds):,}\n• **Usuarios:** {sum(g.member_count for g in bot.guilds):,}", inline=False)

    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    embed.set_footer(text=f"ID del Servidor: {guild.id}")

    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        try:
            await guild.system_channel.send(embed=embed)
        except:
            pass
    else:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                    break
                except:
                    continue

@bot.event
async def on_guild_remove(guild):
    pass

# ============================
# EJECUTAR EL BOT
# ============================

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {e}")
        print("Verifica que el token esté configurado correctamente en el archivo .env")
