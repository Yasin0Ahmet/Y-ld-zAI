# Yıldız Sesli Asistan

Yıldız, Türkçe dil desteği ile çalışan, hem sesli hem de yazılı etkileşim kurabilen bir yapay zeka asistanıdır. TQuAD, BOUN TC-STAR, TR-Claims ve MC-TACO-TR veri setleri kullanılarak eğitilmiştir.

## Özellikler

- Sesli ve yazılı etkileşim
- Türkçe dil desteği
- Kod örnekleri gösterme
- Modern ve kullanıcı dostu arayüz
- Veritabanı destekli sohbet geçmişi

## Kurulum

1. Projeyi klonlayın:
```bash
git clone [repo-url]
cd [repo-directory]
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
# Windows için:
venv\Scripts\activate
# Linux/Mac için:
source venv/bin/activate
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Uygulamayı çalıştırın:
```bash
python hilal.py
```

5. Tarayıcınızda şu adresi açın: `http://localhost:5000`

## Kullanım

- Metin girişi: Mesaj kutusuna yazın ve "Gönder" düğmesine tıklayın veya Enter tuşuna basın
- Sesli giriş: Mikrofon simgesine tıklayın ve konuşun, tekrar tıklayarak kaydı sonlandırın

## Geliştirme

Proje şu teknolojileri kullanmaktadır:
- Flask (Web framework)
- SQLite (Veritabanı)
- HTML5/CSS3
- JavaScript (Ses kaydı ve asenkron iletişim)
- Transformers (NLP modelleri)

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.