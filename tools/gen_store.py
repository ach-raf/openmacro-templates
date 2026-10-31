#!/usr/bin/env python3
"""Builds and validates the OpenMacro template store.

- Emits one `macros/<id>.macro` per template (MacroDroid-compatible wrapper format:
  {"macroExportVersion": 1, "macro": {...}}) — importable by OpenMacro's T-04 interop path.
- Emits `index.json` (the store catalog the in-app browser fetches).
- Validates every authored item against `tools/catalog-schema.json` — a snapshot of the
  OpenMacro catalog: which class types run, and the exact interop field names/enums per
  class. A template using an unknown field, unknown enum value or a fail-closed class
  fails the build.

Run:  python -I tools/gen_store.py
"""

import hashlib
import json
import os
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCHEMA_PATH = os.path.join(HERE, "catalog-schema.json")
MACROS_DIR = os.path.join(ROOT, "macros")
INDEX_PATH = os.path.join(ROOT, "index.json")

BASE_URL = "https://raw.githubusercontent.com/ach-raf/openmacro-templates/main"
INDEX_URL = BASE_URL + "/index.json"
AUTHOR = "openmacro"
TODAY = "2026-10-31"
ADDED_BASE = "2026-10-30"  # date the original 30 curated templates landed

GUID_BASE = 8800000100  # stable, store-collision-safe; the importer reassigns on clash


def every_day():
    return [True] * 7


def weekdays():
    """Monday..Friday enabled. Array is Sunday-first (engine convention)."""
    return [False, True, True, True, True, True, False]


def item(class_type, siguid, params=None, constraints=None):
    it = {
        "m_classType": class_type,
        "m_SIGUID": siguid,
        "m_isDisabled": False,
        "m_isOrCondition": False,
    }
    it.update(params or {})
    if constraints:
        it["m_constraintList"] = [
            item(c[0], siguid * 1000 + i + 1, c[1] if len(c) > 1 else None)
            for i, c in enumerate(constraints)
        ]
    return it


class Template:
    def __init__(self, tid, name, category, description, tags, triggers, actions,
                 constraints=None, variables=None, needs=None, author=None, added=None):
        self.id = tid
        self.name = name
        self.category = category
        self.description = description
        self.tags = tags
        self.triggers = triggers
        self.actions = actions
        # Macro-level constraints are authored as (classType, params) tuples; normalize them
        # to stored items here so validate()/counts()/macro_json() all see the same shape.
        self.constraints = [
            item(c[0], 900000 + i + 1, c[1] if len(c) > 1 else None)
            for i, c in enumerate(constraints or [])
        ]
        self.variables = variables or []
        self.needs = needs or []
        self.author = author or AUTHOR
        self.added = added or ADDED_BASE

    def macro_json(self, guid):
        macro = {
            "m_GUID": guid,
            "m_name": self.name,
            "m_description": self.description,
            "m_category": self.category,
            "m_enabled": True,
            "m_completed": True,
            "m_isOrCondition": False,
            "m_triggerList": self.triggers,
            "m_actionList": self.actions,
            "m_constraintList": self.constraints,
        }
        if self.variables:
            macro["localVariables"] = self.variables
        return {"macroExportVersion": 1, "macro": macro}


def var_str(name, value=""):
    return {"m_name": name, "m_type": 2, "m_stringValue": value}


def var_bool(name, value=False):
    return {"m_name": name, "m_type": 0, "m_booleanValue": value}


def var_dict(name):
    return {"m_name": name, "m_type": 4, "dictionary": {}}


def var_dec(name):
    return {"m_name": name, "m_type": 3, "m_decimalValue": 0}


# ---------------------------------------------------------------------------
# The 30 templates. Field names and enum codes are verbatim interop data,
# validated against OpenMacro's catalog (classes that RUN, not fail-closed).
# ---------------------------------------------------------------------------

T = []
A = T.append

