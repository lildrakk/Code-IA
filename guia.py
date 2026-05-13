import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

# ============================
# CONFIGURACIÓN DE ACCESO
# ============================

# IDs autorizados
AUTHORIZED_ADMIN_IDS = [1330486565528670284, 1394342273919225959]

def is_authorized_admin():
    """Check para permitir solo a IDs autorizados."""
    def predicate(interaction: discord.Interaction):
        return interaction.user.id in AUTHORIZED_ADMIN_IDS
    return app_commands.check(predicate)

# ============================
# COG PRINCIPAL
# ============================

class SlashAdminToolbox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ============================
    # EMBED DE LA GUÍA
    # ============================

    def create_admin_guide_embed(self, admin_user_id: int) -> discord.Embed:
        
        embed = discord.Embed(
            title="📘 Guía de Comandos de Administración (OWN)",
            description="Comandos exclusivos para administradores del bot. Úsalos con responsabilidad.",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        # Thumbnail y autor
        if self.bot.user and self.bot.user.avatar:
            avatar_url = self.bot.user.avatar.url
            embed.set_thumbnail(url=avatar_url)
            embed.set_author(name="Panel de Administración del Bot", icon_url=avatar_url)
        else:
            embed.set_author(name="Panel de Administración del Bot")

        # 1. Estadísticas globales
        embed.add_field(
            name="📊 Estadísticas y Monitoreo Global",
            value=(
                "**Comando** | **Descripción**\n"
                "---|---\n"
                "`/globalstats` | Estadísticas completas del bot.\n"
                "`/serverlist [página]` | Lista paginada de servidores."
            ),
            inline=False
        )

        # 2. Modo mantenimiento
        embed.add_field(
            name="🛠️ Modo Mantenimiento",
            value=(
                "**Comando** | **Uso**\n"
                "---|---\n"
                "`/maintenance <acción> [mensaje]` | Gestiona el modo mantenimiento.\n"
                "**Acciones:** `enable`, `disable`, `status`."
            ),
            inline=False
        )

        # 3. Gestión avanzada de servidores
        embed.add_field(
            name="🛰️ Gestión Avanzada de Servidores (`/globalmanagement`)",
            value=(
                "Requiere **ID del servidor**.\n"
                "**Acción** | **Descripción**\n"
                "---|---\n"
                "`info` | Información detallada.\n"
                "`leave` | Salir del servidor.\n"
                "`channels` | Lista de canales.\n"
                "`roles` | Lista de roles.\n"
                "`members` | Top 10 miembros con más roles."
            ),
            inline=False
        )

        # 4. Backups
        embed.add_field(
            name="💾 Gestión de Backups (`/globalbackup`)",
            value=(
                "Requiere **ID del servidor**.\n"
                "**Acción** | **Descripción**\n"
                "---|---\n"
                "`create <nombre>` | Crear backup.\n"
                "`list` | Listar backups.\n"
                "`info <nombre>` | Info de un backup.\n"
                "`delete <nombre>` | Eliminar backup.\n"
                "`stats` | Estadísticas del servidor."
            ),
            inline=False
        )

        # 5. Blacklist
        embed.add_field(
            name="🚫 Comando de Blacklist",
            value=(
                "**Comando** | **Descripción**\n"
                "---|---\n"
                "`/blacklist <usuario> <acción>` | Gestiona la blacklist global.\n"
                "**Acciones:** `añadir`, `eliminar`, `estado`."
            ),
            inline=False
        )

        embed.set_footer(text=f"Guía solicitada por el Administrador: {admin_user_id}")

        return embed

    # ============================
    # COMANDO /sendguide
    # ============================

    @app_commands.command(
        name="sendguide",
        description="[OWN] Envía la guía de comandos de administración a un usuario por ID."
    )
    @app_commands.describe(user_id="ID del usuario al que enviar la guía.")
    @is_authorized_admin()
    async def send_admin_guide(self, interaction: discord.Interaction, user_id: str):

        await interaction.response.defer(ephemeral=True, thinking=True)

        # Validar ID
        try:
            target_id = int(user_id)
        except ValueError:
            error_embed = discord.Embed(
                title="❌ Error de ID",
                description="El ID debe ser un número válido.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        # Obtener usuario
        target_user = self.bot.get_user(target_id)
        if not target_user:
            try:
                target_user = await self.bot.fetch_user(target_id)
            except:
                target_user = None

        if not target_user:
            error_embed = discord.Embed(
                title="❌ Usuario no encontrado",
                description=f"No se encontró un usuario con el ID `{user_id}`.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        # Crear embed
        guide_embed = self.create_admin_guide_embed(interaction.user.id)

        # Enviar DM
        try:
            await target_user.send(embed=guide_embed)

            success_embed = discord.Embed(
                title="✅ Guía enviada",
                description=f"La guía fue enviada por DM a **{target_user.name}**.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)

        except discord.Forbidden:
            forbidden_embed = discord.Embed(
                title="⚠️ No se pudo enviar DM",
                description=f"**{target_user.name}** tiene los mensajes privados desactivados.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=forbidden_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error desconocido",
                description=f"Ocurrió un error:\n```{e}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

# ============================
# SETUP
# ============================

async def setup(bot):
    await bot.add_cog(SlashAdminToolbox(bot))
