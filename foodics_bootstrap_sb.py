import json, time
import keyring
from getpass import getpass
from seleniumbase import SB

URL_LOGIN  = "https://console.foodics.com/login"
STATE_FILE = r"D:\foodics-automation\foodics_storage.json"  # ⇦ مسار مطلق
TIMEZONE   = "Africa/Cairo"
LOCALE     = "en-US"
SERVICE    = "foodics"  # keyring service name

def get_secret(key: str, label: str, secret: bool = False) -> str:
    val = keyring.get_password(SERVICE, key)
    if val:
        return val
    v = (getpass if secret else input)(f"{label}: ").strip()
    keyring.set_password(SERVICE, key, v)
    return v

def set_timezone(sb, tz):
    try: sb.driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": tz})
    except Exception: pass

def set_locale(sb, loc):
    try: sb.driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": loc})
    except Exception: pass

def wait_out_cloudflare(sb, max_wait=90):
    start = time.time()
    while time.time() - start < max_wait:
        url = sb.get_current_url().lower()
        if ("cdn-cgi/challenge" in url or
            sb.is_element_present("css=iframe[title*='Turnstile']") or
            sb.is_element_present("css=div[id^='cf-']")):
            time.sleep(3)
            continue
        if sb.is_element_present("#business_ref") or sb.is_element_present("[name='email']"):
            return True
        time.sleep(1.2)
    return False

def click_login_anyway(sb):
    if sb.is_element_present("[name='password']"):
        try:
            sb.press_keys("[name='password']", "\n"); time.sleep(1.0); return True
        except Exception: pass
    for sel in [
        "css=button[type='submit']:not([disabled])",
        "css=form button[type='submit']",
        "xpath=//button[@type='submit' and not(@disabled)]",
        "css=button.login",
        "css=[data-testid='login-button']",
        "xpath=//form//button",
    ]:
        if sb.is_element_present(sel):
            try: sb.scroll_to(sel); sb.click(sel); time.sleep(1.0); return True
            except Exception:
                try: sb.js_click(sel); time.sleep(1.0); return True
                except Exception: pass
    try:
        ok = sb.execute_script("""
        (function(){
          var f = document.querySelector('form[action*="login"]') || document.querySelector("form");
          if (f){ f.submit(); return true; }
          return false;
        })();
        """)
        if ok: time.sleep(1.0); return True
    except Exception: pass
    return False

def export_storage(sb, path):
    # اجمع Cookies + localStorage + sessionStorage واكتبهم JSON
    cookies = sb.driver.get_cookies()
    local   = sb.execute_script(
        "var o={},k; for (var i=0;i<localStorage.length;i++){k=localStorage.key(i); o[k]=localStorage.getItem(k);} return o;")
    sess    = sb.execute_script(
        "var o={},k; for (var i=0;i<sessionStorage.length;i++){k=sessionStorage.key(i); o[k]=sessionStorage.getItem(k);} return o;")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"cookies": cookies, "localStorage": local, "sessionStorage": sess}, f, ensure_ascii=False)
    print(f"✓ Saved session to {path}")

def main():
    account = get_secret("account", "Account number")
    email   = get_secret("email",   "Email")
    pwd     = get_secret("password","Password", secret=True)

    with SB(uc=True, headless=False) as sb:  # لازم headed أول مرة
        set_timezone(sb, TIMEZONE); set_locale(sb, LOCALE)
        sb.set_window_size(1280, 860)
        sb.open(URL_LOGIN)
        sb.wait_for_ready_state_complete()
        wait_out_cloudflare(sb, max_wait=90)

        if sb.is_element_present("#business_ref"):
            sb.clear("#business_ref"); sb.type("#business_ref", account)
        if sb.is_element_present("[name='email']"):
            sb.clear("[name='email']"); sb.type("[name='email']", email)
        if sb.is_element_present("[name='password']"):
            sb.clear("[name='password']"); sb.type("[name='password']", pwd)

        if not click_login_anyway(sb):
            sb.save_screenshot("bootstrap_login_not_clicked.png")
            raise SystemExit("Couldn't trigger login. Click the login button manually, then re-run if needed.")

        sb.wait_for_element_visible("#sidebar_inventory", timeout=120)  # الداشبورد
        export_storage(sb, STATE_FILE)

if __name__ == "__main__":
    main()
