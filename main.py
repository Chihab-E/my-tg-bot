import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests, json
from urllib.parse import urlparse, parse_qs
import urllib.parse
import os

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret,
                           models.Language.EN, models.Currency.EUR, 'default')

keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("\u2b50\ufe0f\u0623\u0644\u0639\u0627\u0628 \u0644\u062c\u0645\u0639 \u0627\u0644\u0639\u0645\u0644\u0627\u062a \u0627\u0644\u0645\u0639\u062f\u0646\u064a\u0629\u2b50\ufe0f", callback_data="games")
btn2 = types.InlineKeyboardButton("\u2b50\ufe0f\u062a\u062e\u0641\u064a\u0636 \u0627\u0644\u0639\u0645\u0644\u0627\u062a \u0639\u0644\u0649 \u0645\u0646\u062a\u062c\u0627\u062a \u0627\u0644\u0633\u0644\u0629 \ud83d\ude96\u2b50\ufe0f", callback_data='click')
btn3 = types.InlineKeyboardButton("\u2764\ufe0f \u0627\u0634\u062a\u0631\u0643 \u0641\u064a \u0627\u0644\u0642\u0646\u0627\u0629 \u0644\u0644\u0645\u0632\u064a\u062f \u0645\u0646 \u0627\u0644\u0639\u0631\u0648\u0636 \u2764\ufe0f", url="t.me/Tcoupon")
keyboardStart.add(btn1, btn2, btn3)

keyboard = types.InlineKeyboardMarkup(row_width=1)
keyboard.add(btn1, btn2, btn3)

keyboard_games = types.InlineKeyboardMarkup(row_width=1)
keyboard_games.add(btn1, btn2, btn3)

def extract_product_id(link):
    match = re.search(r'/item/(\d+)\.html', link)
    if match:
        return match.group(1)
    parsed = urlparse(link)
    qs = parse_qs(parsed.query)
    if 'productId' in qs:
        return qs['productId'][0]
    return None

@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(
        message.chat.id,
        "\u0645\u0631\u062d\u0628\u0627 \u0628\u0643\u060c \u0627\u0631\u0633\u0644 \u0644\u0646\u0627 \u0631\u0627\u0628\u0637 \u0627\u0644\u0645\u0646\u062a\u062c \u0627\u0644\u0630\u064a \u062a\u0631\u064a\u062f \u0634\u0631\u0627\u0626\u0647 \u0644\u0646\u0648\u0641\u0631 \u0644\u0643 \u0627\u0641\u0636\u0644 \u0633\u0639\u0631 \u0644\u0647 \ud83d\udc4c \n",
        reply_markup=keyboardStart
    )

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

def get_affiliate_links(message, message_id, link):
    try:
        affiliate_link = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=620&aff_fcid='
        )[0].promotion_link

        super_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=562&aff_fcid='
        )[0].promotion_link

        limit_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=561&aff_fcid='
        )[0].promotion_link

        product_id = extract_product_id(link)

        if product_id:
            product_details = aliexpress.get_products_details([product_id])
            if product_details:
                price_pro = product_details[0].target_sale_price
                title_link = product_details[0].product_title
                img_link = product_details[0].product_main_image_url

                bot.delete_message(message.chat.id, message_id)
                bot.send_photo(message.chat.id,
                               img_link,
                               caption=f" \n\ud83d\uded2 \u0645\u0646\u062a\u062c\u0643 \u0647\u0648  : \ud83d\udd25 \n{title_link} \ud83c\udf6d \n"
                                       f"\u0633\u0639\u0631 \u0627\u0644\u0645\u0646\u062a\u062c  : {price_pro} \u062f\u0648\u0644\u0627\u0631 \ud83d\udcb5\n"
                                       " \n \u0642\u0627\u0631\u0646 \u0628\u064a\u0646 \u0627\u0644\u0627\u0633\u0639\u0627\u0631 \u0648\u0627\u0634\u062a\u0631\u064a \ud83d\udd25 \n"
                                       f"\ud83d\udcb0 \u0639\u0631\u0636 \u0627\u0644\u0639\u0645\u0644\u0627\u062a (\u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u0646\u0647\u0627\u0626\u064a \u0639\u0646\u062f \u0627\u0644\u062f\u0641\u0639)  : \n\u0627\u0644\u0631\u0627\u0628\u0637 {affiliate_link} \n"
                                       f"\ud83d\udc8e \u0639\u0631\u0636 \u0627\u0644\u0633\u0648\u0628\u0631  : \n\u0627\u0644\u0631\u0627\u0628\u0637 {super_links} \n"
                                       f"\u2668\ufe0f \u0639\u0631\u0636 \u0645\u062d\u062f\u0648\u062f  : \n\u0627\u0644\u0631\u0627\u0628\u0637 {limit_links} \n\n"
                                       "La Deals !",
                               reply_markup=keyboard)
                return

        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id,
                         "\u0642\u0627\u0631\u0646 \u0628\u064a\u0646 \u0627\u0644\u0627\u0633\u0639\u0627\u0631 \u0648\u0627\u0634\u062a\u0631\u064a \ud83d\udd25 \n"
                         f"\ud83d\udcb0 \u0639\u0631\u0636 \u0627\u0644\u0639\u0645\u0644\u0627\u062a (\u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u0646\u0647\u0627\u0626\u064a \u0639\u0646\u062f \u0627\u0644\u062f\u0641\u0639) : \n\u0627\u0644\u0631\u0627\u0628\u0637 {affiliate_link} \n"
                         f"\ud83d\udc8e \u0639\u0631\u0636 \u0627\u0644\u0633\u0648\u0628\u0631 : \n\u0627\u0644\u0631\u0627\u0628\u0637 {super_links} \n"
                         f"\u2668\ufe0f \u0639\u0631\u0636 \u0645\u062d\u062f\u0648\u062f : \n\u0627\u0644\u0631\u0627\u0628\u0637 {limit_links} \n\n",
                         reply_markup=keyboard)

    except Exception as e:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id, "\u062d\u062f\u062b \u062e\u0637\u0623 \ud83e\udd37\u200d\u2642\ufe0f")
        print(f"Error: {e}")

