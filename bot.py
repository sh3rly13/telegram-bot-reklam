from telethon import TelegramClient, events
import random
import asyncio
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# .env dosyasından bilgileri al
load_dotenv()

# Telegram API bilgileri
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')  # Telefon numaranız

# Gemini API anahtarı
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# API anahtarı varsa yapılandır
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Gemini API yapılandırması başarılı")
    except Exception as e:
        logger.error(f"Gemini API yapılandırma hatası: {e}")
else:
    logger.warning("Gemini API anahtarı bulunamadı! Statik yorumlar kullanılacak.")

# Statik yorum listesi - Gemini kullanılamadığında yedek olarak kullanılacak
FALLBACK_COMMENTS = [
    "Çok güzel paylaşım 👍",
    "Emeğinize sağlık",
    "Süper içerik",
    "Güzel bilgiler",
    "Bayıldım buna"
]

# Hangi gruplarda veya kanallarda yorum yapılacağı (kullanıcı adları listesi)
TARGET_GROUPS_RAW = os.getenv('TARGET_GROUPS', '')
TARGET_GROUPS = []
TARGET_POSITIVE_IDS = []  # Pozitif ID'ler (Telethon'un verdiği format)
TARGET_ID_MAP = {}  # ID'lerin integer veya string durumunu izlemek için

# Bot ayarları
COMMENT_CHANCE = float(os.getenv('COMMENT_CHANCE', '0.3'))  # Bir gönderiye yorum yapma olasılığı (0.0-1.0 arası)
MIN_DELAY = int(os.getenv('MIN_DELAY', '60'))  # Yorumlar arasında minimum gecikme (saniye)
MAX_DELAY = int(os.getenv('MAX_DELAY', '300'))  # Yorumlar arasında maksimum gecikme (saniye)
MAX_COMMENT_LENGTH = int(os.getenv('MAX_COMMENT_LENGTH', '30'))  # Maksimum yorum uzunluğu
GEMINI_ENABLED = True  # Gemini API'nin kullanılıp kullanılmayacağı

# Bot kullanıcı bilgileri
BOT_USER_ID = None  # Botun kendi kullanıcı ID'si, başlatma sırasında doldurulacak

# TelegramClient başlatma
client = TelegramClient('session_name', API_ID, API_HASH)

async def list_available_models():
    """Kullanılabilir Gemini modellerini listeler"""
    try:
        models = genai.list_models()
        logger.info("Kullanılabilir modeller:")
        for model in models:
            logger.info(f" - {model.name}")
        return models
    except Exception as e:
        logger.error(f"Model listesi alınamadı: {e}")
        return []

async def generate_comment_from_content(content):
    """
    Mesaj içeriğine göre dinamik bir yorum oluşturur.
    Gemini API kullanarak içeriği analiz eder ve uygun bir yorum üretir.
    """
    global GEMINI_ENABLED
    
    # Gemini devre dışı bırakıldıysa statik yorum kullan
    if not GEMINI_ENABLED:
        return random.choice(FALLBACK_COMMENTS)
        
    try:
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API anahtarı bulunamadı")
            
        # Mesaj içeriği boşsa veya çok kısaysa statik bir yorum kullan
        if not content or len(content) < 10:
            return random.choice(FALLBACK_COMMENTS)
        
        # Gemini modeli oluştur - farklı model isimleri deneyelim
        # En son model isimleri dahil
        model_names = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", "gemini-1.0-pro"]
        model = None
        last_error = None
        
        for model_name in model_names:
            try:
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 60,
                }
                
                model = genai.GenerativeModel(model_name=model_name,
                                          generation_config=generation_config)
                logger.info(f"{model_name} modeli başarıyla yüklendi")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"{model_name} modeli yüklenemedi: {e}")
                continue
                
        if not model:
            logger.error(f"Hiçbir model yüklenemedi. Son hata: {last_error}")
            GEMINI_ENABLED = False  # Gemini'yi devre dışı bırak
            return random.choice(FALLBACK_COMMENTS)
            
        # Gemini API'ye istek gönder
        prompt = f"""Aşağıdaki Telegram mesajına kısa (maksimum {MAX_COMMENT_LENGTH} karakter) ve doğal bir Türkçe yorum yaz. 
Yorum çok kısa olmalı, mesajla alakalı, pozitif ve destekleyici olsun. Emoji kullanabilirsin. Sorular sorma.

Mesaj: {content}
"""
        
        # İçeriği hazırla (verdiğiniz curl komutuna benzer şekilde)
        response = model.generate_content(prompt)
        
        # Yanıtı al
        comment = response.text.strip()
        
        # Yorumu belirli bir uzunlukla sınırla
        if len(comment) > MAX_COMMENT_LENGTH:
            comment = comment[:MAX_COMMENT_LENGTH] + "..."
            
        return comment
        
    except Exception as e:
        logger.error(f"Gemini API hatası: {e}")
        
        # Arka arkaya hatalar alınıyorsa Gemini'yi devre dışı bırak
        GEMINI_ENABLED = False
        logger.warning("Gemini API devre dışı bırakıldı, statik yorumlar kullanılacak")
        
        # Hata durumunda önceden tanımlı yorumlardan birini kullan
        return random.choice(FALLBACK_COMMENTS)

