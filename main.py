import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests
from urllib.parse import urlparse, urlunparse
import os

# Initialize bot with faster timeout
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token, parse_mode='HTML')

# AliExpress API with French locale
app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret, models.Language.FR, models.Currency.EUR, 'default')

# ===== IMPROVED URL HANDLING =====
def expand_short_link(url):
    """Follows all redirects for shortened links with retries"""
    try:
        session = requests.Session()
        session.max_redirects = 5
        resp = session.head(url, allow_redirects=True, timeout=10)
        return resp.url
    except:
        return url

def extract_clean_url(text):
    """Extracts and cleans any AliExpress URL format"""
    # Find first URL in message
    url_match = re.search(r'https?://[^\s]+', text)
    if not url_match:
        return None
    
    url = url_match.group()
    
    # Expand shortened links
    if 's.click.aliexpress.com' in url:
        url = expand_short_link(url)
    
    # Parse URL components
    parsed = urlparse(url)
    
    # Force French domain
    domain = parsed.netloc.replace('www.', '').replace('aliexpress.com', 'fr.aliexpress.com')
    
    # Extract product ID from various URL formats
    product_id = None
    path_parts = parsed.path.split('/')
    
    # Standard format: /item/100500123.html
    if len(path_parts) >= 3 and path_parts[1] == 'item':
        product_id = path_parts[2].split('.')[0]
    
    # Alternative format: /i/100500123.html
    elif len(path_parts) >= 3 and path_parts[1] == 'i':
        product_id = path_parts[2].split('.')[0]
    
    # Build clean French URL
    if product_id and product_id.isdigit():
        return f'https://{domain}/item/{product_id}.html'
    
    return None

# ===== BOT HANDLERS =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 أرسل رابط منتج AliExpress للحصول على أفضل العروض!")

@bot.message_handler(func=lambda m: True)
def handle_product_link(message):
    clean_url = extract_clean_url(message.text)
    
    if not clean_url:
        bot.reply_to(message, "❌ لم أتمكن من تحديد رابط منتج صالح. يرجى إرسال رابط مباشر.")
        return
    
    try:
        # Show loading message
        msg = bot.reply_to(message, "🔍 جاري البحث عن أفضل العروض...")
        
        # Extract product ID
        product_id = re.search(r'/item/(\d+)\.html', clean_url).group(1)
        
        # Get product details
        details = aliexpress.get_products_details([product_id])[0]
        
        # Generate affiliate links
        base_link = f"https://fr.aliexpress.com/item/{product_id}.html"
        
        affiliate_links = [
            aliexpress.get_affiliate_links(f"{base_link}?sourceType=620")[0].promotion_link,
            aliexpress.get_affiliate_links(f"{base_link}?sourceType=562")[0].promotion_link,
            aliexpress.get_affiliate_links(f"{base_link}?sourceType=561")[0].promotion_link
        ]
        
        # Prepare response
        caption = (
            f"<b>{details.product_title}</b>\n\n"
            f"💰 السعر: {details.target_sale_price} EUR\n\n"
            f"🔗 <a href='{affiliate_links[0]}'>رابط الشراء الأساسي</a>\n"
            f"🔥 <a href='{affiliate_links[1]}'>عرض السوبر</a>\n"
            f"⚡ <a href='{affiliate_links[2]}'>عرض محدود</a>"
        )
        
        # Send results
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(
            message.chat.id,
            details.product_main_image_url,
            caption=caption,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🛒 شراء الآن", url=affiliate_links[0])
            )
        )
        
    except IndexError:
        bot.reply_to(message, "⚠️ المنتج غير متوفر في المتجر الفرنسي (الرجاء التأكد من الرابط)")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# Start bot with error handling
while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot crashed: {e}")
        continue