# ---- Battery ----
A(Template(
    "battery-saver-auto-on", "Battery saver auto-on", "Battery",
    "Turns battery saver on by itself when the battery drops to 20%, so you never run "
    "out of power because you forgot to flip the switch.",
    ["battery", "battery saver", "power", "automatic"],
    [item("BatteryLevelTrigger", 1, {"m_option": 0, "m_batteryLevel": 20, "m_decreasesTo": True})],
    [item("BatterySaverAction", 2, {"m_option": 0}),
     item("ToastAction", 3, {"m_messageText": "Battery below 20% — battery saver enabled", "m_duration": 2})],
))
A(Template(
    "battery-full-alert", "Battery full alert", "Battery",
    "Vibrates and notifies you when the battery reaches 95% while charging, so you can "
    "unplug in time and go easy on the cell.",
    ["battery", "charging", "notification"],
    [item("BatteryLevelTrigger", 1, {"m_option": 0, "m_batteryLevel": 95, "m_decreasesTo": False})],
    [item("VibrateAction", 2, {"m_vibratePattern": 1}),
     item("NotificationAction", 3, {"m_notificationSubject": "Battery almost full",
                                    "m_notificationText": "Battery is at 95% or more — you can unplug the charger."})],
    constraints=[("ExternalPowerConstraint", {"m_externalPower": True})],
    needs=["Battery (none)"],
))
A(Template(
    "low-battery-warning", "Low battery warning", "Battery",
    "Notifies and buzzes when the battery falls below 15% and the phone is not charging.",
    ["battery", "warning", "notification"],
    [item("BatteryLevelTrigger", 1, {"m_option": 0, "m_batteryLevel": 15, "m_decreasesTo": True})],
    [item("VibrateAction", 2, {"m_vibratePattern": 2}),
     item("NotificationAction", 3, {"m_notificationSubject": "Low battery",
                                    "m_notificationText": "Battery below 15% — enable battery saver or find a charger."})],
    constraints=[("ExternalPowerConstraint", {"m_externalPower": False})],
))
A(Template(
    "overnight-quiet-charge", "Overnight quiet charging", "Battery",
    "Plugs in at night: switches the phone to alarms-only (Do not disturb) and dims the "
    "screen while the charge runs between 22:00 and 07:00.",
    ["charging", "do not disturb", "night", "sleep"],
    [item("ExternalPowerTrigger", 1, {"m_powerConnected": True, "m_powerConnectedOptions": [True, True, True]})],
    [item("SetPriorityMode", 2, {"m_option": 3}),
     item("SetBrightnessAction", 3, {"setBrightnessValue": True, "m_brightnessPercent": 30})],
    constraints=[("TimeOfDayConstraint", {"m_startHour": 22, "m_startMinute": 0, "m_endHour": 7, "m_endMinute": 0})],
    needs=["Do not disturb access"],
))
A(Template(
    "overnight-quiet-restore", "Overnight quiet — restore on unplug", "Battery",
    "The counterpart to 'Overnight quiet charging': unplugging the charger ends alarms-only "
    "mode and puts brightness back to adaptive.",
    ["charging", "do not disturb", "night", "restore"],
    [item("ExternalPowerTrigger", 1, {"m_powerConnected": False, "m_powerConnectedOptions": [True, True, True]})],
    [item("SetPriorityMode", 2, {"m_option": 0}),
     item("SetBrightnessAction", 3, {"setAutoBrightness": True, "autoBrightnessOn": True})],
    needs=["Do not disturb access"],
))
A(Template(
    "saver-dark-theme-on", "Dark theme with battery saver (on)", "Battery",
    "Battery saver switched on? The system dark theme comes with it — easy on the eyes and "
    "the battery at the same time.",
    ["battery saver", "dark theme", "battery"],
    [item("BatterySaverTrigger", 1, {"m_option": 0})],
    [item("DarkThemeAction", 2, {"option": 0})],
))
A(Template(
    "saver-dark-theme-off", "Dark theme with battery saver (off)", "Battery",
    "When battery saver turns off again, dark theme is switched back off.",
    ["battery saver", "dark theme", "battery"],
    [item("BatterySaverTrigger", 1, {"m_option": 1})],
    [item("DarkThemeAction", 2, {"option": 1})],
))

