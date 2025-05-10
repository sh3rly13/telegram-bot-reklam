# Telegram Otomatik Yorum Botu

Bu bot, kendi Telegram hesabınızın üye olduğu grup ve kanallardaki yönetici mesajlarına, içerik analizi yaparak otomatik yorum yapmanızı sağlar.

## 📑 İçindekiler

- [Özellikler](#-özellikler)
- [Gereksinimler](#-gereksinimler)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Ayarlar ve Yapılandırma](#️-ayarlar-ve-yapılandırma)
- [Bot Nasıl Çalışır?](#-bot-nasıl-çalışır)
- [Hedef Grupları Nasıl Bulunur?](#-hedef-grupları-nasıl-bulunur)
- [Uyarılar](#️-uyarılar)
- [Sorun Giderme](#-sorun-giderme)

## 🌟 Özellikler

- Belirttiğiniz grup ve kanallardaki yönetici mesajlarını otomatik takip eder
- Google Gemini API kullanarak mesaj içeriğini analiz eder
- İçeriğe özel, alakalı ve doğal yorumlar oluşturur
- Sadece grup/kanal yöneticilerinin mesajlarına yanıt verir
- Kendi mesajlarınıza yanıt vermez
- Rastgele gecikmeler ekleyerek doğal bir davranış sergiler

## 📋 Gereksinimler

- Python 3.7 veya daha yüksek sürüm
- Telegram hesabı (normal kullanıcı hesabı)
- Google Gemini API anahtarı 
- Telegram API bilgileri (API ID ve API Hash)

## 🔧 Kurulum

1. Bu repoyu bilgisayarınıza klonlayın veya indirin:
   ```
   git clone <repo-url>
   cd telegram-bot-reklam
   ```

2. Gerekli Python kütüphanelerini yükleyin:
   ```
   pip install -r requirements.txt
   ```

3. `.env` dosyası oluşturun ve aşağıdaki bilgileri ekleyin:
   ```
   # Telegram API bilgileri (https://my.telegram.org adresinden alabilirsiniz)
   API_ID=your_api_id
   API_HASH=your_api_hash
   
   # Telefon numaranız (uluslararası formatta, örn: +9050123456789)
   PHONE=+905551234567

   # Grup ID bilgilerini Telegramdaki @username_to_id_bot aracılığıyla bulabilirsiniz.
   
   # Hedef grup veya kanal ID'leri (virgülle ayrılmış)
   # Örnek: -1001234567890,-1009876543210
   TARGET_GROUPS=-1001234567890,-1002345678901
   
   # Google Gemini API anahtarı (https://aistudio.google.com/app/apikey)
   GEMINI_API_KEY=your_gemini_api_key
   
   # Bot ayarları
   COMMENT_CHANCE=0.3  # Yorum yapma olasılığı (0.0-1.0 arası)
   MIN_DELAY=60        # Minimum gecikme (saniye)
   MAX_DELAY=300       # Maksimum gecikme (saniye)
   MAX_COMMENT_LENGTH=30  # Maksimum yorum uzunluğu
   ```

## 🚀 Kullanım

1. Botu başlatın:
   ```
   python bot.py
   ```

2. İlk çalıştırmada Telegram hesabınıza giriş yapmanız gerekecektir:
   - Telefon numaranıza gelen doğrulama kodunu girin
   - Gerekirse iki faktörlü doğrulama kodunu da girin

3. Bot şimdi çalışıyor! Konsolda aşağıdaki bilgileri göreceksiniz:
   - Botun kendi kullanıcı ID'si ve kullanıcı adı
   - Takip edilen gruplar ve kanallar
   - Kullanılabilir Gemini modelleri

[/ilk.png]

## ⚙️ Ayarlar ve Yapılandırma

`.env` dosyasında aşağıdaki parametreleri değiştirebilirsiniz:

- `COMMENT_CHANCE`: Bir mesaja yorum yapma olasılığı (0.0: hiç yorum yapma, 1.0: her mesaja yorum yap)
- `MIN_DELAY` ve `MAX_DELAY`: Yorum yapmadan önceki bekleme süresi (saniye)
- `MAX_COMMENT_LENGTH`: Oluşturulan yorumların maksimum uzunluğu
- `TARGET_GROUPS`: Hedef grup ve kanal ID'leri (virgülle ayrılmış)


## 🤖 Bot Nasıl Çalışır?

1. **Başlangıç**: Bot başlatıldığında, kendi kullanıcı ID'sini alır ve hedef grupları yapılandırır.

2. **Mesaj İzleme**: Belirtilen gruplarda ve kanallarda yeni mesajları izler.

3. **Filtreleme**: Bot şu mesajları filtreler:
   - Hedef gruplarda olmayan mesajlar
   - Kendi gönderdiği mesajlar
   - Yönetici olmayan kullanıcıların mesajları

4. **İçerik Analizi**: Uygun mesajlar için Gemini API kullanarak içerik analizi yapar.

5. **Yorum Oluşturma**: Mesajın içeriğine uygun, kısa ve doğal bir yorum oluşturur.

6. **Gecikme**: Yorum göndermeden önce belirlenen aralıkta rastgele bir süre bekler.

7. **Yanıt Gönderme**: Oluşturulan yorumu orijinal mesaja yanıt olarak gönderir.

## 📱 Hedef Grupları Nasıl Bulunur?

Hedef grup veya kanalların ID'lerini öğrenmek için:

1. Botu ilk kez çalıştırın ve giriş yapın
2. Bot konsolda katıldığınız tüm grupları ve kanalları listeleyecektir
3. Bu listeden istediğiniz grupların veya kanalların ID'lerini alın
4. `.env` dosyasındaki `TARGET_GROUPS` değişkenini bu ID'lerle güncelleyin

## ⚠️ Uyarılar

- Bu bot normal kullanıcı hesabınız üzerinden çalışır (bot API kullanmaz)
- Aşırı kullanım, Telegram kullanım koşullarını ihlal edebilir
- Hesap kısıtlaması riskine karşı makul ayarlar kullanın (`COMMENT_CHANCE` değerini düşük tutun)
- Google Gemini API kullanımının kota ve ücret limitlerine dikkat edin

## 🔍 Sorun Giderme

- **Bot mesajlara yanıt vermiyor**: Log mesajlarını kontrol edin, grup ID'lerinin doğru olduğundan emin olun
- **API hatası alıyorsanız**: API anahtarlarınızı kontrol edin
- **Gemini API çalışmıyorsa**: Bot otomatik olarak statik yorumlara geçiş yapacaktır
