# Gerekli kütüphaneleri içe aktar
import json
import requests
import time
import os

# Hugging Face erişim tokenını ortam değişkeninden al
HF_TOKEN = os.getenv("HF_TOKEN")

# API çağrılarında kullanılacak yetkilendirme başlıkları
headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# Ana modellerin API URL'leri (TR→EN ve EN→TR)
MODELS = {
    "tr_to_en": "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-tr-en",
    "en_to_tr": "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-tc-big-en-tr"
}

# Yedek modellerin API URL'leri (özellikle EN→TR için)
BACKUP_MODELS = {
    "en_to_tr_1": "https://api-inference.huggingface.co/models/facebook/mbart-large-50-many-to-many-mmt",
    "en_to_tr_2": "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-mul-tr",
    "en_to_tr_3": "https://api-inference.huggingface.co/models/google/mt5-base"
}

# Soru eşleştirmeleri için normalizasyon fonksiyonu
def normalize(text):
    return text.strip().lower().replace("'", "'").replace("“", "\"").replace("”", "\"")

# LLM ile çeviri yapan ana fonksiyon
def translate_with_llm(text, source_lang, target_lang, max_retries=3):
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
    
    # Maksimum deneme sayısı kadar modeli çalıştırmayı dene
    for attempt in range(max_retries):
        try:
            print(f"🔄 {direction} çevirisi: {text[:40]}..." + (f" (deneme {attempt+1})" if attempt > 0 else ""))
            response = requests.post(model_url, headers=headers, json=payload, timeout=35)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0 and "translation_text" in result[0]:
                    translation = result[0]["translation_text"].strip()
                    if translation and len(translation) > 1:
                        return translation
            elif response.status_code == 503:
                time.sleep(30)
                continue
            elif response.status_code == 429:
                time.sleep(25)
                continue
            elif response.status_code == 404:
                if source_lang == "en" and target_lang == "tr":
                    for backup_url in BACKUP_MODELS.values():
                        backup_payload = {
                            "inputs": text,
                            "parameters": {"src_lang": "en_XX", "tgt_lang": "tr_TR"}
                        } if "mbart" in backup_url else payload

                        backup_response = requests.post(backup_url, headers=headers, json=backup_payload, timeout=40)
                        if backup_response.status_code == 200:
                            backup_result = backup_response.json()
                            if isinstance(backup_result, list) and len(backup_result) > 0 and "translation_text" in backup_result[0]:
                                return backup_result[0]["translation_text"].strip()
                return None
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout (deneme {attempt+1})")
        except Exception as e:
            print(f"⚠️ Hata: {str(e)[:100]}")
        
        if attempt < max_retries - 1:
            time.sleep((attempt + 1) * 8)
    
    return None

# Ana çeviri işlemlerinin yapıldığı fonksiyon
def process_translations():
    try:
        from google.colab import files
        uploaded = files.upload()
        file_name = list(uploaded.keys())[0]
    except:
        file_name = input("📂 Lütfen işlenecek JSON dosyasının adını girin: ").strip()

    with open(file_name, encoding="utf-8") as f:
        data = json.load(f)

    translated_count = 0
    failed_count = 0

    # Her sayfa veya içerik için dön
    for item in data:
        # İngilizce ve Türkçe içerikleri al
        en_entries = item.get("en", [])
        tr_entries = item.get("tr", [])
        en_map = {normalize(e["question"]): e for e in en_entries}
        tr_map = {normalize(e["question"]): e for e in tr_entries}

        # Türkçe sorular arasında İngilizcesi eksik olanları bul
        for norm_q, tr_entry in tr_map.items():
            if norm_q not in en_map:
                translated_q = translate_with_llm(tr_entry["question"], "tr", "en")
                time.sleep(3)
                if not translated_q:
                    failed_count += 1
                    continue
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
                else:
                    failed_count += 1

        # İngilizce sorular arasında Türkçesi eksik olanları bul
        for norm_q, en_entry in en_map.items():
            if norm_q not in tr_map:
                translated_q = translate_with_llm(en_entry["question"], "en", "tr")
                time.sleep(3)
                if not translated_q:
                    failed_count += 1
                    continue
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
                else:
                    failed_count += 1

        # Güncellenmiş içerikleri tekrar yerleştir
        item["en"] = en_entries
        item["tr"] = tr_entries

    # Çevirisi tamamlanan verileri kaydet
    output_filename = "completed_translations.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Çeviri tamamlandı. Başarılı: {translated_count}, Başarısız: {failed_count}")
    print(f"💾 Kayıt dosyası: {output_filename}")

# Script doğrudan çalıştırıldığında buradan başlar
if __name__ == "__main__":
    if not HF_TOKEN:
        print("❌ HATA: HF_TOKEN ortam değişkeni eksik!")
        print("🔗 Token almak için: https://huggingface.co/settings/tokens")
    else:
        process_translations()

