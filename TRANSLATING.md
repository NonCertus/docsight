# Translating DOCSight

DOCSight uses JSON-based translation files. This guide explains how to add a new language or improve an existing translation.

**Existing languages:** English (en), Deutsch (de), French (fr), Spanish (es)

## File Structure

Translations live in two places:

```
app/
  i18n/                          # Core UI strings (~500 keys)
    en.json                      # Source of truth
    de.json
    fr.json
    es.json
    template.json                # Empty skeleton for new languages
  modules/
    backup/i18n/                 # Module-specific strings
    bnetz/i18n/
    bqm/i18n/
    journal/i18n/
    mqtt/i18n/
    reports/i18n/
    smokeping/i18n/
    speedtest/i18n/
    weather/i18n/
```

Each `i18n/` directory contains:
- **`en.json`** -- the source of truth (all keys must exist here first)
- **`template.json`** -- auto-generated skeleton with empty values
- **`<lang>.json`** -- one file per language (e.g. `de.json`, `fr.json`)

## Adding a New Language

### 1. Copy the templates

Copy `template.json` to `<lang>.json` in **every** `i18n/` directory:

```bash
# Core
cp app/i18n/template.json app/i18n/pt.json

# All modules
for dir in app/modules/*/i18n/; do
  cp "$dir/template.json" "$dir/pt.json"
done
```

### 2. Fill in `_meta`

The core file (`app/i18n/<lang>.json`) must have a `_meta` block at the top:

```json
{
  "_meta": {
    "language_name": "Portugues",
    "flag": "\ud83c\uddf5\ud83c\uddf9"
  },
  "nav": "Navegacao",
  ...
}
```

- `language_name` is shown in the language picker.
- `flag` is a flag emoji for the language.

Module files do **not** have `_meta`.

### 3. Translate the values

Open `en.json` side-by-side and translate each value. Keep the keys unchanged.

```json
// en.json
"health_good": "Good",
"health_marginal": "Marginal",

// pt.json
"health_good": "Bom",
"health_marginal": "Marginal",
```

**Important rules:**

- Translate **values only**, never keys.
- Keep HTML tags (e.g. `<b>`, `<a href='...'>`) intact.
- Keep placeholders like `{dir}`, `{count}`, `{0}`, `{1}`, `{name}` intact.
- Arrays (like `month_names` and `isp_options`) must have the **same number of elements** as `en.json`. Translate each element in order.

```json
// en.json
"month_names": ["January", "February", ..., "December"],

// pt.json
"month_names": ["Janeiro", "Fevereiro", ..., "Dezembro"],
```

### 4. Validate

Run the validation script to check for missing or extra keys:

```bash
python scripts/i18n_check.py --validate
```

A clean run prints:

```
All <N> language file(s) are in sync with en.json.
```

If keys are missing or extra, the script tells you exactly which ones.

### 5. Test locally

Run DOCSight and switch to your language in **Settings > Language**. Walk through the main views to check for truncation, missing strings, or formatting issues.

### 6. Submit a pull request

Create a PR with your `<lang>.json` files. The title should be something like `i18n: add Portuguese translation`. No other files need to change -- the language picker detects new files automatically.

## Updating an Existing Translation

When new keys are added to `en.json`, existing translations will be missing those keys. Run validation to find them:

```bash
python scripts/i18n_check.py --validate
```

Then add the missing keys to each affected language file.

## Regenerating Templates

If you add keys to `en.json`, regenerate all `template.json` files:

```bash
python scripts/i18n_check.py --generate
```

This overwrites every `template.json` with an empty skeleton matching the current `en.json`.

## Tips

- **Start with the core file.** It has ~500 keys and covers the entire UI. Module files are small (5-10 keys each).
- **`en.json` is always the source of truth.** Never add a key to a translation file that does not exist in `en.json`.
- **Partial translations work.** Missing keys fall back to English at runtime, so you can submit an incomplete translation and improve it later.
- **Use a JSON-aware editor** to catch syntax errors (trailing commas, missing quotes) before committing.
