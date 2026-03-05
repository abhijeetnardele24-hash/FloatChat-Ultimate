# 🚀 Free API Keys Setup Guide for FloatChat Ultimate

## **Quick Start - Get Your Free API Keys in 5 Minutes**

### **🔥 Option 1: Groq (Recommended - Fastest & Easiest)**
1. Go to https://console.groq.com/
2. Sign up for free account
3. Navigate to https://console.groq.com/keys
4. Create new API key
5. Add to your `.env` file:
   ```
   GROQ_API_KEY=your_groq_key_here
   GROQ_MODEL=llama-3.1-70b-versatile
   ```

**Benefits:**
- ✅ Free tier with generous limits
- ✅ Extremely fast inference (300+ tokens/sec)
- ✅ Llama 3.1 70B model
- ✅ Perfect for oceanographic analysis

---

### **🤖 Option 2: OpenAI**
1. Go to https://platform.openai.com/
2. Sign up and verify email
3. Navigate to https://platform.openai.com/api-keys
4. Create new secret key
5. Add to `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   OPENAI_MODEL=gpt-4o-mini
   ```

**Benefits:**
- ✅ $5 free credit for new users
- ✅ GPT-4o-mini model
- ✅ High quality responses

---

### **🧠 Option 3: Google Gemini**
1. Go to https://ai.google.dev/
2. Sign up with Google account
3. Get API key from https://aistudio.google.com/app/apikey
4. Add to `.env`:
   ```
   GOOGLE_API_KEY=your_gemini_key
   ```

**Benefits:**
- ✅ Free tier available
- ✅ Gemini Pro model
- ✅ Good for scientific queries

---

### **🏠 Option 4: Local Ollama (No API Key Needed)**
1. Install Ollama: https://ollama.ai/
2. Pull model: `ollama pull llama3.1:8b`
3. Add to `.env`:
   ```
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1:8b
   ```

**Benefits:**
- ✅ Completely free
- ✅ No API key required
- ✅ Runs locally
- ❌ Requires good hardware

---

## **🔧 Environment Setup**

Create or update your `backend/.env` file:

```bash
# Groq (Recommended - Fast & Free)
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# OpenAI (Backup option)
OPENAI_API_KEY=sk-your_key_here
OPENAI_MODEL=gpt-4o-mini

# Google Gemini (Another backup)
GOOGLE_API_KEY=your_gemini_key_here

# Provider Priority (Groq first)
CHAT_GENERAL_PROVIDER_ORDER=groq,gemini,openai,ollama
CHAT_DATA_PROVIDER_ORDER=groq,gemini,openai,ollama
```

---

## **🎯 Recommended Setup for Oceanographic Analysis**

### **Best Performance: Groq + Local Ollama**
```bash
# Primary: Groq for complex analysis
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-70b-versatile

# Backup: Local Ollama for privacy
OLLAMA_MODEL=llama3.1:8b

# Priority order
CHAT_GENERAL_PROVIDER_ORDER=groq,ollama,gemini,openai
```

### **Maximum Accuracy: Multiple Providers**
```bash
# All available providers
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key

# Smart routing based on query type
CHAT_GENERAL_PROVIDER_ORDER=groq,gemini,openai,ollama
CHAT_DATA_PROVIDER_ORDER=groq,gemini,openai,ollama
```

---

## **🚦 Testing Your Setup**

1. Start the backend: `python main_local.py`
2. Test API: `http://localhost:8000/docs`
3. Try queries like:
   - "What are ARGO floats?"
   - "Analyze temperature profiles at 2000m depth"
   - "Explain thermohaline circulation"

---

## **💡 Pro Tips**

- **Groq** is fastest for real-time analysis
- **OpenAI** has best reasoning for complex queries
- **Gemini** excels at scientific explanations
- **Ollama** provides complete privacy
- **Combine multiple** for best results

---

## **🎉 You're Ready!**

Once you have at least one API key, your FloatChat Ultimate will have:
- 🤖 Multiple AI models
- 🌊 Oceanographic expertise
- ⚡ Fast responses
- 🔬 Scientific accuracy
- 💰 Minimal cost

**Get started in 5 minutes with Groq - it's the easiest and fastest option!**