def convert_id_format(id_value):
    """Telegram ID formatları arasında dönüşüm yapar"""
    # String'e çevir
    id_str = str(id_value)
    
    # Pozitif ID'yi negatif formata çevir (-100...)
    if id_str.isdigit() and not id_str.startswith('-'):
        return f"-100{id_str}"
        
    # -100 formatındaki ID'yi pozitif formata çevir
    if id_str.startswith('-100'):
        positive_id = id_str[4:]  # -100 kısmını çıkar
        return positive_id
        
    # -1002... formatındaki ID'yi düzelt
    if id_str.startswith('-1002'):
        correct_id = f"-100{id_str[5:]}"
        return correct_id
        
    # Diğer formatlar için kendisini döndür
    return id_str

async def setup_target_groups():
    """Hedef grupları doğru formatta ayarlar"""
    global TARGET_GROUPS, TARGET_POSITIVE_IDS, TARGET_ID_MAP
    
    if not TARGET_GROUPS_RAW:
        logger.warning("TARGET_GROUPS değişkeni boş! En az bir grup veya kanal belirtmelisiniz.")
        return
    
    # Virgülle ayrılmış hedef grupları ayrıştır
    groups = TARGET_GROUPS_RAW.split(',')
    
    for group in groups:
        group = group.strip()
        if not group:
            continue
            
        # Sayısal ID'leri düzelt
        if group.startswith('-100'):
            # ID zaten -100 formatında
            group_id = int(group)
            TARGET_GROUPS.append(group_id)
            
            # Pozitif ID'yi de kaydet (Telethon'un kullandığı format)
            positive_id = int(group[4:])
            TARGET_POSITIVE_IDS.append(positive_id)
            
            TARGET_ID_MAP[group_id] = positive_id
            logger.debug(f"Negatif ID: {group_id}, Pozitif ID: {positive_id}")
            
        elif group.startswith('-'):
            # ID muhtemelen -1002... formatında veya başka bir negatif format
            if group.startswith('-1002'):
                # -1002... formatını -100... formatına düzelt
                correct_id = int(f"-100{group[5:]}")
                TARGET_GROUPS.append(correct_id)
                
                # Pozitif ID'yi de kaydet
                positive_id = int(group[5:])
                TARGET_POSITIVE_IDS.append(positive_id)
                
                TARGET_ID_MAP[correct_id] = positive_id
                logger.debug(f"Düzeltilmiş Negatif ID: {correct_id}, Pozitif ID: {positive_id}")
                logger.info(f"Grup ID'si düzeltildi: {group} -> {correct_id}")
            else:
                # Normal bir negatif ID, -100 ekle
                correct_id = int(f"-100{group[1:]}")
                TARGET_GROUPS.append(correct_id)
                
                # Pozitif ID'yi de kaydet
                positive_id = int(group[1:])
                TARGET_POSITIVE_IDS.append(positive_id)
                
                TARGET_ID_MAP[correct_id] = positive_id
                logger.debug(f"Düzeltilmiş Negatif ID: {correct_id}, Pozitif ID: {positive_id}")
        else:
            # Kullanıcı adı veya başka bir string
            TARGET_GROUPS.append(group)
            TARGET_ID_MAP[group] = "str"
            logger.debug(f"String ID/username: {group}")
    
    logger.info(f"Hedef gruplar (negatif ID): {TARGET_GROUPS}")
    logger.info(f"Hedef gruplar (pozitif ID): {TARGET_POSITIVE_IDS}")

