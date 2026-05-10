import discord
from discord.ext import commands
from discord import app_commands
import json
import os

BLACKLIST_FILE = "blacklist.json"

def load_blacklist_sync():
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def find_blacklisted_entry_sync(blacklist, user_id: int):
    for entry in blacklist:
        if isinstance(entry, int) and entry == user_id:
            return {"id": entry, "razon": "No disponible (Formato antiguo)", "imagen": None}
        elif isinstance(entry, dict) and entry.get("id") == user_id:
            return entry
    return None


# ---------------- IDs ----------------

CREATOR_IDS = [
    1330486565528670284,
    1394342273919225959
]

MANAGER_IDS = [
]

ADMIN_IDS = [
    981927827198228,
]

MODERATOR_IDS = [

]

MODERATOR_IDS = []

# ---------------- Emojis ----------------
CREADOR_EMOJI   = '<:fundador:1502761763341336726>'
MANAGER_EMOJI   = '<:manager:1502761534995042434>'
ADMIN_EMOJI     = '<:Administrador:1502761704487129158>'
MODERADOR_EMOJI = '<:moderador:1502761650527277329>'

VERIFICADO_EMOJI      = '<:verificado:1502761952470896670>'
BUG_HUNTER_EMOJI      = '<:discordbughunterbadge:1502761952470896670>'
VERIFICADO_ICONO      = 'https://cdn.discordapp.com/emojis/1390641035893280778.webp'
BLACKLIST_EMOJI       = '<a:ban:1503025073471230174>'
NOT_BLACKLISTED_EMOJI = '<a:listocheck:1503026039721296062>'

# ---------------- Insignias ----------------
DEFAULT_BADGE = '<:User:1413203213221494874>'

BADGES = {
    "User":      DEFAULT_BADGE,
    "Developer": '<:Developer:1503026556258357389>',
    "Blacklist": '<:Blacklist:1503025073471230174>',
}

RANK_EMOJIS = {
    "Creador":       CREADOR_EMOJI,
    "Manager":       MANAGER_EMOJI,
    "Administrador": ADMIN_EMOJI,
    "Moderador":     MODERADOR_EMOJI,
    "Verificado":    VERIFICADO_EMOJI,
    "Bug Hunter":    BUG_HUNTER_EMOJI,
}

# ---------------- JSON ----------------

BADGES_FILE = "user_badges.json"

def load_badges():
    if os.path.exists(BADGES_FILE):
        with open(BADGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_badges():
    with open(BADGES_FILE, "w", encoding="utf-8") as f:
        json.dump(user_badges, f, indent=4, ensure_ascii=False)

user_badges = load_badges()

# ---------------- Helper: construir embed de perfil ----------------

async def build_profile_embed(bot, user: discord.User, member: discord.Member | None):
    role        = None
    color       = discord.Color.greyple()
    icon        = "👤"
    footer_text = "Perfil de usuario"
    insignias   = []

    # Blacklist
    blacklist_data  = load_blacklist_sync()
    blacklist_entry = find_blacklisted_entry_sync(blacklist_data, user.id)

    if blacklist_entry:
        blacklist_status = (
            f"{BLACKLIST_EMOJI} **Baneado Globalmente**\n"
            f"Motivo: {blacklist_entry.get('razon', 'Razón no especificada')}"
        )
        if BADGES.get("Blacklist") not in insignias:
            insignias.append(BADGES.get("Blacklist"))
        color = discord.Color.dark_red()
    else:
        blacklist_status = f"{NOT_BLACKLISTED_EMOJI} No está en la blacklist global."

    # Jerarquía por IDs
    if user.id in CREATOR_IDS:
        role        = f'{CREADOR_EMOJI} Creador Oficial de Antiraid SBK'
        color       = discord.Color.blue()
        icon        = CREADOR_EMOJI
        footer_text = 'Perfil verificado - Antiraid SBK'
        t = set(insignias)
        t.update([CREADOR_EMOJI, MANAGER_EMOJI, ADMIN_EMOJI, MODERADOR_EMOJI, VERIFICADO_EMOJI, BUG_HUNTER_EMOJI])
        insignias = list(t)

    elif user.id in MANAGER_IDS:
        role        = f'{MANAGER_EMOJI} Manager Oficial de Antiraid SBK'
        if not blacklist_entry:
            color   = discord.Color.orange()
        icon        = MANAGER_EMOJI
        footer_text = 'Perfil verificado - Antiraid SBK'
        t = set(insignias)
        t.update([MANAGER_EMOJI, ADMIN_EMOJI, MODERADOR_EMOJI, VERIFICADO_EMOJI])
        insignias = list(t)

    elif user.id in ADMIN_IDS:
        role        = f'{ADMIN_EMOJI} Administrador Oficial de Antiraid SBK'
        if not blacklist_entry:
            color   = discord.Color.red()
        icon        = ADMIN_EMOJI
        footer_text = 'Perfil verificado - Antiraid SBK'
        t = set(insignias)
        t.update([ADMIN_EMOJI, MODERADOR_EMOJI, VERIFICADO_EMOJI])
        insignias = list(t)

    elif user.id in MODERATOR_IDS:
        role        = f'{MODERADOR_EMOJI} Moderador Oficial de Antiraid SBK'
        if not blacklist_entry:
            color   = discord.Color.green()
        icon        = MODERADOR_EMOJI
        footer_text = 'Staff del equipo - Antiraid SBK'
        t = set(insignias)
        t.update([MODERADOR_EMOJI, VERIFICADO_EMOJI])
        insignias = list(t)

    # Insignias desde JSON
    uid = str(user.id)
    if uid in user_badges and user_badges[uid]:
        t = set(insignias)
        t.update(user_badges[uid])
        insignias = list(t)

    if not insignias:
        insignias.append(DEFAULT_BADGE)

    embed = discord.Embed(
        title=role or f"{DEFAULT_BADGE} Usuario",
        description=f'Bienvenido al perfil oficial de {user.name}.',
        color=color
    )
    embed.set_author(name=user.name, icon_url=user.display_avatar.url)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name=f'{icon} Usuario',     value=str(user),                                   inline=True)
    embed.add_field(name='🧾 ID',               value=str(user.id),                                inline=True)
    embed.add_field(name='📅 Cuenta creada el', value=f'<t:{int(user.created_at.timestamp())}:D>', inline=False)
    embed.add_field(name='🛡️ Estado de Seguridad Global', value=blacklist_status,                  inline=False)
    if member and member.joined_at:
        embed.add_field(name='📌 Miembro desde', value=f'<t:{int(member.joined_at.timestamp())}:D>', inline=False)
    embed.add_field(name=f'{SERVERS_EMOJI} Servidores visibles', value=str(len(bot.guilds)),        inline=True)
    if insignias:
        embed.add_field(name=f'{INSIGNIA_EMOJI} Insignias', value=" ".join(insignias),              inline=False)
    embed.set_footer(text=footer_text, icon_url=VERIFICADO_ICONO)
    return embed


