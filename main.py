import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests, json
from urllib.parse import urlparse, parse_qs, urlunparse
import urllib.parse
import os

# Load environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret,
                           models.Language.FR, models.Currency.EUR, 'default')  # Force French

# Keyboard setup
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="t.me/Tcoupon")
keyboardStart.add(btn1, btn2, btn3)

keyboard = types.InlineKeyboardMarkup(row_width=1)
keyboard.add(btn1, btn2, btn3)

keyboard_games = types.InlineKeyboardMarkup(row_width=1)
keyboard_games.add(btn1, btn2, btn3)

# ===== NEW: Function to force French version of AliExpress links =====
def force_french_version(url):
    try:
        parsed = urlparse(url)
        if "aliexpress.com" in parsed.netloc:
            # Replace domain with fr.aliexpress.com
            new_netloc = parsed.netloc.replace("www.aliexpress.com", "fr.aliexpress.com") \
                                     .replace("aliexpress.com", "fr.aliexpress.com") \
                                     .replace("s.click.aliexpress.com", "fr.aliexpress.com")
            # Rebuild URL
            new_parsed = parsed._replace(netloc=new_netloc)
            return urlunparse(new_parsed)
        return url
    except Exception as e:
        print(f"Error forcing French version: {e}")
        return url

# ===== NEW: Improved URL expander with French enforcement =====
def expand_shortened_url(short_url):
    try:
        session = requests.Session()
        response = session.head(short_url, allow_redirects=True, timeout=5)
        final_url = response.url
        return force_french_version(final_url)  # Force French after expanding
    except Exception as e:
        print(f"Error expanding URL: {e}")
        return force_french_version(short_url)  # Fallback with French enforcement

# ===== Extract link and ensure it's French =====
def extract_link(text):
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        link = links[0]
        # Expand if it's a shortened link
        if "s.click.aliexpress.com" in link:
            link = expand_shortened_url(link)
        # Force French version
        link = force_french_version(link)
        return link
    return None

# ===== Modified to work ONLY with fr.aliexpress.com =====
def get_affiliate_links(message, message_id, link):
    try:
        # Ensure link is in French version
        link = force_french_version(link)
        print(f"Processing link: {link}")  # Debug log

        # Generate affiliate links
        affiliate_link = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=620&aff_fcid='
        )[0].promotion_link

        super_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=562&aff_fcid='
        )[0].promotion_link

        limit_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=561&aff_fcid='
        )[0].promotion_link

        try:
            # Extract product ID from URL
            product_id_match = re.search(r'/item/(\d+)\.html', link)
            if product_id_match:
                product_id = product_id_match.group(1)
                product_details = aliexpress.get_products_details([product_id])
                
                if product_details:
                    price_pro = product_details[0].target_sale_price
                    title_link = product_details[0].product_title
                    img_link = product_details[0].product_main_image_url

                    bot.delete_message(message.chat.id, message_id)
                    bot.send_photo(
                        message.chat.id,
                        img_link,
                        caption=f" \n🛒 منتجك هو  : 🔥 \n{title_link} 🛍 \n"
                               f"سعر المنتج  : {price_pro} دولار 💵\n"
                               " \n قارن بين الاسعار واشتري 🔥 \n"
                               f"💰 عرض العملات (السعر النهائي عند الدفع)  : \nالرابط {affiliate_link} \n"
                               f"💎 عرض السوبر  : \nالرابط {super_links} \n"
                               f"♨️ عرض محدود  : \نالرابط {limit_links} \n\n"
                               "t.me/tcoupon !",
                        reply_markup=keyboard
                    )
                    return

        except Exception as e:
            print(f"Error getting product details: {e}")

        # Fallback if product details fail
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(
            message.chat.id,
            "قارن بين الاسعار واشتري 🔥 \n"
            f"💰 عرض العملات (السعر النهائي عند الدفع) : \nالرابط {affiliate_link} \n"
            f"💎 عرض السوبر : \nالرابط {super_links} \n"
            f"♨️ عرض محدود : \nالرابط {limit_links} \n\n",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Error in get_affiliate_links: {e}")
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# ===== Rest of the code remains the same =====
@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(
        message.chat.id,
        "مرحبا بك، ارسل لنا رابط المنتج الذي تريد شرائه لنوفر لك افضل سعر له 👌 \n",
        reply_markup=keyboardStart
    )

@bot.callback_query_handler(func=lambda call: call.data == 'click')
def button_click(callback_query):
    bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="..."
    )
    img_link1 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
    bot.send_photo(
        callback_query.message.chat.id,
        img_link1,
        caption="",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: True)
def get_link(message):
    link = extract_link(message.text)
    if not link:
        bot.send_message(
            message.chat.id,
            "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n"
            "قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج",
            parse_mode='HTML'
        )
        return

    sent_message = bot.send_message(message.chat.id, 'المرجو الانتظار قليلا، يتم تجهيز العروض ⏳')
    message_id = sent_message.message_id

    if "aliexpress.com" in link:
        if "availableProductShopcartIds".lower() in message.text.lower():
            get_affiliate_shopcart_link(link, message)
        else:
            get_affiliate_links(message, message_id, link)
    else:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(
            message.chat.id,
            "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n"
            "قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج",
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "games":
        bot.send_message(call.message.chat.id, "..")
        img_link2 = "https://i.postimg.cc/zvDbVTS0/photo-5893070682508606110-x.jpg"
        bot.send_photo(
            call.message.chat.id,
            img_link2,
            caption="روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، "
                    "قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇",
            reply_markup=keyboard_games
        )

bot.infinity_polling(timeout=10, long_polling_timeout=5)
