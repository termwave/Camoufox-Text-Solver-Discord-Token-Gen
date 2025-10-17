import asyncio
import os
import time
import json
import random
import requests
import math
from typing import Optional, Dict, List, Tuple
import groq

class Agent:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.api_key = None
        self.model = None
        self.client = None
        self.max_tokens = 10
        self.temperature = 0.0
        self.base_url = "https://api.groq.com/openai/v1"
        self.load_config()

    def load_config(self):
        try:
            if not os.path.isfile(self.config_path):
                return False
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.api_key = config.get('groq_api_key')
            if not self.api_key or self.api_key == "your_groq_api_key_here":
                return False
            self.model = config.get('model', 'llama-3.1-70b-versatile')
            self.max_tokens = config.get('max_tokens', 10)
            self.temperature = config.get('temperature', 0.0)
            return self.initialize_groq_client()
        except Exception:
            return False

    def initialize_groq_client(self):
        try:
            try:
                self.client = groq.Groq(api_key=self.api_key)
                return True
            except ImportError:
                pass
            if not self.client:
                self.client = GroqClient(self.api_key, self.base_url)
                return True
            return False
        except Exception:
            try:
                self.client = GroqClient(self.api_key, self.base_url)
                return True
            except Exception:
                return False

    async def solve_text_question(self, question_text: str, max_retries: int = 2) -> Optional[str]:
        for attempt in range(max_retries):
            answer = self.solve_text_only(question_text)
            if answer:
                return answer
            await asyncio.sleep(0.1)
        return None

    def solve_text_only(self, question_text: str) -> Optional[str]:
        try:
            if not self.client:
                return None
            system_prompt = """You must respond with ONLY "True" or "False". No punctuation. No explanation. No other words.
    - If answer is YES: respond "True"
    - If answer is NO: respond "False"
    Nothing else allowed."""
            content = f"{system_prompt}\n\nQuestion: {question_text}\n\nResponse:"
            messages = [
                {"role": "user", "content": content}
            ]
            try:
                if hasattr(self.client, 'chat'):
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=3,
                        temperature=0.0
                    )
                    if response and response.choices:
                        raw_answer = response.choices[0].message.content.strip()
                        return self.convert_to_german(raw_answer) 
                else:
                    response = self.client.create_completion(
                        model=self.model,
                        messages=messages,
                        max_tokens=3,
                        temperature=0.0
                    )
                    if response and 'choices' in response:
                        raw_answer = response['choices'][0]['message']['content'].strip()
                        return self.convert_to_german(raw_answer)  
                return None 
            except Exception:
                return None
        except Exception:
            return None

    def convert_to_german(self, response: str) -> str:
        if not response:
            return "nein"
        import re
        clean = re.sub(r'[^a-zA-Z]', '', response).lower()
        if clean == "true" or clean.startswith("t"):
            return "ja"
        elif clean == "false" or clean.startswith("f"):
            return "nein"
        return "nein"


class GroqClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_completion(self, model: str, messages: List[Dict], max_tokens: int, temperature: float) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            response = self.session.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None

