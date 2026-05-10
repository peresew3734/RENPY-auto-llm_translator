# Ren'Py LLM Auto-Translator 

This tool allows you to seamlessly translate any Ren'Py visual novel in real-time using local, uncensored AI models. Everything runs offline on your PC, ensuring total privacy and exact, unfiltered translations.

---

## 🖥️ Hardware & Recommended Models

To get the best uncensored and accurate translations without breaking the immersion, we highly recommend the following models based on your Graphics Card (VRAM). 

> 💡 **Important Optimization Note:**
> Set your AI's **Context Length to `4096`**. Game dialogues are short, so 4096 is more than enough. Setting it higher will unnecessarily consume your RAM/VRAM and slow down the game!

*   **For High-End GPUs (8GB+ VRAM):**
    *   **Model Name:** `gemma-4-e4b-uncensored-hauhaucs-aggressive`
    *   **Why:** Provides maximum accuracy, zero censorship, and excellent context understanding for complex sentences.
*   **For Low/Mid-End GPUs (Under 8GB VRAM):**
    *   **Model Name:** `gemma-4-e2b-it-ultra-uncensored-heretic`
    *   **Why:** Extremely fast, lightweight, and aggressively uncensored to bypass standard AI safety filters while still running smoothly on older hardware.

---

## ⚙️ Step 1: Setup Your Local AI Server

You need an AI backend to process the text. You can use either **LM Studio** (Visual UI, highly recommended) or **Ollama** (Terminal-based, very lightweight). Choose ONE of the methods below:

### Option A: Using LM Studio (Highly Recommended)
LM Studio is the easiest way to search, download, and run AI models directly from HuggingFace.

1. **Download:** Go to [https://lmstudio.ai](https://lmstudio.ai) and download the version for Windows.
2. **Install & Open:** Run the installer and launch the application.
3. **Download the Model:**
   * Use the search bar at the very top of LM Studio.
   * Paste the name of your recommended model:
     * *If > 8GB VRAM:* Search `gemma-4-e4b-uncensored-hauhaucs-aggressive`
     * *If < 8GB VRAM:* Search `gemma-4-e2b-it-ultra-uncensored-heretic`
   * Look for the **GGUF** format in the search results and click **Download**. *(Tip: Choose a `Q4_K_M` or `Q5_K_M` quantization file for the best balance of speed and quality).*
4. **Start the Local Server:**
   * Go to the **Local Server** tab (the `<->` icon on the left sidebar).
   * Select the model you just downloaded from the drop-down menu at the top.
   * In the Right Panel settings, set the **Context Length (n_ctx)** to `4096`.
   * Click the **Start Server** button. (It will run on port `1234`).

### Option B: Using Ollama
Ollama is highly optimized and runs completely in the background without a heavy UI.

1. **Download:** Go to [https://ollama.com/download](https://ollama.com/download) and install it for Windows.
2. **Download the GGUF File:**
   * Go to [HuggingFace](https://huggingface.co/models) in your browser.
   * Search for your specific model (`gemma-4-e4b-uncensored-hauhaucs-aggressive` or `gemma-4-e2b-it-ultra-uncensored-heretic`) and download its `.gguf` file to your PC.
3. **Import to Ollama:**
   * Create a blank text file named `Modelfile` in the exact same folder as your `.gguf` file.
   * Open the text file and add this single line: `FROM ./your-downloaded-model-file.gguf` *(replace with the actual file name)*.
   * Open Command Prompt (`cmd`) in that folder and run: 
     `ollama create my-translator -f Modelfile`
4. **Start Ollama:** 
   * Run the command: `ollama run my-translator`
   * Keep it running. It automatically serves the API on port `11434`.

---

## 🚀 Step 2: Inject the Translator into Your Game

Now that your AI server is running and waiting for text, let's connect your game to it!

1. Open the **`injector.exe`** application provided.
2. *(Optional)* Select your preferred **UI Language** from the top left.
3. **Language Settings:** 
   * Select the original language of the game (Source).
   * Select the language you want it translated to (Target).
4. **LLM Backend Settings:** 
   * Select the radio button for the software you are running (**LM Studio** or **Ollama**).
   * The API URL will automatically fill in.
   * **Model Name:** 
     * If using LM Studio, you can usually leave this as `local-model` or `-1`.
     * If using Ollama, type the name you created (e.g., `my-translator`).
5. Click **"Select Game .exe"** and browse to the executable file of the Ren'Py game you want to play.
6. Click the big green **"INJECT TRANSLATOR"** button. You will see a success message!

🎉 **You are completely done!** 
Simply launch your game normally. Whenever a character speaks or a choice appears, the game will silently ping your local AI and swap the text in real-time! 

> **Pro-Tip:** The translator automatically saves every translated line to a `translation_cache.json` file in the game's folder. This means if you replay a scene or see a repeated sentence, the translation will appear instantly with zero delay!
