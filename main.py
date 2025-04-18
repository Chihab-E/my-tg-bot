import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests
from urllib.parse import urlparse, urlunparse, parse_qs
import os

# Initialize bot
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(bot_token, parse_mode='HTML')

# AliExpress API with French locale
app_key = os.getenv('ALIEXPRESS_APP_KEY')
app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
aliexpress = AliexpressApi(app_key, app_secret, models.Language.FR, models.Currency.EUR, 'default')

# ===== ULTIMATE URL CLEANER =====
def clean_aliexpress_url(url):
    """Converts any AliExpress URL to clean fr.aliexpress.com format"""
    try:
        # Follow redirects for shortened links
        if 's.click.aliexpress.com' in url:
            try:
                session = requests.Session()
                session.max_redirects = 5
                resp = session.head(url, allow_redirects=True, timeout=10)
                url = resp.url
            except:
                pass
        
        # Parse URL components
        parsed = urlparse(url)
        
        # Convert any country domain to French (vi., es., de. → fr.)
        domain_parts = parsed.netloc.split('.')
        if len(domain_parts) > 1 and domain_parts[0] in ['vi', 'es', 'de', 'it', 'ru']:
            domain_parts[0] = 'fr'
        
        # Rebuild domain (ensure it's fr.aliexpress.com)
        new_domain = '.'.join(domain_parts).replace('www.', '').replace('aliexpress.com', 'fr.aliexpress.com')
        
        # Extract product ID from various URL formats
        product_id = None
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # Standard formats: /item/100500123.html or /i/100500123.html
        if len(path_parts) >= 2 and path_parts[-2] in ['item', 'i']:
            product_id = path_parts[-1].split('.')[0]
        
        # Verify we have a valid product ID
        if product_id and product_id.isdigit() and len(product_id) >= 9:
            return f'https://{new_domain}/item/{product_id}.html'
        
    except Exception as e:
        print(f"URL cleaning error: {e}")
    
    return None

# ===== BOT HANDLERS =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🛍️ أرسل رابط منتج AliExpress للحصول على أفضل العروض!")

@bot.message_handler(func=lambda m: True)
def handle_product_link(message):
    # Extract and clean URL
    url_match = re.search(r'https?://[^\s]+', message.text)
    if not url_match:
        bot.reply_to(message, "❌ الرابط غير صالح. يرجى إرسال رابط منتج AliExpress مباشر.")
        return
    
    clean_url = clean_aliexpress_url(url_match.group())
    
    if not clean_url:
        bot.reply_to(message, "❌ لم أتمكن من تحويل الرابط إلى صيغة صالحة. يرجى المحاولة برابط آخر.")
        return
    
    try:
        # Show loading message
        msg = bot.reply_to(message, "🔍 جاري معالجة الرابط...")
        
        # Extract product ID
        product_id = re.search(r'/item/(\d+)\.html', clean_url).group(1)
        
        # Get product details
        details = aliexpress.get_products_details([product_id])[0]
        
        # Generate affiliate links
        base_link = f"https://fr.aliexpress.com/item/{product_id}.html"
        
        affiliate_links = {
            'standard': aliexpress.get_affiliate_links(f"{base_link}?sourceType=620")[0].promotion_link,
            'super': aliexpress.get_affiliate_links(f"{base_link}?sourceType=562")[0].promotion_link,
            'limited': aliexpress.get_affiliate_links(f"{base_link}?sourceType=561")[0].promotion_link
        }
        
        # Prepare response
        caption = (
            f"<b>{details.product_title}</b>\n\n"
            f"💰 السعر: {details.target_sale_price} EUR\n\n"
            f"🔗 <a href='{affiliate_links['standard']}'>رابط الشراء الأساسي</a>\n"
            f"🔥 <a href='{affiliate_links['super']}'>عرض السوبر</a>\n"
            f"⚡ <a href='{affiliate_links['limited']}'>عرض محدود</a>"
        )
        
        # Send results
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(
            message.chat.id,
            details.product_main_image_url,
            caption=caption,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🛒 شراء الآن", url=affiliate_links['standard'])
            )
        )
        
    except IndexError:
        bot.reply_to(message, "⚠️ المنتج غير متوفر في المتجر الفرنسي")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

# Start bot with error handling
while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot error: {e}")
        continue