def is_target_group_id(chat_id):
    """Verilen chat_id'nin hedef gruplardan biri olup olmadığını doğrudan kontrol eder"""
    global TARGET_GROUPS, TARGET_POSITIVE_IDS
    
    # Detaylı debug logları ekle
    logger.debug(f"Kontrol edilen chat_id: {chat_id}, tip: {type(chat_id)}")
    
    # 1. Pozitif ID formatını kontrol et (Telethon genelde bunu verir)
    if chat_id in TARGET_POSITIVE_IDS:
        logger.debug(f"{chat_id} pozitif ID listesinde bulundu!")
        return True
    
    # 2. Negatif ID formatını kontrol et (-100...)
    if chat_id in TARGET_GROUPS:
        logger.debug(f"{chat_id} negatif ID listesinde bulundu!")
        return True
        
    # 3. String formatları kontrol et
    str_chat_id = str(chat_id)
    
    # 4. Dönüşüm yaparak kontrol et
    if str_chat_id.isdigit():  # Pozitif sayısal ID
        # Pozitif ID'yi negatif formata çevir
        negative_id = f"-100{str_chat_id}"
        if negative_id in str(TARGET_GROUPS):
            logger.debug(f"Negatif forma çevrilen ID {negative_id} hedef gruplar arasında bulundu!")
            return True
    
    # 5. Negatif ID'yi pozitif formata çevir
    if str_chat_id.startswith('-100'):
        positive_id = int(str_chat_id[4:])
        if positive_id in TARGET_POSITIVE_IDS:
            logger.debug(f"Pozitif forma çevrilen ID {positive_id} hedef gruplar arasında bulundu!")
            return True
    
    # Eğer buraya kadar geldiyse, hedef değil
    logger.debug(f"{chat_id} hedef gruplar arasında bulunamadı!")
    return False

async def get_group_info():
    """Tüm katılınan gruplar ve kanallar hakkında bilgi toplar"""
    try:
        dialogs = await client.get_dialogs()
        
        groups_and_channels = []
        logger.info("Katılınan gruplar ve kanallar:")
        
        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                entity_type = "Grup" if dialog.is_group else "Kanal"
                id_raw = dialog.id
                id_str = str(id_raw)
                name = dialog.title
                
                # Hem pozitif hem negatif ID formlarını logla
                negative_id = f"-100{id_raw}" if not id_str.startswith('-') else id_str
                
                # Hedef listesinde olup olmadığını kontrol et
                is_target = is_target_group_id(id_raw)
                target_status = "✅ Hedef" if is_target else "❌ Hedef değil"
                
                groups_and_channels.append((id_str, name, entity_type, target_status))
                logger.info(f"ID: {id_raw} (Pozitif), {negative_id} (Negatif), İsim: {name}, Tür: {entity_type}, Durum: {target_status}")
        
        return groups_and_channels
    except Exception as e:
        logger.error(f"Grup bilgileri alınırken hata: {e}")
        return []

async def is_admin(chat, user_id):
    """Kullanıcının belirtilen sohbette yönetici olup olmadığını kontrol eder"""
    try:
        # Sohbet varlığını al
        entity = await client.get_entity(chat)
        
        # Yöneticileri al
        admins = await client.get_participants(entity, filter=lambda x: x.admin_rights)
        admin_ids = [admin.id for admin in admins]
        
        # Kanal sahibini ekle (varsa)
        if hasattr(entity, 'creator') and entity.creator:
            admin_ids.append(entity.creator.id)
            
        # Kanal/grup sahibini ekle
        try:
            creator = await client.get_entity(entity.creator_id)
            admin_ids.append(creator.id)
        except:
            pass
            
        # Admin mi kontrol et
        return user_id in admin_ids
    except Exception as e:
        logger.debug(f"Yönetici kontrolü yapılırken hata oluştu: {e}")
        # Hata durumunda, güvenli tarafta kal ve evet döndür
        return True

