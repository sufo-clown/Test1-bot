import os
import sqlite3
import random

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = "users.db"

NAME, USERNAME, AGE, PHONE, CONFIRM = range(5)


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT,
            age INTEGER NOT NULL,
            phone TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )

    user = cursor.fetchone()
    conn.close()

    return user


def save_user(telegram_id, name, username, age, phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users
        (telegram_id, name, username, age, phone)
        VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, name, username, age, phone))

    conn.commit()
    conn.close()


# =========================
# MAIN MENU
# =========================

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🎮 Tic-Tac-Toe"],
            ["👤 Profile"]
        ],
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if user:
        await update.message.reply_text(
            "👋 Welcome back!\n\n"
            "Choose an option:",
            reply_markup=main_menu()
        )
        return

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "You need to register before using the bot.",
        reply_markup=ReplyKeyboardMarkup(
            [["📝 Register"]],
            resize_keyboard=True
        )
    )


# =========================
# REGISTRATION
# =========================

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if user:
        await update.message.reply_text(
            "You are already registered. ✅",
            reply_markup=main_menu()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 Registration started.\n\n"
        "What is your name?",
        reply_markup=ReplyKeyboardRemove()
    )

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "What is your username?\n\n"
        "Example: @john123\n"
        "If you don't have one, type: None"
    )

    return USERNAME


