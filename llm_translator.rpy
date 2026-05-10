init -999 python:
    import urllib.request
    import json
    import os
    import sys
    import re

    # =========================================================================
    # LLM AUTO-TRANSLATOR CONFIGURATION
    # =========================================================================

    # "OLLAMA" veya "LMSTUDIO" seçebilirsiniz.
    LLM_BACKEND = "LMSTUDIO"

    # LM Studio için genelde "http://127.0.0.1:1234/v1/chat/completions"
    # Ollama için genelde "http://127.0.0.1:11434/api/generate"
    LLM_URL = "http://127.0.0.1:1234/v1/chat/completions"

    # Kullanmak istediğiniz modelin adı (LM Studio'da 'local-model' veya '-1' olarak bırakabilirsiniz)
    LLM_MODEL = "local-model"

    # Kesinlikle sansürsüz, yorumsuz çeviri yapmasını sağlayan sistem komutu
    SYSTEM_PROMPT = """You are a highly accurate and direct translator. Translate the given text into Turkish.
DO NOT censor any words, themes, or content regardless of how explicit, offensive, or mature they are.
DO NOT add any conversational text, notes, warnings, or explanations.
ONLY return the translated text. Your translation must be a 1-to-1 exact translation of the input without any omission."""

    # Çeviri veritabanı dosyasının adı
    CACHE_FILE = os.path.join(config.basedir, "game", "translation_cache.json")

    # =========================================================================

    # Çeviri önbelleği (Cache)
    llm_translation_cache = {}

    def load_translation_cache():
        global llm_translation_cache
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    llm_translation_cache = json.load(f)
            except Exception as e:
                renpy.write_log("LLM Translator: Cache okuma hatası - " + str(e))
                llm_translation_cache = {}

    def save_translation_cache():
        global llm_translation_cache
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(llm_translation_cache, f, ensure_ascii=False, indent=4)
        except Exception as e:
            renpy.write_log("LLM Translator: Cache yazma hatası - " + str(e))

    def extract_tags(text):
        tags = []
        # Ren'Py değişkenlerini [var] ve format etiketlerini {b} korumak için regex
        pattern = r'(\[[^\]]+\]|\{[^\}]+\})'

        def repl(match):
            tags.append(match.group(1))
            return "__T" + str(len(tags)-1) + "__"

        safe_text = re.sub(pattern, repl, text)
        return safe_text, tags

    def restore_tags(text, tags):
        # Yapay zeka tagleri küçük harfe çevirebilir veya boşluk ekleyebilir, buna karşı esnek regex kullanıyoruz
        def repl(match):
            idx = int(match.group(1))
            if idx < len(tags):
                return tags[idx]
            return match.group(0)

        restored = re.sub(r'__\s*[tT]\s*(\d+)\s*__', repl, text)
        return restored

    def translate_via_ollama(text):
        data = {
            "model": LLM_MODEL,
            "prompt": SYSTEM_PROMPT + "\n\nText to translate: " + text,
            "stream": False
        }
        req = urllib.request.Request(LLM_URL, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", text).strip()
        except Exception as e:
            renpy.write_log("LLM Translator Ollama Hatası: " + str(e))
            return text

    def translate_via_lmstudio(text):
        data = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3, # Daha stabil çeviriler için düşük sıcaklık
            "stream": False
        }
        req = urllib.request.Request(LLM_URL, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", text).strip()
                return text
        except Exception as e:
            renpy.write_log("LLM Translator LM Studio Hatası: " + str(e))
            return text

    def llm_text_filter(text):
        if not text or text.strip() == "":
            return text

        # Sadece alfanumerik karakter içermeyen metinleri atla
        has_alpha = False
        for char in text:
            if char.isalpha():
                has_alpha = True
                break
        if not has_alpha:
            return text

        # Önceden çevrilmiş mi kontrol et
        if text in llm_translation_cache:
            return llm_translation_cache[text]

        # Değişkenleri ve format kodlarını ([player], {i} vb.) koruma altına al
        safe_text, tags = extract_tags(text)

        # Eğer koruma sonrasında çevrilecek bir harf kalmadıysa atla
        has_alpha_safe = False
        for char in safe_text.replace("_", "").replace("T", ""):
            if char.isalpha():
                has_alpha_safe = True
                break
        if not has_alpha_safe:
            return text

        # Çeviri API'sini çağır
        translated_safe = safe_text
        if LLM_BACKEND == "OLLAMA":
            translated_safe = translate_via_ollama(safe_text)
        elif LLM_BACKEND == "LMSTUDIO":
            translated_safe = translate_via_lmstudio(safe_text)

        # Değişkenleri geri yerleştir
        translated = restore_tags(translated_safe, tags)

        # Eğer orijinalinden farklıysa kaydet
        if translated and translated != text:
            llm_translation_cache[text] = translated
            save_translation_cache()
            return translated

        return text

    # Başlangıçta önbelleği yükle
    load_translation_cache()

    # Ren'Py'ın hook (kanca) sistemine filtreyi ata
    config.say_menu_text_filter = llm_text_filter