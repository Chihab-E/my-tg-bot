import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests
from urllib.parse import urlparse, urlunparse, parse_qs
import os

# Load environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret,
                         models.Language.FR, models.Currency.EUR, 'default')

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

def clean_aliexpress_url(url):
    """Convert any AliExpress URL to clean fr.aliexpress.com product URL"""
    try:
        parsed = urlparse(url)
        
        # Handle shortened links
        if "s.click.aliexpress.com" in parsed.netloc:
            session = requests.Session()
            response = session.head(url, allow_redirects=True, timeout=5)
            url = response.url
            parsed = urlparse(url)
        
        # Force French domain
        if "aliexpress.com" in parsed.netloc:
            new_netloc = parsed.netloc.replace("www.aliexpress.com", "fr.aliexpress.com") \
                                     .replace("aliexpress.com", "fr.aliexpress.com")
            
            # Keep only the essential product path and ID
            if "/item/" in parsed.path:
                path_parts = parsed.path.split('/')
                product_id = path_parts[2].split('.')[0] if len(path_parts) > 2 else None
                if product_id:
                    clean_path = f"/item/{product_id}.html"
                    return urlunparse(('https', new_netloc, clean_path, '', '', ''))
        
        return url
    except Exception as e:
        print(f"Error cleaning URL: {e}")
        return url

def extract_link(text):
    """Extract first URL from text and clean it"""
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        return clean_aliexpress_url(links[0])
    return None

def get_affiliate_links(message, message_id, original_link):
    try:
        # Get clean product URL
        clean_link = clean_aliexpress_url(original_link)
        print(f"Clean product URL: {clean_link}")  # Debug
        
        # Generate affiliate links
        affiliate_link = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={clean_link}?sourceType=620&aff_fcid='
        )[0].promotion_link

        super_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={clean_link}?sourceType=562&aff_fcid='
        )[0].promotion_link

        limit_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={clean_link}?sourceType=561&aff_fcid='
        )[0].promotion_link

        try:
            # Extract product ID for details lookup
            product_id_match = re.search(r'/item/(\d+)\.html', clean_link)
            if product_id_match:
                product_id = product_id_match.group(1)
                print(f"Fetching details for product ID: {product_id}")  # Debug
                product_details = aliexpress.get_products_details([product_id])
                
                if product_details and hasattr(product_details[0], 'product_main_image_url'):
                    price_pro = product_details[0].target_sale_price
                    title_link = product_details[0].product_title
                    img_link = product_details[0].product_main_image_url

                    bot.delete_message(message.chat.id, message_id)
                    bot.send_photo(
                        message.chat.id,
                        img_link,
                        caption=f"🛒 المنتج: {title_link}\n"
                               f"💰 السعر: {price_pro} دولار\n\n"
                               f"🔗 عرض العملات: {affiliate_link}\n"
                               f"💎 عرض السوبر: {super_links}\n"
                               f"⏳ عرض محدود: {limit_links}",
                        reply_markup=keyboard
                    )
                    return

        except Exception as e:
            print(f"Product details error: {e}")

        # Fallback to just affiliate links
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(
            message.chat.id,
            f"🔗 عرض العملات: {affiliate_link}\n"
            f"💎 عرض السوبر: {super_links}\n"
            f"⏳ عرض محدود: {limit_links}",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Affiliate links error: {e}")
        bot.send_message(message.chat.id, "حدث خطأ في معالجة الرابط 🤷🏻‍♂️")

# Rest of your handlers remain the same...
@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(
        message.chat.id,
        "مرحبا بك، ارسل لنا رابط المنتج الذي تريد شرائه لنوفر لك افضل سعر له 👌",
        reply_markup=keyboardStart
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    link = extract_link(message.text)
    if not link:
        bot.send_message(
            message.chat.id,
            "الرابط غير صحيح! تأكد من إرسال رابط منتج AliExpress صالح.",
            parse_mode='HTML'
        )
        return

    sent_message = bot.send_message(message.chat.id, 'جاري تجهيز العروض... ⏳')
    get_affiliate_links(message, sent_message.message_id, link)

bot.infinity_polling()