class Behavior:
    def __init__(self):
        self.current_x = 0
        self.current_y = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_move_time = time.time()
    
    def generate_bezier_path(self, start_x: float, start_y: float, end_x: float, end_y: float, 
                           control_points: int = 2) -> List[Tuple[float, float]]:
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        control_offset = min(distance * 0.15, 50)
        if control_points == 2:
            control_x = (start_x + end_x) / 2 + random.uniform(-control_offset, control_offset)
            control_y = (start_y + end_y) / 2 + random.uniform(-control_offset, control_offset)
            points = []
            steps = max(4, int(distance / 40))
            for i in range(steps + 1):
                t = i / steps
                x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * end_x
                y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * end_y
                points.append((x, y))
            return points
        return [(start_x, start_y), (end_x, end_y)]
    
    def add_mouse_momentum(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
        timed_points = []
        for i, (x, y) in enumerate(points):
            if i == 0:
                delay = random.uniform(0.001, 0.003)
            else:
                prev_x, prev_y = points[i-1]
                distance = math.sqrt((x - prev_x)**2 + (y - prev_y)**2)
                base_delay = min(0.005, distance / 5000)
                delay = base_delay + random.uniform(0.0005, 0.002)
                if i > len(points) * 0.85:
                    delay *= random.uniform(1.1, 1.3)
            timed_points.append((x, y, delay))
        return timed_points
    
    async def move_to_element_naturally(self, page, element, offset_range: int = 10):
        try:
            box = await element.bounding_box()
            if not box:
                return False
            target_x = box['x'] + box['width'] / 2 + random.uniform(-offset_range, offset_range)
            target_y = box['y'] + box['height'] / 2 + random.uniform(-offset_range, offset_range)
            try:
                current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
                start_x = current_pos.get('x', self.current_x)
                start_y = current_pos.get('y', self.current_y)
                if start_x == 0 and start_y == 0:
                    start_x = self.current_x if self.current_x != 0 else page.viewport_size['width'] / 2
                    start_y = self.current_y if self.current_y != 0 else page.viewport_size['height'] / 2
            except:
                start_x = self.current_x if self.current_x != 0 else page.viewport_size['width'] / 2
                start_y = self.current_y if self.current_y != 0 else page.viewport_size['height'] / 2
            path_points = self.generate_bezier_path(start_x, start_y, target_x, target_y)
            timed_points = self.add_mouse_momentum(path_points)
            for x, y, delay in timed_points:
                await page.mouse.move(x, y)
                await asyncio.sleep(delay)
                await page.evaluate(f"() => {{ window.mouseX = {x}; window.mouseY = {y}; }}")
            self.current_x = target_x
            self.current_y = target_y
            self.last_move_time = time.time()
            return True
        except Exception:
            return False
    
    async def add_pre_click_hesitation(self, page):
        hesitation_time = random.uniform(0.01, 0.05)
        micro_movements = random.randint(1, 2)
        for _ in range(micro_movements):
            offset_x = random.uniform(-1, 1)
            offset_y = random.uniform(-1, 1)
            try:
                current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
                new_x = current_pos.get('x', self.current_x) + offset_x
                new_y = current_pos.get('y', self.current_y) + offset_y
                await page.mouse.move(new_x, new_y)
                await asyncio.sleep(hesitation_time / micro_movements)
            except:
                await asyncio.sleep(hesitation_time / micro_movements)

class Solver:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.challenge_count = 0
        self.screenshot_files = []
        self.ai_agent = None
        self.human_behavior = Behavior()
        self.start_time = None
        self.end_time = None

    def cleanup_files(self):
        try:
            for file_path in self.screenshot_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            self.screenshot_files.clear()
        except Exception:
            pass

    def initialize_ai_agent(self):
        try:
            self.ai_agent = Agent()
            if self.ai_agent and hasattr(self.ai_agent, 'client') and self.ai_agent.client:
                return True
            else:
                return False
        except Exception:
            self.ai_agent = None
            return False

    async def extract_hcaptcha_token(self, page):
        try:
            token_info = await page.evaluate("""
                () => {
                    const tokenSelectors = [
                        'textarea[name="h-captcha-response"]',
                        'input[name="h-captcha-response"]',
                        'textarea[name*="hcaptcha-response"]',
                        'input[name*="hcaptcha-response"]',
                        'textarea[name*="hcaptcha"]',
                        'input[name*="hcaptcha"]'
                    ];
                    for (let selector of tokenSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.value && element.value.length > 20) {
                            return {
                                token: element.value,
                                selector: selector,
                                length: element.value.length,
                                name: element.name || element.getAttribute('name'),
                                id: element.id || element.getAttribute('id')
                            };
                        }
                    }
                    if (window.hcaptcha && typeof window.hcaptcha.getResponse === 'function') {
                        try {
                            const apiResponse = window.hcaptcha.getResponse();
                            if (apiResponse && apiResponse.length > 20) {
                                return {
                                    token: apiResponse,
                                    selector: 'hcaptcha.getResponse()',
                                    length: apiResponse.length,
                                    source: 'hCaptcha API'
                                };
                            }
                        } catch (e) {

                        }
                    }
                    const hiddenInputs = document.querySelectorAll('input[type="hidden"]');
                    for (let input of hiddenInputs) {
                        if (input.value && input.value.length > 50 && 
                            (input.name && input.name.toLowerCase().includes('captcha')) ||
                            (input.id && input.id.toLowerCase().includes('captcha'))) {
                            return {
                                token: input.value,
                                selector: input.name ? `input[name="${input.name}"]` : `input[id="${input.id}"]`,
                                length: input.value.length,
                                name: input.name,
                                id: input.id,
                                type: 'hidden'
                            };
                        }
                    }
                    return null;
                }
            """)
            
            return token_info
        except Exception as e:
            return None
        
    async def human_like_delay(self, min_delay=0.2, max_delay=0.6):
        delay = random.uniform(min_delay, max_delay)
        reading_pauses = random.randint(0, 1)
        for _ in range(reading_pauses):
            await asyncio.sleep(delay / (reading_pauses + 1))
            await asyncio.sleep(random.uniform(0.01, 0.03))

    async def human_like_click(self, page, element):
        try:
            if not await self.human_behavior.move_to_element_naturally(page, element):
                box = await element.bounding_box()
                if box:
                    x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
                    y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
                    await page.mouse.move(x, y)
            await self.human_behavior.add_pre_click_hesitation(page)
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await element.click()
            await self.human_like_delay(0.3, 0.8)
            return True
        except Exception:
            return False

    async def wait_for_element_extended(self, frame, selector, timeout=10, check_interval=0.2):
        end_time = time.time() + timeout 
        while time.time() < end_time:
            try:
                element = await frame.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        return element
            except Exception:
                pass
            await asyncio.sleep(check_interval)
        return None

    async def wait_for_frame_ready(self, frame, timeout=15):
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                ready_check = await frame.evaluate("""
                    () => {
                        return document.readyState === 'complete' && 
                               document.body && 
                               document.body.children.length > 0;
                    }
                """)
                if ready_check:
                    await asyncio.sleep(0.3)
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.2)
        return False

    async def detect_initial_state(self, frame):
        try:
            state_info = await frame.evaluate("""
                () => {
                    const result = {
                        type: 'none',
                        ready: false,
                        details: {}
                    };
                    const checkbox = document.querySelector('#checkbox');
                    if (checkbox) {
                        const checkboxStyle = window.getComputedStyle(checkbox);
                        const isVisible = checkbox.offsetHeight > 0 && 
                                        checkbox.offsetWidth > 0 && 
                                        checkboxStyle.display !== 'none' && 
                                        checkboxStyle.visibility !== 'hidden';
                        if (isVisible) {
                            const isChecked = checkbox.getAttribute('aria-checked') === 'true';
                            result.type = 'checkbox';
                            result.ready = true;
                            result.details.checked = isChecked;
                            result.details.ariaChecked = checkbox.getAttribute('aria-checked');
                            result.details.role = checkbox.getAttribute('role');
                            return result;
                        }
                    }
                    const textInput = document.querySelector('.input-field');
                    const promptText = document.querySelector('#prompt-text > span:nth-child(1)');
                    if (textInput && textInput.offsetHeight > 0 && promptText) {
                        const questionText = promptText.innerText || '';
                        if (questionText.trim().length > 3) {
                            result.type = 'text';
                            result.ready = true;
                            result.details.question = questionText.trim();
                            return result;
                        }
                    }
                    const challengeImages = document.querySelectorAll('.challenge-image, .task-image, [class*="image"][class*="challenge"]');
                    const taskContainer = document.querySelector('.task-container, .challenge-container, .prompt-container');
                    if (challengeImages.length > 0 || taskContainer) {
                        result.type = 'image';
                        result.ready = challengeImages.length > 0;
                        result.details.imageCount = challengeImages.length;
                        return result;
                    }
                    return result;
                }
            """)
            return state_info
        except Exception:
            return {'type': 'error', 'ready': False, 'details': {}}

    async def is_checkbox_checked(self, checkbox_frame):
        try:
            checked_selectors = [
                'span[data-checked="true"]',
                'input[type="checkbox"]:checked',
                'div[aria-checked="true"]',
                '.checkbox-checked',
                '[class*="checked"]'
            ]
            for selector in checked_selectors:
                try:
                    element = await checkbox_frame.query_selector(selector)
                    if element and await element.is_visible():
                        return True
                except:
                    continue
            try:
                challenge_indicators = await checkbox_frame.query_selector_all('iframe[src*="challenge"]')
                if challenge_indicators:
                    return True
            except:
                pass
            
            return False
        except:
            return False

    async def check_for_rate_limit_message(self, frame):
        try:
            rate_limit_messages = [
                "Your computer is sending too many requests",
                "too many requests",
                "rate limit",
                "try again later",
                "slow down"
            ]
            page_text = await frame.evaluate("() => document.body.innerText.toLowerCase()")
            for message in rate_limit_messages:
                if message in page_text:
                    return True
            return False
        except:
            return False

    async def handle_checkbox_with_human_motion(self, page, frame, max_attempts=3):
        try:
            for attempt in range(max_attempts):
                if await self.is_checkbox_checked(frame):
                    return True
                checkbox = await frame.query_selector('#checkbox')
                if not checkbox:
                    return False
                success = await self.human_behavior.move_to_element_naturally(page, checkbox, offset_range=5)
                if not success:
                    box = await checkbox.bounding_box()
                    if box:
                        target_x = box['x'] + box['width'] / 2 + random.uniform(-3, 3)
                        target_y = box['y'] + box['height'] / 2 + random.uniform(-3, 3)
                        await page.mouse.move(target_x, target_y)
                await self.human_behavior.add_pre_click_hesitation(page)
                await asyncio.sleep(random.uniform(0.05, 0.1))
                await checkbox.click()
                await self.human_like_delay(0.5, 1.0)
                if await self.check_for_rate_limit_message(frame):
                    await asyncio.sleep(random.uniform(6.0, 7.0))
                    continue
                if await self.is_checkbox_checked(frame):
                    return True
                await self.human_like_delay(0.3, 0.6)
            return False
        except Exception:
            return False

    async def debug_and_click_checkbox(self, page, frame):
        try:            
            checkbox = await frame.query_selector('#checkbox')
            if not checkbox:
                return False
            checkbox_info = await frame.evaluate("""
                () => {
                    const checkbox = document.querySelector('#checkbox');
                    if (checkbox) {
                        const rect = checkbox.getBoundingClientRect();
                        return {
                            found: true,
                            id: checkbox.id,
                            ariaChecked: checkbox.getAttribute('aria-checked'),
                            visible: rect.width > 0 && rect.height > 0,
                            rect: rect
                        };
                    }
                    return { found: false };
                }
            """)
            if checkbox_info['found'] and checkbox_info['visible']:
                await self.human_like_click(page, checkbox)
                await asyncio.sleep(0.5)
                new_state = await frame.evaluate("""
                    () => {
                        const el = document.querySelector('#checkbox');
                        return el ? el.getAttribute('aria-checked') : null;
                    }
                """)
                return new_state == 'true'
            return False
        except Exception:
            return False

    async def try_all_frames_for_checkbox(self, page):
        try:
            all_frames = page.frames
            for i, frame in enumerate(all_frames):
                try:
                    frame_url = frame.url
                    
                    if 'hcaptcha' in frame_url.lower():
                        checkbox_found = await frame.evaluate("""
                            () => {
                                const checkbox = document.querySelector('#checkbox');
                                if (checkbox) {
                                    const rect = checkbox.getBoundingClientRect();
                                    return {
                                        found: true,
                                        id: checkbox.id,
                                        ariaChecked: checkbox.getAttribute('aria-checked'),
                                        visible: rect.width > 0 && rect.height > 0,
                                        rect: rect
                                    };
                                }
                                return { found: false };
                            }
                        """)
                        
                        if checkbox_found['found']:
                            success = await self.debug_and_click_checkbox(page, frame)
                            if success:
                                return frame   
                except Exception:
                    continue
            return None
        except Exception:
            return None

    async def wait_for_challenge_ready(self, frame, timeout=15):
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                checkbox_found = await frame.evaluate("""
                    () => {
                        const checkbox = document.querySelector('#checkbox') ||
                                       document.querySelector('[role="checkbox"]') ||
                                       document.querySelector('[aria-checked]');
                        if (checkbox) {
                            const rect = checkbox.getBoundingClientRect();
                            return {
                                found: true,
                                visible: rect.width > 0 && rect.height > 0,
                                ariaChecked: checkbox.getAttribute('aria-checked'),
                                id: checkbox.id
                            };
                        }
                        return { found: false };
                    }
                """)
                
                if checkbox_found['found']:
                    return {
                        'type': 'checkbox',
                        'ready': True,
                        'details': {
                            'checked': checkbox_found['ariaChecked'] == 'true',
                            'ariaChecked': checkbox_found['ariaChecked'],
                            'id': checkbox_found.get('id', 'checkbox')
                        }
                    }
                challenge_info = await self.detect_challenge_type(frame)
                if challenge_info['ready']:
                    return challenge_info
                elif challenge_info['type'] != 'none':
                    pass
                await asyncio.sleep(0.3)
            except Exception:
                await asyncio.sleep(0.3)
        return {'type': 'timeout', 'ready': False, 'details': {}}

    async def check_hcaptcha_frames_exist(self, page):
        try:
            frames_exist = await page.evaluate("""
                () => {
                    const challengeFrames = document.querySelectorAll('iframe[src*="hcaptcha.com"][src*="challenge"]');
                    let activeFrames = 0;
                    for (let frame of challengeFrames) {
                        const rect = frame.getBoundingClientRect();
                        const computedStyle = window.getComputedStyle(frame);
                        
                        if (computedStyle.display !== 'none' && 
                            computedStyle.visibility !== 'hidden' &&
                            frame.offsetHeight > 0 && 
                            frame.offsetWidth > 0 &&
                            rect.height > 0 && 
                            rect.width > 0) {
                            activeFrames++;
                        }
                    }
                    return {
                        totalFrames: challengeFrames.length,
                        activeFrames: activeFrames
                    };
                }
            """)
            return frames_exist['activeFrames'] > 0
        except Exception:
            return True

    async def is_captcha_solved(self, page):
        try:
            await asyncio.sleep(0.8)
            current_url = page.url
            if 'hcaptcha' not in current_url.lower():
                return True
            solved_check = await page.evaluate("""
                () => {
                    const responseFields = document.querySelectorAll('textarea[name*="captcha"], input[name*="captcha"], textarea[name*="hcaptcha"], input[name*="hcaptcha"]');
                    for (let field of responseFields) {
                        if (field.value && field.value.length > 10) {
                            return true;
                        }
                    }
                    if (window.hcaptcha && window.hcaptcha.getResponse) {
                        try {
                            const response = window.hcaptcha.getResponse();
                            if (response && response.length > 10) {
                                return true;
                            }
                        } catch (e) {}
                    }
                    const challengeFrames = document.querySelectorAll('iframe[src*="hcaptcha.com"][src*="challenge"]');
                    let activeChallenges = 0;
                    
                    for (let frame of challengeFrames) {
                        const rect = frame.getBoundingClientRect();
                        if (frame.style.display !== 'none' && 
                            frame.offsetHeight > 0 && 
                            frame.offsetWidth > 0 &&
                            rect.height > 0 && 
                            rect.width > 0) {
                            activeChallenges++;
                        }
                    }
                    return challengeFrames.length > 0 && activeChallenges === 0;
                }
            """)
            return solved_check
        except Exception:
            return False

    async def click_menu_button(self, page, frame):
        try:
            await self.human_like_delay(0.3, 0.6)
            menu_btn = await self.wait_for_element_extended(frame, '.info-off > svg:nth-child(1)', 15)
            if not menu_btn:
                alternative_selectors = [
                    '.info-off svg',
                    '[data-cy="menu-button"]',
                    'button[aria-label*="menu"]',
                    '.menu-button'
                ]
                for selector in alternative_selectors:
                    menu_btn = await self.wait_for_element_extended(frame, selector, 5)
                    if menu_btn:
                        break
                if not menu_btn:
                    return False
            await self.human_like_click(page, menu_btn)
            await self.human_like_delay(1.0, 2.0)
            return True
        except Exception:
            return False

    async def click_accessibility_challenge(self, page, frame):
        try:
            await self.human_like_delay(1.0, 2.0)
            accessibility_btn = await self.wait_for_element_extended(frame, '#text_challenge', 12)
            if not accessibility_btn:
                alternative_selectors = [
                    '[data-cy="text-challenge"]',
                    'button[aria-label*="text"]',
                    'button[aria-label*="accessibility"]',
                    '.text-challenge-button'
                ]
                for selector in alternative_selectors:
                    accessibility_btn = await self.wait_for_element_extended(frame, selector, 3)
                    if accessibility_btn:
                        break
                if not accessibility_btn:
                    return False
            await self.human_like_click(page, accessibility_btn)
            return True
        except Exception:
            return False

    async def wait_for_text_challenge(self, frame, timeout=20):
        try:
            input_element = await self.wait_for_element_extended(frame, '.input-field', timeout)
            if input_element:
                question_element = await self.wait_for_element_extended(frame, '#prompt-text > span:nth-child(1)', 5)
                if question_element:
                    return True
                else:
                    await asyncio.sleep(0.5)
                    return await self.has_new_challenge(frame)
            return False
            
        except Exception:
            return False

    async def extract_question(self, frame):
        try:
            await asyncio.sleep(0.3)
            element = await frame.query_selector('#prompt-text > span:nth-child(1)')
            if element:
                text = await element.inner_text()
                if text and len(text.strip()) > 3:
                    return text.strip()
            alternative_selectors = [
                '#prompt-text span',
                '.prompt-text',
                '[data-cy="challenge-prompt"]'
            ]
            for selector in alternative_selectors:
                element = await frame.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 3:
                        return text.strip()
            return "Question not found"
        except Exception:
            return "Error extracting question"

    async def input_answer(self, page, frame, answer):
        try:
            element = await self.wait_for_element_extended(frame, '.input-field', 10)
            if not element:
                return False
            await self.human_behavior.move_to_element_naturally(page, element)
            await self.human_behavior.add_pre_click_hesitation(page)
            await element.click()
            await self.human_like_delay(0.05, 0.1)
            await element.press('Control+a')
            await asyncio.sleep(random.uniform(0.02, 0.05))
            await element.press('Delete')
            await asyncio.sleep(random.uniform(0.02, 0.05))
            for i, char in enumerate(answer):
                await element.type(char)
                if i % 3 == 0:
                    await asyncio.sleep(random.uniform(0.01, 0.02))
                else:
                    await asyncio.sleep(random.uniform(0.005, 0.015))
                if random.random() < 0.02:
                    await asyncio.sleep(random.uniform(0.02, 0.05))
                    await element.press('Backspace')
                    await asyncio.sleep(random.uniform(0.02, 0.05))
                    await element.type(char)
            await self.human_like_delay(0.05, 0.1)
            await element.press('Enter')
            await self.human_like_delay(0.1, 0.2)
            return True
        except Exception:
            return False

    async def has_new_challenge(self, frame):
        try:
            await asyncio.sleep(0.4)
            input_element = await frame.query_selector('.input-field')
            if input_element and await input_element.is_visible():
                question_element = await frame.query_selector('#prompt-text > span:nth-child(1)')
                if question_element:
                    question_text = await question_element.inner_text()
                    if question_text and len(question_text.strip()) > 3:
                        return True
            return False
        except Exception:
            return False

    async def change_language_to_german(self, page, frame):
        try:

            language_selector = await frame.query_selector('#display-language > div')
            if not language_selector:
                language_selector = await frame.query_selector('#display-language')
            if not language_selector:
                return False
            await language_selector.click()
            await asyncio.sleep(0.2)
            await frame.evaluate('''
                () => {
                    const options = document.querySelectorAll('div.option[role="option"]');
                    for (let option of options) {
                        if ((option.innerText || '').toLowerCase().includes('german')) {
                            option.click();
                            break;
                        }
                    }
                }
            ''')
            await asyncio.sleep(0.2)
            return True
        except Exception:
            return False

    async def skip_image_challenge(self, page, frame):
        try:
            language_changed = await self.change_language_to_german(page, frame)
            if language_changed:
                await self.human_like_delay(0.1, 0.2)
                
                new_state = await self.detect_challenge_type(frame)
                if new_state['type'] == 'text':
                    return True
                elif new_state['type'] == 'checkbox':
                    return True
            skip_selectors = [
                'button[aria-label*="skip"]',
                'button:contains("Skip")',
                '.skip-button',
                '[data-cy="skip"]',
                'button[title*="skip"]'
            ]
            for selector in skip_selectors:
                try:
                    skip_button = await frame.query_selector(selector)
                    if skip_button and await skip_button.is_visible():
                        await self.human_like_click(page, skip_button)
                        await self.human_like_delay(2.0, 4.0)
                        return True
                except:
                    continue
            return await self.try_access_text_challenge(page, frame, max_attempts=2)
            
        except Exception:
            return False

    async def try_access_text_challenge(self, page, main_frame, max_attempts=3):
        try:
            for attempt in range(max_attempts):
                await self.wait_for_frame_ready(main_frame)
                if await self.click_menu_button(page, main_frame):
                    await self.human_like_delay(0.1, 0.2)
                    if await self.click_accessibility_challenge(page, main_frame):
                        await self.human_like_delay(0.2, 0.4)
                        if await self.wait_for_text_challenge(main_frame):
                            return True
                if attempt < max_attempts - 1:
                    await self.human_like_delay(0.5, 1.0)
            return False
        except Exception:
            return False

    async def wait_for_loading_complete(self, page, timeout=30):
        end_time = time.time() + timeout
        stable_count = 0
        required_stable_checks = 2
        while time.time() < end_time and stable_count < required_stable_checks:
            try:
                frames = [f for f in page.frames if 'hcaptcha.com' in f.url]
                if frames:
                    main_frame = None
                    for frame in frames:
                        if 'challenge' in frame.url:
                            main_frame = frame
                            break
                    if not main_frame:
                        main_frame = frames[0]
                    try:
                        challenge_info = await self.detect_challenge_type(frame)
                        if challenge_info['ready'] or challenge_info['type'] in ['text', 'image', 'checkbox']:
                            return True
                    except:
                        pass
                loading_check = await page.evaluate("""
                    () => {
                        if (document.readyState !== 'complete') {
                            return { loading: true, reason: 'document not ready' };
                        }
                        const loadingSelectors = [
                            '.loading', '.spinner', '.loader', 
                            '[data-loading="true"]', '.fa-spinner',
                            '.hcaptcha-loading'
                        ];
                        for (let selector of loadingSelectors) {
                            const elements = document.querySelectorAll(selector);
                            for (let el of elements) {
                                if (el.offsetHeight > 0 && el.offsetWidth > 0) {
                                    return { loading: true, reason: 'loading indicator visible' };
                                }
                            }
                        }
                        const frames = document.querySelectorAll('iframe[src*="hcaptcha.com"]');
                        let activeFrames = 0;
                        for (let frame of frames) {
                            if (frame.offsetHeight > 0 && frame.offsetWidth > 0) {
                                activeFrames++;
                            }
                        }
                        if (activeFrames > 0) {
                            return { loading: false, reason: 'frames active' };
                        }
                        return { loading: false, reason: 'all loaded' };
                    }
                """)
                if not loading_check['loading']:
                    stable_count += 1
                    await asyncio.sleep(1)
                else:
                    stable_count = 0
                    await asyncio.sleep(0.4)
            except Exception:
                await asyncio.sleep(1)
        return True

    async def comprehensive_solve_check(self, page):
        try:
            api_solved = await self.is_captcha_solved(page)
            frames_exist = await self.check_hcaptcha_frames_exist(page)
            current_url = page.url
            url_changed = 'hcaptcha' not in current_url.lower()
            token_check = await page.evaluate("""
                () => {
                    const tokenSelectors = [
                        'textarea[name*="captcha-response"]',
                        'textarea[name*="h-captcha-response"]', 
                        'textarea[name*="hcaptcha"]',
                        'input[name*="captcha"]',
                        'textarea[id*="captcha"]'
                    ];
                    for (let selector of tokenSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.value && element.value.length > 20) {
                            return true;
                        }
                    }
                    if (window.hcaptcha) {
                        try {
                            const responses = window.hcaptcha.getResponse();
                            if (responses && responses.length > 20) {
                                return true;
                            }
                        } catch (e) {
                        }
                    }
                    
                    return false;
                }
            """)
            solve_indicators = {
                'api_check': api_solved,
                'frames_gone': not frames_exist,
                'url_changed': url_changed,
                'token_present': token_check
            }
            strong_indicators = [solve_indicators['api_check'], solve_indicators['frames_gone'], solve_indicators['token_present']]
            is_solved = any(strong_indicators)
            return {
                'solved': is_solved,
                'indicators': solve_indicators,
                'confidence': 'high' if sum(strong_indicators) >= 2 else 'medium' if any(strong_indicators) else 'low'
            }
        except Exception:
            return {'solved': False, 'indicators': {}, 'confidence': 'error'}

    async def detect_challenge_type(self, frame):
        try:
            challenge_info = await frame.evaluate("""
                () => {
                    const result = {
                        type: 'none',
                        ready: false,
                        details: {}
                    };
                    const checkbox = document.querySelector('#checkbox');
                    const checkboxByRole = document.querySelector('[role="checkbox"]');
                    const checkboxByAria = document.querySelector('[aria-checked]');
                    const foundCheckbox = checkbox || checkboxByRole || checkboxByAria;
                    if (foundCheckbox) {
                        const rect = foundCheckbox.getBoundingClientRect();
                        const checkboxStyle = window.getComputedStyle(foundCheckbox);
                        const isVisible = foundCheckbox.offsetHeight > 0 && 
                                        foundCheckbox.offsetWidth > 0 && 
                                        checkboxStyle.display !== 'none' && 
                                        checkboxStyle.visibility !== 'hidden' &&
                                        rect.width > 0 && rect.height > 0;
                        if (isVisible) {
                            const isChecked = foundCheckbox.getAttribute('aria-checked') === 'true';
                            result.type = 'checkbox';
                            result.ready = true;
                            result.details.checked = isChecked;
                            result.details.ariaChecked = foundCheckbox.getAttribute('aria-checked');
                            result.details.role = foundCheckbox.getAttribute('role');
                            result.details.id = foundCheckbox.id;
                            result.details.selector = foundCheckbox.id ? '#' + foundCheckbox.id : '[role="checkbox"]';
                            return result;
                        }
                    }
                    const textInput = document.querySelector('.input-field');
                    const promptText = document.querySelector('#prompt-text > span:nth-child(1)');
                    if (textInput && textInput.offsetHeight > 0 && promptText) {
                        const questionText = promptText.innerText || '';
                        if (questionText.trim().length > 3) {
                            result.type = 'text';
                            result.ready = true;
                            result.details.question = questionText.trim();
                            return result;
                        }
                    }
                    const challengeImages = document.querySelectorAll('.challenge-image, .task-image, [class*="image"][class*="challenge"]');
                    const taskContainer = document.querySelector('.task-container, .challenge-container, .prompt-container');
                    const promptElement = document.querySelector('.prompt-text, .task-text, .challenge-prompt');
                    if (challengeImages.length > 0 || taskContainer || promptElement) {
                        let prompt = '';
                        const promptSelectors = [
                            '.prompt-text', '.task-text', '.challenge-prompt',
                            'h2', 'h3', '[class*="prompt"]', '[class*="task"]'
                        ];
                        for (let selector of promptSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.innerText && element.innerText.trim().length > 10) {
                                prompt = element.innerText.trim();
                                break;
                            }
                        }
                        const clickableImages = document.querySelectorAll('div[role="button"], .challenge-image, .task-image, [tabindex="0"]');
                        let imageCount = 0;
                        for (let img of clickableImages) {
                            if (img.offsetHeight > 50 && img.offsetWidth > 50) {
                                imageCount++;
                            }
                        }
                        if (prompt || imageCount > 0) {
                            result.type = 'image';
                            result.ready = imageCount > 0;
                            result.details.prompt = prompt;
                            result.details.imageCount = imageCount;
                            return result;
                        }
                    }
                    const hasContent = document.body && document.body.children.length > 0;
                    if (hasContent) {
                        result.type = 'unknown';
                        result.ready = false;
                        result.details.bodyChildren = document.body.children.length;
                        result.details.checkboxFound = !!foundCheckbox;
                        result.details.checkboxVisible = foundCheckbox ? (foundCheckbox.offsetHeight > 0 && foundCheckbox.offsetWidth > 0) : false;
                        result.details.textInputFound = !!document.querySelector('.input-field');
                        result.details.imageElementsFound = document.querySelectorAll('.challenge-image, .task-image').length;
                        result.details.allElements = document.body.innerHTML.length;
                        if (foundCheckbox) {
                            result.type = 'checkbox';
                            result.ready = true;
                            result.details.checked = foundCheckbox.getAttribute('aria-checked') === 'true';
                            result.details.forceDetected = true;
                        }
                    }
                    return result;
                }
            """)
            return challenge_info
            
        except Exception:
            return {'type': 'error', 'ready': False, 'details': {}}

    async def solve_captcha(self, page):
        try:
            self.start_time = time.time()
            await page.wait_for_load_state('domcontentloaded', timeout=30000)
            await self.wait_for_loading_complete(page, timeout=30)
            await self.human_like_delay(3.0, 5.0)
            if not self.initialize_ai_agent():
                self.cleanup_files()
                return {'success': False, 'error': 'AI agent initialization failed'}
            frames = []
            for attempt in range(5):
                frames = [f for f in page.frames if 'hcaptcha.com' in f.url]
                if frames:
                    break
            if not frames:
                self.cleanup_files()
                return {'success': False, 'error': 'No hCaptcha frames found'}
            main_frame = None
            for frame in frames:
                if 'challenge' in frame.url:
                    main_frame = frame
                    break
            if not main_frame:
                main_frame = frames[0]
            await self.wait_for_frame_ready(main_frame)
            await self.human_like_delay(2.0, 4.0)
            initial_state = await self.detect_initial_state(main_frame)
            checkbox_frame = await self.try_all_frames_for_checkbox(page)
            if checkbox_frame:
                await self.human_like_delay(2.0, 4.0)
                if await self.is_captcha_solved(page):
                    self.end_time = time.time()
                    solve_time = self.end_time - self.start_time
                    token_info = await self.extract_hcaptcha_token(page)
                    self.cleanup_files()
                    return {'success': True, 'challenges_solved': 0, 'method': 'force_checkbox', 'solve_time': solve_time, 'token': token_info, 'error': None}
                main_frame = checkbox_frame
                initial_state = await self.detect_initial_state(main_frame)
            if initial_state['type'] == 'checkbox':
                checkbox_success = await self.debug_and_click_checkbox(page, main_frame)
                if checkbox_success:
                    await self.human_like_delay(0.8, 1.5)
                    if await self.is_captcha_solved(page):
                        self.end_time = time.time()
                        solve_time = self.end_time - self.start_time
                        token_info = await self.extract_hcaptcha_token(page)
                        self.cleanup_files()
                        return {'success': True, 'challenges_solved': 0, 'method': 'debug_checkbox', 'solve_time': solve_time, 'token': token_info, 'error': None}
                    follow_up_state = await self.detect_initial_state(main_frame)
                    if follow_up_state['type'] in ['text', 'image']:
                        initial_state = follow_up_state
            elif initial_state['type'] in ['text', 'image']:
                pass
            else:
                if await self.try_access_text_challenge(page, main_frame):
                    initial_state = await self.detect_initial_state(main_frame)
            solved_challenges = 0
            consecutive_failures = 0
            max_consecutive_failures = 4
            no_challenge_attempts = 0
            max_no_challenge_attempts = 6
            while consecutive_failures < max_consecutive_failures:
                challenge_info = await self.wait_for_challenge_ready(main_frame, timeout=15)
                if challenge_info['type'] == 'timeout':
                    no_challenge_attempts += 1
                    frames_still_exist = await self.check_hcaptcha_frames_exist(page)
                    if not frames_still_exist:
                        break
                    if no_challenge_attempts >= max_no_challenge_attempts:
                        break
                    await self.human_like_delay(2.0, 4.0)
                    continue
                elif challenge_info['type'] == 'checkbox':
                    checkbox_details = challenge_info.get('details', {})
                    is_checked = checkbox_details.get('checked', False)
                    if not is_checked:
                        checkbox_success = await self.debug_and_click_checkbox(page, main_frame)
                        if checkbox_success:
                            await self.human_like_delay(3.0, 6.0)
                            final_check = await self.is_captcha_solved(page)
                            frames_check = await self.check_hcaptcha_frames_exist(page)
                            if final_check or not frames_check:
                                break
                            else:
                                no_challenge_attempts = 0
                                consecutive_failures = 0
                                continue
                        else:
                            consecutive_failures += 1
                            await self.human_like_delay(2.0, 4.0)
                            continue
                    else:
                        await self.human_like_delay(3.0, 5.0)
                        if await self.is_captcha_solved(page):
                            break
                        else:
                            continue
                elif challenge_info['type'] == 'image':
                    if await self.skip_image_challenge(page, main_frame):
                        await self.human_like_delay(2.0, 4.0)
                        continue
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            break
                        await self.human_like_delay(3.0, 5.0)
                        continue
                elif challenge_info['type'] == 'text' and challenge_info['ready']:
                    no_challenge_attempts = 0
                    question = challenge_info['details'].get('question', '')
                    if not question or len(question.strip()) < 3:
                        question = await self.extract_question(main_frame)
                    if not self.ai_agent:
                        if not self.initialize_ai_agent():
                            consecutive_failures += 1
                            continue
                    ai_answer = await self.ai_agent.solve_text_question(question, max_retries=2)
                    if not ai_answer:
                        consecutive_failures += 1
                        await self.human_like_delay(3.0, 5.0)
                        continue
                    await self.human_like_delay(0.3, 0.7)
                    result = await self.input_answer(page, main_frame, ai_answer)
                    if result:
                        solved_challenges += 1
                        consecutive_failures = 0
                        await self.human_like_delay(0.6, 1.1)
                        post_challenge_check = await self.detect_challenge_type(main_frame)
                        if post_challenge_check['type'] == 'checkbox':
                            pass
                    else:
                        consecutive_failures += 1
                        await self.human_like_delay(1.0, 1.8)
                else:
                    quick_checkbox_check = await main_frame.evaluate("""
                        () => {
                            const checkbox = document.querySelector('#checkbox') || 
                                           document.querySelector('[role="checkbox"]') || 
                                           document.querySelector('[aria-checked]');
                            return {
                                found: !!checkbox,
                                visible: checkbox ? (checkbox.offsetHeight > 0 && checkbox.offsetWidth > 0) : false,
                                ariaChecked: checkbox ? checkbox.getAttribute('aria-checked') : null
                            };
                        }
                    """)
                    if quick_checkbox_check['found']:
                        challenge_info = {'type': 'checkbox', 'ready': True, 'details': {'checked': quick_checkbox_check['ariaChecked'] == 'true'}}
                        continue
                    no_challenge_attempts += 1
                    if no_challenge_attempts >= max_no_challenge_attempts:
                        if await self.try_access_text_challenge(page, main_frame, max_attempts=2):
                            no_challenge_attempts = 0
                            continue
                        else:
                            break
                    await self.human_like_delay(2.0, 4.0)
            await self.human_like_delay(3.0, 5.0)
            solve_status = await self.comprehensive_solve_check(page)
            if not solve_status['solved'] or solve_status['confidence'] == 'low':
                await self.human_like_delay(3.0, 5.0)
                solve_status_2 = await self.comprehensive_solve_check(page)
                final_solved = solve_status['solved'] or solve_status_2['solved']
                final_confidence = 'high' if (solve_status['confidence'] == 'high' or solve_status_2['confidence'] == 'high') else 'medium'
            else:
                final_solved = solve_status['solved']
                final_confidence = solve_status['confidence']
            self.end_time = time.time()
            solve_time = self.end_time - self.start_time
            token_info = await self.extract_hcaptcha_token(page)
            self.cleanup_files()
            if final_solved:
                return {
                    'success': True,
                    'challenges_solved': solved_challenges,
                    'confidence': final_confidence,
                    'indicators': solve_status.get('indicators', {}),
                    'solve_time': solve_time,
                    'token': token_info,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'challenges_solved': solved_challenges,
                    'confidence': final_confidence,
                    'indicators': solve_status.get('indicators', {}),
                    'solve_time': solve_time,
                    'token': token_info,
                    'error': f'Captcha not fully solved after {solved_challenges} challenges'
                }
        except Exception as e:
            if self.start_time:
                self.end_time = time.time()
                solve_time = self.end_time - self.start_time
            else:
                solve_time = 0
            self.cleanup_files()
            return {'success': False, 'error': f'Solver error: {str(e)}', 'solve_time': solve_time}