# ---- Time & focus ----
A(Template(
    "bedtime-alarms-only", "Bedtime — alarms only", "Time & Focus",
    "Every night at 23:00 the phone goes to alarms-only (Do not disturb). Alarms still "
    "ring, everything else stays quiet.",
    ["bedtime", "do not disturb", "sleep", "schedule"],
    [item("TimerTrigger", 1, {"m_hour": 23, "m_minute": 0, "m_second": 0,
                              "m_daysOfWeek": every_day(), "m_useAlarm": True})],
    [item("SetPriorityMode", 2, {"m_option": 3})],
    needs=["Do not disturb access"],
))
A(Template(
    "morning-dnd-off", "Morning — end do not disturb", "Time & Focus",
    "Every morning at 07:00 do not disturb is switched off and the phone is audible again.",
    ["morning", "do not disturb", "sleep", "schedule"],
    [item("TimerTrigger", 1, {"m_hour": 7, "m_minute": 0, "m_second": 0,
                              "m_daysOfWeek": every_day(), "m_useAlarm": True})],
    [item("SetPriorityMode", 2, {"m_option": 0})],
    needs=["Do not disturb access"],
))
A(Template(
    "hydrate-reminder", "Hourly water reminder", "Time & Focus",
    "A gentle notification every hour between 09:00 and 21:00 reminding you to drink "
    "water — the classic health nudge.",
    ["health", "reminder", "water", "hourly"],
    [item("RegularIntervalTrigger", 1, {"m_seconds": 3600})],
    [item("NotificationAction", 2, {"m_notificationSubject": "Hydration reminder",
                                    "m_notificationText": "Time for a glass of water."})],
    constraints=[("TimeOfDayConstraint", {"m_startHour": 9, "m_startMinute": 0, "m_endHour": 21, "m_endMinute": 0})],
))
A(Template(
    "evening-journal-prompt", "Evening journal prompt", "Time & Focus",
    "At 21:30 a notification asks how your day was — the journaling habit, borrowed from "
    "the most-saved Apple Shortcuts.",
    ["journal", "evening", "habit", "reminder"],
    [item("TimerTrigger", 1, {"m_hour": 21, "m_minute": 30, "m_second": 0,
                              "m_daysOfWeek": every_day(), "m_useAlarm": True})],
    [item("NotificationAction", 2, {"m_notificationSubject": "Journal time",
                                    "m_notificationText": "How was your day? Write three lines before bed."})],
))

# ---- Location ----
A(Template(
    "wifi-on-home", "Wi-Fi on when arriving home", "Location",
    "When you enter your home area, Wi-Fi switches on automatically. Edit the trigger to "
    "set your own coordinates and radius.",
    ["location", "wifi", "home", "geofence"],
    [item("LocationTrigger", 1, {"m_enterArea": True, "m_geofenceId": "home",
                                 "m_newTriggerFromUnknown": 1,
                                 "m_latitude": 52.52, "m_longitude": 13.405, "m_radius": 150})],
    [item("SetWifiAction", 2, {"m_state": 0}),
     item("ToastAction", 3, {"m_messageText": "Welcome home — Wi-Fi on", "m_duration": 2})],
    needs=["Location permission"],
))
A(Template(
    "wifi-off-away", "Wi-Fi off when leaving home", "Location",
    "When you leave your home area, Wi-Fi switches off to save battery. Edit the trigger "
    "to set your own coordinates and radius.",
    ["location", "wifi", "home", "geofence"],
    [item("LocationTrigger", 1, {"m_enterArea": False, "m_geofenceId": "home",
                                 "m_newTriggerFromUnknown": 1,
                                 "m_latitude": 52.52, "m_longitude": 13.405, "m_radius": 150})],
    [item("SetWifiAction", 2, {"m_state": 1}),
     item("ToastAction", 3, {"m_messageText": "Leaving — Wi-Fi off", "m_duration": 2})],
    needs=["Location permission"],
))
A(Template(
    "work-silent-on", "Work mode — silence on office Wi-Fi", "Location",
    "Detecting your office Wi-Fi switches the phone to silent+vibrate. Replace the SSID "
    "with your workplace network.",
    ["wifi", "work", "silent", "meeting"],
    [item("WifiSSIDTrigger", 1, {"m_SSID": "YourWorkWifi", "m_InRange": True})],
    [item("SetVibrateAction", 2, {"m_optionInt": 0}),
     item("ToastAction", 3, {"m_messageText": "Work mode — silenced", "m_duration": 2})],
    needs=["Location permission (Wi-Fi SSID)"],
))
A(Template(
    "work-silent-off", "Work mode — leave office Wi-Fi", "Location",
    "Losing your office Wi-Fi restores the normal loud ringer. Replace the SSID with your "
    "workplace network.",
    ["wifi", "work", "ringer", "restore"],
    [item("WifiSSIDTrigger", 1, {"m_SSID": "YourWorkWifi", "m_InRange": False})],
    [item("SetVibrateAction", 2, {"m_optionInt": 1})],
    needs=["Location permission (Wi-Fi SSID)"],
))

