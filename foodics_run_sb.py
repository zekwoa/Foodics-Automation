# foodics_run_from_state_sb.py — v2 (robust Branch/Reason select)
import json, time, random, re
from pathlib import Path
from seleniumbase import SB

# ============ CONFIG ============
BASE_ORIGIN   = "https://console.foodics.com"
URL_DASHBOARD = f"{BASE_ORIGIN}/dashboard"
INDEX_URLS    = [
    f"{BASE_ORIGIN}/inventory/quantity-adjustments",
    f"{BASE_ORIGIN}/inventory/quantity_adjustments",
]
STATE_FILE    = r"D:\foodics-automation\foodics_storage.json"   # <-- session JSON (cookies + storages)
TIMEZONE      = "Africa/Cairo"
LOCALE        = "en-US"
HEADLESS      = False  # keep False while testing

# Tasks
TASKS = [
    {"branch": "Drive 2", "reason": "Expired",
     "csv": r"E:\Pao\Transfers Templete\Quantity Adjustment (Expired).csv"},
    {"branch": "Drive 2", "reason": "Waste Production",
     "csv": r"E:\Pao\Transfers Templete\Quantity Adjustment(Waste Production).csv"},
]

# ============ HELPERS ============
def rnd(a=0.6, b=1.3): time.sleep(random.uniform(a, b))

def set_timezone(sb, tz):
    try: sb.driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": tz})
    except Exception: pass

def set_locale(sb, loc):
    try: sb.driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": loc})
    except Exception: pass

def import_storage(sb, path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cookies = data.get("cookies", []); local = data.get("localStorage", {}); ses = data.get("sessionStorage", {})

    sb.open(BASE_ORIGIN); sb.wait_for_ready_state_complete()

    for c in cookies:
        c2 = {k: c.get(k) for k in ("name","value","domain","path","secure","expiry","httpOnly","sameSite") if k in c}
        if "expiry" in c2 and isinstance(c2["expiry"], float):
            c2["expiry"] = int(c2["expiry"])
        try: sb.driver.add_cookie(c2)
        except Exception: pass

    for k, v in local.items():
        sb.execute_script("localStorage.setItem(arguments[0], arguments[1]);", k, v)
    for k, v in ses.items():
        sb.execute_script("sessionStorage.setItem(arguments[0], arguments[1]);", k, v)

def ensure_logged_in(sb):
    sb.open(URL_DASHBOARD); sb.wait_for_ready_state_complete()
    if "/login" in sb.get_current_url().lower():
        raise SystemExit("Session invalid (redirected to /login). Re-run bootstrap to refresh STATE_FILE.")
    sb.wait_for_element_visible("#sidebar_inventory", timeout=40)

def goto_quantity_adjustments(sb):
    for u in INDEX_URLS:
        sb.open(u); sb.wait_for_ready_state_complete(); rnd()
        if "quantity-adjustments" in sb.get_current_url().lower().replace("_","-"):
            return
    sb.click("#sidebar_inventory"); rnd()
    sb.click("#sidebar_inventory_more"); rnd()
    sb.click("#sidebar_inventory_quantity_adjustments"); rnd(1.0, 1.6)
    sb.wait_for_ready_state_complete()

def open_new_adjustment(sb):
    if sb.is_element_present("#quantity-adjustment\\.new"):
        sb.click("#quantity-adjustment\\.new")
    else:
        sb.click("xpath=//button[contains(normalize-space(),'New Quantity Adjustment')]")
    rnd(0.8, 1.2)

def is_details_page(sb):
    url = sb.get_current_url().lower()
    if re.search(r"/inventory/quantity[-_]adjustments/[^/]+$", url): return True
    if sb.is_element_present("#transactions\\.items\\.import"): return True
    if sb.is_text_visible("Import Items", timeout=1): return True
    return False

# ---------- NEW: robust selector for Branch / Reason ----------
def _label_xpath(label_text):
    return (
        "xpath=//label[contains(translate(normalize-space(.),"
        " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        f" '{label_text.lower()}')]"
    )

