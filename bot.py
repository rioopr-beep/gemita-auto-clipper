import os
import logging
import yt_dlp
import subprocess
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Token API Baru Gemita
TOKEN = "8546189574:AAHC6fJ6VbvtaLRkOVufiGMd9bbrloaHEq4"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 **Gemita Auto-Clipper Aktif!**\nKirim link video, dan saya akan carikan bagian paling menariknya.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    context.user_data['current_url'] = url

    keyboard = [
        [InlineKeyboardButton("📥 Full Download", callback_data='full')],
        [InlineKeyboardButton("🔥 Auto Highlight (15s)", callback_data='highlight')]
    ]
    await update.message.reply_text("Pilih opsi unduhan:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('current_url')
    mode = query.data
    
    await query.edit_message_text("⏳ Sedang memproses... Mohon tunggu.")
    file_name = f"clipper_{query.from_user.id}.mp4"

    try:
        with yt_dlp.YoutubeDL({'format': 'best[ext=mp4]/best'}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info['url']

            if mode == 'full':
                ydl.download([url])
                caption = "Berhasil unduh full video! ✅"
            else:
                # Logika mencari bagian paling ramai ditonton (Heatmap)
                heatmap = info.get('heatmap')
                start_time = max(heatmap, key=lambda x: x['value'])['start_time'] if heatmap else info.get('duration', 30) / 2
                
                # Memotong video secara langsung dari stream (Sangat Cepat)
                subprocess.run(['ffmpeg', '-ss', str(start_time), '-i', video_url, '-t', '15', '-c', 'copy', file_name], check=True)
                caption = f"🔥 Bagian paling menarik ditemukan! (Detik: {int(start_time)})"

        with open(file_name, 'rb') as v:
            await query.message.reply_video(video=v, caption=caption)
        os.remove(file_name)
        await query.message.delete()

    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")
        if os.path.exists(file_name): os.remove(file_name)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True)