# ---------------- Cog ----------------

class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------- /perfil ---------
    @app_commands.command(name="perfil", description="Muestra el perfil de un usuario")
    @app_commands.describe(
        usuario="Menciona al usuario (opcional)",
        id="ID del usuario (opcional, si no mencionas a nadie)"
    )
    async def perfil(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member | None = None,
        id: str | None = None
    ):
        await interaction.response.defer()

        # Resolver quién es el objetivo
        target_user   = None
        target_member = None

        if usuario:
            target_user   = usuario
            target_member = usuario  # ya es Member

        elif id:
            try:
                uid = int(id)
            except ValueError:
                return await interaction.followup.send("❌ La ID proporcionada no es válida.", ephemeral=True)

            # Intentar obtenerlo como miembro del servidor primero
            target_member = interaction.guild.get_member(uid)
            if target_member:
                target_user = target_member
            else:
                # Fetch global (puede no estar en el servidor)
                try:
                    target_user = await self.bot.fetch_user(uid)
                except discord.NotFound:
                    return await interaction.followup.send("❌ No se encontró ningún usuario con esa ID.", ephemeral=True)

        else:
            # Sin argumentos → perfil propio
            target_user   = interaction.user
            target_member = interaction.guild.get_member(interaction.user.id)

        embed = await build_profile_embed(self.bot, target_user, target_member)
        await interaction.followup.send(embed=embed)

    # --------- /insignia ---------
    @app_commands.command(name="insignia", description="Asigna una insignia a un usuario (solo creators y managers)")
    @app_commands.describe(usuario="Usuario al que quieres asignar la insignia", insignia="Elige la insignia")
    @app_commands.choices(insignia=[app_commands.Choice(name=n, value=n) for n in BADGES.keys()])
    async def insignia(self, interaction: discord.Interaction, usuario: discord.Member, insignia: app_commands.Choice[str]):
        if not (interaction.user.id in CREATOR_IDS or interaction.user.id in MANAGER_IDS):
            return await interaction.response.send_message("🚫 No tienes permisos.", ephemeral=True)
        uid = str(usuario.id)
        if uid not in user_badges:
            user_badges[uid] = []
        badge = BADGES.get(insignia.value, DEFAULT_BADGE)
        if badge not in user_badges[uid]:
            user_badges[uid].append(badge)
            save_badges()
            msg = f"✅ Se agregó la insignia **{insignia.value}** a {usuario.mention}"
        else:
            msg = f"⚠️ {usuario.mention} ya tiene la insignia **{insignia.value}**"
        await interaction.response.send_message(msg, ephemeral=True)

    # --------- /removeinsignia ---------
    @app_commands.command(name="removeinsignia", description="Quita una insignia a un usuario (solo creators y managers)")
    @app_commands.describe(usuario="Usuario al que quieres quitar la insignia", insignia="Elige la insignia a quitar")
    @app_commands.choices(insignia=[app_commands.Choice(name=n, value=n) for n in BADGES.keys()])
    async def removeinsignia(self, interaction: discord.Interaction, usuario: discord.Member, insignia: app_commands.Choice[str]):
        if not (interaction.user.id in CREATOR_IDS or interaction.user.id in MANAGER_IDS):
            return await interaction.response.send_message("🚫 No tienes permisos.", ephemeral=True)
        uid = str(usuario.id)
        badge = BADGES.get(insignia.value, DEFAULT_BADGE)
        if uid in user_badges and badge in user_badges[uid]:
            user_badges[uid].remove(badge)
            save_badges()
            msg = f"🗑️ Se quitó la insignia **{insignia.value}** de {usuario.mention}"
        else:
            msg = f"⚠️ {usuario.mention} no tiene la insignia **{insignia.value}**"
        await interaction.response.send_message(msg, ephemeral=True)


# --------- Setup ---------

async def setup(bot):
    await bot.add_cog(Perfil(bot))