def select_dropdown(sb, label_text, value_text):
    """Open dropdown near label -> type if search exists -> click matching option (case-insensitive)."""
    # 1) افتح الـ dropdown المربوط بالـ label (لو موجود)
    label = _label_xpath(label_text)
    opener = None
    if sb.is_element_present(label):
        # احتمالات trigger بعد الـ label
        for sel in [
            f"{label}/following::*[@role='combobox'][1]",
            f"{label}/following::div[contains(@class,'input') and contains(@class,'cursor-pointer')][1]",
            f"{label}/following::*[self::button or self::div][1]",
        ]:
            if sb.is_element_present(sel):
                opener = sel; break

    # لو مفيش label/trigger واضح: استخدم أنماط معروفة
    if not opener:
        if label_text.lower() == "branch":
            opener = ("xpath=//div[@class='input flex items-center cursor-pointer p-2']"
                      "/span[contains(normalize-space(),'Choose...')]")
        else:
            opener = ("xpath=(//div[@tabindex='1' and contains(@class,'input') and "
                      "contains(@class,'cursor-pointer') and contains(@class,'p-2')])[2]")

    sb.scroll_to(opener); sb.click(opener); time.sleep(0.25)

    # 2) لو فيه search input، اكتب القيمة
    search_candidates = [
        "xpath=//div[@id='app-teleport']//input[@placeholder='Type something to start searching']",
        "xpath=//div[@id='app-teleport']//input[@type='text' or @type='search']",
        "xpath=(//*[@role='listbox' or @role='dialog' or contains(@class,'menu') or contains(@class,'dropdown')])[last()]//input[@type='text' or @type='search']",
    ]
    typed = False
    for s in search_candidates:
        if sb.is_element_present(s):
            sb.click(s); sb.clear(s); sb.type(s, value_text); typed = True; break
    if not typed:
        # fallback: اكتب على الـ active element (بعض القوائم تقبل كتابة مباشرة)
        try:
            sb.type("xpath=//body", value_text); typed = True
        except Exception:
            pass
    rnd(0.7, 1.1)

    # 3) دور على option يحتوي النص (case-insensitive) واضغطه
    val = value_text.strip().lower()
    opt_candidates = [
        ("xpath=//div[@id='app-teleport']"
         "//*[self::a or self::div or self::li or self::button]"
         "[(@role='option' or contains(@class,'item') or contains(@class,'option') "
         "  or contains(@class,'menu') or contains(@class,'list') or contains(@class,'truncate')) and "
         f"contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{val}')]"),
        # أي option ظاهر كـ احتياطي
        "xpath=(//*[@role='option' or contains(@class,'item') or contains(@class,'option')])[1]",
    ]
    clicked = False
    for sel in opt_candidates:
        if sb.is_element_present(sel):
            try:
                # لو لقيت أكتر من عنصر، اختار أقرب نص
                els = sb.find_elements(sel)
                if len(els) > 1:
                    def score(el):
                        t = (el.text or "").strip().lower()
                        if t == val: return 0
                        if val in t: return 1
                        return 2
                    els.sort(key=score)
                    sb.scroll_to(els[0]); els[0].click()
                else:
                    sb.scroll_to(sel); sb.click(sel)
                clicked = True
                break
            except Exception:
                try:
                    sb.js_click(sel); clicked = True; break
                except Exception:
                    continue

    # 4) آخر محاولة: ARROWDOWN + ENTER
    if not clicked:
        try:
            sb.press_keys("xpath=//body", "ARROWDOWN"); time.sleep(0.2)
            sb.press_keys("xpath=//body", "ENTER"); clicked = True
        except Exception:
            pass
    if not clicked:
        raise Exception(f"Couldn't pick option for {label_text}: '{value_text}'")
    rnd(0.4, 0.7)

def save_before_import(sb):
    sb.click("#form_save_button"); rnd(0.8, 1.2)
    end = time.time() + 25
    while time.time() < end:
        if is_details_page(sb): return True
        time.sleep(0.3)
    return False

def import_csv_and_save(sb, csv_path):
    if sb.is_element_present("#transactions\\.items\\.import"):
        sb.click("#transactions\\.items\\.import")
    else:
        sb.click("xpath=//*[@id='transactions.items.import' or contains(.,'Import Items')]")
    rnd(0.6, 1.0)

    sb.choose_file("#file", csv_path); rnd(1.6, 2.2)

    near_tpl = "xpath=//div[contains(., 'Download Template')]//button[@id='form_save_button']"
    if sb.is_element_present(near_tpl):
        sb.click(near_tpl)
    else:
        sb.click("xpath=(//button[@id='form_save_button'])[last()]")
    rnd(1.0, 1.5)

# ============ RUN ONE TASK ============
def run_task(sb, task):
    branch, reason, csv = task["branch"], task["reason"], task.get("csv")
    print(f"[RUN] {branch} — {reason}")

    goto_quantity_adjustments(sb)
    open_new_adjustment(sb)

    # <-- هنا المشكلة عندك: خلّيتها robust -->
    select_dropdown(sb, "Branch", branch)
    select_dropdown(sb, "Reason", reason)

    ok = save_before_import(sb)
    if not ok:
        raise Exception("Didn't navigate to details page after Save.")

    if csv:
        from os.path import exists
        if exists(csv):
            import_csv_and_save(sb, csv)
        else:
            print(f"[SKIP] CSV not found: {csv}")

    print(f"[OK]  {branch} — {reason}")

# ============ MAIN ============
def main():
    if not Path(STATE_FILE).exists():
        raise SystemExit(f"Missing {STATE_FILE}. Run the bootstrap to save your session first.")

    with SB(uc=True, headless=HEADLESS) as sb:
        set_timezone(sb, TIMEZONE); set_locale(sb, LOCALE)
        sb.set_window_size(1366, 900)

        import_storage(sb, STATE_FILE)
        ensure_logged_in(sb)

        for t in TASKS:
            try:
                run_task(sb, t)
                rnd(1.2, 1.8)
            except Exception as e:
                try:
                    ts = int(time.time())
                    sb.save_screenshot(f"err_{t['branch']}_{t['reason']}_{ts}.png")
                    sb.save_page_source(f"err_{t['branch']}_{t['reason']}_{ts}.html")
                except Exception:
                    pass
                print(f"[ERR] {t['branch']} — {t['reason']}: {e}")

        print("All tasks completed.")

if __name__ == "__main__":
    main()
