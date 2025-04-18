import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests
from urllib.parse import urlparse, urlunparse
import os

# Initialize bot
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

# AliExpress API (French locale required)
app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret, models.Language.FR, models.Currency.EUR, 'default')

# --- Helper Functions ---
def force_fr_link(url):
    """Convert any AliExpress link to fr.aliexpress.com format"""
    if "s.click.aliexpress.com" in url:
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            url = response.url
        except:
            pass
    
    parsed = urlparse(url)
    if "aliexpress.com" in parsed.netloc:
        # Force French domain
        new_netloc = parsed.netloc.replace("www.aliexpress.com", "fr.aliexpress.com") \
                                 .replace("aliexpress.com", "fr.aliexpress.com")
        
        # Keep only the product ID (remove tracking params)
        if "/item/" in parsed.path:
            path_parts = parsed.path.split('/')
            product_id = path_parts[2].split('.')[0] if len(path_parts) > 2 else None
            if product_id:
                return f"https://fr.aliexpress.com/item/{product_id}.html"
    
    return url

def extract_product_id(url):
    """Extracts product ID from URL (e.g., 100500123456789)"""
    match = re.search(r'/item/(\d+)\.html', url)
    return match.group(1) if match else None

# --- Bot Handlers ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أرسل رابط منتج AliExpress للحصول على أفضل سعر.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    # Extract and clean URL
    url_match = re.search(r'https?://[^\s]+', message.text)
    if not url_match:
        bot.reply_to(message, "⚠️ الرابط غير صالح. يرجى إرسال رابط AliExpress صحيح.")
        return
    
    original_url = url_match.group()
    clean_url = force_fr_link(original_url)
    product_id = extract_product_id(clean_url)
    
    if not product_id:
        bot.reply_to(message, "❌ لم يتم العثور على معرف المنتج في الرابط.")
        return
    
    # Generate affiliate links
    try:
        msg = bot.reply_to(message, "🔍 جاري البحث عن العروض...")
        
        # Get product details
        details = aliexpress.get_products_details([product_id])[0]
        price = details.target_sale_price
        title = details.product_title
        image = details.product_main_image_url
        
        # Generate affiliate links
        affiliate = aliexpress.get_affiliate_links(
            f"https://fr.aliexpress.com/item/{product_id}.html?sourceType=620"
        )[0].promotion_link
        
        super_deal = aliexpress.get_affiliate_links(
            f"https://fr.aliexpress.com/item/{product_id}.html?sourceType=562"
        )[0].promotion_link
        
        # Send results
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(
            message.chat.id,
            image,
            caption=f"🛍️ {title}\n💰 السعر: {price} EUR\n\n🔗 [رابط الشراء]({affiliate})\n🔥 [عرض السوبر]({super_deal})",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# Start bot
bot.infinity_polling()
