import discord
from discord import app_commands
from discord.ui import View, Button, Select
import asyncio
import os

# ===================== 설정 =====================
GUILD_ID = 1548721753570680872          # 서버 ID
TICKET_CATEGORY_ID = 1548722663822860400 # 티켓 채널이 모일 카테고리 ID
ADMIN_ROLE_ID = 1548722627760234629      # 관리자 역할 ID
TICKET_LOG_CHANNEL_ID = 1549075828422213773 # 티켓 로그 채널 ID

# 렌더(Render) 환경 변수에서 토큰을 안전하게 불러옵니다.
BOT_TOKEN = os.getenv("MTU0OTAzMTY4MzYyNDQwNzIwMQ.GsasFO.xKL6OTEqnVO2SvkZzuBJPNKIa7tz1zmqrMSYzQ")
# =================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# 이미 열린 티켓 중복 방지용
open_tickets = set()

# =================================================
# 티켓 생성 드롭다운
# =================================================
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="구매 문의", value="구매 문의", emoji="🛒"),
            discord.SelectOption(label="기타 문의", value="기타 문의", emoji="📩")
        ]
        super().__init__(placeholder="문의 사항을 선택하세요...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # 이미 티켓 열었는지 확인
        if interaction.user.id in open_tickets:
            return await interaction.followup.send("❌ 이미 열어둔 티켓이 있습니다!", ephemeral=True)

        ticket_type = self.values[0]
        
        # 카테고리 가져오기
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            return await interaction.followup.send("❌ 티켓 카테고리를 찾을 수 없습니다! 카테고리 ID를 확인해주세요.", ephemeral=True)

        # 채널 권한 설정
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        # 티켓 채널 생성
        channel_name = f"티켓-{interaction.user.name}"
        channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            topic=f"문의 유형: {ticket_type} | 유저: {interaction.user.mention}"
        )

        # 열린 티켓에 추가
        open_tickets.add(interaction.user.id)

        # 로그 채널에 기록
        log_channel = bot.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="✅ 티켓 생성됨", color=discord.Color.green())
            embed.add_field(name="유저", value=f"{interaction.user.mention}\n{interaction.user.name}", inline=True)
            embed.add_field(name="유형", value=ticket_type, inline=True)
            embed.add_field(name="채널", value=channel.mention, inline=False)
            await log_channel.send(embed=embed)

        # 티켓 채널 안에 보낼 메시지
        close_view = TicketCloseView()
        embed = discord.Embed(title="🎫 문의가 접수되었습니다!", color=discord.Color.blue())
        embed.add_field(name="문의 유형", value=ticket_type, inline=False)
        embed.add_field(name="유저", value=interaction.user.mention, inline=False)
        embed.description = "관리자가 곧 답변드릴 예정입니다.\n문의 내용을 남겨주세요.\n\n✅ 닫으려면 아래 버튼을 누르세요."
        
        await channel.send(embed=embed, view=close_view)
        await interaction.followup.send(f"✅ 티켓이 생성되었습니다! → {channel.mention}", ephemeral=True)


# =================================================
# 티켓 열기 메인 뷰
# =================================================
class TicketMainView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# =================================================
# 티켓 닫기 버튼
# =================================================
class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="티켓 닫기", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        
        # 채널 삭제 전 유저 ID 추출
        topic = interaction.channel.topic or ""
        user_id = None
        for m in interaction.guild.members:
            if str(m.id) in topic:
                user_id = m.id
                break

        # 티켓 목록에서 제거
        if user_id and user_id in open_tickets:
            open_tickets.remove(user_id)

        # 로그 기록
        log_channel = bot.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="🔒 티켓 닫힘", color=discord.Color.orange())
            embed.add_field(name="채널", value=interaction.channel.name, inline=False)
            embed.add_field(name="닫은 사람", value=interaction.user.mention, inline=True)
            await log_channel.send(embed=embed)

        # 채널 삭제
        await interaction.channel.delete(reason="티켓 닫기")


# =================================================
# 슬래시 명령어 - 인증 패널(티켓) 전송
# =================================================
@tree.command(name="인증패널설치", description="티켓을 여는 패널 메시지를 전송합니다 (관리자 전용)")
async def setup_ticket(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ 관리자만 사용할 수 있습니다!", ephemeral=True)

    await interaction.response.send_message("✅ 티켓 패널을 전송합니다!", ephemeral=True)

    embed = discord.Embed(title="🎫 모든 문의 티켓", color=discord.Color.blue())
    embed.description = "아래 드롭다운을 클릭하여 새로운 지원 티켓을 생성하세요."
    view = TicketMainView()
    
    await interaction.channel.send(embed=embed, view=view)


# =================================================
# 봇 시작
# =================================================
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ 티켓봇 온라인: {bot.user}")
    print(f"✅ /인증패널설치 명령어 동기화 완료")

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다!")
