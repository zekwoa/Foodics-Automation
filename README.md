# Foodics-Automation

Automate creating **Quantity Adjustments** in Foodics and importing item lines from **CSV** — reliably, fast, and repeatable.  
The runner starts from a **saved session JSON** (cookies + local/session storage), so it **skips login** and goes straight to work.

---

## Highlights

- **One-click run**: Inventory → Quantity Adjustments → **New** → select **Branch/Reason** → **Save** → **Import CSV** → **Save**
- **Session reuse**: Uses `foodics_storage.json` (exported once by a small bootstrap script)
- **Robust selectors**: Label-aware & search-based dropdown picking (UI-safe)
- **Batch-ready**: Drive multiple tasks via a simple Python list (`{branch, reason, csv}`)
- **Debug-friendly**: Auto-saves screenshot & HTML on errors
- **Configurable**: Headless/headed, timezone, locale

---

## How It Works (flow)

1. Load session from `foodics_storage.json`
2. Navigate to **Inventory → Quantity Adjustments**
3. Open **New Quantity Adjustment**
4. Select **Branch** & **Reason**
5. **Save** (lands on details page)
6. **Upload CSV** and **Save** again

## Project Layout (suggested)

├─ foodics_bootstrap_sb.py        
# one-time login; saves session JSON
├─ foodics_run_from_state_sb.py   
# main runner; loads session & uploads CSVs
├─ foodics_storage.json           
# saved session (DO NOT COMMIT)
└─ csvs/
   ├─ Quantity Adjustment (Expired).csv
   └─ Quantity Adjustment (Waste Production).csv
