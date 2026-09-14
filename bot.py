from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Replace with your bot token from BotFather
BOT_TOKEN = "8771937001:AAEr41o0QqlndZUr1mBv0QLmgVRTXrrUMRY"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with inline buttons when /start is issued."""
    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data="1")],
        [InlineKeyboardButton("Option 2", callback_data="2")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Hi! Click a button below:",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "1":
        await query.edit_message_text(text="You clicked Option 1!")
    elif query.data == "2":
        await query.edit_message_text(text="You clicked Option 2!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await update.message.reply_text("Use /start to see buttons or /help for this message.")

def main():
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_click))
    
    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main()
