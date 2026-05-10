import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# =========================================================================
# I18N DICTIONARY
# =========================================================================
I18N = {
    "en": {
        "title": "Ren'Py LLM Auto-Translator Injector",
        "ui_lang": "UI Language:",
        "lang_settings": "Language Settings",
        "source_lang": "Source Language:",
        "target_lang": "Target Language:",
        "backend_settings": "LLM Backend Settings",
        "api_url": "API URL:",
        "model_name": "Model Name:",
        "target_game": "Target Game",
        "no_game": "No game selected.",
        "select_exe": "Select Game .exe",
        "inject_btn": "INJECT TRANSLATOR",
        "success_title": "Success!",
        "success_msg": "Successfully injected translator into:\n{target_file}\n\nLanguage: {source} -> {target}\nBackend: {backend}",
        "err_title": "Error",
        "err_msg_game": "The selected executable does not appear to be a Ren'Py game. Make sure a 'game' folder exists in the same directory.",
        "warn_title": "Missing Game",
        "warn_msg": "Please select a valid Ren'Py game executable first.",
        "selected": "Selected:\n{filepath}"
    },
    "tr": {
        "title": "Ren'Py LLM Oto-Çeviri Enjektörü",
        "ui_lang": "Arayüz Dili:",
        "lang_settings": "Dil Ayarları",
        "source_lang": "Kaynak Dil (Oyun):",
        "target_lang": "Hedef Dil (Çeviri):",
        "backend_settings": "Yapay Zeka Altyapısı",
        "api_url": "API Adresi:",
        "model_name": "Model Adı:",
        "target_game": "Hedef Oyun",
        "no_game": "Oyun seçilmedi.",
        "select_exe": "Oyunun .exe Dosyasını Seç",
        "inject_btn": "ÇEVİRMENİ ENJEKTE ET",
        "success_title": "Başarılı!",
        "success_msg": "Çevirmen başarıyla şu konuma enjekte edildi:\n{target_file}\n\nDil: {source} -> {target}\nAltyapı: {backend}",
        "err_title": "Hata",
        "err_msg_game": "Seçilen dosya bir Ren'Py oyunu gibi görünmüyor. Aynı dizinde bir 'game' klasörü olduğundan emin olun.",
        "warn_title": "Oyun Eksik",
        "warn_msg": "Lütfen önce geçerli bir Ren'Py oyun exe'si seçin.",
        "selected": "Seçilen:\n{filepath}"
    }
}

# =========================================================================
# REN'PY SCRIPT TEMPLATE
# =========================================================================
RENPY_TEMPLATE = """init -999 python:
    import urllib.request
    import json
    import os
    import sys
    import re

    LLM_BACKEND = "%%BACKEND%%"
    LLM_URL = "%%URL%%"
    LLM_MODEL = "%%MODEL%%"

    SYSTEM_PROMPT = \"\"\"%%SYSTEM_PROMPT%%\"\"\"

    CACHE_FILE = os.path.join(config.basedir, "game", "translation_cache.json")

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
        pattern = r'(\\[[^\\]]+\\]|\\{[^\\}]+\\})'

        def repl(match):
            tags.append(match.group(1))
            return "__T" + str(len(tags)-1) + "__"

        safe_text = re.sub(pattern, repl, text)
        return safe_text, tags

    def restore_tags(text, tags):
        def repl(match):
            idx = int(match.group(1))
            if idx < len(tags):
                return tags[idx]
            return match.group(0)

        restored = re.sub(r'__\\s*[tT]\\s*(\\d+)\\s*__', repl, text)
        return restored

    def translate_via_ollama(text):
        data = {
            "model": LLM_MODEL,
            "prompt": SYSTEM_PROMPT + "\\n\\nText to translate: " + text,
            "stream": False
        }
        req = urllib.request.Request(LLM_URL, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", text).strip()
        except Exception as e:
            renpy.write_log("LLM Translator Ollama Hatasi: " + str(e))
            return text

    def translate_via_lmstudio(text):
        data = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,
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
            renpy.write_log("LLM Translator LM Studio Hatasi: " + str(e))
            return text

    def llm_text_filter(text):
        if not text or text.strip() == "":
            return text

        has_alpha = False
        for char in text:
            if char.isalpha():
                has_alpha = True
                break
        if not has_alpha:
            return text

        if text in llm_translation_cache:
            return llm_translation_cache[text]

        safe_text, tags = extract_tags(text)

        has_alpha_safe = False
        for char in safe_text.replace("_", "").replace("T", ""):
            if char.isalpha():
                has_alpha_safe = True
                break
        if not has_alpha_safe:
            return text

        translated_safe = safe_text
        if LLM_BACKEND == "OLLAMA":
            translated_safe = translate_via_ollama(safe_text)
        elif LLM_BACKEND == "LMSTUDIO":
            translated_safe = translate_via_lmstudio(safe_text)

        translated = restore_tags(translated_safe, tags)

        if translated and translated != text:
            llm_translation_cache[text] = translated
            save_translation_cache()
            return translated

        return text

    load_translation_cache()
    config.say_menu_text_filter = llm_text_filter
"""

