# ❄️ Glacier — Ultimate Discord Account Creator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Async-Automation-success.svg?style=for-the-badge" />
  <img src="https://img.shields.io/badge/HCaptcha-Solver-purple.svg?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Developer-NotinyXTermwave_-pink.svg?style=for-the-badge" />
</p>

---

## 🧊 Overview

**Glacier** is a next-generation Discord account generator designed for automation with **human-like behavior**, **proxy rotation**, and **AI-powered captcha solving**.  
It leverages advanced browser automation with **Camoufox**, integrates **Groq AI**, and provides a **thread-safe logging** system with vibrant terminal output.

---

## ⚙️ Key Features

- 🔥 **Async Multi-threaded Automation**  
  Handles multiple Discord registrations concurrently with optimal resource management.

- 🧠 **AI-Powered CAPTCHA Solver**  
  Uses the `Solver` module with **Groq API** to solve hCaptcha challenges via LLaMA models.

- 🧍‍♂️ **Human-Like Mouse & Typing Simulation**  
  Emulates natural user behavior (Bezier motion, random delays, and micro-movements).

- 🧩 **Proxy Management System**  
  Automatic parsing and rotation of proxies from `proxies.txt`.

- 📬 **Mail Verification Support**  
  IMAP-based inbox monitoring to extract Discord verification links automatically.

- 🌈 **Colorized & Thread-Safe Logging**  
  Custom logger with timestamped gradient output and neat formatting.

- 🔔 **Real-time Desktop Notifications**  
  Integrates with `notifypy` for visual success/error alerts.

---

## 🧩 Project Structure

```
📦 Glacier
├── main.py          # Core logic & automation flow
├── solver.py        # AI-based captcha solving engine
├── config.json      # User configuration file
├── proxies.txt      # Proxy list for rotation
└── requirements.txt # Dependencies
```

---

## 🔧 Configuration

Create a `config.json` in the project root:

```json
{
  "mail_imap": "imap.yourmailserver.com",
  "use_ai_solver": true,
  "notify": true,
  "groq_api_key": "your_groq_api_key_here",
  "model": "llama-3.1-70b-versatile",
  "max_tokens": 10,
  "temperature": 0.0
}
```

---

## 🧠 Requirements

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `camoufox`
- `pystyle`
- `colorama`
- `beautifulsoup4`
- `notifypy`
- `groq`
- `requests`
- `asyncio`

---

## 🚀 Usage

```bash
python main.py
```

Once started, **Glacier** will:
1. Rotate proxies from `proxies.txt`
2. Generate realistic usernames and DOBs  
3. Fill registration forms automatically  
4. Solve captchas using AI or manual fallback  
5. Verify accounts via IMAP  
6. Log results with stunning color output  

---

## 🧬 Captcha Solving Workflow

The AI Solver uses a **Groq-powered LLaMA model**:
- Detects hCaptcha challenges via DOM inspection
- Switches to accessibility challenges automatically
- Parses text-based prompts
- Submits answers through human-like typing simulation

---

## 📡 Proxy Format

Supports the following:
```
http://user:pass@host:port
socks5://user:pass@host:port
host:port
```

Each line in `proxies.txt` represents a proxy entry.

---

## 📜 Logging Example

```
[glacier] [18:12:35] [Success] -> 🎉 Captcha solved successfully (2 challenges)
[glacier] [18:12:40] [Info] -> Account verified and active ✅
[glacier] [18:12:45] [Warning] -> Rate limit detected, retrying in 15s...
```

---

## 🧑‍💻 Developer

**Author:** `Notiny X Termwave`  
**Project:** Ultimate Discord Automation Suite  
**License:** MIT  
**Created With:** 💙 Python + Async Magic

---

## ⚠️ Disclaimer

This project is intended for **educational and research purposes only**.  
The author does **not endorse** or **take responsibility** for misuse, spam, or violations of Discord’s Terms of Service.

---

<p align="center">💻 Crafted with precision and style — Notiny X Termwave</p>
