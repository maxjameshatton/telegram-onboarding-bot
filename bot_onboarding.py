#!/usr/bin/env python3
"""
Telegram Onboarding Bot
Requires: python-telegram-bot v20+ (async)
"""

import re
import sqlite3
import logging
import os
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

# States for ConversationHandler
NAME, EMAIL = range(2)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database
DB_PATH = "users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            tg_username TEXT,
            full_name TEXT,
            email TEXT,
            created_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def save_user(user_id: int, username: str, full_name: str, email: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT OR REPLACE INTO users
        (user_id, tg_username, full_name, email, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, username, full_name, email, now),
    )
    conn.commit()
    conn.close()


# Email validation
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


# ---------------------------
# Conversation Handlers
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    await update.message.reply_text(
        "Welcome! I'm excited to have you join the trading community.\n\n"
        "First, please tell me your *full name*.",
        parse_mode="Markdown",
    )
    return NAME


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    full_name = update.message.text.strip()
    context.user_data["full_name"] = full_name

    await update.message.reply_text(
        f"Thanks {full_name} — please enter your *email address* for full access.",
        parse_mode="Markdown",
    )
    return EMAIL


async def email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    email = update.message.text.strip()

    if not is_valid_email(email):
        await update.message.reply_text("That doesn't look like a valid email. Try again.")
        return EMAIL

    full_name = context.user_data.get("full_name", "")
    username = user.username if user else None

    save_user(user.id, username, full_name, email)
    context.user_data.clear()

    first_name = full_name.split()[0] if full_name else ""

    # Main onboarding flow
    await update.message.reply_text(
        f"Thanks for that {first_name}.\n\n"
        "Here's a quick rundown of what you'll get inside our free trading community:"
    )

    await update.message.reply_text(
        "✅ 2-5+ High quality trades per day.\n"
        "✅ 80% success rate on our gold signals week in week out.\n"
        "✅ Full step by step guide on how to take the trades.\n"
        "✅ Weekly calls including giveaways and trading tips.\n"
        "✅ Trusted broker partnership for your security."
    )

    await update.message.reply_text(
        "And the best part:\n\n"
        "💰 No setup costs\n"
        "💰 No monthly fees\n"
        "💰 No contracts ever\n\n"
        "Most importantly, you're in full control of your capital."
    )

    keyboard = [
        ["Next Steps"],
        ["Why is it free?"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Choose an option below to continue:",
        reply_markup=reply_markup,
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Registration canceled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ---------------------------
# Button Handlers
# ---------------------------

async def next_steps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        ["Yes, I do 💪"],
        ["No, I'm new to this"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Amazing!\n\n"
        "Now before we begin, do you already have an account with Vantage Markets?\n\n"
        "If not, we'd be happy to guide you through the simple setup process.",
        reply_markup=reply_markup,
    )


async def why_is_it_free(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    first_name = user.first_name if user and user.first_name else ""

    await update.message.reply_text(
        f"Great question {first_name}!\n\n"
        "Here's the simple breakdown:"
    )

    await update.message.reply_text(
        "We've been using the same partner broker now for coming on 3 years and have built an amazing relationship with them. "
        "They are one of the world's leading platforms when it comes to trading and they cover all the costs for us.\n\n"
        "When you trade through them, they sponsor your entire membership."
    )

    await update.message.reply_text(
        "So you get:\n"
        "- All the gold signals from our expert traders\n"
        "- Full community access\n"
        "- Weekly training\n"
        "- Daily support"
    )

    keyboard = [["I'm ready!"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "...all completely free.\n\n"
        "It's a win-win that lets us focus on what matters, helping you profit!",
        reply_markup=reply_markup,
    )


async def has_vantage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pressed 'Yes, I do 💪'."""
    await update.message.reply_text(
        'Please contact @maxjameshatton and say "already registered with vantage".',
        reply_markup=ReplyKeyboardRemove(),
    )


async def new_to_vantage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pressed 'No, I'm new to this' – show Vantage setup flow."""
    user = update.effective_user
    first_name = user.first_name if user and user.first_name else ""

    # Message 1 (like screenshot 1)
    await update.message.reply_text(
        f"No worries {first_name}!\n\n"
        "To get started and receive our gold signals for FREE, you'll need to create a "
        "Vantage Markets account using our specific referral link."
    )

    # Message 2 (like screenshot 2, with your updated link)
    await update.message.reply_text(
        "Important: Please follow these steps carefully:\n\n"
"- Click this link to open your Vantage Markets account:\n\n"
"https://www.vantagemarkets.com/open-live-account/?affid=NzM2MzQ1MQ==\n\n"
"- Complete the registration process directly through this link without navigating away or closing the page.\n\n"
"- This special link ensures you're properly allocated to our team network, which is what qualifies you for free access to our signals.\n\n"
"- When the page opens, enter your *email* and create a password, then click **Proceed**.\n\n"
"- When choosing your account type, select: STANDARD STP ACCOUNT ✅\n\n"
"- Please then verify with an ID (Driving License or Passport works, plus a utility bill).\n\n"
"- Lastly, to become a member of the VIP community, fund your account with a minimum of £300. (This is your trading capital)\n\n"
"If you need any help at all, message me directly: @maxjameshatton"
    )

    # Message 3 + DONE button
    keyboard = [["DONE ✅"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        'Once your account is created, return here and click "Done" so we can proceed with the next steps.',
        reply_markup=reply_markup,
    )


async def im_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Redirects the user back to the Vantage question flow."""
    await next_steps(update, context)


async def vantage_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User clicked DONE ✅ after creating Vantage account."""
    await update.message.reply_text(
        "Amazing, here is the link to join the community. "
        "https://t.me/+Rverm3diRHU5NWY0. "
        "Please request to join and then send @maxjameshatton your Full Name and "
        "Vantage Account Number and we will get you added asap!",
        reply_markup=ReplyKeyboardRemove(),
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("I didn't understand that. Try tapping a button.")


# ---------------------------
# Main App
# ---------------------------

def main():
    init_db()

    # OPTION 1: Use environment variable
    token = os.environ.get("BOT_TOKEN")

    # OPTION 2: Hard-code token for testing
    # token = "PASTE_YOUR_BOT_TOKEN_HERE"

    if not token:
        raise RuntimeError("No token found. Set BOT_TOKEN or hard-code it in main().")

    app = ApplicationBuilder().token(token).concurrent_updates(True).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Main flow buttons
    app.add_handler(MessageHandler(filters.Regex("^Next Steps$"), next_steps))
    app.add_handler(MessageHandler(filters.Regex("^Why is it free\\?$"), why_is_it_free))

    # Follow-up buttons
    app.add_handler(MessageHandler(filters.Regex("^Yes, I do 💪$"), has_vantage))
    app.add_handler(MessageHandler(filters.Regex("^No, I'm new to this$"), new_to_vantage))
    app.add_handler(MessageHandler(filters.Regex("^I'm ready!$"), im_ready))
    app.add_handler(MessageHandler(filters.Regex("^DONE ✅$"), vantage_done))

    # Unknown command
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("Bot running…")
    app.run_polling()


if __name__ == "__main__":
    main()


