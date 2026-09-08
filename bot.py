import discord
from discord.ext import commands
import requests
import os
import random
import string

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Penyimpanan sementara untuk password akun
# Format: { "email@domain.com": "password" }
ACCOUNTS_DB = {}

@bot.event
async def on_ready():
    print(f"Bot berhasil masuk sebagai {bot.user}")

@bot.command(name="tempmail")
async def tempmail(ctx):
    """Menghasilkan alamat email sementara baru."""
    try:
        # 1. Ambil domain yang tersedia dari mail.gw
        res_domain = requests.get("https://api.mail.gw/domains")
        if res_domain.status_code != 200:
            await ctx.send("Gagal terhubung ke layanan temp mail.")
            return
        
        domains = res_domain.json().get("hydra:member", [])
        if not domains:
            await ctx.send("Domain temp mail tidak tersedia.")
            return
        
        domain = domains[0]["domain"]
        
        # 2. Buat username & password random
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{username}@{domain}"
        password = username + "Pass123!"
        
        # 3. Buat akun di mail.gw
        payload = {
            "address": email,
            "password": password
        }
        res_create = requests.post("https://api.mail.gw/accounts", json=payload)
        
        if res_create.status_code in [200, 201]:
            ACCOUNTS_DB[email] = password
            await ctx.send(f"✉️ **Email Sementara Anda:** `{email}`\nGunakan perintah `!inbox {email}` untuk mengecek pesan masuk.")
        else:
            await ctx.send(f"Gagal membuat email (Status: {res_create.status_code}).")
            
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

@bot.command(name="inbox")
async def inbox(ctx, email_address: str):
    """Mengecek daftar pesan masuk untuk email tertentu."""
    try:
        if email_address not in ACCOUNTS_DB:
            await ctx.send("Email tidak ditemukan di memori bot atau bot baru saja direstart. Silakan buat email baru dengan `!tempmail`.")
            return
        
        password = ACCOUNTS_DB[email_address]
        
        # 1. Dapatkan token akses (login)
        auth_payload = {
            "address": email_address,
            "password": password
        }
        res_token = requests.post("https://api.mail.gw/token", json=auth_payload)
        if res_token.status_code != 200:
            await ctx.send("Gagal melakukan autentikasi ke layanan email.")
            return
        
        token = res_token.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Ambil daftar pesan
        res_msgs = requests.get("https://api.mail.gw/messages", headers=headers)
        if res_msgs.status_code == 200:
            data = res_msgs.json()
            messages = data.get("hydra:member", [])
            
            if not messages:
                await ctx.send(f"📭 Inbox untuk `{email_address}` masih kosong.")
                return
            
            msg_list = f"📬 **Inbox untuk `{email_address}` ({len(messages)} pesan):**\n"
            for msg in messages:
                msg_id = msg.get("id")
                from_sender = msg.get("from", {}).get("address", "Unknown")
                subject = msg.get("subject", "Tanpa Subjek")
                msg_list += f"- **ID:** `{msg_id}` | **Dari:** {from_sender} | **Subjek:** {subject}\n"
            
            msg_list += "\nGunakan `!baca <email> <id_pesan>` untuk membaca isi pesan."
            await ctx.send(msg_list)
        else:
            await ctx.send("Gagal mengambil data inbox.")
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

@bot.command(name="baca")
async def baca_pesan(ctx, email_address: str, msg_id: str):
    """Membaca isi detail pesan berdasarkan ID."""
    try:
        if email_address not in ACCOUNTS_DB:
            await ctx.send("Email tidak ditemukan di memori bot. Silakan buat email baru dengan `!tempmail`.")
            return
        
        password = ACCOUNTS_DB[email_address]
        
        # 1. Dapatkan token akses
        auth_payload = {
            "address": email_address,
            "password": password
        }
        res_token = requests.post("https://api.mail.gw/token", json=auth_payload)
        if res_token.status_code != 200:
            await ctx.send("Gagal melakukan autentikasi.")
            return
        
        token = res_token.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Ambil detail pesan
        res_msg = requests.get(f"https://api.mail.gw/messages/{msg_id}", headers=headers)
        if res_msg.status_code == 200:
            data = res_msg.json()
            sender = data.get("from", {}).get("address", "Unknown")
            subject = data.get("subject", "Tanpa Subjek")
            date = data.get("createdAt", "Unknown")
            text_body = data.get("text", "Tidak ada teks")
            
            embed = discord.Embed(title=f"Subjek: {subject}", color=discord.Color.blue())
            embed.add_field(name="Dari", value=sender, inline=False)
            embed.add_field(name="Tanggal", value=date, inline=False)
            embed.add_field(name="Pesan", value=text_body[:1000] if text_body else "Tidak ada isi teks", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Gagal membaca pesan atau ID pesan tidak valid.")
    except Exception as e:
        await ctx.send(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN tidak ditemukan di environment variables.")
            
