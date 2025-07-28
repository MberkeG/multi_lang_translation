# 🌍 Çok Dilli Web Sayfası İçerik Tamamlama Aracı

Bu proje, çoklu dil destekli bir web platformunda eksik kalan çevirileri otomatik olarak tamamlamak amacıyla geliştirilmiştir. TR ⇄ EN dilleri arasında eksik içerikler Light LLM modelleri (Helsinki-NLP) ile çevrilerek yapılandırılmış JSON formatına entegre edilir.

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Dosya Formatları](#-dosya-formatları)
- [Kullanılan Modeller](#-kullanılan-modeller)
- [Sorun Giderme](#-sorun-giderme)
- [Güvenlik](#️-güvenlik)

## 🔧 Özellikler

- 🔁 **Çift Yönlü Çeviri**: TR → EN ve EN → TR yönlerinde tam destek
- 🤖 **AI Destekli**: Hugging Face üzerindeki Light LLM modelleri (Helsinki-NLP, mBART, MT5)
- 🧠 **Akıllı Tespit**: Eksik çevirileri otomatik olarak tespit ve eşleştirme
- 🛠️ **Güvenilirlik**: Yedek model desteği ve kapsamlı hata yönetimi
- 📊 **İstatistikler**: Detaylı çeviri raporu ve başarı oranı
- 📂 **Yapılandırılmış Çıktı**: `completed_translations.json` formatında sonuç

## 🚀 Kurulum

### Gereksinimler

```bash
pip install requests
```

**Platform Desteği:**
- ✅ Google Colab (Önerilen)
- ✅ Jupyter Notebook
- ✅ Yerel Python ortamı (3.7+)

### 1. Hugging Face Token Alma

1. [Hugging Face](https://huggingface.co/join) hesabı oluşturun (ücretsiz)
2. [Token sayfasına](https://huggingface.co/settings/tokens) gidin
3. **"New token"** → **"Read"** yetkisi seçin
4. Token'ı kopyalayın: `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. Token Kurulumu

**Google Colab için:**
```python
HF_TOKEN = "hf_your_token_here"  # Koda direkt yazın
```

**Yerel ortam için:**
```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 🚀 Kullanım

### Adım 1: Script'i Çalıştırma

**Google Colab'da:**
1. Script'i Colab'a yükleyin
2. Token'ı kod içindeki `HF_TOKEN = ""` kısmına yapıştırın
3. Çalıştırın: `Ctrl + F9`

**Yerel ortamda:**
```bash
python ceviri_scripti.py
```

### Adım 2: Dosya Yükleme

Script çalıştığında size bir dosya seçme arayüzü gösterecek:
- `.json` formatında dosyanız olmalı
- Dosya boyutu sınırı: ~50MB
- Örnek: `filtered_2.json`, `website_content.json`

### Adım 3: İşlem Takibi

Script çalışırken şunları göreceksiniz:
```
🧪 MODEL TEST BAŞLIYOR...
1️⃣ TR→EN Test: ✅ Başarılı
2️⃣ EN→TR Test: ✅ Başarılı

📄 Sayfa 1/10 işleniyor...
🔄 TR→EN: Havalimanında check-in işlemi nasıl...
✅ TR→EN eklendi
```

### Adım 4: Sonuç Alma

- İşlem bitince `completed_translations.json` otomatik indirilir
- Detaylı istatistik raporu görüntülenir
- Başarı oranı ve çeviri sayısı gösterilir

## 📁 Dosya Formatları

### Giriş Dosyası Formatı

```json
[
  {
    "url": "https://airlinehelp.com/tr/check-in",
    "title": "Check-in Yardım Sayfası",
    "tr": [
      {
        "question": "Havalimanında check-in işlemi nasıl yapılır?",
        "answer": "Check-in işlemi havalimanındaki kiosklardan yapılabilir.",
        "page_url": "https://airlinehelp.com/tr/check-in",
        "page_title": "Check-in Rehberi"
      }
    ],
    "en": [
      {
        "question": "How do I check in at the airport?",
        "answer": "You can check in using kiosks at the airport.",
        "page_url": "https://airlinehelp.com/en/check-in", 
        "page_title": "Check-in Guide"
      }
    ]
  }
]
```

### Çıktı Dosyası Formatı

Aynı yapı korunur, sadece eksik çeviriler eklenir:

```json
{
  "question": "What documents do I need for check-in?",
  "answer": "You need your passport and booking confirmation.",
  "page_url": "https://airlinehelp.com/tr/check-in",
  "page_title": "Check-in Rehberi",
  "language": "en",
  "modified_date": "Translated by Helsinki-NLP"
}
```

## 🤖 Kullanılan Modeller

### Ana Modeller
| Yön | Model | Açıklama |
|-----|-------|----------|
| 🇹🇷→🇬🇧 | `Helsinki-NLP/opus-mt-tr-en` | Türkçe'den İngilizce'ye özel |
| 🇬🇧→🇹🇷 | `Helsinki-NLP/opus-mt-tc-big-en-tr` | Büyük İngilizce→Türkçe modeli |

### Yedek Modeller
- `facebook/mbart-large-50-many-to-many-mmt` (Çok dilli, yüksek kalite)
- `Helsinki-NLP/opus-mt-mul-tr` (Çok dilli→Türkçe)
- `google/mt5-base` (Google'ın çok dilli modeli)

### Model Seçim Algoritması

1. **Ana model** denenir (opus-mt serisi)
2. Hata durumunda **yedek modeller** sırayla test edilir
3. **503 hatası**: 30 saniye bekleyip tekrar dener
4. **429 hatası**: Rate limit, 25 saniye bekler
5. **404 hatası**: Yedek modele geçer

## 🔍 Sorun Giderme

### Yaygın Hatalar

**❌ "HF_TOKEN boş" Hatası**
```
Çözüm: Token'ı doğru şekilde yapıştırdığınızdan emin olun
Kontrol: Token hf_xxxxxxxx ile başlamalı
```

**❌ "Model 404" Hatası**
```
Neden: Model geçici olarak kapalı
Çözüm: Script otomatik olarak yedek model dener
Bekleme: 30-60 saniye sabırlı olun
```

**❌ "Rate Limit" (429) Hatası**
```
Neden: Çok hızlı istek gönderimi
Çözüm: Script otomatik olarak bekler
Manuel: time.sleep() sürelerini artırın
```

**❌ JSON Formatı Hatası**
```
Kontrol: Dosyanızda "tr" ve "en" anahtarları var mı?
Validation: JSON formatı geçerli mi? (jsonlint.com)
Encoding: UTF-8 kodlaması kullanılmalı
```

### Performans İpuçları

- **Büyük dosyalar**: 1000+ soru için işlem 2-3 saat sürebilir
- **Hız artırma**: `time.sleep()` değerlerini azaltın (dikkatli)
- **İnternet**: Stabil bağlantı gerekli (Hugging Face API)

## 🛡️ Güvenlik

### Token Güvenliği
- ❌ **Token'ı kod içine yazmayın** (public repo'larda)
- ✅ **Ortam değişkeni kullanın** (`os.getenv()`)
- ✅ **Token'ı başkalarıyla paylaşmayın**
- ✅ **Kullanım sonrası revoke edin** (isteğe bağlı)

### Veri Güvenliği
- Script sadece çeviri yapar, veri toplamaz
- Hugging Face API'ye gönderilen veriler geçicidir
- Yerel dosyalar Google Colab ortamında kalır

## 👤 Geliştirici Notu

Bu araç, çoklu dil destekli içerik sistemlerinde çeviri eksiklerini yapay zeka destekli çözümlerle tamamlamak amacıyla hazırlanmıştır. İşletmelerin ve geliştiricilerin uluslararasılaşma süreçlerini hızlandırmayı hedefler.