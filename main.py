import asyncio, threading, time, random, json, os, re, sys, string, warnings, imaplib, email, requests; from datetime import datetime; from typing import Optional, List, Dict; from enum import Enum; from concurrent.futures import ThreadPoolExecutor, as_completed; from pystyle import System, Center; from colorama import Fore, Style; from camoufox.async_api import AsyncCamoufox; from bs4 import BeautifulSoup; from solver import Solver

warnings.filterwarnings("ignore", message=".*geoip=True.*", category=Warning)

RESET = "\033[0m"
ANSI_PATTERN = re.compile(r'\033\[[0-9;]*m')

def write_print(text, interval=0.01, hide_cursor=True, end=RESET):
    if hide_cursor:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
    i = 0
    while i < len(text):
        if text[i] == '\033':
            match = ANSI_PATTERN.match(text, i)
            if match:
                sys.stdout.write(match.group())
                sys.stdout.flush()
                i = match.end()
                continue
        sys.stdout.write(text[i])
        sys.stdout.flush()
        time.sleep(interval)
        i += 1
    sys.stdout.write(end)
    sys.stdout.flush()
    if hide_cursor:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    SUCCESS = 4
    ERROR = 5
    CRITICAL = 6

async def check_acc_disability(page, thread_id: int, email: str):
    try:
        await asyncio.sleep(3)
        current_url = page.url.lower()
        if ('discord.com/login' in current_url or '/login' in current_url) and not ('discord.com/channels/@me' in current_url or 'discord.com/app' in current_url or '/app' in current_url):
            log.warning(f"❌ Account disabled {email}")
            return True, "account_disabled"
        elif ('discord.com/channels/@me' in current_url or 
              'discord.com/app' in current_url or 
              '/app' in current_url or 
              'discord.com/channels' in current_url):
            return False, "account_active"
        page_content = await page.evaluate("""
            () => {
                const bodyText = document.body.textContent?.toLowerCase() || '';
                const disabilityIndicators = [
                    'account disabled', 'account suspended', 'account banned',
                    'your account has been', 'this account is', 'account terminated',
                    'violations of', 'terms of service'
                ];
                const hasDisabilityText = disabilityIndicators.some(indicator => 
                    bodyText.includes(indicator)
                );
                return {
                    hasDisabilityText: hasDisabilityText,
                    bodyText: bodyText.substring(0, 200) 
                };
            }
        """)
        if page_content.get('hasDisabilityText', False):
            log.warning(f"❌ Account disabled {email}")
            return True, "account_disabled"
        return False, "status_unknown"
    except Exception as e:
        log.warning(f"❌ Could not check account status {e}")
        return False, "check_failed"

class Logger:
    def __init__(self, level: LogLevel = LogLevel.DEBUG):
        self.level = level
        self.prefix = "\033[38;5;176m[\033[38;5;97mglacier\033[38;5;176m] "
        self.WHITE = "\u001b[37m"
        self.MAGENTA = "\033[38;5;97m"
        self.BRIGHT_MAGENTA = "\033[38;2;157;38;255m"
        self.LIGHT_CORAL = "\033[38;5;210m"
        self.RED = "\033[38;5;196m"
        self.GREEN = "\033[38;5;40m"
        self.YELLOW = "\033[38;5;220m"
        self.BLUE = "\033[38;5;21m"
        self.PINK = "\033[38;5;176m"
        self.CYAN = "\033[96m"
        self.write_lock = threading.Lock()
    def get_time(self):
        return datetime.now().strftime("%H:%M:%S")
    def _should_log(self, message_level: LogLevel) -> bool:
        return message_level.value >= self.level.value
    def _write(self, level_color, level_tag, message):
        with self.write_lock:
            output = f"{self.prefix}[{self.BRIGHT_MAGENTA}{self.get_time()}{self.PINK}] {self.PINK}[{level_color}{level_tag}{self.PINK}] -> {level_color}{message}{Style.RESET_ALL}"
            print(output)
            sys.stdout.flush()
    def info(self, message: str):
        if self._should_log(LogLevel.INFO):
            self._write(self.CYAN, "!", message)
    def success(self, message: str):
        if self._should_log(LogLevel.SUCCESS):
            self._write(self.GREEN, "Success", message)
    def warning(self, message: str):
        if self._should_log(LogLevel.WARNING):
            self._write(self.YELLOW, "Warning", message)
    def error(self, message: str):
        if self._should_log(LogLevel.ERROR):
            self._write(self.RED, "Error", message)
    def debug(self, message: str):
        if self._should_log(LogLevel.DEBUG):
            self._write(self.BLUE, "DEBUG", message)
    def failure(self, message: str):
        if self._should_log(LogLevel.ERROR):
            self._write(self.RED, "Failure", message)

log = Logger()

def print_gradient(text, start_color=(137, 207, 240), end_color=(25, 25, 112)):
    lines = text.split('\n')
    total_lines = len(lines)
    try:
        with log.write_lock:
            for i, line in enumerate(lines):
                if not line.strip():
                    print(line)
                    continue
                r = int(start_color[0] + (end_color[0] - start_color[0]) * i / total_lines)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * i / total_lines)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * i / total_lines)
                color_code = f"\033[38;2;{r};{g};{b}m"
                print(f"{color_code}{line}{Style.RESET_ALL}")
            sys.stdout.flush()
    except:
        for i, line in enumerate(lines):
            if not line.strip():
                print(line)
                continue
            r = int(start_color[0] + (end_color[0] - start_color[0]) * i / total_lines)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * i / total_lines)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * i / total_lines)
            color_code = f"\033[38;2;{r};{g};{b}m"
            print(f"{color_code}{line}{Style.RESET_ALL}")

def thread_print(message: str, color: str = ""):
    try:
        with log.write_lock:
            if color:
                print(f"{color}{message}{Style.RESET_ALL}")
            else:
                print(message)
            sys.stdout.flush()
    except:
        if color:
            print(f"{color}{message}{Style.RESET_ALL}")
        else:
            print(message)

async def extract_token(page):
    attempt = 0
    start_time = datetime.now()
    last_captcha_check = datetime.now()
    last_rate_limit_check = datetime.now()
    while True:
        attempt += 1
        elapsed_time = datetime.now() - start_time
        elapsed_seconds = int(elapsed_time.total_seconds())
        current_time = datetime.now()
        if (current_time - last_rate_limit_check).total_seconds() >= 15:
            last_rate_limit_check = current_time
            rate_limit_status = await detect_rate_limit(page)
            if rate_limit_status.get('detected', False):
                log.warning("Rate limit detected during token extraction!")
                await wait_for_rate_limit_to_clear(page)
                continue
        if (current_time - last_captcha_check).total_seconds() >= 10:
            last_captcha_check = current_time
            captcha_handled = await monitor_for_captcha(page, "token extraction")
            if not captcha_handled:
                log.error("Captcha handling failed during token extraction")
                continue
        try:
            token = await page.evaluate("""
                () => {
                    try {
                        let token = localStorage.getItem('token');
                        if (token && token !== 'undefined' && token.length > 20) {
                            return token.replace(/"/g, '');
                        }
                        const tokenKey = Object.keys(localStorage).find(key =>
                            key.includes('token') && localStorage.getItem(key) &&
                            localStorage.getItem(key).length > 20
                        );
                        if (tokenKey) {
                            const foundToken = localStorage.getItem(tokenKey);
                            if (foundToken && foundToken !== 'undefined' && foundToken.length > 20) {
                                return foundToken.replace(/"/g, '');
                            }
                        }
                        token = sessionStorage.getItem('token');
                        if (token && token !== 'undefined' && token.length > 20) {
                            return token.replace(/"/g, '');
                        }
                        if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.token) {
                            return window.__INITIAL_STATE__.token;
                        }
                        return null;
                    } catch (error) {
                        return null;
                    }
                }
            """)
            if token and len(token) > 20:
                return token
            current_url = await page.evaluate("window.location.href")
            if 'discord.com/channels' in current_url or 'discord.com/app' in current_url:
                await asyncio.sleep(2)
                token = await page.evaluate("""
                    () => {
                        const token = localStorage.getItem('token');
                        return token && token !== 'undefined' && token.length > 20 ? token.replace(/"/g, '') : null;
                    }
                """)
                if token:
                    return token
                else:
                    return "REGISTRATION_SUCCESS_NO_TOKEN"
        except Exception as e:
            log.error(f"❌ Token extraction error {e}")
        if elapsed_seconds >= 300:
            log.warning("❌ Token extraction timeout")
            return None
        await asyncio.sleep(1)

def send_notif(title, message):
    pass