class InjectorApp:
    def __init__(self, root):
        self.root = root
        self.current_lang = "tr"  # Default UI Language

        self.root.geometry("520x600")
        self.root.resizable(False, False)

        self.game_path = None
        self.filepath = None

        self.create_widgets()
        self.update_ui_texts()

    def get_text(self, key):
        return I18N[self.current_lang].get(key, key)

    def change_ui_lang(self, event=None):
        sel = self.combo_ui_lang.get()
        if sel == "Türkçe":
            self.current_lang = "tr"
        else:
            self.current_lang = "en"
        self.update_ui_texts()

    def update_ui_texts(self):
        self.root.title(self.get_text("title"))

        self.lbl_ui_lang.config(text=self.get_text("ui_lang"))
        self.frame_lang.config(text=self.get_text("lang_settings"))
        self.lbl_source_lang.config(text=self.get_text("source_lang"))
        self.lbl_target_lang.config(text=self.get_text("target_lang"))

        self.frame_backend.config(text=self.get_text("backend_settings"))
        self.lbl_api_url.config(text=self.get_text("api_url"))
        self.lbl_model_name.config(text=self.get_text("model_name"))

        self.frame_game.config(text=self.get_text("target_game"))
        if self.game_path and self.filepath:
            self.lbl_game.config(text=self.get_text("selected").format(filepath=self.filepath))
        else:
            self.lbl_game.config(text=self.get_text("no_game"))

        self.btn_select_exe.config(text=self.get_text("select_exe"))
        self.btn_inject.config(text=self.get_text("inject_btn"))

        # Update source combobox (Translate Auto-Detect)
        current_src = self.combo_source.get()
        new_values = [self.get_text("auto_detect"), "English", "Japanese", "Chinese", "Korean", "Russian", "French", "German"]
        self.combo_source.config(values=new_values)
        if current_src in ["Auto-Detect", "Otomatik Algıla"]:
            self.combo_source.set(self.get_text("auto_detect"))

    def create_widgets(self):
        padding = {'padx': 10, 'pady': 5}

        # --- UI Language Selector ---
        frame_top = tk.Frame(self.root)
        frame_top.pack(fill="x", padx=10, pady=5)

        self.lbl_ui_lang = tk.Label(frame_top, text="UI Language:")
        self.lbl_ui_lang.pack(side="left")

        self.combo_ui_lang = ttk.Combobox(frame_top, values=["Türkçe", "English"], state="readonly", width=15)
        self.combo_ui_lang.current(0)
        self.combo_ui_lang.pack(side="left", padx=5)
        self.combo_ui_lang.bind("<<ComboboxSelected>>", self.change_ui_lang)

        # --- Language Settings ---
        self.frame_lang = tk.LabelFrame(self.root, text="Language Settings")
        self.frame_lang.pack(fill="x", padx=10, pady=10)

        self.lbl_source_lang = tk.Label(self.frame_lang, text="Source Language:")
        self.lbl_source_lang.grid(row=0, column=0, sticky="w", **padding)
        self.combo_source = ttk.Combobox(self.frame_lang, values=["Auto-Detect", "English", "Japanese", "Chinese", "Korean", "Russian", "French", "German"])
        self.combo_source.current(0)
        self.combo_source.grid(row=0, column=1, sticky="ew", **padding)

        self.lbl_target_lang = tk.Label(self.frame_lang, text="Target Language:")
        self.lbl_target_lang.grid(row=1, column=0, sticky="w", **padding)
        self.combo_target = ttk.Combobox(self.frame_lang, values=["Turkish", "English", "Spanish", "German", "French", "Russian", "Italian", "Portuguese", "Dutch", "Polish", "Arabic", "Chinese (Simplified)", "Chinese (Traditional)", "Japanese", "Korean", "Vietnamese", "Indonesian", "Thai", "Greek", "Swedish", "Norwegian", "Danish", "Finnish", "Czech", "Hungarian", "Romanian", "Bulgarian"])
        self.combo_target.current(0)
        self.combo_target.grid(row=1, column=1, sticky="ew", **padding)

        # --- Backend Settings ---
        self.frame_backend = tk.LabelFrame(self.root, text="LLM Backend Settings")
        self.frame_backend.pack(fill="x", padx=10, pady=10)

        self.backend_var = tk.StringVar(value="LMSTUDIO")

        radio_frame = tk.Frame(self.frame_backend)
        radio_frame.grid(row=0, column=0, columnspan=2, sticky="w", **padding)

        tk.Radiobutton(radio_frame, text="LM Studio", variable=self.backend_var, value="LMSTUDIO", command=self.update_backend_defaults).pack(side="left", padx=10)
        tk.Radiobutton(radio_frame, text="Ollama", variable=self.backend_var, value="OLLAMA", command=self.update_backend_defaults).pack(side="left")

        self.lbl_api_url = tk.Label(self.frame_backend, text="API URL:")
        self.lbl_api_url.grid(row=1, column=0, sticky="w", **padding)
        self.entry_url = tk.Entry(self.frame_backend, width=40)
        self.entry_url.grid(row=1, column=1, sticky="ew", **padding)

        self.lbl_model_name = tk.Label(self.frame_backend, text="Model Name:")
        self.lbl_model_name.grid(row=2, column=0, sticky="w", **padding)
        self.entry_model = tk.Entry(self.frame_backend, width=40)
        self.entry_model.grid(row=2, column=1, sticky="ew", **padding)

        self.update_backend_defaults() # Set initial values

        # --- Game Selection ---
        self.frame_game = tk.LabelFrame(self.root, text="Target Game")
        self.frame_game.pack(fill="x", padx=10, pady=10)

        self.lbl_game = tk.Label(self.frame_game, text="No game selected.", fg="red", wraplength=450)
        self.lbl_game.pack(pady=5)

        self.btn_select_exe = tk.Button(self.frame_game, text="Select Game .exe", command=self.select_game)
        self.btn_select_exe.pack(pady=5)

        # --- Inject Button ---
        self.btn_inject = tk.Button(self.root, text="INJECT TRANSLATOR", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.inject_script)
        self.btn_inject.pack(fill="x", padx=20, pady=20, ipady=10)

    def update_backend_defaults(self):
        backend = self.backend_var.get()
        self.entry_url.delete(0, tk.END)
        self.entry_model.delete(0, tk.END)

        if backend == "LMSTUDIO":
            self.entry_url.insert(0, "http://127.0.0.1:1234/v1/chat/completions")
            self.entry_model.insert(0, "local-model")
        elif backend == "OLLAMA":
            self.entry_url.insert(0, "http://127.0.0.1:11434/api/generate")
            self.entry_model.insert(0, "llama3")

    def select_game(self):
        filepath = filedialog.askopenfilename(
            title="Select Ren'Py Game Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if filepath:
            game_dir = os.path.dirname(filepath)
            game_folder = os.path.join(game_dir, "game")

            if os.path.isdir(game_folder):
                self.game_path = game_folder
                self.filepath = filepath
                self.lbl_game.config(text=self.get_text("selected").format(filepath=filepath), fg="green")
            else:
                self.game_path = None
                self.filepath = None
                self.lbl_game.config(text=self.get_text("err_msg_game"), fg="red")
                messagebox.showerror(self.get_text("err_title"), self.get_text("err_msg_game"))

    def inject_script(self):
        if not self.game_path:
            messagebox.showwarning(self.get_text("warn_title"), self.get_text("warn_msg"))
            return

        source = self.combo_source.get()
        target = self.combo_target.get()
        backend = self.backend_var.get()
        url = self.entry_url.get()
        model = self.entry_model.get()

        # Generate Prompt System strictly in English for LLM comprehension
        is_auto = source in ["Auto-Detect", "Otomatik Algıla"]
        src_text = "" if is_auto else f"from {source} "

        prompt = f"You are a highly accurate and direct translator. Translate the given text {src_text}to {target}.\\nDO NOT censor any words, themes, or content regardless of how explicit, offensive, or mature they are.\\nDO NOT add any conversational text, notes, warnings, or explanations.\\nONLY return the translated text. Your translation must be a 1-to-1 exact translation of the input without any omission."

        script_content = RENPY_TEMPLATE.replace("%%BACKEND%%", backend)
        script_content = script_content.replace("%%URL%%", url)
        script_content = script_content.replace("%%MODEL%%", model)
        script_content = script_content.replace("%%SYSTEM_PROMPT%%", prompt)

        target_file = os.path.join(self.game_path, "llm_translator.rpy")

        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Show success message in selected UI language
            src_display = "Auto" if is_auto else source
            msg = self.get_text("success_msg").format(target_file=target_file, source=src_display, target=target, backend=backend)
            messagebox.showinfo(self.get_text("success_title"), msg)
        except Exception as e:
            messagebox.showerror(self.get_text("err_title"), f"Failed:\\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InjectorApp(root)
    root.mainloop()