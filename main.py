import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import json
import os
import random
import string
from datetime import datetime, timedelta, time

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Global data storage
TRANSACTIONS_FILE = "transactions.json"
POINTS_FILE = "points.json"
DEFAULT_CURRENCY = "IDR"

def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            return json.load(f)
    return {}

def save_data(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

def generate_transaction_id():
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PG{random_str}"

def add_points(user_id, amount):
    points = load_data(POINTS_FILE)
    if user_id not in points:
        points[user_id] = 0

    if 1000 <= amount <= 50000:
        points[user_id] += 100
    elif 60000 <= amount <= 100000:
        points[user_id] += 250

    save_data(POINTS_FILE, points)

@bot.event
async def on_ready():
    print("Welcome to Snowy Payment Gateway | Dibuat oleh: Snowy")
    print(f"Logged in as {bot.user}")
    send_monthly_report.start()

# Command to create a new transaction
@bot.command()
async def buatbaru(ctx, amount: int):
    transactions = load_data(TRANSACTIONS_FILE)
    user_transactions = [t for t in transactions.values() if t["user"] == ctx.author.id and t["status"] == "pending"]

    if user_transactions:
        await ctx.send("Anda masih memiliki transaksi yang belum selesai. Selesaikan atau batalkan transaksi tersebut terlebih dahulu.")
        return

    transaction_id = generate_transaction_id()
    transactions[transaction_id] = {
        "user": ctx.author.id,
        "amount": amount,
        "status": "pending",
        "date": datetime.now().isoformat(),
    }
    save_data(TRANSACTIONS_FILE, transactions)

    # Send QR code image along with the message
    image_path = "images/qris.jpg"
    if os.path.exists(image_path):
        await ctx.send(
            f"Transaksi baru berhasil dibuat dengan ID {transaction_id} dan jumlah {amount} {DEFAULT_CURRENCY}.",
            file=discord.File(image_path),
        )
    else:
        await ctx.send(
            f"Transaksi baru berhasil dibuat dengan ID {transaction_id} dan jumlah {amount} {DEFAULT_CURRENCY}. (QRIS tidak ditemukan)"
        )

# Command to cancel a transaction
@bot.command()
async def cancel(ctx, transaction_id: str):
    transactions = load_data(TRANSACTIONS_FILE)

    if transaction_id not in transactions:
        await ctx.send("Transaksi tidak ditemukan.")
        return

    if transactions[transaction_id]["user"] != ctx.author.id:
        await ctx.send("Anda tidak memiliki izin untuk membatalkan transaksi ini.")
        return

    if transactions[transaction_id]["status"] != "pending":
        await ctx.send("Transaksi ini tidak dapat dibatalkan karena sudah diproses.")
        return

    del transactions[transaction_id]
    save_data(TRANSACTIONS_FILE, transactions)

    await ctx.send(f"Transaksi dengan ID {transaction_id} berhasil dibatalkan.")

# Command to update transaction status
@bot.command()
@commands.has_role("bidiz")
async def update(ctx, transaction_id: str, status: str):
    transactions = load_data(TRANSACTIONS_FILE)

    if transaction_id not in transactions:
        await ctx.send("Transaksi tidak ditemukan.")
        return

    transactions[transaction_id]["status"] = status
    save_data(TRANSACTIONS_FILE, transactions)

    if status == "berhasil":
        user_id = transactions[transaction_id]["user"]
        amount = transactions[transaction_id]["amount"]
        add_points(str(user_id), amount)

    await ctx.send(f"Status transaksi {transaction_id} diperbarui menjadi {status}.")

# Command to display leaderboard
@bot.command()
async def leaderboard(ctx):
    points = load_data(POINTS_FILE)
    if not points:
        await ctx.send("Belum ada data poin yang tersedia.")
        return

    sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)
    leaderboard_message = "**Leaderboard Poin**\n"

    for rank, (user_id, point) in enumerate(sorted_points, start=1):
        user = await bot.fetch_user(int(user_id))
        leaderboard_message += f"{rank}. {user.name}: {point} poin\n"

    await ctx.send(leaderboard_message)

# Monthly report task
@tasks.loop(time=time(23, 59))
async def send_monthly_report():
    transactions = load_data(TRANSACTIONS_FILE)
    if not transactions:
        print("Tidak ada transaksi untuk laporan bulanan.")
        return

    report_message = "**Laporan Bulanan Transaksi**\n"
    report_message += f"Bulan: {datetime.now().strftime('%B %Y')}\n"

    for transaction_id, transaction in transactions.items():
        user = await bot.fetch_user(int(transaction["user"]))
        report_message += (
            f"ID Transaksi: {transaction_id}, User: {user.name}, Jumlah: {transaction['amount']} {DEFAULT_CURRENCY}, Status: {transaction['status']}, Tanggal: {transaction['date']}\n"
        )

    admin_role_name = "bidiz"

    for guild in bot.guilds:
        for member in guild.members:
            if admin_role_name in [role.name for role in member.roles]:
                try:
                    await member.send(report_message)
                except Exception as e:
                    print(f"Gagal mengirim laporan ke {member}: {e}")

# Command to send the monthly report manually
@bot.command()
@commands.has_role("bidiz")
async def kirimlaporan(ctx):
    transactions = load_data(TRANSACTIONS_FILE)
    if not transactions:
        await ctx.send("Tidak ada transaksi untuk laporan bulanan.")
        return

    report_message = "**Laporan Bulanan Transaksi**\n"
    report_message += f"Bulan: {datetime.now().strftime('%B %Y')}\n"

    for transaction_id, transaction in transactions.items():
        user = await bot.fetch_user(int(transaction["user"]))
        report_message += (
            f"ID Transaksi: {transaction_id}, User: {user.name}, Jumlah: {transaction['amount']} {DEFAULT_CURRENCY}, Status: {transaction['status']}, Tanggal: {transaction['date']}\n"
        )

    await ctx.send(report_message)

# Command to display available commands
@bot.command()
async def bantuan(ctx):
    user_roles = [role.name for role in ctx.author.roles]
    is_admin = "bidiz" in user_roles

    commands_list = [
        {"command": "/buatbaru <jumlah>", "description": "Membuat transaksi baru."},
        {"command": "/leaderboard", "description": "Menampilkan leaderboard poin."},
        {"command": "/cancel <id_transaksi>", "description": "Membatalkan transaksi."},
    ]

    admin_commands = [
        {"command": "/update <id_transaksi> <status>", "description": "Memperbarui status transaksi."},
        {"command": "/kirimlaporan", "description": "Mengirim laporan bulanan secara manual."},
    ]

    help_message = "__**Daftar Perintah yang Tersedia**__\n"
    help_message += "\n".join([f"**{cmd['command']}**: {cmd['description']}" for cmd in commands_list])

    if is_admin:
        help_message += "\n\n__**Perintah Admin**__\n"
        help_message += "\n".join([f"**{cmd['command']}**: {cmd['description']}" for cmd in admin_commands])

    embed = discord.Embed(title="Daftar Perintah", description=help_message, color=discord.Color.blue())
    embed.set_footer(text="Gunakan perintah sesuai kebutuhan Anda.")

    await ctx.send(embed=embed)

# Run the bot
bot.run("TOKEN_BOT_TARO_SINI")
