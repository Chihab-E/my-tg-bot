import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests, json
from urllib.parse import urlparse, parse_qs
import urllib.parse
import os

# Load environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret,
                           models.Language.FR, models.Currency.EUR, 'default')  # Changed to FR for French

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

# Helper function to expand shortened AliExpress URLs
def expand_shortened_url(short_url):
    try:
        session = requests.Session()
        response = session.head(short_url, allow_redirects=True, timeout=5)
        final_url = response.url
        return final_url
    except Exception as e:
        print(f"Error expanding URL: {e}")
        return short_url  # Fallback to original if expansion fails

# Improved link extraction with URL expansion
def extract_link(text):
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        link = links[0]
        # Expand if it's a shortened AliExpress link
        if "s.click.aliexpress.com" in link:
            link = expand_shortened_url(link)
        return link
    return None

# Modified to handle all URL formats
def get_affiliate_links(message, message_id, link):
    try:
        # Ensure we have the final product URL
        if "s.click.aliexpress.com" in link:
            link = expand_shortened_url(link)
        
        # Force French version for API compatibility
        if "aliexpress.com" in link and not link.startswith("https://fr.aliexpress.com"):
            parsed = urlparse(link)
            link = f"https://fr.aliexpress.com{parsed.path}?{parsed.query}" if parsed.query else f"https://fr.aliexpress.com{parsed.path}"

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
                               f"♨️ عرض محدود  : \nالرابط {limit_links} \n\n"
                               "t.me/tcoupon !",
                        reply_markup=keyboard
                    )
                    return

        except Exception as e:
            print(f"Error getting product details: {e}")

        # Fallback if product details not available
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

# Shopping cart link handler (unchanged)
def build_shopcart_link(link):
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params["availableProductShopcartIds"]),
        "extraParams": json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

def get_url_params(link):
    parsed = urlparse(link)
    return parse_qs(parsed.query)

def create_query_string_url(link, params):
    return link + urllib.parse.urlencode(params)

def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link
        text2 = f"هذا رابط تخفيض السلة \n{str(affiliate_link)}"
        img_link3 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
        bot.send_photo(message.chat.id, img_link3, caption=text2)
    except Exception as e:
        print(f"Error in shopcart: {e}")
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# Message handlers (unchanged)
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
