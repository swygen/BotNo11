import logging
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from keep_alive import keep_alive  # Keep alive import
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Your Telegram Bot Token
API_TOKEN = '7602137317:AAEQdvdj4KjgqXw7MR_dA7S_87b8e-O95J8'  # Replace with your Telegram bot token
# Your Hugging Face API Token
API_TOKEN_HF = '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'  # Replace with your Hugging Face token
# Telegram Group Username (Without @)
GROUP_USERNAME = 'swygenbd'  # Replace with your Telegram group username

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Store user language preference and image generation count
user_lang = {}
user_image_count = {}

# Welcome message
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=f"@{GROUP_USERNAME}", user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            await show_language_selection(message)
        else:
            await prompt_join_group(message)
    except:
        await prompt_join_group(message)

async def prompt_join_group(message: types.Message):
    join_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Joined", callback_data="check_join")
    )
    text = (
        "বট ব্যবহারের আগে আপনাকে আমাদের অফিসিয়াল গ্রুপে যোগ দিতে হবে: https://t.me/swygenbd\n\nগ্রুপে যোগ দিয়ে নিচের 'Joined' বাটনে ক্লিক করুন।"
    )
    await message.answer(text, parse_mode='Markdown', reply_markup=join_kb)

@dp.callback_query_handler(lambda c: c.data == 'check_join')
async def check_joined(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=f"@{GROUP_USERNAME}", user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            await show_language_selection(callback_query.message)
        else:
            await prompt_join_group(callback_query.message)
    except:
        await prompt_join_group(callback_query.message)

async def show_language_selection(message):
    lang_kb = InlineKeyboardMarkup(row_width=2)
    lang_kb.add(
        InlineKeyboardButton("বাংলা", callback_data='lang_bn'),
        InlineKeyboardButton("English", callback_data='lang_en')
    )
    user_full_name = message.from_user.full_name
    welcome_text = f"স্বাগতম, {user_full_name}!\n\nPlease select your language / দয়া করে আপনার ভাষা নির্বাচন করুন:"
    await message.reply(welcome_text, reply_markup=lang_kb)

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def set_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split('_')[1]
    user_lang[callback_query.from_user.id] = lang
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🖼️ ছবি তৈরি করুন / Generate Image", callback_data='generate_image')
    )
    user_full_name = callback_query.from_user.full_name
    welcome_msg = f"স্বাগতম, {user_full_name}! নিচে ক্লিক করে ছবি তৈরি করুন:" if lang == 'bn' else f"Welcome, {user_full_name}! Click below to generate an image:"
    await bot.send_message(callback_query.from_user.id, welcome_msg, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'generate_image')
async def generate_image(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = user_lang.get(user_id, 'en')

    # Check image count
    if user_image_count.get(user_id, 0) >= 5:
        # VIP Membership unlock message
        if lang == 'bn':
            await callback_query.message.answer("আপনার দৈনিক ছবি সীমা শেষ! VIP Membership আনলক করুন।")
        else:
            await callback_query.message.answer("You have reached the daily limit for image generation! Unlock VIP Membership.")
    else:
        # Generate the image
        prompt = "A futuristic city skyline at sunset"  # Example prompt, customize as needed
        generated_image = await get_huggingface_image(prompt)

        # Increment image count
        user_image_count[user_id] = user_image_count.get(user_id, 0) + 1

        # Send generated image to user
        if generated_image:
            await bot.send_photo(callback_query.from_user.id, photo=generated_image)
        else:
            await bot.send_message(callback_query.from_user.id, "Failed to generate image.")

# Function to interact with Hugging Face API
async def get_huggingface_image(prompt):
    headers = {
        "Authorization": f"Bearer {API_TOKEN_HF}"
    }
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    payload = {
        "inputs": prompt
    }
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.content
    else:
        print("Error in image generation:", response.status_code)
        return None

# Start polling
if __name__ == '__main__':
    keep_alive()  # Start keep-alive server
    executor.start_polling(dp, skip_updates=True)
