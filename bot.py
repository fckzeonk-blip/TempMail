import discord
from discord.ext import commands
import requests
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot berhasil masuk sebagai {bot.user}")

@bot.command(name="tempmail")
async def tempmail(ctx):
    """Menghasilkan alamat email sementara baru."""
    try:
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        if response.status_code == 200:
            data = response.json()
            if data:
                email = data[0]
                await ctx.send(f"✉️ **Email Sementara Anda:** `{email}`\nGunakan perintah `!inbox {email}` untuk mengecek pesan masuk.")
            else:
                await ctx.send("Gagal menghasilkan email. Silakan coba lagi.")
        else:
            await ctx.send("Gagal terhubung ke layanan temp mail.")
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

@bot.command(name="inbox")
async def inbox(ctx, email_address: str):
    """Mengecek daftar pesan masuk untuk email tertentu."""
    try:
        if "@" not in email_address:
            await ctx.send("Format email tidak valid.")
            return
        
        login, domain = email_address.split("@")
        url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
        response = requests.get(url)
        
        if response.status_code == 200:
            messages = response.json()
            if not messages:
                await ctx.send(f"📭 Inbox untuk `{email_address}` masih kosong.")
                return
            
            msg_list = f"📬 **Inbox untuk `{email_address}` ({len(messages)} pesan):**\n"
            for msg in messages:
                msg_id = msg.get("id")
                from_sender = msg.get("from")
                subject = msg.get("subject")
                msg_list += f"- **ID:** {msg_id} | **Dari:** {from_sender} | **Subjek:** {subject}\n"
            
            msg_list += "\nGunakan `!baca <email> <id_pesan>` untuk membaca isi pesan."
            await ctx.send(msg_list)
        else:
            await ctx.send("Gagal mengambil data inbox.")
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

@bot.command(name="baca")
async def baca_pesan(ctx, email_address: str, msg_id: int):
    """Membaca isi detail pesan berdasarkan ID."""
    try:
        login, domain = email_address.split("@")
        url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            sender = data.get("from")
            subject = data.get("subject")
            date = data.get("date")
            body = data.get("textBody", "Tidak ada teks")
            
            embed = discord.Embed(title=f"Subjek: {subject}", color=discord.Color.blue())
            embed.add_field(name="Dari", value=sender, inline=False)
            embed.add_field(name="Tanggal", value=date, inline=False)
            embed.add_field(name="Pesan", value=body[:1000], inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Gagal membaca pesan.")
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN tidak ditemukan di environment variables.")
                   
