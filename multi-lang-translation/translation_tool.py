import json
import requests
import time
import os
import sys
from pathlib import Path

# 📌 Hugging Face Token'ını buraya yapıştır veya çevre değişkeni kullan
HF_TOKEN = os.getenv("HF_TOKEN") or "YOUR_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# ÇALIŞAN ALTERNATIF MODELLER
MODELS = {
    "tr_to_en": "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-tr-en",
    "en_to_tr": "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-tc-big-en-tr"
}

# Yedek modeller
BACKUP_MODELS = {
    "en_to_tr_1": "https://api-inference.huggingface.co/models/facebook/mbart-large-50-many-to-many-mmt",
    "en_to_tr_2": "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-mul-tr",
    "en_to_tr_3": "https://api-inference.huggingface.co/models/google/mt5-base"
}

def detect_environment():
    """Çalışma ortamını tespit et"""
    try:
        import google.colab
        return "colab"
    except ImportError:
        return "local"

def get_input_file():
    """Ortama göre dosya yükleme"""
    env = detect_environment()
    
    if env == "colab":
        print("🌐 Google Colab ortamı tespit edildi")
        from google.colab import files
        uploaded = files.upload()
        file_name = list(uploaded.keys())[0]
        return file_name
    else:
        print("💻 Yerel ortam tespit edildi")
        
        # Komut satırı argümanı kontrol et
        if len(sys.argv) > 1:
            file_name = sys.argv[1]
            if os.path.exists(file_name):
                return file_name
            else:
                print(f"❌ Dosya bulunamadı: {file_name}")
        
        # Mevcut dizindeki JSON dosyalarını listele
        json_files = list(Path(".").glob("*.json"))
        
        if not json_files:
            print("❌ Mevcut dizinde JSON dosyası bulunamadı!")
            print("💡 Kullanım: python script.py dosya_adi.json")
            return None
        
        print("📂 Bulunan JSON dosyaları:")
        for i, file in enumerate(json_files, 1):
            print(f"  {i}. {file.name}")
        
        while True:
            try:
                choice = input(f"\nHangi dosyayı kullanmak istiyorsunuz? (1-{len(json_files)}): ")
                if choice.lower() == 'q':
                    return None
                    
                index = int(choice) - 1
                if 0 <= index < len(json_files):
                    return str(json_files[index])
                else:
                    print(f"❌ Geçersiz seçim! 1-{len(json_files)} arası bir sayı girin.")
            except ValueError:
                print("❌ Geçersiz giriş! Sayı girin veya çıkmak için 'q' yazın.")

def save_and_download(data, output_filename):
    """Ortama göre dosya kaydetme"""
    env = detect_environment()
    
    # Dosyayı kaydet
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    if env == "colab":
        # Colab'da indir
        from google.colab import files
        files.download(output_filename)
        print(f"📥 Dosya Colab'dan indirildi: {output_filename}")
    else:
        # Yerel ortamda sadece kaydet
        abs_path = os.path.abspath(output_filename)
        print(f"💾 Dosya kaydedildi: {abs_path}")

def normalize(text):
    """Metni normalize et"""
    return text.strip().lower().replace("'", "'").replace(""", "\"").replace(""", "\"")

