
#!/usr/bin/env python
# coding: utf-8

import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests, json
from urllib.parse import urlparse, parse_qs
import urllib.parse
import os

# Initialize the bot with your token from the environment variable
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

# Initialize the AliExpress API with your credentials from environment variables
app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret,
                           models.Language.EN, models.Currency.EUR, 'default')

# Define the keyboards
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="t.me/LaDeals")
keyboardStart.add(btn1, btn2, btn3)

keyboard = types.InlineKeyboardMarkup(row_width=1)
keyboard.add(btn1, btn2, btn3)

keyboard_games = types.InlineKeyboardMarkup(row_width=1)
keyboard_games.add(btn1, btn2, btn3)

# Welcome message handler
@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(
        message.chat.id,
        "مرحبا بك، ارسل لنا رابط المنتج الذي تريد شرائه لنوفر لك افضل سعر له 👌 \n",
        reply_markup=keyboardStart
    )

# Callback handler for 'click' button
@bot.callback_query_handler(func=lambda call: call.data == 'click')
def button_click(callback_query):
    bot.edit_message_text(chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id,
                          text="...")

    img_link1 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
    bot.send_photo(callback_query.message.chat.id,
                   img_link1,
                   caption="",
                   reply_markup=keyboard)

# Function to get affiliate links and product details
def get_affiliate_links(message, message_id, link):
    try:
        # Extract product ID from the link
        product_id_pattern = r"item\/(\d+)\.html"
        match = re.search(product_id_pattern, link)
        if match:
            product_id = match.group(1)

        # Use AliExpress API to fetch product details
        api_url = f"https://api.aliexpress.com/product/{product_id}"  # Replace with the actual API endpoint
        headers = {
            "Authorization": "UBrTeeNkF8kjCQabs3UZsSosXIHZYzlS"  # Replace with your API token
        }
        response = requests.get(api_url, headers=headers)
        product_details = json.loads(response.text)

        # Extract product details
        product_name = product_details['title']
        product_rating = product_details['rating']
        product_image_url = product_details['image_url']

        # ... (rest of your code to get affiliate links)

        # Send product details and image to the user
        bot.send_photo(message.chat.id, product_image_url,
                      caption=f"Product Name: {product_name}\nRating: {product_rating}\n\n{affiliate_link_message}")

    except Exception as e:
        # Handle errors gracefully
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")
        affiliate_link = aliexpress.get_affiliate_links(
            f'https://vi.aliexpress.com/item/[product_id].html?sourceType=620&channel=coin&aff_fcid=21d231ec67b048deb8113c21bad4b7e5-1730491505984-05606-_oBHwjeb&aff_fsk=_oBHwjeb&aff_platform=api-new-link-generate&sk=_oBHwjeb&aff_trace_key=21d231ec67b048deb8113c21bad4b7e5-1730491505984-05606-_oBHwjeb&terminal_id=18e426222265424dbc2fd34c66f1d3a2
')[0].promotion_link

        super_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=562&aff_fcid='
        )[0].promotion_link

        limit_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=561&aff_fcid='
        )[0].promotion_link

        try:
            product_details = aliexpress.get_products_details([
                '1000006468625',
                f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}'
            ])
            price_pro = product_details[0].target_sale_price
            title_link = product_details[0].product_title
            img_link = product_details[0].product_main_image_url

            bot.delete_message(message.chat.id, message_id)
            bot.send_photo(message.chat.id,
                           img_link,
                           caption=f" \n🛒 منتجك هو  : 🔥 \n{title_link} 🛍 \n"
                                   f"سعر المنتج  : {price_pro} دولار 💵\n"
                                   " \n قارن بين الاسعار واشتري 🔥 \n"
                                   f"💰 عرض العملات (السعر النهائي عند الدفع)  : \nالرابط {affiliate_link} \n"
                                   f"💎 عرض السوبر  : \nالرابط {super_links} \n"
                                   f"♨️ عرض محدود  : \nالرابط {limit_links} \n\n"
                                   "La Deals !",
                           reply_markup=keyboard)

        except:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, 
                             "قارن بين الاسعار واشتري 🔥 \n"
                             f"💰 عرض العملات (السعر النهائي عند الدفع) : \nالرابط {affiliate_link} \n"
                             f"💎 عرض السوبر : \nالرابط {super_links} \n"
                             f"♨️ عرض محدود : \nالرابط {limit_links} \n\n"
                             ,
                             reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# Function to extract links from text
def extract_link(text):
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        return links[0]
    return None

# Function to build shopcart link
def build_shopcart_link(link):
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params["availableProductShopcartIds"]),
        "extraParams": json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

# Function to parse URL parameters
def get_url_params(link):
    parsed_url = urlparse(link)
    params = parse_qs(parsed_url.query)
    return params

# Function to create a URL with query string
def create_query_string_url(link, params):
    return link + urllib.parse.urlencode(params)

# Function to get shopcart affiliate link
def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link

        text2 = f"هذا رابط تخفيض السلة \n{str(affiliate_link)}"
        img_link3 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
        bot.send_photo(message.chat.id, img_link3, caption=text2)

    except:
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# Message handler for all text messages
@bot.message_handler(func=lambda message: True)
def get_link(message):
    link = extract_link(message.text)

    sent_message = bot.send_message(message.chat.id, 'المرجو الانتظار قليلا، يتم تجهيز العروض ⏳')
    message_id = sent_message.message_id

    if link and "aliexpress.com" in link and not ("p/shoppingcart" in message.text.lower()):
        if "availableProductShopcartIds".lower() in message.text.lower():
            get_affiliate_shopcart_link(link, message)
            return
        get_affiliate_links(message, message_id, link)
    else:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id,
                         "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n"
                         "قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج",
                         parse_mode='HTML')

# Callback handler for any callback query
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    bot.send_message(call.message.chat.id, "..")

    img_link2 = "https://i.postimg.cc/zvDbVTS0/photo-5893070682508606110-x.jpg"
    bot.send_photo(
        call.message.chat.id,
        img_link2,
        caption="روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، "
                "قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇",
        reply_markup=keyboard_games)

# Keep the bot alive
bot.infinity_polling(timeout=10, long_polling_timeout=5)