# ---- Connectivity ----
A(Template(
    "bluetooth-auto-off", "Bluetooth auto-off", "Connectivity",
    "When no Bluetooth device has been connected for 5 minutes, Bluetooth switches off to "
    "save battery.",
    ["bluetooth", "battery", "idle"],
    [item("BluetoothTrigger", 1, {"m_btState": 3, "m_anyDevice": True})],
    [item("PauseAction", 2, {"m_delayInSeconds": 300}),
     item("SetBluetoothAction", 3, {"m_state": 1},
          constraints=[("BluetoothConstraint", {"m_btState": 3, "m_anyDevice": True})])],
    needs=["Bluetooth permission (Android 12+)"],
))

# ---- Car & audio ----
A(Template(
    "car-mode", "Car mode — maps + greeting", "Car & Audio",
    "When your phone pairs with the car, Google Maps opens and a voice wishes you a safe "
    "drive. Set your head unit's Bluetooth name in the trigger.",
    ["car", "bluetooth", "driving", "maps"],
    [item("BluetoothTrigger", 1, {"m_btState": 2, "m_deviceName": "YourCar", "m_anyDevice": False})],
    [item("LaunchActivityAction", 2, {"option": 1,
                                      "m_packageToLaunch": "com.google.android.apps.maps",
                                      "m_applicationName": "Maps"}),
     item("SpeakTextAction", 3, {"m_textToSay": "Connected to the car. Have a safe drive."})],
    needs=["Bluetooth permission (Android 12+)", "Text-to-speech engine"],
))
A(Template(
    "headphones-autoplay", "Headphones in — launch music", "Car & Audio",
    "Plugging in headphones opens your music app straight away — the Tasker classic. Set "
    "your preferred app's package in the action.",
    ["headphones", "music", "audio"],
    [item("HeadphonesTrigger", 1, {"m_headphonesConnected": True, "m_micOption": 0})],
    [item("LaunchActivityAction", 2, {"option": 1,
                                      "m_packageToLaunch": "com.spotify.music",
                                      "m_applicationName": "Spotify"})],
))
A(Template(
    "headphones-pause", "Headphones out — pause", "Car & Audio",
    "Unplugging the headphones pauses whatever is playing — no more music blasting from "
    "the speaker.",
    ["headphones", "music", "pause"],
    [item("HeadphonesTrigger", 1, {"m_headphonesConnected": False, "m_micOption": 0})],
    [item("ControlMediaAction", 2, {"optionInt": 4})],
))
A(Template(
    "screen-off-pause-music", "Screen off — pause music", "Car & Audio",
    "Locking the screen pauses media playback — handy for podcasts you keep losing track "
    "of.",
    ["screen", "music", "pause", "podcast"],
    [item("ScreenOnOffTrigger", 1, {"m_screenOn": False})],
    [item("ControlMediaAction", 2, {"optionInt": 4})],
))

