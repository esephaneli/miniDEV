# 🏢 Mini ChatDev

> **Multi-Agent AI Yazılım Geliştirme Sistemi — Google Gemini ile Tamamen Ücretsiz!**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange?logo=google)](https://aistudio.google.com)
[![Cost](https://img.shields.io/badge/Maliyet-$0.00-brightgreen)](https://ai.google.dev/pricing)

---

## 🤔 Ne İşe Yarar?

Mini ChatDev, bir yazılım şirketini simüle eder. 5 AI agent Gemini API üzerinden birbirleriyle konuşarak yazılım üretir:

| Agent | Rol | Görev |
|-------|-----|-------|
| 👔 Ahmet (CEO) | Ürün Yöneticisi | Talebi analiz eder, ürün tanımı oluşturur |
| 🔧 Zeynep (CTO) | Teknik Lider | Mimari tasarımı yapar, teknoloji seçer |
| 💻 Can (Programmer) | Geliştirici | Çalışan Python kodu yazar |
| 🔍 Elif (Reviewer) | Kod İnceleme | Kodu review eder, bugları düzeltir |
| 🧪 Burak (Tester) | Test Mühendisi | Kalite raporu oluşturur |

## 🚀 Kurulum

### 1. Gereksinimler
```bash
pip install openai rich
# veya
uv pip install openai rich
```

### 2. API Key
[Google AI Studio](https://aistudio.google.com/apikey) → Ücretsiz API key al.

```bash
# PowerShell
$env:GEMINI_API_KEY = "AIzaSy..."

# Linux/Mac
export GEMINI_API_KEY="AIzaSy..."

# veya .env dosyası oluştur
echo 'GEMINI_API_KEY=AIzaSy...' > .env
```

### 3. Çalıştır!
```bash
python mini_chatdev.py --task "tkinter ile hesap makinesi yap"
```

## 📖 Kullanım Örnekleri

```bash
# Türkçe — Hesap Makinesi
python mini_chatdev.py --task "tkinter ile hesap makinesi yap" --name "Calculator"

# Türkçe — Oyun
python mini_chatdev.py --task "pygame ile yılan oyunu yap" --name "SnakeGame"

# Türkçe — CLI Aracı
python mini_chatdev.py --task "komut satırı todo list uygulaması yap" --name "TodoApp"

# English — Pomodoro Timer
python mini_chatdev.py --task "create a pomodoro timer with tkinter" --name "Pomodoro" --lang en

# Farklı model
python mini_chatdev.py --task "not defteri yap" --model gemini-2.0-flash
```

## ⚙️ Parametreler

| Parametre | Kısa | Varsayılan | Açıklama |
|-----------|-------|------------|----------|
| `--task` | `-t` | *(zorunlu)* | Yazılım görevi |
| `--name` | `-n` | MyProject | Proje adı |
| `--model` | `-m` | gemini-2.5-flash | Gemini model |
| `--lang` | `-l` | tr | Agent dili (tr/en) |
| `--output` | `-o` | output/ | Çıktı dizini |

## 📁 Çıktı Yapısı

Her çalıştırmada `output/` dizininde yeni bir proje klasörü oluşur:

```
output/
└── Calculator_20260225_143052/
    ├── calculator.py          ← Üretilen çalışan kod
    ├── conversation_log.json  ← Tüm agent diyalogları
    └── README.md              ← Otomatik üretilen dökümantasyon
```

## 💡 En İyi Sonuç İçin İpuçları

✅ **İyi promptlar:**
- "tkinter ile basit hesap makinesi yap, 4 işlem yapabilsin"
- "komut satırından çalışan not defteri, kaydetme ve yükleme olsun"
- "pygame ile pong oyunu yap, iki oyunculu"

❌ **Kaçınılması gereken promptlar:**
- "web sitesi yap" (Flask/Django çok karmaşık)
- "veritabanı ile tam bir e-ticaret sistemi" (tek dosyada olmaz)
- "makine öğrenmesi modeli eğit" (veri lazım)

## 🔧 Nasıl Çalışır?

```
Kullanıcı Talebi
      │
      ▼
👔 CEO → Ürün tanımı oluşturur
      │
      ▼
🔧 CTO → Teknik mimari tasarlar
      │
      ▼
💻 Programmer → Python kodu yazar
      │
      ▼
🔍 Reviewer → Kodu inceler, iyileştirir
      │
      ▼
🧪 Tester → Test raporu oluşturur
      │
      ▼
💾 Dosyaya Kaydet → output/{proje_adı}/
```

## 📊 Gemini Free Tier Limitleri

| Model | RPM | RPD | Yeterli mi? |
|-------|-----|-----|-------------|
| gemini-2.5-flash | 10 | 500 | ✅ (5 çağrı/proje) |
| gemini-2.0-flash | 15 | 1500 | ✅ Bol bol yeter |


## 📄 Lisans

MIT License — Dilediğiniz gibi kullanın!

---

<p align="center">
  <b>🏢 Mini ChatDev</b> ile ❤️ ile yapıldı<br>
  <sub>Powered by Google Gemini — Zero Cost AI Development</sub>
</p>