def extract_link(text):
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        return links[0]
    return None

def build_shopcart_link(link):
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params.get("availableProductShopcartIds", [])),
        "extraParams": json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

def get_url_params(link):
    parsed_url = urlparse(link)
    params = parse_qs(parsed_url.query)
    return params

def create_query_string_url(link, params):
    return link + urllib.parse.urlencode(params)

def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link

        text2 = f"\u0647\u0630\u0627 \u0631\u0627\u0628\u0637 \u062a\u062e\u0641\u064a\u0636 \u0627\u0644\u0633\u0644\u0629 \n{str(affiliate_link)}"
        img_link3 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
        bot.send_photo(message.chat.id, img_link3, caption=text2)

    except:
        bot.send_message(message.chat.id, "\u062d\u062f\u062b \u062e\u0637\u0623 \ud83e\udd37\u200d\u2642\ufe0f")

@bot.message_handler(func=lambda message: True)
def get_link(message):
    link = extract_link(message.text)

    sent_message = bot.send_message(message.chat.id, '\u0627\u0644\u0645\u0631\u062c\u0648 \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631 \u0642\u0644\u064a\u0644\u0627\u060c \u064a\u062a\u0645 \u062a\u062c\u0647\u064a\u0632 \u0627\u0644\u0639\u0631\u0648\u0636 \u23f3')
    message_id = sent_message.message_id

    if link and "aliexpress.com" in link and not ("p/shoppingcart" in message.text.lower()):
        if "availableProductShopcartIds".lower() in message.text.lower():
            get_affiliate_shopcart_link(link, message)
            return
        get_affiliate_links(message, message_id, link)
    else:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id,
                         "\u0627\u0644\u0631\u0627\u0628\u0637 \u063a\u064a\u0631 \u0635\u062d\u064a\u062d ! \u062a\u0623\u0643\u062f \u0645\u0646 \u0631\u0627\u0628\u0637 \u0627\u0644\u0645\u0646\u062a\u062c \u0623\u0648 \u0627\u0639\u062f \u0627\u0644\u0645\u062d\u0627\u0648\u0644\u0629.\n\u0642\u0645 \u0628\u0625\u0631\u0633\u0627\u0644 <b> \u0627\u0644\u0631\u0627\u0628\u0637 \u0641\u0642\u0637</b> \u0628\u062f\u0648\u0646 \u0639\u0646\u0648\u0627\u0646 \u0627\u0644\u0645\u0646\u062a\u062c",
                         parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    bot.send_message(call.message.chat.id, "..")

    img_link2 = "https://i.postimg.cc/zvDbVTS0/photo-5893070682508606110-x.jpg"
    bot.send_photo(
        call.message.chat.id,
        img_link2,
        caption="\u0631\u0648\u0627\u0628\u0637 \u0623\u0644\u0639\u0627\u0628 \u062c\u0645\u0639 \u0627\u0644\u0639\u0645\u0644\u0627\u062a \u0627\u0644\u0645\u0639\u062f\u0646\u064a\u0629 \u0644\u0625\u0633\u062a\u0639\u0645\u0627\u0644\u0647\u0627 \u0641\u064a \u062e\u0641\u0636 \u0627\u0644\u0633\u0639\u0631 \u0644\u0628\u0639\u0636 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a\u060c \n\u0642\u0645 \u0628\u0627\u0644\u062f\u062e\u0648\u0644 \u064a\u0648\u0645\u064a\u0627 \u0644\u0647\u0627 \u0644\u0644\u062d\u0635\u0648\u0644 \u0639\u0644\u0649 \u0623\u0643\u0628