# ---- Gestures ----
A(Template(
    "flip-to-silence", "Flip to silence a call", "Gestures",
    "Turn the phone face-down while a call is ringing to silence it — the classic "
    "flip-to-mute, no button needed.",
    ["call", "silence", "gesture", "flip"],
    [item("FlipDeviceTrigger", 1, {"m_faceDown": True, "m_workWithScreenOff": True})],
    [item("SetVibrateAction", 2, {"m_optionInt": 0},
          constraints=[("InCallConstraint", {"m_inCall": True})]),
     item("ToastAction", 3, {"m_messageText": "Flipped — call silenced", "m_duration": 2})],
))
A(Template(
    "shake-torch", "Shake to toggle flashlight", "Gestures",
    "Shake the phone to toggle the flashlight — find the keyhole without unlocking.",
    ["flashlight", "torch", "shake", "gesture"],
    [item("ShakeDeviceTrigger", 1)],
    [item("CameraFlashLightAction", 2, {"m_state": 2})],
    needs=["Camera flash unit"],
))
A(Template(
    "power-quick-camera", "Double-press power for camera", "Gestures",
    "Press the power button twice to open the camera — like the stock shortcut, built "
    "from a trigger that counts screen-off toggles.",
    ["camera", "power button", "gesture", "quick"],
    [item("PowerButtonToggleTrigger", 1, {"m_numToggles": 2})],
    [item("LaunchActivityAction", 2, {"option": 1,
                                      "m_packageToLaunch": "com.android.camera2",
                                      "m_applicationName": "Camera"})],
))
A(Template(
    "widget-torch-button", "Home-screen torch button", "Gestures",
    "Add this macro's widget to your home screen for a one-tap flashlight toggle.",
    ["widget", "flashlight", "torch", "home screen"],
    [item("WidgetPressedTrigger", 1, {"m_widgetType": 0, "m_widgetLabel": "Torch"})],
    [item("CameraFlashLightAction", 2, {"m_state": 2})],
    needs=["Home-screen widget", "Camera flash unit"],
))
A(Template(
    "widget-wifi-toggle", "Home-screen Wi-Fi button", "Gestures",
    "A home-screen widget that toggles Wi-Fi with one tap.",
    ["widget", "wifi", "toggle", "home screen"],
    [item("WidgetPressedTrigger", 1, {"m_widgetType": 0, "m_widgetLabel": "Wi-Fi"})],
    [item("SetWifiAction", 2, {"m_state": 2})],
    needs=["Home-screen widget"],
))

# ---- Safety ----
A(Template(
    "anti-theft-locate-reply", "Anti-theft: text 'locate' for GPS reply", "Safety",
    "Text this phone the word 'locate' and it replies by SMS with its current GPS "
    "coordinates — find a lost or stolen phone from any other phone.",
    ["security", "sms", "location", "anti-theft"],
    [item("IncomingSMSTrigger", 1, {"m_option": 3, "m_smsContent": "locate",
                                    "m_exactMatch": False, "ignoreCase": True})],
    [item("ForceLocationUpdateAction", 2, {"timeoutSeconds": 30, "blockNextAction": True,
                                           "dictionaryVariableName": "loc"}),
     item("SendSMSAction", 3, {"m_number": "{sms_number}",
                               "m_messageContent": "My current location: {lv=loc[latitude]}, {lv=loc[longitude]}"})],
    variables=[var_dict("loc")],
    needs=["SMS permission", "Fine location permission"],
))
A(Template(
    "driving-sms-autoreply", "Driving auto-reply", "Safety",
    "While a Bluetooth device is connected (your car), any incoming SMS gets an automatic "
    "reply sent from its notification — 'I'm driving'.",
    ["driving", "sms", "auto-reply", "bluetooth"],
    [item("IncomingSMSTrigger", 1, {"m_option": 3})],
    [item("NotificationReplyAction", 2, {"packageName": "", "matchText": "",
                                         "replyText": "I'm driving right now — I'll get back to you soon."})],
    constraints=[("BluetoothConstraint", {"m_btState": 2, "m_anyDevice": True})],
    needs=["Notification listener access", "Bluetooth permission (Android 12+)"],
))
A(Template(
    "quiet-hours-missed-call", "Quiet-hours missed call note", "Safety",
    "A missed call between 22:00 and 07:00 leaves you a notification, so overnight "
    "callers are never forgotten.",
    ["missed call", "night", "notification"],
    [item("CallMissedTrigger", 1)],
    [item("NotificationAction", 2, {"m_notificationSubject": "Missed call during quiet hours",
                                    "m_notificationText": "You missed a call overnight — maybe check who it was."})],
    constraints=[("TimeOfDayConstraint", {"m_startHour": 22, "m_startMinute": 0, "m_endHour": 7, "m_endMinute": 0})],
))

