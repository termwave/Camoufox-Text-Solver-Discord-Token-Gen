# ❄️ Glacier — Discord Account Creator

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge)
![Async Automation](https://img.shields.io/badge/Async-Automation-success.svg?style=for-the-badge)
![HCaptcha Solver](https://img.shields.io/badge/HCaptcha-Solver-purple.svg?style=for-the-badge)

---

## What is Glacier?

Glacier is an automated Discord account creation tool that helps you generate accounts efficiently. It mimics real user behavior, handles proxy rotation, and can solve captchas using AI assistance. The tool uses advanced browser automation to make the process feel natural and includes a clean, colorful terminal interface.

---

## What Can It Do?

**Runs Multiple Tasks at Once**  
Create several Discord accounts simultaneously without slowing down your system.

**Smart Captcha Solving**  
Uses Groq AI and LLaMA models to automatically handle hCaptcha challenges when they pop up.

**Acts Like a Real Person**  
Moves the mouse naturally, types at human speed, and adds random pauses to avoid detection.

**Proxy Support Built-In**  
Automatically reads and switches between proxies from your proxy list.

**Email Verification**  
Monitors your inbox through IMAP and grabs verification links automatically.

**Beautiful Console Output**  
Thread-safe logging with colors, timestamps, and gradient effects that make monitoring easy.

**Desktop Alerts**  
Get notifications on your desktop when accounts are created successfully or if something goes wrong.

---

## Project Files

Here's what you'll find in the folder:

```
Glacier/
├── main.py          → The main automation script
├── solver.py        → Captcha solving logic
├── config.json      → Your settings
├── proxies.txt      → Your proxy list
└── requirements.txt → Required Python packages
```

---

## Setting Things Up

First, create a `config.json` file with your settings:

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

## Installing Dependencies

Run this command to install everything you need:

```bash
pip install -r requirements.txt
```

The main packages include:
- `camoufox` — Browser automation
- `pystyle` — Terminal styling
- `colorama` — Colored text
- `beautifulsoup4` — HTML parsing
- `notifypy` — Desktop notifications
- `groq` — AI captcha solving
- `requests` — HTTP requests
- `asyncio` — Async operations

---

## Running Glacier

Just run:

```bash
python main.py
```

Once it starts, Glacier will:
1. Pick proxies from your list
2. Generate realistic usernames and birthdays
3. Fill out Discord's registration form
4. Solve any captchas that appear (using AI or manual help)
5. Verify the account through email
6. Show you colorful progress updates in real-time

---

## How Captcha Solving Works

The AI solver is powered by Groq's LLaMA model:
- It detects when Discord throws up a captcha
- Automatically switches to text-based challenges
- Reads the question and figures out the answer
- Types the response just like a human would

---

## Setting Up Proxies

Add your proxies to `proxies.txt`, one per line. Supported formats:

```
http://user:pass@host:port
socks5://user:pass@host:port
host:port
```

---

## What the Logs Look Like

You'll see colorful messages like:

```
[glacier] [18:12:35] [Success] → 🎉 Captcha solved successfully (2 challenges)
[glacier] [18:12:40] [Info] → Account verified and active ✅
[glacier] [18:12:45] [Warning] → Rate limit detected, retrying in 15s...
```

---

## Credits

**Created by:** Notiny X Termwave  
**Contributed by:** DevDream  
**Built with:** Python, async programming, and a lot of coffee ☕

---

## Important Notice

**This tool is for educational purposes only.** 

I'm sharing this to help people learn about automation, web scraping, and async programming. Please use it responsibly and ethically. I'm not responsible for how you use this tool, and I don't encourage breaking Discord's Terms of Service or creating spam accounts.

Be cool, be responsible, and happy coding! 💙

---

*Made with care by Notiny X Termwave*