class ProxyManager:
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies: List[Dict[str, str]] = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.load_proxies()

    def load_proxies(self) -> None:
        try:
            if not os.path.exists(self.proxy_file):
                print(f"Proxy file {self.proxy_file} not found!")
                return
            with open(self.proxy_file, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
                for line in lines:
                    try:
                        proxy = self._parse_proxy_line(line)
                        if proxy:
                            self.proxies.append(proxy)
                    except Exception as e:
                        print(f"Invalid proxy format: {line} ({str(e)})")
                        continue
            if self.proxies:
                print(f"Loaded {len(self.proxies)} proxies")
            else:
                print("No valid proxies loaded")
        except Exception as e:
            print(f"Error loading proxies: {str(e)}")

    def _parse_proxy_line(self, line: str) -> Optional[Dict[str, str]]:
        if "://" in line:
            protocol, rest = line.split("://", 1)
        else:
            protocol = "http"
            rest = line
        
        if "@" in rest:
            credentials, host_port = rest.split("@", 1)
            if ":" in credentials:
                username, password = credentials.split(":", 1)
            else:
                username = credentials
                password = ""
        else:
            username = None
            password = None
            host_port = rest
        
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
        else:
            host = host_port
            port = "8080" if protocol == "http" else "1080"
        
        return {
            "protocol": protocol.lower(),
            "host": host,
            "port": port,
            "username": username,
            "password": password
        }

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            print("No proxies available")
            return None
        with self.lock:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def get_proxy_dict(self, proxy: Dict[str, str]) -> Optional[Dict[str, str]]:
        if not proxy:
            return None
        
        protocol = proxy['protocol']
        if protocol not in ['http', 'https', 'socks4', 'socks5']:
            protocol = 'http'
        
        proxy_url = f"{protocol}://{proxy['host']}:{proxy['port']}"
        
        if proxy['username'] and proxy['password']:
            return {
                "server": proxy_url,
                "username": proxy['username'],
                "password": proxy['password']
            }
        return {"server": proxy_url}

    def get_proxy_for_camoufox(self, proxy: Dict[str, str]) -> Optional[Dict[str, str]]:
        if not proxy:
            return None
        
        result = {
            "http": f"http://{proxy['host']}:{proxy['port']}",
            "https": f"http://{proxy['host']}:{proxy['port']}"
        }
        
        if proxy['username'] and proxy['password']:
            auth_http = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            result = {
                "http": auth_http,
                "https": auth_http
            }
        
        return result

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        with self.lock:
            proxy = random.choice(self.proxies)
        return proxy

    def get_proxy_dict_legacy(self) -> Optional[Dict[str, str]]:
        proxy = self.get_next_proxy()
        return self.get_proxy_dict(proxy) if proxy else None

    def get_working_proxy_dict(self) -> Optional[Dict[str, str]]:
        proxy = self.get_next_proxy()
        return self.get_proxy_for_camoufox(proxy) if proxy else None

with open('config.json', 'r') as f:
    config = json.load(f)

def gen_name():
    return ''.join(random.choices(string.ascii_letters, k=8))

def verify(
    email_user,
    email_pass,
    subject_filter="Verify email address for Discord",
    timeout=100,
    interval=1
):
    imap= config.get("mail_imap")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            mail = imaplib.IMAP4_SSL(imap)
            mail.login(email_user, email_pass)
            mail.select("inbox")
            result, data = mail.search(None, "ALL")
            mail_ids = data[0].split()
            for i in reversed(mail_ids[-10:]):
                result, msg_data = mail.fetch(i, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = msg.get("Subject", "")
                sender = msg.get("From", "")
                if subject_filter not in subject and "discord" not in sender.lower():
                    continue
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            soup = BeautifulSoup(body, "html.parser")
                            for a_tag in soup.find_all("a", href=True):
                                href = a_tag["href"]
                                if "click.discord.com/ls/click" in href:
                                    try:
                                        resolved = requests.get(href, allow_redirects=True, timeout=10)
                                        if "discord.com/verify" in resolved.url:
                                            mail.logout()
                                            return resolved.url
                                    except Exception as e:
                                        log.error(f"❌ Could not resolve Discord link {e}")
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                    match = re.search(r"https://click\\.discord\\.com/ls/click\\?[^\"'<>]+", body)
                    if match:
                        try:
                            resolved = requests.get(match.group(), allow_redirects=True, timeout=10)
                            if "discord.com/verify" in resolved.url:
                                mail.logout()
                                return resolved.url
                        except Exception as e:
                            log.error(f"❌ Could not resolve Discord link {e}")
            mail.logout()
        except Exception as e:
            log.error(f"⚠️ IMAP error {e}")
        time.sleep(interval)
    log.error("❌ No verification link found in time.")
    return None

async def captcha_solver(page):
    global captcha_solving
    captcha_solving = True
    captcha_start_time = datetime.now()  
    try:
        captcha_present = await detect_captcha_thoroughly(page)
        if not captcha_present:
            log.info("No captcha detected initially")
            captcha_solving = False
            return True
        log.warning("Captcha detected!")
        captcha_timeout = 300  
        await asyncio.sleep(3)
        captcha_ready = await wait_for_captcha_ready(page)
        if not captcha_ready:
            log.warning("Captcha not ready after 30 seconds - skipping account")
            captcha_solving = False
            return False
        if config.get("use_ai_solver", True):
            try:
                solver_start_time = datetime.now()  
                solver = Solver()
                result = await solver.solve_captcha(page)
                if result.get('success', False):
                    challenges_solved = result.get('challenges_solved', 0)
                    elapsed_time = datetime.now() - solver_start_time
                    time_taken = int(elapsed_time.total_seconds())
                    if challenges_solved > 0:
                        log.success(f"🎉 Successfully solved captcha! (challenges:{challenges_solved}, time taken: {time_taken}s)")
                    else:
                        log.success(f"🎉 Captcha was already solved! (time taken: {time_taken}s)")
                    if await is_captcha_truly_solved(page):
                        captcha_solving = False
                        return True
                    else:
                        log.warning("❌ AI reported success but captcha still present")
                        return await retry_ai_solver_until_solved_or_timeout(page, captcha_start_time, captcha_timeout)
                else:
                    error_msg = result.get('error', 'Unknown error')
                    log.warning(f"AI solving failed: {error_msg}")
                    return await retry_ai_solver_until_solved_or_timeout(page, captcha_start_time, captcha_timeout)
            except Exception as e:
                log.error(f"AI solver error: {e}")
                return await retry_ai_solver_until_solved_or_timeout(page, captcha_start_time, captcha_timeout)
        log.warning("❌ Falling back to manual captcha solving...")
        send_notif("Ultimate", "Please solve the CAPTCHA manually!")
        return await wait_for_manual_captcha_completion_with_timeout(page, captcha_timeout, captcha_start_time)
    except Exception as e:
        log.error(f"❌ Captcha solver error {e}")
        captcha_solving = False
        return False

async def wait_for_captcha_ready(page):
    while True:
        try:
            checkbox_ready = await page.evaluate("""
                () => {
                    const checkbox = document.querySelector('#checkbox');
                    if (checkbox) {
                        return checkbox.offsetHeight > 0 && checkbox.offsetWidth > 0;
                    }
                    return false;
                }
            """)
            if checkbox_ready:
                return True
            image_captcha_ready = await page.evaluate("""
                () => {
                    const images = document.querySelectorAll('img[src*="hcaptcha"], img[src*="captcha"], .challenge-image, [class*="challenge"] img');
                    if (images.length > 0) {
                        for (const img of images) {
                            if (img.offsetHeight > 50 && img.offsetWidth > 50) {
                                return true;
                            }
                        }
                    }
                    const iframes = document.querySelectorAll('iframe[src*="hcaptcha"], iframe[src*="captcha"]');
                    for (const iframe of iframes) {
                        if (iframe.offsetHeight > 100 && iframe.offsetWidth > 200) {
                            try {
                                if (iframe.contentDocument || iframe.contentWindow) {
                                    return true;
                                }
                            } catch (e) {
                                return true;
                            }
                        }
                    }
                    return false;
                }
            """)
            if image_captcha_ready:
                return True
            await asyncio.sleep(1)
        except Exception as e:
            log.debug(f"❌ Captcha ready check error {e}")
            await asyncio.sleep(1)

async def retry_ai_solver_until_solved_or_timeout(page, start_time, total_timeout):
    attempt = 1
    max_attempts = 10
    while attempt <= max_attempts:
        elapsed_time = datetime.now() - start_time
        if elapsed_time.total_seconds() > total_timeout:
            log.warning(f"❌ Total captcha timeout ({total_timeout//60} minutes) exceeded - closing account")
            return False
        remaining_time = total_timeout - elapsed_time.total_seconds()
        log.info(f"❌ AI Solver retry attempt {attempt}/{max_attempts} | Time remaining: {int(remaining_time//60)}:{int(remaining_time%60):02d}")
        try:
            captcha_still_present = await detect_captcha_thoroughly(page)
            if not captcha_still_present:
                log.success("🎉 Captcha solved - proceeding...")
                return True
            captcha_ready = await wait_for_captcha_ready(page)
            if not captcha_ready:
                log.warning(f"🎉 Captcha not ready on retry attempt {attempt}")
                attempt += 1
                continue
            solver = Solver()
            result = await solver.solve_captcha(page)
            if result.get('success', False):
                challenges_solved = result.get('challenges_solved', 0)
                if challenges_solved > 0:
                    log.success(f"❌ AI retry successful! ({challenges_solved} challenges)")
                else:
                    log.success(f"❌ AI confirmed captcha was solved!")
                if await is_captcha_truly_solved(page):
                    return True
                else:
                    log.warning(f"❌ AI retry {attempt} reported success but captcha still present")
            else:
                error_msg = result.get('error', 'Unknown error')
                log.warning(f"❌ AI retry {attempt} failed: {error_msg}")
        except Exception as e:
            log.error(f"❌ AI retry {attempt} error: {e}")
        attempt += 1
    elapsed_time = datetime.now() - start_time
    if elapsed_time.total_seconds() > total_timeout:
        log.warning(f"Total captcha timeout exceeded after AI retries - closing account")
        return False
    log.warning("❌ All AI retry attempts failed - falling back to manual solving...")
    send_notif("Ultimate", "Please solve the CAPTCHA manually!")
    return await wait_for_manual_captcha_completion_with_timeout(page, total_timeout, start_time)

async def wait_for_captcha_frames(page, timeout: int = 15):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            await page.evaluate("""
                () => {
                    const hcaptcha_frames = document.querySelectorAll('iframe[src*="hcaptcha"], iframe[data-hcaptcha-widget-id]');
                    const recaptcha_frames = document.querySelectorAll('iframe[src*="recaptcha"]');
                    const turnstile_frames = document.querySelectorAll('iframe[src*="turnstile"], .cf-turnstile iframe');
                    const all_frames = [...hcaptcha_frames, ...recaptcha_frames, ...turnstile_frames];
                    let frames_ready = 0;
                    let total_frames = all_frames.length;
                    for (const frame of all_frames) {
                        if (frame.offsetHeight > 0 && frame.offsetWidth > 0 && 
                            frame.style.display !== 'none' && frame.style.visibility !== 'hidden') {
                            frames_ready++;
                        }
                    }
                    return {
                        total_frames: total_frames,
                        frames_ready: frames_ready,
                        ready: frames_ready > 0 && frames_ready === total_frames
                    };
                }
            """)
        except Exception as e:
            log.debug(f"❌ Frame check error {e}")
    log.warning(f"❌ Captcha frames not ready after {timeout} seconds")
    return False

async def detect_captcha_thoroughly(page):
    try:
        await asyncio.sleep(1)
        iframe_captcha = await page.evaluate("""
            () => {
                const iframes = document.querySelectorAll('iframe');
                for (const iframe of iframes) {
                    const src = iframe.src?.toLowerCase() || '';
                    if (src.includes('captcha') || src.includes('hcaptcha') || 
                        src.includes('recaptcha') || src.includes('turnstile')) {
                        return iframe.style.display !== 'none' && iframe.offsetHeight > 0;
                    }
                }
                return false;
            }
        """)
        if iframe_captcha:
            return True
        dom_captcha = await page.evaluate("""
            () => {
                const captchaSelectors = [
                    'div[class*="captcha"]', 'div[id*="captcha"]', 'div[data-captcha]',
                    '.h-captcha', '.g-recaptcha', '.cf-turnstile', '.hcaptcha', '.recaptcha',
                    '[data-testid="captcha"]', '[data-testid="h-captcha"]',
                    '.challenge', '#challenge', 'div[class*="challenge"]',
                    'div[class*="verification"]', 'div[class*="verify"]'
                ];
                for (const selector of captchaSelectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const element of elements) {
                        if (element.style.display !== 'none' && element.offsetHeight > 0) {
                            return true;
                        }
                    }
                }
                return false;
            }
        """)
        if dom_captcha:
            return True
        text_captcha = await page.evaluate("""
            () => {
                const bodyText = document.body.textContent?.toLowerCase() || '';
                const captchaKeywords = [
                    'verify you are human', 'prove you are human', 'human verification',
                    'captcha', 'recaptcha', 'hcaptcha', 'turnstile',
                    'security check', 'bot verification', 'please verify'
                ];
                return captchaKeywords.some(keyword => bodyText.includes(keyword));
            }
        """)
        if text_captcha:
            log.debug("Text-based captcha indicators found")
            return True
        return False
    except Exception as e:
        log.debug(f"Captcha detection error: {e}")
        return False

async def is_captcha_truly_solved(page):
    try:
        await asyncio.sleep(2)
        current_url = page.url
        if any(indicator in current_url.lower() for indicator in ['channels', 'app', 'success', 'dashboard']):
            return True
        captcha_gone = await page.evaluate("""
            () => {
                const iframes = document.querySelectorAll('iframe[src*="captcha"], iframe[src*="hcaptcha"], iframe[src*="recaptcha"]');
                for (const iframe of iframes) {
                    if (iframe.style.display !== 'none' && iframe.offsetHeight > 0) {
                        return false;
                    }
                }
                const captchaContainers = document.querySelectorAll('div[class*="captcha"], .h-captcha, .g-recaptcha, [data-testid="captcha"]');
                for (const container of captchaContainers) {
                    if (container.style.display !== 'none' && container.offsetHeight > 0) {
                        return false;
                    }
                }
                const successElements = document.querySelectorAll('[data-verified="true"], [class*="success"], [class*="verified"]');
                if (successElements.length > 0) {
                    return true;
                }
                try {
                    const token = localStorage.getItem('token');
                    if (token && token !== 'undefined' && token.length > 20) {
                        return true;
                    }
                } catch (e) {}
                return true;
            }
        """)
        return captcha_gone
    except Exception:
        return False

async def wait_for_manual_captcha_completion_with_timeout(page, timeout_seconds, start_time):
    check_interval = 2
    while True:
        try:
            elapsed_time = datetime.now() - start_time
            if elapsed_time.total_seconds() > timeout_seconds:
                log.warning(f"❌ Captcha solving timeout ({timeout_seconds//60} minutes exceeded) - closing account")
                return False
            remaining_seconds = timeout_seconds - elapsed_time.total_seconds()
            if int(elapsed_time.total_seconds()) % 30 == 0 and int(elapsed_time.total_seconds()) > 0:
                remaining_minutes = int(remaining_seconds // 60)
                remaining_secs = int(remaining_seconds % 60)
                log.info(f"❌ Captcha timeout {remaining_minutes}:{remaining_secs:02d} remaining")
            if await is_captcha_truly_solved(page):
                log.success("🎉 Captcha manually solved!")
                return True
            await asyncio.sleep(check_interval)
        except Exception as e:
            log.debug(f"❌ Manual captcha wait error {e}")
            await asyncio.sleep(1)

async def wait_for_manual_captcha_completion(page):
    return await wait_for_manual_captcha_completion_with_timeout(page, 300, datetime.now())

async def monitor_for_captcha(page, phase_name, timeout_minutes=5):
    try:
        captcha_present = await detect_captcha_thoroughly(page)
        if captcha_present:
            start_time = datetime.now()
            completion_success = await wait_for_manual_captcha_completion_with_timeout(
                page, timeout_minutes * 60, start_time
            )
            if completion_success:
                return True
            else:
                log.error(f"❌ Failed to solve captcha during {phase_name} (timeout)")
                return False
        return True
    except Exception as e:
        log.debug(f"❌ Captcha monitoring error during {phase_name} {e}")
        return True

async def wait_for_page_ready_infinite(page, timeout_minutes=2):
    pass

def generate_username():
    first_names = [
        "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn",
        "Blake", "Cameron", "Drew", "Hayden", "Jamie", "Kendall", "Logan", "Parker",
        "Sage", "Skylar", "Reese", "Phoenix", "River", "Rowan", "Dakota", "Emery"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
    ]
    tech_words = [
        "Tech", "Code", "Byte", "Pixel", "Data", "Neo", "Cyber", "Digital", "Virtual",
        "Alpha", "Beta", "Prime", "Core", "Edge", "Link", "Node", "Grid", "Wave"
    ]
    style = random.choice(["realistic", "gaming", "mixed"])
    use_underscore = random.choice([True, False, False, False, True])
    if style == "realistic":
        first = random.choice(first_names)
        last = random.choice(last_names)
        num = random.randint(10, 999)
        if use_underscore:
            username = f"{first.lower()}_{last.lower()}{num}___"
        else:
            username = f"{first.lower()}{last.lower()}{num}___"
        display_name = f"{first} {last}"
    elif style == "gaming":
        tech = random.choice(tech_words)
        name = random.choice(first_names)
        num = random.randint(100, 9999)
        if use_underscore:
            username = f"{tech.lower()}_{name.lower()}{num}___"
        else:
            username = f"{tech.lower()}{name.lower()}{num}___"
        display_name = f"{tech} {name}"
    else:
        first = random.choice(first_names)
        tech = random.choice(tech_words)
        num = random.randint(10, 999)
        if use_underscore:
            username = f"{first.lower()}_{tech.lower()}{num}___"
        else:
            username = f"{first.lower()}{tech.lower()}{num}___"
        display_name = f"{first} {tech}"
    return username, display_name

def generate_dob():
    current_year = datetime.now().year
    birth_year = random.randint(current_year - 30, current_year - 18)
    birth_month = random.randint(1, 12)
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    birth_day = random.randint(1, days_in_month[birth_month - 1])
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    return birth_month, birth_day, birth_year, month_names[birth_month - 1]

async def fast_fill_form_with_retry(page, email, password, username, display_name):
    attempt = 0
    max_username_attempts = 10
    current_username = username
    while True:
        attempt += 1
        captcha_handled = await monitor_for_captcha(page, "form filling")
        if not captcha_handled:
            continue
        try:
            fill_result = await page.evaluate("""
                async (formData) => {
                    const { email, password, username, display_name } = formData;
                    const emailField = document.querySelector('input[type="email"]');
                    const displayField = document.querySelector('input[name="global_name"]');
                    const usernameField = document.querySelector('input[name="username"]');
                    const passwordField = document.querySelector('input[type="password"]');
                    if (!emailField || !passwordField) {
                        return { success: false, reason: 'required_fields_missing' };
                    }
                    const fillField = (field, value) => {
                        if (field && value) {
                            field.focus();
                            field.value = '';
                            field.value = value;
                            field.dispatchEvent(new Event('input', { bubbles: true }));
                            field.dispatchEvent(new Event('change', { bubbles: true }));
                            field.blur();
                        }
                    };
                    fillField(emailField, email);
                    fillField(passwordField, password);
                    fillField(displayField, display_name);
                    fillField(usernameField, username);
                    const emailFilled = emailField.value === email;
                    const passwordFilled = passwordField.value === password;
                    const usernameFilled = usernameField && usernameField.value === username;
                    return {
                        success: emailFilled && passwordFilled && usernameFilled,
                        emailFilled,
                        passwordFilled,
                        usernameFilled
                    };
                }
            """, {
                'email': email,
                'password': password,
                'username': current_username,
                'display_name': display_name
            })
            if fill_result.get('success', False):
                return True, current_username
        except Exception as e:
            log.debug(f"Form fill error: {e}")
        await asyncio.sleep(1)

async def fast_fill_form(page, email, password, username, display_name):
    success, final_username = await fast_fill_form_with_retry(page, email, password, username, display_name)
    return success

async def fast_date_fill_infinite(page, birth_month, birth_day, birth_year, month_name):
    attempt = 0
    max_attempts = 5
    while attempt < max_attempts:
        attempt += 1
        captcha_handled = await monitor_for_captcha(page, "date filling")
        if not captcha_handled:
            continue
        try:
            await page.wait_for_timeout(300)
            await page.evaluate("() => { window.scrollTo(0, 0); }")
            try:
                await page.wait_for_selector('div.wrapper__3412a.select__3f413', timeout=3000)
            except:
                pass
            date_filled = await page.evaluate("""
                async (dateData) => {
                    const { monthName, birthDay, birthYear } = dateData;
                    const findDateSelectors = () => {
                        const allSelects = document.querySelectorAll('div.wrapper__3412a.select__3f413');
                        let monthSelect = null;
                        let daySelect = null;
                        let yearSelect = null;
                        for (const select of allSelects) {
                            const placeholder = select.querySelector('span.placeholder__3f413');
                            if (placeholder) {
                                const text = placeholder.textContent.trim().toLowerCase();
                                if (text === 'month') monthSelect = select;
                                else if (text === 'day') daySelect = select;
                                else if (text === 'year') yearSelect = select;
                            }
                        }
                        if (!monthSelect || !daySelect || !yearSelect) {
                            monthSelect = monthSelect || document.querySelector('div.month_b0f4cc > div > div > div');
                            daySelect = daySelect || document.querySelector('div.day_b0f4cc > div > div > div');
                            yearSelect = yearSelect || document.querySelector('div.year_b0f4cc > div > div > div');
                        }
                        if (!monthSelect || !daySelect || !yearSelect) {
                            const fallbackMonth = document.querySelector('div[class*="month"] > div > div > div, select[aria-label*="month" i]');
                            const fallbackDay = document.querySelector('div[class*="day"] > div > div > div, select[aria-label*="day" i]');
                            const fallbackYear = document.querySelector('div[class*="year"] > div > div > div, select[aria-label*="year" i]');
                            return {
                                monthSelect: monthSelect || fallbackMonth,
                                daySelect: daySelect || fallbackDay,
                                yearSelect: yearSelect || fallbackYear
                            };
                        }
                        return { monthSelect, daySelect, yearSelect };
                    };
                    const fastClickDropdown = async (element, value, isNumeric = false) => {
                        if (!element) return false;
                        try {
                            element.scrollIntoView({ block: 'center' });
                            element.click();
                            await new Promise(resolve => setTimeout(resolve, 200));
                            const prioritySelectors = [
                                'div[role="option"]',
                                '[data-list-item-id]',
                                'div[class*="option"]',
                                'div[role="menuitem"]'
                            ];
                            for (const selector of prioritySelectors) {
                                const options = document.querySelectorAll(selector);
                                for (const option of options) {
                                    const text = option.textContent?.trim();
                                    if (text) {
                                        const matches = isNumeric 
                                            ? text === value.toString()
                                            : text.toLowerCase() === value.toLowerCase() || 
                                              text.toLowerCase().startsWith(value.toLowerCase().substring(0, 3));
                                            
                                        if (matches) {
                                            option.click();
                                            await new Promise(resolve => setTimeout(resolve, 100));
                                            return true;
                                        }
                                    }
                                }
                            }
                            const textElements = document.querySelectorAll('*');
                            for (const el of textElements) {
                                if (el.children.length === 0 && el.offsetParent !== null) {
                                    const text = el.textContent?.trim();
                                    if (text && (
                                        (isNumeric && text === value.toString()) ||
                                        (!isNumeric && text.toLowerCase() === value.toLowerCase())
                                    )) {
                                        el.click();
                                        await new Promise(resolve => setTimeout(resolve, 50));
                                        return true;
                                    }
                                }
                            }
                            return false;
                        } catch (error) {
                            return false;
                        }
                    };
                    const { monthSelect, daySelect, yearSelect } = findDateSelectors();
                    if (!monthSelect || !daySelect || !yearSelect) {
                        return { success: false, reason: 'date_selectors_not_found' };
                    }
                    const monthResult = await fastClickDropdown(monthSelect, monthName, false);
                    await new Promise(resolve => setTimeout(resolve, 150));
                    const dayResult = await fastClickDropdown(daySelect, birthDay, true);
                    await new Promise(resolve => setTimeout(resolve, 150));
                    const yearResult = await fastClickDropdown(yearSelect, birthYear, true);
                    await new Promise(resolve => setTimeout(resolve, 100));
                    return { 
                        success: monthResult && dayResult && yearResult,
                        details: { monthResult, dayResult, yearResult }
                    };
                }
            """, {
                'monthName': month_name,
                'birthDay': birth_day,
                'birthYear': birth_year
            })
            if date_filled.get('success', False):
                return True
            else:
                details = date_filled.get('details', {})
                pass
        except Exception as e:
            pass  
        await asyncio.sleep(0.5)
    return False

async def detect_rate_limit(page):
    try:
        rate_limit_detected = await page.evaluate("""
            () => {
                const bodyText = document.body.textContent?.toLowerCase() || '';
                const rateLimitKeywords = [
                    'rate limit', 'rate limited', 'too many requests', 'slow down',
                    'try again later', 'resource is being rate limited',
                    'please wait before', 'temporarily blocked'
                ];
                const hasRateLimitText = rateLimitKeywords.some(keyword => bodyText.includes(keyword));
                const rateLimitElements = document.querySelectorAll([
                    '[class*="rate-limit"]',
                    '[class*="rateLimit"]', 
                    '[class*="rate_limit"]',
                    '[id*="rate-limit"]',
                    '[id*="rateLimit"]',
                    '[data-testid*="rate-limit"]',
                    '.error-message',
                    '.rate-limited',
                    '.too-many-requests'
                ].join(', '));
                const hasRateLimitElement = Array.from(rateLimitElements).some(el => 
                    el.style.display !== 'none' && el.offsetHeight > 0
                );
                const submitButtons = document.querySelectorAll('button[type="submit"], button[class*="submit"]');
                const hasDisabledSubmit = Array.from(submitButtons).some(btn => {
                    const isDisabled = btn.disabled || btn.hasAttribute('disabled');
                    const text = btn.textContent?.toLowerCase() || '';
                    const hasRateLimitStyling = btn.classList.toString().toLowerCase().includes('rate') ||
                                             btn.classList.toString().toLowerCase().includes('limit') ||
                                             btn.classList.toString().toLowerCase().includes('disabled');
                    return isDisabled && (hasRateLimitStyling || text.includes('wait'));
                });
                const currentUrl = window.location.href.toLowerCase();
                const hasRateLimitUrl = currentUrl.includes('rate-limit') || 
                                      currentUrl.includes('ratelimit') ||
                                      currentUrl.includes('blocked');
                return {
                    detected: hasRateLimitText || hasRateLimitElement || hasDisabledSubmit || hasRateLimitUrl,
                    textDetected: hasRateLimitText,
                    elementDetected: hasRateLimitElement,
                    submitDisabled: hasDisabledSubmit,
                    urlDetected: hasRateLimitUrl
                };
            }
        """)
        return rate_limit_detected
    except Exception as e:
        log.debug(f"Rate limit detection error: {e}")
        return {"detected": False}

async def wait_for_rate_limit_to_clear(page):
    send_notif("Termwave", "Rate limited! Waiting 2 minutes...")
    for i in range(120):
        remaining = 120 - i
        minutes = remaining // 60
        seconds = remaining % 60
        sys.stdout.write(
            f"\r\033[38;5;176m[\033[38;5;97mtermwave\033[38;5;176m] "
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"[⏳] -> Going to sleep for {remaining} seconds, reason: rate limit"
        )
        sys.stdout.flush()
        await asyncio.sleep(1)
    print()

async def fast_tos_and_submit_with_rate_limit_handling(page):
    attempt = 0
    rate_limit_wait_done = False
    while True:
        attempt += 1
        captcha_handled = await monitor_for_captcha(page, "form submission")
        if not captcha_handled:
            continue
        try:
            if not rate_limit_wait_done:
                rate_limit_status = await detect_rate_limit(page)
                if rate_limit_status.get('detected', False):
                    log.warning("⚠️ Rate limit detected before submission attempt")
                    await wait_for_rate_limit_to_clear(page)
                    rate_limit_wait_done = True
            result = await page.evaluate("""
                () => {
                    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                    let checkedCount = 0;

                    checkboxes.forEach(checkbox => {
                        if (!checkbox.checked && !checkbox.disabled) {
                            try {
                                checkbox.click();
                                checkedCount++;
                            } catch (e) {
                                checkbox.checked = true;
                                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                                checkedCount++;
                            }
                        }
                    });
                    const customCheckboxes = document.querySelectorAll('div[role="checkbox"], span[role="checkbox"]');
                    customCheckboxes.forEach(checkbox => {
                        if (checkbox.getAttribute('aria-checked') !== 'true') {
                            try {
                                checkbox.click();
                                checkedCount++;
                            } catch (e) {
                                checkbox.setAttribute('aria-checked', 'true');
                                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                                checkedCount++;
                            }
                        }
                    });
                    const submitButtons = document.querySelectorAll('button, div[role="button"]');
                    for (const btn of submitButtons) {
                        const text = (btn.textContent || '').trim().toLowerCase();
                        if (text.includes('create account') || text.includes('register') || btn.type === 'submit') {
                            try {
                                btn.click();
                                return {
                                    success: true,
                                    checkboxesChecked: checkedCount,
                                    totalCheckboxes: checkboxes.length + customCheckboxes.length,
                                    buttonClicked: true
                                };
                            } catch (e) {
                                try {
                                    btn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    return {
                                        success: true,
                                        checkboxesChecked: checkedCount,
                                        totalCheckboxes: checkboxes.length + customCheckboxes.length,
                                        buttonClicked: true
                                    };
                                } catch (e2) {
                                    return {
                                        success: false,
                                        reason: 'click_failed',
                                        error: e2.toString(),
                                        checkboxesChecked: checkedCount,
                                        totalCheckboxes: checkboxes.length + customCheckboxes.length
                                    };
                                }
                            }
                        }
                    }
                    const form = document.querySelector('form');
                    if (form) {
                        try {
                            form.submit();
                            return {
                                success: true,
                                checkboxesChecked: checkedCount,
                                totalCheckboxes: checkboxes.length + customCheckboxes.length,
                                formSubmitted: true
                            };
                        } catch (e) {
                            return {
                                success: false,
                                reason: 'form_submit_failed',
                                error: e.toString(),
                                checkboxesChecked: checkedCount,
                                totalCheckboxes: checkboxes.length + customCheckboxes.length
                            };
                        }
                    }
                    return {
                        success: false,
                        reason: 'no_submit_button',
                        checkboxesChecked: checkedCount,
                        totalCheckboxes: checkboxes.length + customCheckboxes.length
                    };
                }
            """)
            if result.get('success', False):
                await asyncio.sleep(3)
                current_url = page.url
                if 'register' in current_url.lower():
                    rate_limit_status = await detect_rate_limit(page)
                    if rate_limit_status.get('detected', False) and not rate_limit_wait_done:
                        log.warning("⚠️ Rate limit detected after form submission")
                        await wait_for_rate_limit_to_clear(page)
                        rate_limit_wait_done = True
                        continue
                    elif rate_limit_status.get('detected', False) and rate_limit_wait_done:
                        log.info("⚠️ Rate limit text still visible but continuing (button should be clickable)")
                return True
            else:
                error_reason = result.get('reason', 'unknown')
                if error_reason == 'click_failed' or error_reason == 'form_submit_failed':
                    log.warning(f"⚠️ Submit failed ({error_reason}), retrying...")
                    continue
                elif error_reason == 'no_submit_button':
                    log.error("❌ No submit button found")
                    continue
        except Exception as e:
            log.debug(f"Submission error: {e}")
            if not rate_limit_wait_done:
                rate_limit_status = await detect_rate_limit(page)
                if rate_limit_status.get('detected', False):
                    await wait_for_rate_limit_to_clear(page)
                    rate_limit_wait_done = True
                    continue
        await asyncio.sleep(1)

async def fast_tos_and_submit(page):
    return await fast_tos_and_submit_with_rate_limit_handling(page)

async def post_submission_captcha_monitoring(page, email):
    captcha_present = await detect_captcha_thoroughly(page)
    if captcha_present:
        completion_success = await captcha_solver(page)
        if completion_success:
            return True
        else:
            log.error("❌ Failed to solve post-submission captcha")
            return False
    monitor_start = datetime.now()
    check_count = 0
    while True:
        check_count += 1
        elapsed_time = datetime.now() - monitor_start
        elapsed_seconds = int(elapsed_time.total_seconds())
        if check_count > 10 and check_count % 10 == 0:
            rate_limit_status = await detect_rate_limit(page)
            if rate_limit_status.get('detected', False):
                button_clickable = await page.evaluate("""
                    () => {
                        const submitButtons = document.querySelectorAll('button[type="submit"], button[class*="submit"]');
                        for (const btn of submitButtons) {
                            const text = (btn.textContent || '').trim().toLowerCase();
                            if (text.includes('create account') || text.includes('register')) {
                                return !btn.disabled && !btn.hasAttribute('disabled');
                            }
                        }
                        return false;
                    }
                """)
                if not button_clickable:
                    log.warning(f"⚠️ Rate limit detected with disabled button during post-submission monitoring!")
                    await wait_for_rate_limit_to_clear(page)
                    return False
        if check_count % 3 == 0:
            captcha_present = await detect_captcha_thoroughly(page)
            if captcha_present:
                log.warning(f"⚠️ Late captcha detected after {elapsed_seconds}s!")
                completion_success = await captcha_solver(page)
                if completion_success:
                    log.success(f"🎉 Late captcha successfully solved!")
                    return True
                else:
                    log.error("❌ Failed to solve late captcha")
                    return False
        try:
            current_url = await page.evaluate("window.location.href")
            if any(indicator in current_url.lower() for indicator in ['channels', 'app', 'verify', 'login']):
                return True
        except:
            pass
        can_proceed = await page.evaluate("""
            () => {
                try {
                    const token = localStorage.getItem('token');
                    if (token && token !== 'undefined' && token.length > 20) {
                        return true;
                    }
                } catch (e) {}
                const currentUrl = window.location.href.toLowerCase();
                if (currentUrl.includes('verify') || currentUrl.includes('login') || 
                    currentUrl.includes('channels') || currentUrl.includes('app')) {
                    return true;
                }
                const successElements = document.querySelectorAll(
                    '[class*="success"], [class*="verified"], [data-verified="true"]'
                );
                if (successElements.length > 0) {
                    return true;
                }
                return false;
            }
        """)
        if can_proceed:
            log.info("🎉 Registration appears successful")
            return True
        if elapsed_seconds >= 60:
            log.warning("⚠️ Post-submission monitoring timeout")
            return True
        await asyncio.sleep(1)

async def fill_discord_form(page, email, password):
    try:
        username, display_name = generate_username()
        birth_month, birth_day, birth_year, month_name = generate_dob()
        log.info(f"✉️ Using {email}")
        form_success, final_username = await fast_fill_form_with_retry(page, email, password, username, display_name)
        if not form_success:
            log.warning("⚠️ Failed to fill form fields")
            return {"success": False, "token": None}
        await fast_date_fill_infinite(page, birth_month, birth_day, birth_year, month_name)
        submission_success = await fast_tos_and_submit(page)
        if not submission_success:
            log.warning("Form submission failed")
            return {"success": False, "token": None}
        log.info("✅ Submitted Registration Form")
        captcha_success = await post_submission_captcha_monitoring(page, email)
        if not captcha_success:
            log.warning("Post-submission monitoring failed")
            return {"success": False, "token": None}
        token = await extract_token(page)
        if token and token != "REGISTRATION_SUCCESS_NO_TOKEN":
            log.success(f"🎉 Fetched Token {token:15}********************************************")
            return {"success": True, "token": token}
        elif token == "REGISTRATION_SUCCESS_NO_TOKEN":
            return {"success": True, "token": None}
        return {"success": False, "token": None}
    except Exception as e:
        log.error(f"Form filling error: {e}")
        return {"success": False, "token": None}

async def close_browser():
    try:
        global browser_instance
        if browser_instance:
            await browser_instance.__aexit__(None, None, None)
    except Exception:
        pass

async def handle_verification_link(page, verification_link):
    try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await page.goto(verification_link, wait_until='domcontentloaded', timeout=60000)
                current_url = page.url
                if current_url and 'discord' in current_url.lower():
                    break
            except Exception:
                if attempt < max_retries - 1:
                    continue
                return False
        rate_limit_status = await detect_rate_limit(page)
        if rate_limit_status.get('detected', False):
            log.warning("⚠️ Rate limit detected during email verification!")
            await wait_for_rate_limit_to_clear(page)
            try:
                await page.goto(verification_link, wait_until='domcontentloaded', timeout=60000)
            except:
                return False
        page_content = await page.content()
        page_text = page_content.lower()
        success_indicators = [
            'email verified', 'verification complete', 'successfully verified',
            'account verified', 'continue to discord', 'verification successful'
        ]
        already_verified = any(indicator in page_text for indicator in success_indicators)
        if already_verified:
            log.info(f"🎉 Email Verified Successfully!")
            return True
        captcha_present = await detect_captcha_thoroughly(page)
        if captcha_present:
            log.warning(f"⚠️ Captcha detected during email verification!")
            captcha_success = await captcha_solver(page)
            if not captcha_success:
                log.error("❌ Failed to solve verification captcha")
                return False
        max_wait_time = 30
        check_interval = 2
        for i in range(max_wait_time // check_interval):
            try:
                if i % 3 == 0:
                    rate_limit_status = await detect_rate_limit(page)
                    if rate_limit_status.get('detected', False):
                        log.warning(f"⚠️ Rate limit appeared during verification wait!")
                        await wait_for_rate_limit_to_clear(page)
                        return False
                page_content = await page.content()
                page_text = page_content.lower()
                success_found = any(indicator in page_text for indicator in success_indicators)
                if success_found:
                    log.info(f"✅ Email Verified Successfully!")
                    return True
                current_url = page.url
                if 'discord.com/app' in current_url or 'discord.com/channels' in current_url:
                    return True
                if i % 5 == 0:
                    captcha_present = await detect_captcha_thoroughly(page)
                    if captcha_present:
                        captcha_success = await captcha_solver(page)
                        if not captcha_success:
                            return False
                await asyncio.sleep(check_interval)
            except Exception:
                await asyncio.sleep(check_interval)
                continue
    except Exception as e:
        log.error(f"❌ Verification handling error {e}")
        return False

class AccountManager:
    def __init__(self):
        self.completed_count = 0
        self.total_accounts = 0
        self.proxy_manager = self.setup_proxy_manager()
        self.stats_lock = threading.Lock()
        self.successful = 0
        self.failed = 0
        self.locked = 0
        self.suspended = 0
        self.max_threads = 1
        self.active_threads = 0
        self.thread_lock = threading.Lock()
        self.file_write_lock = threading.Lock()

    def setup_proxy_manager(self) -> Optional[ProxyManager]:
        if not config.get("proxies", True):
            return None
        try:
            proxy_manager = ProxyManager()
            if hasattr(proxy_manager, 'proxies') and proxy_manager.proxies: 
                return proxy_manager
            else:
                return None
        except Exception as e:
            return None

    def get_proxy_for_thread(self, thread_id: int) -> Optional[dict]:
        if not self.proxy_manager:
            return None
        try:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                proxy_dict = self.proxy_manager.get_proxy_dict(proxy)
                return proxy_dict
            return None
        except Exception as e:
            log.error(f"Error getting proxy for thread {thread_id}: {e}")
            return None

    def progress(self, thread_id: int, message: str, status: str = "info"):
        if "Starting:" in message:
            email = message.split("Starting: ")[1]
        elif "SUCCESS:" in message:
            email = message.split("SUCCESS: ")[1]
            log.success(f"🎉 Success {email}!")
        elif "ERROR:" in message:
            error_part = message.split("ERROR: ")[1] if "ERROR: " in message else message
            log.error(f"[T{thread_id:02d}] {error_part}")
        else:
            clean_message = message.replace("ERROR ", "").replace("SUCCESS ", "")
            log.info(f"[T{thread_id:02d}] {clean_message}")

    def stats(self, status: str):
        with self.stats_lock:
            if status == "success":
                self.successful += 1
            else:
                self.failed += 1

    def get_current_stats(self) -> tuple:
        with self.stats_lock:
            return self.successful, self.locked, self.suspended, self.failed

    def increment_active_threads(self):
        with self.thread_lock:
            self.active_threads += 1

    def decrement_active_threads(self):
        with self.thread_lock:
            self.active_threads -= 1

    def get_active_threads(self) -> int:
        with self.thread_lock:
            return self.active_threads

    def process_account_sync(
        self,
        thread_id: int,
        email: str,
        password: str,
        headless: bool = None
    ) -> tuple:
        self.increment_active_threads()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            page_instance, result = loop.run_until_complete(
                self.process_account_async(thread_id, email, password, headless)
            )
            return page_instance, result
        except Exception as e:
            log.error(f"Thread {thread_id} crashed: {e}")
            return None, {
                "thread_id": thread_id,
                "email": email,
                "success": False,
                "status": "thread_error",
                "token": None,
                "error": str(e)
            }
        finally:
            try:
                loop.close()
            except:
                pass
            self.decrement_active_threads()

    async def process_account_async(self, thread_id: int, email: str, password: str, headless: bool = None) -> tuple:
        start_time = time.time()
        timeout_seconds = 600
        result = {
            "thread_id": thread_id,
            "email": email,
            "success": False,
            "status": "failed",
            "token": None
        } 
        browser_instance = None
        page_instance = None
        form_result = None
        def check_timeout():
            elapsed = time.time() - start_time
            return elapsed >= timeout_seconds
        try:
            if check_timeout():
                log.debug(f"❌ Time Ran of limit")
                result["status"] = "timeout"
                return page_instance, result
                    
            proxy = self.get_proxy_for_thread(thread_id)
            try:
                if check_timeout():
                    log.debug(f"❌ Time Ran of limit")
                    result["status"] = "timeout"
                    return page_instance, result
                    
                if headless is None:
                    headless = config.get("headless", False)
                browser_kwargs = {
                    "headless": headless,
                    "window": (1280, 720),
                    "disable_coop": True,
                    "i_know_what_im_doing": True
                }
                if proxy:
                    browser_kwargs["proxy"] = proxy
                browser_instance = AsyncCamoufox(**browser_kwargs)
                browser = await browser_instance.__aenter__()
                page_instance = await browser.new_page()
            except Exception as e:
                result["status"] = "browser_setup_failed"
                self.progress(thread_id, f"Browser setup failed {email} - {str(e)}", "error")
                return page_instance, result
            try:
                if check_timeout():
                    log.debug(f"❌ Time Ran of limit")
                    result["status"] = "timeout"
                    return page_instance, result
                page_load_start = time.time()
                page_load_timeout = 120
                try:
                    await page_instance.goto("https://discord.com/register", wait_until='domcontentloaded', timeout=page_load_timeout * 1000)
                except Exception as e:
                    elapsed_page_load = time.time() - page_load_start
                    if elapsed_page_load >= page_load_timeout or "timeout" in str(e).lower():
                        log.debug(f"❌ Page load timeout after 2 minutes")
                        result["status"] = "page_load_timeout"
                        return page_instance, result
                    else:
                        raise e
                if check_timeout():
                    log.debug(f"❌ Time Ran of limit")
                    result["status"] = "timeout"
                    return page_instance, result
                form_result = await fill_discord_form(page_instance, email, password)
                if not form_result or not form_result.get("success"):
                    result["status"] = "registration_failed"
                    self.progress(thread_id, f"❌ Registration failed {email}", "error")
                    return page_instance, result
            except Exception as e:
                result["status"] = "registration_error"
                self.progress(thread_id, f"❌ Registration error {email} - {str(e)}", "error")
                return page_instance, result
            if check_timeout():
                log.debug(f"❌ Time Ran of limit")
                result["status"] = "timeout"
                return page_instance, result
            verification_link = None
            try:
                if check_timeout():
                    log.debug(f"❌ Time Ran of limit")
                    result["status"] = "timeout"
                    return page_instance, result
                elapsed = time.time() - start_time
                remaining_time = timeout_seconds - elapsed
                if remaining_time <= 10:
                    log.debug(f"❌ Time Ran of limit")
                    result["status"] = "timeout"
                    return page_instance, result
                verification_link = verify(email, password)
                if verification_link:
                    log.info("📧 Email Verification link fetched!")
                else:
                    log.warning(f"❌ No verification email received")     
            except Exception as e:
                log.error(f"❌ Verification email error {e}")
            if verification_link:
                try:
                    if check_timeout():
                        log.debug(f"❌ Time Ran of limit")
                        result["status"] = "timeout"
                        return page_instance, result
                    verification_success = await handle_verification_link(page_instance, verification_link)
                    await asyncio.sleep(2)
                    current_url = page_instance.url
                except Exception as e:
                    log.error(f"❌ Verification handling error {e}")
                    verification_success = False
                if not verification_success:
                    result["status"] = "verification_failed"
                    self.progress(thread_id, f"❌ Verification failed {email}", "error")
                    return page_instance, result
            else:
                result["status"] = "no_verification_email"
                self.progress(thread_id, f"❌ No verification email {email}", "error")
                return page_instance, result
            if check_timeout():
                log.debug(f"❌ Time Ran of limit")
                result["status"] = "timeout"
                return page_instance, result
            try:
                is_disabled, disability_status = await check_acc_disability(page_instance, thread_id, email)
                if is_disabled:
                    result["status"] = "account_disabled"
                    self.progress(thread_id, f"❌ Account disabled {email}", "error")
                    return page_instance, result
            except Exception as e:
                log.warning(f"❌ Disability check failed {e}")
            token = form_result.get("token") if form_result else None
            result["success"] = True
            result["status"] = "success"
            result["token"] = token
            with self.file_write_lock:
                with open("tokens.txt", "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password}:{token}\n")
                    f.flush()
                    
            elapsed = time.time() - start_time
            elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
            self.stats("success")
            return page_instance, result
        except Exception as e:
            if check_timeout():
                log.debug(f"❌ Time Ran of limit")
                result["status"] = "timeout"
            else:
                result["error"] = str(e)
                result["status"] = "error"
                self.progress(thread_id, f"ERROR: {email} - {str(e)}", "error")
                self.stats("failed")
            return page_instance, result
        finally:
            try:
                if browser_instance:
                    await browser_instance.__aexit__(None, None, None)
            except Exception as e:
                log.debug(f"❌ Browser cleanup error {e}")

    async def navigate_to_discord_with_retry(self, page, thread_id: int, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                await asyncio.wait_for(
                    page.goto("https://discord.com/register", wait_until='domcontentloaded'),
                    timeout=30
                )
                current_url = page.url
                if 'discord.com' in current_url.lower():
                    await self.wait_for_page_ready_with_timeout(page, thread_id)
                    return True
            except Exception as e:
                log.debug(f"❌ Navigation attempt {attempt + 1} failed {e}")
                if attempt < max_retries - 1:
                    continue
                raise e

    async def wait_for_page_ready_with_timeout(self, page, thread_id: int, timeout: int = 30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                email_field = await page.query_selector('input[type="email"]')
                if email_field:
                    is_visible = await email_field.is_visible()
                    is_enabled = await email_field.is_enabled()
                    if is_visible and is_enabled:
                        return True
                page_error = await page.evaluate("""
                    () => {
                        const errorTexts = ['error', 'failed', 'timeout', 'connection'];
                        const pageText = document.body.textContent.toLowerCase();
                        return errorTexts.some(error => pageText.includes(error));
                    }
                """)
                if page_error:
                    await page.reload(wait_until='domcontentloaded')
            except Exception:
                continue
        raise TimeoutError(f"❌ Page ready timeout")

    async def fill_discord_form_with_retry(self, page, email: str, password: str, thread_id: int) -> bool:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                form_result = await fill_discord_form(page, email, password)
                if form_result.get("skip_account", False):
                    return form_result  
                if form_result.get("success", False):
                    return form_result
                log.warning(f"❌ Form filling attempt {attempt + 1} failed")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
            except Exception as e:
                log.error(f"❌ Form filling error on attempt {attempt + 1} {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
            return {"success": False, "token": None}
        
    def run(self):
        try:
            accounts_per_thread = int(input(Fore.CYAN + f"[{Fore.MAGENTA}?{Fore.CYAN}] Number of accounts to create : "))
            if accounts_per_thread < 0:
                log.warning("Invalid number, using infinite mode")
                accounts_per_thread = 0
        except ValueError:
            log.warning("Invalid input. Using 1 account per thread.")
            accounts_per_thread = 1
        try:
            max_threads = int(input(Fore.CYAN + f"[{Fore.MAGENTA}?{Fore.CYAN}] Number of threads to use : "))
            if max_threads < 1:
                max_threads = 1
                log.warning("Minimum 1 thread required, using 1")
            elif max_threads > 10:
                max_threads = 10
                log.warning("Maximum 10 threads allowed, using 10")
            self.max_threads = max_threads
            log.info(f"Using {self.max_threads} threads")
        except ValueError:
            self.max_threads = 1
            log.warning("Invalid input. Using 1 thread.")
        if accounts_per_thread == 0:
            self.total_accounts = 0
            log.info(f"Infinite mode: Each thread will create accounts continuously")
        else:
            self.total_accounts = accounts_per_thread * self.max_threads
        try:
            headless_input = input(Fore.CYAN + f"[{Fore.MAGENTA}?{Fore.CYAN}] Run browser in headless mode? (y/n) [default: config.json]: ").strip().lower()
            if headless_input == 'y' or headless_input == 'yes':
                headless_mode = True
            elif headless_input == 'n' or headless_input == 'no':
                headless_mode = False
            else:
                headless_mode = None
                config_headless = config.get("headless", False)
                log.info(f"Using config setting - Headless: {config_headless}")
        except:
            headless_mode = None
            log.info("Using config headless setting")
        if self.proxy_manager and hasattr(self.proxy_manager, 'proxies') and self.proxy_manager.proxies:
            log.info(f"Loaded {len(self.proxy_manager.proxies)} proxies")
        else:
            pass
        if accounts_per_thread == 0:
            log.info("Infinite mode activated")
            log.info("Press Ctrl+C to stop")
            try:
                self._process_infinite_mode_parallel(headless_mode)
            except KeyboardInterrupt:
                log.warning("Infinite mode stopped by user")
        else:
            try:
                _, result = self._process_accounts_per_thread(accounts_per_thread, headless_mode)
            except KeyboardInterrupt:
                log.warning("Account creation interrupted by user")
            except Exception as e:
                log.error(f"❌ Account creation error {e}")
        if self.get_active_threads() > 0:
            log.info("⚠️ Waiting for threads to complete...")
            max_wait_time = 30
            wait_start = time.time()
            while self.get_active_threads() > 0 and (time.time() - wait_start) < max_wait_time:
                active_count = self.get_active_threads()
                with log.write_lock:
                    print(f"\rActive threads {active_count}", end="", flush=True)
                time.sleep(2)
            with log.write_lock:
                print()
            if self.get_active_threads() > 0:
                log.warning(f"{self.get_active_threads()} thread(s) still active after timeout")
        self._print_final_statistics(accounts_per_thread)

    def _print_final_statistics(self, accounts_per_thread):
        successful, locked, suspended, failed = self.get_current_stats()
        total_processed = successful + locked + suspended + failed
        with log.write_lock:
            print(f"{Fore.CYAN}Results{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Successful Accounts: {successful}{Style.RESET_ALL}")
            print(f"{Fore.RED}Failed Accounts: {failed}{Style.RESET_ALL}")
            sys.stdout.flush()

    def _process_infinite_mode_parallel(self, headless_mode: bool):
        log.info(f"Starting {self.max_threads} threads for infinite account creation...")
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []
            for thread_id in range(1, self.max_threads + 1):
                future = executor.submit(self._infinite_thread_worker, thread_id, headless_mode)
                futures.append(future)
            try:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        log.error(f"Thread worker error: {e}")
            except KeyboardInterrupt:
                log.warning("Stopping all infinite threads...")
                for future in futures:
                    future.cancel()

    def _infinite_thread_worker(self, thread_id: int, headless_mode: bool):
        account_counter = 0
        try:
            while True:
                account_counter += 1
                try:
                    with open("input.txt", "r") as f:
                        acc_line = f.readline().strip()
                        email, password = acc_line.split(":")
                        lines = f.readlines()
                    with open("input.txt", "w") as f:
                        f.writelines(lines[1:])
                    self.increment_active_threads()
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            _, result = loop.run_until_complete(
                                self.process_account_async(thread_id, email, password, headless_mode)
                            )
                            if result and result.get("status") in ["page_timeout_skipped", "account_timeout"]:
                                continue  
                        finally:
                            loop.close()  
                    finally:
                        self.decrement_active_threads()
                    if account_counter % 5 == 0:
                        successful, locked, suspended, failed = self.get_current_stats()
                        total_processed = successful + locked + suspended + failed
                        log.info(f"[T{thread_id:02d}] Progress: {account_counter} created | Total: S:{successful} L:{locked} Sus:{suspended} F:{failed}")
                    if account_counter % 3 == 0 and config.get("check_ratelimit", True):
                        try:
                            wait_time = self._check_rate_limit_threadsafe()
                            if wait_time > 0:
                                print(f"\r\033[38;5;176m[\033[38;5;97mtermwave\033[38;5;176m] [{datetime.now().strftime('%H:%M:%S')}] [⏳] -> Going to sleep for {wait_time} seconds, reason: rate limit")
                                time.sleep(wait_time)
                        except Exception:
                            pass
                    time.sleep(random.uniform(1, 3))
                except KeyboardInterrupt:
                    log.warning(f"[T{thread_id:02d}] Stopped after {account_counter} accounts")
                    break
                except Exception as e:
                    log.error(f"[T{thread_id:02d}] Error on account #{account_counter}: {str(e)[:50]}...")
                    self.update_stats("failed")
                    time.sleep(random.uniform(2, 5))
        except KeyboardInterrupt:
            log.warning(f"[T{thread_id:02d}] Worker stopped")

    def _process_accounts_per_thread(self, accounts_per_thread: int, headless_mode: bool):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []
            for thread_id in range(1, self.max_threads + 1):
                future = executor.submit(self._thread_worker, thread_id, accounts_per_thread, headless_mode)
                futures.append(future)
            completed_threads = 0
            for future in as_completed(futures, timeout=1800):
                try:
                    result = future.result()
                    completed_threads += 1
                    log.info(f"Thread {completed_threads}/{self.max_threads} completed")
                except Exception as e:
                    log.error(f"Thread failed: {e}")
                    completed_threads += 1
        log.success(f"All {self.max_threads} threads completed!")
        return None, {"success": True, "completed_threads": completed_threads}

    def _thread_worker(self, thread_id: int, accounts_per_thread: int, headless_mode: bool):
        for account_num in range(1, accounts_per_thread + 1):
            try:
                with open("input.txt", "r") as f:
                    acc_line = f.readline().strip()
                    email, password = acc_line.split(":")
                    lines = f.readlines()
                with open("input.txt", "w") as f:
                    f.writelines(lines[1:])
                self.increment_active_threads()
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        _, result = loop.run_until_complete(
                            self.process_account_async(thread_id, email, password, headless_mode)
                        )
                        if result and result.get("status") in ["page_timeout_skipped", "account_timeout"]:
                            continue  
                    finally:
                        loop.close() 
                finally:
                    self.decrement_active_threads()
                if account_num < accounts_per_thread and config.get("check_ratelimit", True):
                    try:
                        wait_time = self._check_rate_limit_threadsafe()
                        if wait_time > 0:
                            print(f"\r\033[38;5;176m[\033[38;5;97mtermwave\033[38;5;176m] [{datetime.now().strftime('%H:%M:%S')}] [⏳] -> Going to sleep for {wait_time} seconds, reason: rate limit")
                            time.sleep(wait_time)
                    except Exception:
                        pass
                if account_num < accounts_per_thread:
                    time.sleep(random.uniform(1, 3))
            except Exception as e:
                log.error(f"[T{thread_id:02d}] Error {account_num}/{accounts_per_thread}: {str(e)[:50]}...")
                self.update_stats("failed")

    def _check_rate_limit_threadsafe(self):
        try:
            time.sleep(random.uniform(0.1, 0.5))
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.5",
                "Content-Type": "application/json",
                "DNT": "1",
                "Host": "discord.com",
                "Origin": "https://discord.com",
                "Referer": "https://discord.com/register",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            }
            mailbaba = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
            email = mailbaba + "@gmail.com"
            nam = gen_name()
            paassword = "$TermTUSiCE2169#"
            data = {
                'email': email,
                'password': paassword,
                'date_of_birth': "2000-09-20",
                'username': email,
                'global_name': nam,
                'consent': True,
                'captcha_service': 'hcaptcha',
                'captcha_key': None,
                'invite': None,
                'promotional_email_opt_in': False,
                'gift_code_sku_id': None
            }
            
            req = requests.post('https://discord.com/api/v9/auth/register', json=data, headers=headers, timeout=30)
            try:
                resp_data = req.json()
            except Exception:
                return 1
            if req.status_code == 429 or 'retry_after' in resp_data:
                limit = resp_data.get('retry_after', 1)
                return int(float(limit)) + 1 if limit else 1
            else:
                return 1
        except Exception as e:
            log.debug(f"Rate limit check failed: {e}")
            return 1

banner = '''   ▄████   ██▓    ▄▄▄       ▄████▄   ██▓ ▓█████ ██▀███  
▒ ██▒ ▀█▒ ▓██▒   ▒████▄    ▒██▀ ▀█ ▒▓██▒ ▓█   ▀▓██ ▒ ██▒
░▒██░▄▄▄░ ▒██░   ▒██  ▀█▄  ▒▓█    ▄▒▒██▒ ▒███  ▓██ ░▄█ ▒
░▓█  ██▓ ▒██░   ░██▄▄▄▄██▒▒▓▓▄ ▄██░░██░ ▒▓█  ▄▒██▀▀█▄  
░▒▓███▀▒░▒░██████▒▓█   ▓██░▒ ▓███▀ ░░██░▒░▒████░██▓ ▒██▒
 ░▒   ▒  ░░ ▒░▓  ░▒▒   ▓▒█░░ ░▒ ▒   ░▓  ░░░ ▒░ ░ ▒▓ ░▒▓░
  ░   ░  ░░ ░ ▒  ░ ░   ▒▒    ░  ▒  ░ ▒ ░░ ░ ░    ░▒ ░ ▒ 
░ ░   ░ ░   ░ ░    ░   ▒   ░       ░ ▒ ░    ░    ░░   ░ 
      ░  ░    ░        ░   ░ ░       ░  ░   ░     ░     
'''
cret = '''[+] Creator - NoTinyxd X Termwave'''
contri = '''[+] Contributor - DevDream'''
if __name__ == "__main__":
    try:
        System.Clear()
        print("\n")
        print_gradient(Center.XCenter(banner))
        print_gradient(Center.XCenter(cret))
        print_gradient(Center.XCenter(contri))
        print("\n")
        if not config.get("notify", True):
            log.warning("Notification Alert is disabled at config.json.")
        if not config.get("check_ratelimit", True):
            log.warning("Ratelimit Handler is disabled at config.json.")
        if config.get("use_ai_solver", True):
            pass
        else:
            log.warning("Captcha Solver is disabled.")
        manager = AccountManager()
        manager.run()
        thread_print("All processing completed! Press ENTER to exit...", Fore.GREEN)
        input()
    except KeyboardInterrupt:
        thread_print("Process interrupted by user", Fore.YELLOW)
    except Exception as e:
        thread_print(f"\nCritical error: {str(e)}", Fore.RED)
        thread_print("Press ENTER to exit...", Fore.RED)
    input()