# ---- Utilities ----
A(Template(
    "weekly-data-usage", "Weekly mobile data report", "Utilities",
    "Every Monday at 08:00 the week's mobile data usage is measured and posted as a "
    "notification.",
    ["data usage", "report", "weekly", "network"],
    [item("TimerTrigger", 1, {"m_hour": 8, "m_minute": 0, "m_second": 0,
                              "m_daysOfWeek": [False, False, True, False, False, False, False],
                              "m_useAlarm": True})],
    [item("GetDataUsedAction", 2, {"networkType": 0, "unit": 2, "periodKind": 1,
                                   "calendarScope": 1, "variableName": "dataused"}),
     item("NotificationAction", 3, {"m_notificationSubject": "Weekly data usage",
                                    "m_notificationText": "Mobile data this week: {lv=dataused} GB"})],
    variables=[var_dec("dataused")],
    needs=["Usage access"],
))
A(Template(
    "morning-weather-briefing", "Morning weather briefing (TTS)", "Utilities",
    "Weekday mornings the phone fetches today's weather (Open-Meteo, no API key) and "
    "reads it aloud. Edit the URL to your own latitude/longitude.",
    ["weather", "morning", "tts", "briefing"],
    [item("TimerTrigger", 1, {"m_hour": 7, "m_minute": 30, "m_second": 0,
                              "m_daysOfWeek": weekdays(), "m_useAlarm": True})],
    [item("HttpRequestAction", 2, {
        "requestConfig": {
            "urlToOpen": "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41"
                         "&current=temperature_2m,apparent_temperature",
            "requestType": 0,
            "requestTimeOutSeconds": 30,
            "followRedirects": True,
            "saveResponseType": 1,
            "responseVariableName": "resp",
        }}),
     item("JsonParseAction", 3, {"stringVarName": "resp", "dictionaryVarName": "weather"}),
     item("SpeakTextAction", 4, {"m_textToSay": "Good morning. It is {lv=weather[current][temperature_2m]} degrees, "
                                                "feels like {lv=weather[current][apparent_temperature]} degrees."})],
    variables=[var_str("resp"), var_dict("weather")],
    needs=["Internet", "Text-to-speech engine"],
))

# BespredeL/MacroDroid imports (MIT; re-authored runnable cores, see bespredel_imports.py).
import sys
if HERE not in sys.path:  # python -I strips the script dir; restore it for sibling imports
    sys.path.insert(0, HERE)
import bespredel_imports
bespredel_imports.register(T, A, Template, var_str, var_bool, var_dict, var_dec, item)
del sys, bespredel_imports

# ---------------------------------------------------------------------------
# Build + validate
# ---------------------------------------------------------------------------