async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["username"] = update.message.text

    await update.message.reply_text(
        "How old are you?\n\n"
        "Enter your age as a number."
    )

    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        age = int(update.message.text)

        if age < 1 or age > 120:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid age between 1 and 120."
        )
        return AGE

    context.user_data["age"] = age

    keyboard = [
        ["📱 Share Phone Number"],
        ["⏭️ Skip"]
    ]

    await update.message.reply_text(
        "Would you like to provide your phone number?\n\n"
        "You can skip this step.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "⏭️ Skip":
        context.user_data["phone"] = "Not provided"
    else:
        context.user_data["phone"] = text

    data = context.user_data

    keyboard = [
        ["✅ Confirm"],
        ["❌ Cancel"]
    ]

    await update.message.reply_text(
        "📋 Please check your information:\n\n"
        f"👤 Name: {data['name']}\n"
        f"🔹 Username: {data['username']}\n"
        f"🎂 Age: {data['age']}\n"
        f"📱 Phone: {data['phone']}\n\n"
        "Is everything correct?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = context.user_data

    save_user(
        update.effective_user.id,
        data["name"],
        data["username"],
        data["age"],
        data["phone"]
    )

    context.user_data.clear()

    await update.message.reply_text(
        "🎉 Registration successful!\n\n"
        "Welcome to the bot! ✅",
        reply_markup=main_menu()
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Registration cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


# =========================
# PROFILE
# =========================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if not user:
        await update.message.reply_text(
            "❌ You aren't registered yet.\n\n"
            "Use /start to register."
        )
        return

    telegram_id, name, username, age, phone = user

    await update.message.reply_text(
        "👤 YOUR PROFILE\n\n"
        f"Name: {name}\n"
        f"Username: {username}\n"
        f"Age: {age}\n"
        f"Phone: {phone}",
        reply_markup=main_menu()
    )


# =========================
# TIC-TAC-TOE
# =========================

def create_board():
    return [" "] * 9


def board_keyboard(board):
    keyboard = []

    for row in range(3):
        buttons = []

        for col in range(3):
            index = row * 3 + col

            value = board[index]

            if value == " ":
                text = "⬜"
            elif value == "X":
                text = "❌"
            else:
                text = "⭕"

            buttons.append(
                InlineKeyboardButton(
                    text,
                    callback_data=f"ttt_{index}"
                )
            )

        keyboard.append(buttons)

    return InlineKeyboardMarkup(keyboard)


def check_winner(board):

    winning_lines = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6)
    ]

    for a, b, c in winning_lines:

        if (
            board[a] != " "
            and board[a] == board[b]
            and board[b] == board[c]
        ):
            return board[a]

    if " " not in board:
        return "DRAW"

    return None


def bot_move(board):

    available = [
        i for i, value in enumerate(board)
        if value == " "
    ]

    if available:
        return random.choice(available)

    return None


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if not user:
        await update.message.reply_text(
            "❌ Please register first using /start."
        )
        return

    board = create_board()

    context.user_data["ttt_board"] = board

    await update.message.reply_text(
        "🎮 TIC-TAC-TOE\n\n"
        "You are ❌\n"
        "I am ⭕\n\n"
        "Choose a square:",
        reply_markup=board_keyboard(board)
    )


async def ttt_move(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    board = context.user_data.get("ttt_board")

    if board is None:
        await query.edit_message_text(
            "This game has ended. Start a new game."
        )
        return

    index = int(query.data.split("_")[1])

    # Square already occupied
    if board[index] != " ":
        await query.answer(
            "That square is already taken!",
            show_alert=True
        )
        return

    # Player move
    board[index] = "X"

    winner = check_winner(board)

    if winner == "X":

        await query.edit_message_text(
            "🎉 YOU WIN! 🏆\n\n"
            "Congratulations!",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔄 Play Again",
                        callback_data="ttt_new"
                    )
                ]
            ])
        )

        context.user_data.pop("ttt_board", None)
        return

    if winner == "DRAW":

        await query.edit_message_text(
            "🤝 DRAW!\n\n"
            "Nobody wins this time.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔄 Play Again",
                        callback_data="ttt_new"
                    )
                ]
            ])
        )

        context.user_data.pop("ttt_board", None)
        return

    # Bot move
    move = bot_move(board)

    if move is not None:
        board[move] = "O"

    winner = check_winner(board)

    if winner == "O":

        await query.edit_message_text(
            "🤖 I WIN! 😎\n\n"
            "Better luck next time!",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔄 Play Again",
                        callback_data="ttt_new"
                    )
                ]
            ])
        )

        context.user_data.pop("ttt_board", None)
        return

    if winner == "DRAW":

        await query.edit_message_text(
            "🤝 DRAW!\n\n"
            "That was close!",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔄 Play Again",
                        callback_data="ttt_new"
                    )
                ]
            ])
        )

        context.user_data.pop("ttt_board", None)
        return

    await query.edit_message_text(
        "🎮 TIC-TAC-TOE\n\n"
        "You are ❌\n"
        "I am ⭕\n\n"
        "Your turn:",
        reply_markup=board_keyboard(board)
    )


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    board = create_board()

    context.user_data["ttt_board"] = board

    await query.edit_message_text(
        "🎮 NEW GAME\n\n"
        "You are ❌\n"
        "I am ⭕\n\n"
        "Your turn:",
        reply_markup=board_keyboard(board)
    )


# =========================
# TEXT MENU
# =========================

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎮 Tic-Tac-Toe":
        await start_game(update, context)

    elif text == "👤 Profile":
        await profile(update, context)


# =========================
# MAIN
# =========================

def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    registration_handler = ConversationHandler(

        entry_points=[
            CommandHandler("register", register),

            MessageHandler(
                filters.Regex("^📝 Register$"),
                register
            )
        ],

        states={

            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name
                )
            ],

            USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_username
                )
            ],

            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_age
                )
            ],

            PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_phone
                )
            ],

            CONFIRM: [
                MessageHandler(
                    filters.Regex("^✅ Confirm$"),
                    confirm
                ),

                MessageHandler(
                    filters.Regex("^❌ Cancel$"),
                    cancel
                )
            ]
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ]
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("register", register))

    # Registration
    app.add_handler(registration_handler)

    # Tic-Tac-Toe buttons
    app.add_handler(
        CallbackQueryHandler(
            ttt_move,
            pattern=r"^ttt_\d+$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            new_game,
            pattern=r"^ttt_new$"
        )
    )

    # Main menu
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_click))
    
    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main()