# Mesaj işleme fonksiyonu - direkt olarak decorator ile tanımlanmış
@client.on(events.NewMessage)
async def message_handler(event):
    """Gelen tüm mesajları işler"""
    try:
        # Her mesaj için log tut
        logger.debug("=== YENİ MESAJ ALINDI ===")
        
        # Grup veya kanal adını ve ID'sini al
        chat = await event.get_chat()
        chat_id = chat.id
        chat_title = getattr(chat, 'title', str(chat_id))
        
        # Çeşitli ID formatlarını logla
        logger.debug(f"Mesaj alındı - Chat ID: {chat_id} (Pozitif format), -100{chat_id} (Negatif format)")
        logger.debug(f"Chat başlığı: {chat_title}")
        
        # Mesaj içeriğini logla
        message_content = event.message.message
        logger.debug(f"Mesaj içeriği: {message_content[:100]}...")
        
        # Bu grup/kanal hedef listesinde mi kontrol et
        if chat_id in TARGET_POSITIVE_IDS:
            is_target = True
            logger.debug(f"✅ {chat_id} pozitif ID listesinde bulundu - HEDEF GRUP!")
        else:
            is_target = False
            logger.debug(f"❌ {chat_id} pozitif ID listesinde bulunamadı")
            
        if not is_target:
            logger.debug(f"'{chat_title}' (ID: {chat_id}) hedef gruplardan değil, mesaj yok sayıldı")
            return
        
        # Mesajı gönderen kullanıcının ID'sini al
        sender = await event.get_sender()
        sender_id = sender.id
        
        # 1. Kendi mesajımıza yanıt vermiyoruz
        if sender_id == BOT_USER_ID:
            logger.debug(f"Mesaj botun kendisinden geldi (ID: {sender_id}), yanıt verilmeyecek")
            return
            
        # 2. Sadece adminlerin mesajlarına yanıt veriyoruz
        is_admin_user = await is_admin(chat, sender_id)
        if not is_admin_user:
            logger.debug(f"Kullanıcı (ID: {sender_id}) yönetici değil, yanıt verilmeyecek")
            return
            
        logger.info(f"👁️ '{chat_title}' (ID: {chat_id}) grubunda/kanalında yöneticinin yeni bir mesajı tespit edildi")
        
        # Belirli bir olasılıkla yorum yap
        if random.random() < COMMENT_CHANCE:
            # Mesaj içeriği kontrolü
            if not message_content:
                logger.info("Mesaj içeriği boş, yorum yapılmayacak")
                return
                
            logger.info(f"📝 Mesaj içeriği: {message_content[:30]}...")
            
            # İçeriğe göre yorum oluştur
            comment = await generate_comment_from_content(message_content)
            
            # Rastgele bir gecikme süresi belirle
            delay = random.randint(MIN_DELAY, MAX_DELAY)
            logger.info(f"⏱️ {delay} saniye sonra yorum yapılacak: '{comment}'")
            
            # Gecikme uygula
            await asyncio.sleep(delay)
            
            # Yorumu gönder
            try:
                await event.reply(comment)
                logger.info(f"✅ Yorum başarıyla gönderildi: '{comment}'")
            except Exception as reply_err:
                logger.error(f"❌ Yorum gönderilirken hata oluştu: {reply_err}")
        else:
            logger.info(f"🎲 Şans faktörü nedeniyle bu mesaja yorum yapılmayacak (şans: {COMMENT_CHANCE})")
    except Exception as e:
        logger.error(f"❌ Mesaj işleme hatası: {e}")

async def main():
    global BOT_USER_ID
    
    # Kullanıcı olarak giriş yap
    await client.start()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE)
        code = input('Telefonunuza gelen kodu girin: ')
        await client.sign_in(PHONE, code)
    
    # Kendi kullanıcı bilgilerimizi al
    me = await client.get_me()
    BOT_USER_ID = me.id
    logger.info(f"Bot kullanıcı ID: {BOT_USER_ID}, Kullanıcı adı: @{me.username}")
    
    # Hedef grupları ayarla
    await setup_target_groups()
    
    # Katılınan gruplar hakkında bilgi göster
    await get_group_info()
    
    # Gemini API kullanılabilirliğini kontrol et
    if GEMINI_API_KEY:
        try:
            await list_available_models()
        except Exception as e:
            logger.error(f"Gemini API modelleri listelenirken hata: {e}")
            logger.warning("Gemini API kullanılamıyor, statik yorumlar kullanılacak")
            global GEMINI_ENABLED
            GEMINI_ENABLED = False
    
    # Event handler zaten dekoratör ile tanımlandı
    # client.add_event_handler yaklaşımı devre dışı bırakıldı
    
    logger.info("🚀 Bot başlatıldı ve SADECE belirtilen hedef gruplardaki YÖNETİCİLERİN mesajlarına yanıt verecek")
    logger.info(f"📋 Takip edilen gruplar (negatif ID): {TARGET_GROUPS}")
    logger.info(f"📋 Takip edilen gruplar (pozitif ID): {TARGET_POSITIVE_IDS}")
    
    # Test mesajı
    logger.info("📢 Bot mesajları yanıtlamaya hazır! Hedef grupların herhangi birine bir mesaj gönderin.")
    
    # Botu çalıştır
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