def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate(schema, templates):
    errors = []
    runnable = schema["runnable"]
    # params are nested per kind: {triggers: {class: [...]}, actions: {...}, constraints: {...}}
    kind_of = {"triggers": "TRIGGER", "actions": "ACTION", "constraints": "CONSTRAINT"}

    def check_item(kind, it, where):
        ct = it.get("m_classType")
        if ct not in runnable[kind]:
            errors.append(f"{where}: {kind} class '{ct}' is not runnable in OpenMacro")
            return
        known = schema["params"][kind].get(ct)
        if known is None:
            errors.append(f"{where}: no param schema for '{ct}'")
            return
        known_names = {p["n"] for p in known}
        enums = {p["n"]: p.get("e") for p in known if p.get("e")}
        for name, value in it.items():
            if name in ("m_classType", "m_SIGUID", "m_isDisabled", "m_isOrCondition", "m_constraintList"):
                continue
            if name not in known_names:
                errors.append(f"{where}: '{ct}' has unknown field '{name}'")
            if name in enums and isinstance(value, int) and str(value) not in enums[name] \
                    and value not in enums[name]:
                errors.append(f"{where}: '{ct}' field '{name}' = {value} is not a valid enum code {enums[name]}")

    for t in templates:
        where = t.id
        for i, tr in enumerate(t.triggers):
            check_item("triggers", tr, f"{where} trigger#{i}")
            for c in tr.get("m_constraintList", []):
                check_item("constraints", c, f"{where} trigger#{i} constraint")
        for i, ac in enumerate(t.actions):
            check_item("actions", ac, f"{where} action#{i}")
            for c in ac.get("m_constraintList", []):
                check_item("constraints", c, f"{where} action#{i} constraint")
        for i, c in enumerate(t.constraints):
            check_item("constraints", c, f"{where} macro constraint#{i}")
    return errors


def counts(schema, t):
    runnable = schema["runnable"]
    tr = len(t.triggers)
    ac = len(t.actions)
    co = len(t.constraints) + sum(len(i.get("m_constraintList", [])) for i in t.triggers + t.actions)
    all_items = t.triggers + t.actions + t.constraints \
        + [c for i in t.triggers + t.actions for c in i.get("m_constraintList", [])]
    runnable_all = set(runnable["triggers"]) | set(runnable["actions"]) | set(runnable["constraints"])
    supported_all = sum(1 for i in all_items if i["m_classType"] in runnable_all)
    return {
        "items": {"triggers": tr, "actions": ac, "constraints": co, "total": tr + ac + co},
        "supported": {"total": supported_all},
    }


def main():
    schema = load_schema()
    errors = validate(schema, T)
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(1)

    os.makedirs(MACROS_DIR, exist_ok=True)
    # Clean previous build output so removed templates disappear from the store too.
    for old in os.listdir(MACROS_DIR):
        if old.endswith(".macro"):
            os.remove(os.path.join(MACROS_DIR, old))

    index_entries = []
    for n, t in enumerate(T):
        guid = GUID_BASE + n + 1
        doc = t.macro_json(guid)
        payload = json.dumps(doc, ensure_ascii=False)
        fname = f"{t.id}.macro"
        path = os.path.join(MACROS_DIR, fname)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        c = counts(schema, t)
        index_entries.append({
            "id": t.id,
            "name": t.name,
            "author": t.author,
            "category": t.category,
            "description": t.description,
            "tags": t.tags,
            "file": f"macros/{fname}",
            "url": f"{BASE_URL}/macros/{fname}",
            "sha256": digest,
            "sizeBytes": len(payload.encode("utf-8")),
            "guid": guid,
            "added": t.added,
            "items": c["items"],
            "supportedTotal": c["supported"]["total"],
            "itemClasses": {
                "triggers": sorted({i["m_classType"] for i in t.triggers}),
                "actions": sorted({i["m_classType"] for i in t.actions}),
                "constraints": sorted({i["m_classType"] for i in t.constraints}),
            },
            "needs": t.needs,
        })

    index = {
        "version": 1,
        "generated": TODAY,
        "indexUrl": INDEX_URL,
        "templates": index_entries,
    }
    with open(INDEX_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"OK: {len(T)} templates written, index.json generated")
    for e in index_entries:
        print(f"  {e['id']:32s} {e['category']:14s} items={e['items']['total']:2d} supported={e['supportedTotal']:2d}")


if __name__ == "__main__":
    main()