def translate_with_llm(text, source_lang, target_lang, max_retries=3):
    """Çeviri fonksiyonu - Yedek modellerle"""
    
    # Model seç
    if source_lang == "tr" and target_lang == "en":
        model_url = MODELS["tr_to_en"]
        direction = "TR→EN"
        payload = {"inputs": text}
    elif source_lang == "en" and target_lang == "tr":
        model_url = MODELS["en_to_tr"]
        direction = "EN→TR"
        payload = {"inputs": text}
    else:
        return None
    
    model_name = model_url.split('/')[-1]
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 {direction} çevirisi: {text[:40]}..." + (f" (deneme {attempt+1})" if attempt > 0 else ""))
            print(f"📡 Model: {model_name}")
            
            response = requests.post(model_url, headers=headers, json=payload, timeout=35)
            
            if response.status_code == 200:
                result = response.json()
                print(f"📋 API Response: {result}")
                
                # Başarılı yanıt formatları
                if isinstance(result, list) and len(result) > 0:
                    if "translation_text" in result[0]:
                        translation = result[0]["translation_text"].strip()
                        if translation and len(translation) > 1:
                            print(f"✅ Başarılı: {translation[:50]}...")
                            return translation
                elif isinstance(result, dict) and "translation_text" in result:
                    translation = result["translation_text"].strip()
                    if translation and len(translation) > 1:
                        print(f"✅ Başarılı: {translation[:50]}...")
                        return translation
                
                print(f"⚠ Beklenmeyen yanıt: {result}")
                
            elif response.status_code == 503:
                print(f"⏳ Model loading... 30 saniye bekleniyor")
                time.sleep(30)
                continue
            elif response.status_code == 429:
                print(f"🚫 Rate limit, 25 saniye bekleniyor")
                time.sleep(25)
                continue
            elif response.status_code == 404:
                print(f"❌ Model 404: {model_name}")
                
                # EN→TR için yedek modelleri dene
                if source_lang == "en" and target_lang == "tr":
                    backup_models = [
                        BACKUP_MODELS["en_to_tr_1"],
                        BACKUP_MODELS["en_to_tr_2"], 
                        BACKUP_MODELS["en_to_tr_3"]
                    ]
                    
                    for backup_url in backup_models:
                        backup_name = backup_url.split('/')[-1]
                        print(f"🔄 Yedek model deneniyor: {backup_name}")
                        
                        # mBART için özel format
                        if "mbart" in backup_url:
                            backup_payload = {
                                "inputs": text,
                                "parameters": {"src_lang": "en_XX", "tgt_lang": "tr_TR"}
                            }
                        else:
                            backup_payload = payload
                        
                        try:
                            backup_response = requests.post(backup_url, headers=headers, json=backup_payload, timeout=40)
                            
                            if backup_response.status_code == 200:
                                backup_result = backup_response.json()
                                print(f"📋 Yedek API Response: {backup_result}")
                                
                                if isinstance(backup_result, list) and len(backup_result) > 0:
                                    if "translation_text" in backup_result[0]:
                                        translation = backup_result[0]["translation_text"].strip()
                                        if translation and len(translation) > 1:
                                            print(f"✅ Yedek model başarılı: {translation[:50]}...")
                                            return translation
                                
                            elif backup_response.status_code == 503:
                                print(f"⏳ Yedek model yükleniyor...")
                                time.sleep(15)
                                continue
                            else:
                                print(f"❌ Yedek model {backup_response.status_code}")
                                
                        except Exception as e:
                            print(f"⚠ Yedek model hatası: {str(e)[:50]}")
                            continue
                
                return None
            elif response.status_code == 401:
                print(f"❌ Token hatası! HF_TOKEN kontrol edin")
                return None
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"📄 Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ 35s timeout (deneme {attempt+1})")
        except Exception as e:
            print(f"⚠ Error: {str(e)[:100]}")
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 8
            print(f"⏳ {wait_time} saniye bekleniyor...")
            time.sleep(wait_time)
    
    print(f"❌ {direction} çeviri başarısız")
    return None

def test_models():
    """Modelleri test et"""
    print("🧪 MODEL TEST BAŞLIYOR...")
    print("=" * 50)
    
    # Test metinleri
    test_tr = "Merhaba, nasılsın?"
    test_en = "Hello, how are you?"
    
    print("⿡ TR→EN Test:")
    result1 = translate_with_llm(test_tr, "tr", "en")
    print(f"Sonuç: {result1}\n")
    
    print("⿢ EN→TR Test:")
    result2 = translate_with_llm(test_en, "en", "tr")
    print(f"Sonuç: {result2}\n")
    
    if result1 and result2:
        print("✅ Her iki model de çalışıyor!")
        return True
    else:
        print("❌ Model sorunu var")
        return False

