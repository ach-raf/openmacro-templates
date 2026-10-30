# openmacro-templates

The **OpenMacro template store** — a community collection of 30 ready-made automation
macros, curated from the most useful recipes of Apple Shortcuts, MacroDroid, Tasker and
IFTTT. No server, no accounts: this repo *is* the store. The OpenMacro app fetches
[`index.json`](index.json) from here and imports any template with one tap.

- **Store index (what the app fetches):** `https://raw.githubusercontent.com/ach-raf/openmacro-templates/main/index.json`
- **App:** [OpenMacro](https://github.com/ach-raf/openmacro) — open-source automation engine (clean-room, GPL-3)
- **License:** MIT (templates are data; the GPL-3 app consumes them fine)

## Categories (30 templates)

| Category | Templates |
|---|---|
| Battery | battery-saver-auto-on, battery-full-alert, low-battery-warning, overnight-quiet-charge, overnight-quiet-restore, saver-dark-theme-on, saver-dark-theme-off |
| Time & Focus | bedtime-alarms-only, morning-dnd-off, hydrate-reminder, evening-journal-prompt |
| Location | wifi-on-home, wifi-off-away, work-silent-on, work-silent-off |
| Connectivity | bluetooth-auto-off |
| Car & Audio | car-mode, headphones-autoplay, headphones-pause, screen-off-pause-music |
| Gestures | flip-to-silence, shake-torch, power-quick-camera, widget-torch-button, widget-wifi-toggle |
| Safety | anti-theft-locate-reply, driving-sms-autoreply, quiet-hours-missed-call |
| Utilities | weekly-data-usage, morning-weather-briefing |

Where the ideas come from: the Tasker official example profiles, the MacroDroid
community's "everyone should have" threads, and Apple Shortcuts' most-saved gallery
recipes (bedtime/focus routines, journaling prompts, charging automations), re-authored
from scratch as OpenMacro `.macro` files. Every template uses only blocks that **run** in
the current OpenMacro build — nothing ships that would log a fail-closed reason.

## Using a template

**In the app (recommended):** OpenMacro → **Store** tab → browse or search → tap a card →
**Add**. The template lands in your macro list like any imported macro; placeholders
(Wi-Fi SSID, coordinates, device names, package ids) are marked in each description.

**Manual import:** download `macros/<id>.macro` and import it via Data → Import. The
files are plain MacroDroid-compatible exports (`macroExportVersion: 1`).

**Customize after import:** each template's description tells you what to edit — typical
placeholders: `YourWorkWifi` (SSID), `YourCar` (Bluetooth name), `52.52, 13.405`
(home coordinates), `com.spotify.music` (app package).

## Contributing a template

No accounts, no server — **git is the moderation** (plan §8):

1. Export your macro from the OpenMacro editor (or hand-write one against the catalog).
2. Fork this repo, add `macros/<your-template>.macro`.
3. Regenerate the index: `python -I tools/gen_store.py` — but first add your template to
   the `T` list in `tools/gen_store.py` (id, name, category, description, tags, items)
   so it is validated and indexed. See `tools/catalog-schema.json` for the runnable-class
   sets and per-class field schemas the validator checks against.
4. Open a pull request. Review = validation passes + description is accurate.

Rules: original work only (do not republish someone else's macro without attribution),
no vendor assets or strings, templates must import cleanly on the current OpenMacro
release, and anything needing unusual grants (root, device admin, accessibility) must say
so in its `needs` list.

## Repo layout

```
macros/                 one .macro file per template (importable JSON)
index.json              the store catalog the app fetches (sha256-pinned entries)
tools/gen_store.py      builds + validates macros/ and index.json (python -I, no deps)
tools/catalog-schema.json  runnable-class sets + param schemas (snapshot of OpenMacro's catalog)
```

## Index schema (v1)

```jsonc
{
  "version": 1,
  "generated": "YYYY-MM-DD",
  "templates": [{
    "id": "...", "name": "...", "author": "...", "category": "...",
    "description": "...", "tags": ["..."],
    "file": "macros/<id>.macro", "url": "https://raw.githubusercontent.com/.../<id>.macro",
    "sha256": "<64 hex>", "sizeBytes": 1234, "guid": 8800000101, "added": "YYYY-MM-DD",
    "items": {"triggers": 1, "actions": 2, "constraints": 0, "total": 3},
    "supportedTotal": 3,
    "itemClasses": {"triggers": ["..."], "actions": ["..."], "constraints": ["..."]},
    "needs": ["SMS permission"]
  }]
}
```

`supportedTotal`/`itemClasses` power the app's support badge (full/partial, computed
against the app's own catalog before import). The schema intentionally leaves room for a
future `stats` block (comments, stars) — deferred per plan §8 until a hosted backend ever
exists.
