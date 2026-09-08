import os
import discord
from discord.ext import commands
import requests

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Mengambil API Key dari Environment Variable Railway
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Sesuaikan host jika menggunakan provider spesifik dari RapidAPI
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "temp-mail48.p.rapidapi.com" 
}

@bot.event
async def on_ready():
    print(f"Bot berhasil masuk sebagai {bot.user}")

@bot.command(name="tempmail")
async def tempmail(ctx):
    """Menghasilkan alamat email sementara baru."""
    if not RAPIDAPI_KEY:
        await ctx.send("Error: RAPIDAPI_KEY belum disetel di Environment Variables Railway.")
        return
        
    try:
        # Endpoint contoh untuk membuat/mendapatkan email dari RapidAPI temp-mail
        url = "https://temp-mail48.p.rapidapi.com/email/new" 
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Sesuaikan key JSON ('email') berdasarkan dokumentasi API yang Anda pilih di RapidAPI
            email = data.get("email") or data.get("mail")
            if email:
                await ctx.send(f"✉️ **Email Sementara Anda:** `{email}`\nGunakan perintah `!inbox {email}` untuk mengecek pesan masuk.")
            else:
                await ctx.send("Gagal mengurai data email dari server.")
        else:
            await ctx.send(f"Gagal terhubung (Status: {response.status_code}). Periksa kembali API Key Anda.")
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

@bot.command(name="inbox")
async def inbox(ctx, email_address: str):
    """Mengecek daftar pesan masuk untuk email tertentu."""
    if not RAPIDAPI_KEY:
        await ctx.send("Error: RAPIDAPI_KEY belum disetel.")
        return
        
    try:
        url = f"https://temp-mail48.p.rapidapi.com/email/inbox/{email_address}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
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
                msg_list += f"- **ID:** `{msg_id}` | **Dari:** {from_sender} | **Subjek:** {subject}\n"
            
            await ctx.send(msg_list)
        else:
            await ctx.send("Gagal mengambil data inbox.")
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN tidak ditemukan di environment variables.")