def process_translations():
    """Ana çeviri işlemi"""
    
    # Önce modelleri test et
    if not test_models():
        print("⚠ Modeller çalışmıyor, işlem durduruluyor")
        return
    
    # Dosya al
    file_name = get_input_file()
    if not file_name:
        print("❌ Dosya seçilmedi, işlem sonlandırılıyor")
        return
    
    # Dosyayı oku
    try:
        with open(file_name, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return
    
    print(f"📂 Dosya: {file_name}")
    print(f"📊 Sayfa sayısı: {len(data)}")
    print("=" * 60)
    
    translated_count = 0
    failed_count = 0
    
    # Her sayfa için işlem
    for page_idx, item in enumerate(data):
        print(f"\n📄 Sayfa {page_idx + 1}/{len(data)}")
        
        en_entries = item.get("en", [])
        tr_entries = item.get("tr", [])
        
        # Normalize edilmiş haritalar
        en_map = {normalize(e["question"]): e for e in en_entries}
        tr_map = {normalize(e["question"]): e for e in tr_entries}
        
        # TR → EN çevirileri
        for norm_q, tr_entry in tr_map.items():
            if norm_q not in en_map:
                print(f"🔄 TR→EN: {tr_entry['question'][:30]}...")
                
                # Soru çevir
                translated_q = translate_with_llm(tr_entry["question"], "tr", "en")
                time.sleep(3)
                
                if not translated_q:
                    failed_count += 1
                    continue
                
                # Cevap çevir
                translated_a = translate_with_llm(tr_entry["answer"], "tr", "en")
                time.sleep(3)
                
                if translated_a:
                    en_entries.append({
                        "page_url": tr_entry.get("page_url", item.get("url", "")),
                        "page_title": tr_entry.get("page_title", ""),
                        "language": "en", 
                        "modified_date": "Translated by Helsinki-NLP",
                        "question": translated_q,
                        "answer": translated_a
                    })
                    translated_count += 1
                    print(f"✅ TR→EN eklendi")
                else:
                    failed_count += 1
        
        # EN → TR çevirileri
        for norm_q, en_entry in en_map.items():
            if norm_q not in tr_map:
                print(f"🔄 EN→TR: {en_entry['question'][:30]}...")
                
                # Soru çevir
                translated_q = translate_with_llm(en_entry["question"], "en", "tr")
                time.sleep(3)
                
                if not translated_q:
                    failed_count += 1
                    continue
                
                # Cevap çevir  
                translated_a = translate_with_llm(en_entry["answer"], "en", "tr")
                time.sleep(3)
                
                if translated_a:
                    tr_entries.append({
                        "page_url": en_entry.get("page_url", item.get("url", "")),
                        "page_title": en_entry.get("page_title", ""),
                        "language": "tr",
                        "modified_date": "Helsinki-NLP tarafından çevrildi", 
                        "question": translated_q,
                        "answer": translated_a
                    })
                    translated_count += 1
                    print(f"✅ EN→TR eklendi")
                else:
                    failed_count += 1
        
        # Güncelle
        item["en"] = en_entries
        item["tr"] = tr_entries
    
    # Sonuç dosyasını kaydet ve indir
    output_filename = "completed_translations.json"
    save_and_download(data, output_filename)
    
    print("\n" + "=" * 60)
    print(f"🎉 İŞLEM TAMAMLANDI!")
    print(f"✅ Başarılı: {translated_count}")
    print(f"❌ Başarısız: {failed_count}")
    if (translated_count + failed_count) > 0:
        success_rate = (translated_count / (translated_count + failed_count)) * 100
        print(f"📊 Başarı oranı: {success_rate:.1f}%")
    
    return translated_count, failed_count

# Çalıştır
if __name__ == "__main__":
    print("🚀 Helsinki-NLP Çeviri Sistemi (Evrensel)")
    print("📍 Ortam otomatik tespit ediliyor...")
    
    env = detect_environment()
    print(f"🖥️  Ortam: {'Google Colab' if env == 'colab' else 'Yerel Python'}")
    
    if not HF_TOKEN or HF_TOKEN == "YOUR_TOKEN_HERE":
        print("❌ HATA: HF_TOKEN ayarlanmamış!")
        print("🔧 Lütfen HF_TOKEN değişkenini ayarlayın:")
        print("   • Kodu düzenleyip YOUR_TOKEN_HERE yerine token'ınızı yazın")
        print("   • Veya çevre değişkeni: export HF_TOKEN=your_token")  
        print("🔗 Token almak için: https://huggingface.co/settings/tokens")
        return
    else:
        print("✅ Token bulundu, işlem başlıyor...")
        process_translations()
