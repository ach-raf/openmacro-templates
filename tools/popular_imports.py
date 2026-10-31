#!/usr/bin/env python3
"""Templates drawn from the most-used automations of iPhone Shortcuts, MacroDroid and Tasker.

Sources surveyed 2026-10-31: guidingtech "best iPhone automation ideas", switchingtomac "20 easy
iPhone automations", hongkiat "automate Android with MacroDroid", Apple's Shortcuts personal
automation triggers (battery, charger, app open/close, arrive/leave, time of day, Focus/Sleep),
plus the IFTTT applets from the user's list. Each is re-authored with engine-runnable classes only.

Branching on which trigger fired uses TriggerThatInvokedConstraint with m_triggerIndex.
"""

ADDED = "2026-10-31"
WEEKDAYS = [False, True, True, True, True, True, False]


def register(T, A, Template, var_str, var_bool, var_dict, var_dec, item):
    def var(name, t):
        return {"m_name": name, "m_type": t}

    def tpl(tid, name, category, description, tags, triggers, actions, **kw):
        A(Template(tid, name, category, description, ["popular"] + tags, triggers, actions,
                   added=ADDED, **kw))

    def which(siguid, index):
        return ("TriggerThatInvokedConstraint", {"m_triggerIndex": index})

    def app_trigger(siguid, launched, packages):
        return item("ApplicationLaunchedTrigger", siguid, {
            "m_launched": launched, "m_packageNameList": packages, "usePackageNameOption": 0,
            "isAllApps": False, "excludeMode": False})

    def media_volume(siguid, percent):
        return item("SetVolumeAction", siguid, {
            "m_streamIndexArray": [False, True, False, False, False, False, False, False],
            "m_streamVolumeArray": [0, percent, 0, 0, 0, 0, 0, 0], "m_volume": -1})

    def home_trigger(siguid, enter):
        return item("LocationTrigger", siguid, {"m_enterArea": enter, "m_geofenceId": "home",
                                                "m_newTriggerFromUnknown": 1, "m_latitude": 52.52,
                                                "m_longitude": 13.405, "m_radius": 150})

    def work_trigger(siguid, enter):
        return item("LocationTrigger", siguid, {"m_enterArea": enter, "m_geofenceId": "work",
                                                "m_newTriggerFromUnknown": 1, "m_latitude": 52.50,
                                                "m_longitude": 13.30, "m_radius": 150})

    def at(siguid, hour, minute=0, days=None):
        return item("TimerTrigger", siguid, {"m_hour": hour, "m_minute": minute, "m_second": 0,
                                             "m_daysOfWeek": days or [True] * 7, "m_useAlarm": True})

    # ---- Apps -----------------------------------------------------------------------------
    tpl("streaming-app-dnd", "Do Not Disturb while streaming", "Apps",
        "Opening Netflix turns Do Not Disturb on so calls and pings do not interrupt the show; "
        "closing it turns Do Not Disturb off again. Swap the package name for YouTube "
        "(com.google.android.youtube), Disney+ or any video app.",
        ["netflix", "dnd", "video", "focus"],
        [app_trigger(1, True, ["com.netflix.mediaclient"]), app_trigger(2, False, ["com.netflix.mediaclient"])],
        [item("IfConditionAction", 3, constraints=[which(3, 0)]),
         item("SetPriorityMode", 4, {"m_option": 3}),
         item("ElseAction", 5),
         item("SetPriorityMode", 6, {"m_option": 0}),
         item("EndIfAction", 7)],
        needs=["Accessibility service", "Do not disturb access"])

    tpl("streaming-app-rotate", "Unlock rotation in video apps", "Apps",
        "Auto-rotate switches on while Netflix is open and off again when you leave it, so the "
        "phone stays portrait everywhere else. Change the package for any video app.",
        ["netflix", "rotation", "video"],
        [app_trigger(1, True, ["com.netflix.mediaclient"]), app_trigger(2, False, ["com.netflix.mediaclient"])],
        [item("IfConditionAction", 3, constraints=[which(3, 0)]),
         item("SetAutoRotateAction", 4, {"m_state": 0}),
         item("ElseAction", 5),
         item("SetAutoRotateAction", 6, {"m_state": 1}),
         item("EndIfAction", 7)],
        needs=["Accessibility service"])

    tpl("focus-hours-app-blocker", "Block distracting apps in work hours", "Apps",
        "Between 09:00 and 17:00 on weekdays, opening Instagram, TikTok or Facebook sends you "
        "straight back to the home screen with a reminder. Edit the package list to taste.",
        ["focus", "productivity", "apps", "block"],
        [item("ApplicationLaunchedTrigger", 1, {
            "m_launched": True, "usePackageNameOption": 0, "isAllApps": False, "excludeMode": False,
            "m_packageNameList": ["com.instagram.android", "com.zhiliaoapp.musically",
                                  "com.facebook.katana"]})],
        [item("LaunchHomeScreenAction", 2, {"useAccessibilityService": True}),
         item("ToastAction", 3, {"m_messageText": "Focus hours - back to work", "m_duration": 2})],
        constraints=[("TimeOfDayConstraint", {"m_startHour": 9, "m_startMinute": 0,
                                              "m_endHour": 17, "m_endMinute": 0}),
                     ("DayOfWeekConstraint", {"m_daysOfWeek": WEEKDAYS})],
        needs=["Accessibility service"])

    # ---- Battery & charging ---------------------------------------------------------------
    tpl("charge-80-reminder", "Unplug reminder at 80%", "Battery",
        "While charging, a notification tells you when the battery reaches 80% so you can unplug "
        "and keep the battery healthier (a popular Apple Shortcuts automation).",
        ["battery", "charging", "health"],
        [item("BatteryLevelTrigger", 1, {"m_option": 0, "m_batteryLevel": 80, "m_decreasesTo": False})],
        [item("NotificationAction", 2, {"m_notificationSubject": "Battery at 80%",
                                        "m_notificationText": "Unplug the charger to protect the battery"})],
        constraints=[("ExternalPowerConstraint", {"m_externalPower": True,
                                                  "m_powerConnectedOptions": [True, True, True]})])

    tpl("charger-start-music", "Play music when charging starts", "Car & Audio",
        "Plugging in the charger resumes your music player - handy at the desk or in the car.",
        ["charger", "music", "media"],
        [item("ExternalPowerTrigger", 1, {"m_powerConnected": True, "m_powerConnectedOptions": [True, True, True]})],
        [item("ControlMediaAction", 2, {"optionInt": 3, "m_simulateMediaButton": True})])

    tpl("low-battery-sos-sms", "Low battery: text my location", "Safety",
        "When the battery falls to 5%, your location is texted to someone you trust so they know "
        "where you were. Put their number in the action.",
        ["battery", "sos", "location", "sms"],
        [item("BatteryLevelTrigger", 1, {"m_option": 0, "m_batteryLevel": 5, "m_decreasesTo": True})],
        [item("ForceLocationUpdateAction", 2, {"timeoutSeconds": 20, "blockNextAction": True,
                                               "dictionaryVariableName": "loc"}),
         item("SendSMSAction", 3, {"m_number": "+10000000000",
                                   "m_messageContent": "Battery at 5%. Last location: "
                                                       "https://maps.google.com/?q={lv=loc[latitude]},{lv=loc[longitude]}"})],
        variables=[var_dict("loc")],
        needs=["SMS permission", "Location permission"])

    # ---- Places ---------------------------------------------------------------------------
    tpl("leave-home-directions", "Directions to work when I leave home", "Location",
        "On weekday mornings (6-10) leaving home opens driving directions to your workplace. Edit "
        "the destination in the link and the coordinates in the trigger.",
        ["directions", "commute", "maps", "location"],
        [home_trigger(1, False)],
        [item("OpenWebPageAction", 2, {"m_urlToOpen": "https://www.google.com/maps/dir/?api=1&destination=Work&travelmode=driving",
                                       "m_httpGet": False})],
        constraints=[("TimeOfDayConstraint", {"m_startHour": 6, "m_startMinute": 0, "m_endHour": 10, "m_endMinute": 0}),
                     ("DayOfWeekConstraint", {"m_daysOfWeek": WEEKDAYS})],
        needs=["Location permission"])

    tpl("work-always-on-display", "Always-on display at work", "Location",
        "Arriving at work turns the always-on display on so the clock is glanceable at the desk; "
        "leaving turns it off to save battery.",
        ["aod", "work", "location", "display"],
        [work_trigger(1, True), work_trigger(2, False)],
        [item("IfConditionAction", 3, constraints=[which(3, 0)]),
         item("AmbientDisplayAction", 4, {"m_settingOption": 1, "m_option": 0}),
         item("ElseAction", 5),
         item("AmbientDisplayAction", 6, {"m_settingOption": 1, "m_option": 1}),
         item("EndIfAction", 7)],
        needs=["Location permission"])

    tpl("arrive-home-music", "Music on when I get home", "Location",
        "Arriving home starts your music and bumps media volume to a comfortable level.",
        ["home", "music", "arrive"],
        [home_trigger(1, True)],
        [media_volume(2, 40), item("ControlMediaAction", 3, {"optionInt": 3, "m_simulateMediaButton": True})],
        needs=["Location permission"])

    # ---- Time -----------------------------------------------------------------------------
    tpl("school-hours-mute", "Silent during school or office hours", "Time & Focus",
        "Weekdays at 08:00 the phone goes silent with vibrate off, and at 15:30 it returns to normal "
        "sound. Change the two times to your schedule.",
        ["mute", "school", "office", "schedule"],
        [at(1, 8, 0, WEEKDAYS), at(2, 15, 30, WEEKDAYS)],
        [item("IfConditionAction", 3, constraints=[which(3, 0)]),
         item("SetVibrateAction", 4, {"m_optionInt": 0}),
         item("ElseAction", 5),
         item("SetVibrateAction", 6, {"m_optionInt": 1}),
         item("EndIfAction", 7)])

    tpl("monthly-rent-reminder", "Monthly rent reminder", "Time & Focus",
        "On the 1st of every month at 09:00 you get a reminder notification (IFTTT: rent "
        "reminders). Edit the text and day in the trigger for any monthly bill.",
        ["monthly", "reminder", "bills", "rent"],
        [item("DayTrigger", 1, {"m_option": 1, "m_dayOfMonth": 1, "m_hour": 9, "m_minute": 0,
                                "m_useAlarm": True})],
        [item("NotificationAction", 2, {"m_notificationSubject": "Rent due",
                                        "m_notificationText": "It is the 1st - time to pay the rent"})])

    tpl("wind-down-routine", "Bedtime wind-down", "Time & Focus",
        "At 22:00 the phone winds down: alarms-only Do Not Disturb, dark theme, dim screen. "
        "Pair with morning-dnd-off for the morning.",
        ["bedtime", "sleep", "night", "dnd"],
        [at(1, 22, 0)],
        [item("SetPriorityMode", 2, {"m_option": 3}),
         item("DarkThemeAction", 3, {"option": 0}),
         item("SetBrightnessAction", 4, {"setBrightnessValue": True, "m_brightnessPercent": 15}),
         item("ToastAction", 5, {"m_messageText": "Wind-down mode on", "m_duration": 2})],
        needs=["Do not disturb access"])

    tpl("sleep-mode-night-settings", "Night settings when sleep starts", "Time & Focus",
        "When the system enters sleep mode, Do Not Disturb (alarms only) and dark theme come on; "
        "when sleep ends everything returns to normal.",
        ["sleep", "night", "dnd", "dark"],
        [item("SleepTrigger", 1, {"option": 0}), item("SleepTrigger", 2, {"option": 1})],
        [item("IfConditionAction", 3, constraints=[which(3, 0)]),
         item("SetPriorityMode", 4, {"m_option": 3}),
         item("DarkThemeAction", 5, {"option": 0}),
         item("ElseAction", 6),
         item("SetPriorityMode", 7, {"m_option": 0}),
         item("DarkThemeAction", 8, {"option": 1}),
         item("EndIfAction", 9)],
        needs=["Do not disturb access"])

    # ---- Audio & notifications ------------------------------------------------------------
    tpl("headphones-volume-preset", "Safe volume when headphones connect", "Car & Audio",
        "Plugging in or connecting headphones sets media volume to a safe 35% so a loud video "
        "never blasts your ears.",
        ["headphones", "volume", "safety"],
        [item("HeadphonesTrigger", 1, {"m_headphonesConnected": True, "m_micOption": 0})],
        [media_volume(2, 35)])

    tpl("speak-notifications-headphones", "Read messages aloud on headphones", "Car & Audio",
        "With headphones connected, new WhatsApp, Telegram and Signal messages are spoken aloud "
        "(sender and text) so you never touch the phone.",
        ["tts", "notifications", "messages", "headphones"],
        [item("NotificationTrigger", 1, {
            "m_option": 0, "m_packageNameList": ["com.whatsapp", "org.telegram.messenger", "org.thoughtcrime.securesms"],
            "m_excludeApps": False, "m_ignoreOngoing": True})],
        [item("SpeakTextAction", 2, {"m_textToSay": "{notification_title} says {notification_text}",
                                     "m_skipEmojis": True})],
        constraints=[("HeadphonesConnectionConstraint", {"m_connected": True})],
        needs=["Notification listener access", "Text-to-speech engine"])

    tpl("announce-caller", "Announce who is calling", "Car & Audio",
        "Incoming calls are announced out loud with the caller's number, so you can tell who is "
        "ringing without looking at the phone.",
        ["call", "tts", "caller"],
        [item("IncomingCallTrigger", 1, {"m_option": 3})],
        [item("SpeakTextAction", 2, {"m_textToSay": "Incoming call from {call_number}", "m_readNumbersIndividually": True})],
        needs=["Phone permission", "Text-to-speech engine"])

    # ---- Capture & clipboard --------------------------------------------------------------
    tpl("clipboard-history-log", "Clipboard history log", "Utilities",
        "Every time you copy something it is appended with the time to /sdcard/OpenMacro/clipboard.txt "
        "- a poor man's clipboard manager (a favourite 'underrated' iPhone shortcut).",
        ["clipboard", "history", "log"],
        [item("ClipboardChangeTrigger", 1, {"m_text": "", "isConfigured": True})],
        [item("WriteToFileAction", 2, {"m_logText": "{hour}:{minute} {clipboard_text}\n", "m_filename": "clipboard.txt",
                                       "m_append": True, "useAllFilesAccess": True,
                                       "allFilesPath": "/sdcard/OpenMacro"})],
        needs=["All-files access"])

    tpl("share-to-notes-file", "Share to a quick-notes file", "Utilities",
        "Pick OpenMacro in any app's Share sheet and the shared text or link is appended to "
        "/sdcard/OpenMacro/notes.txt (Apple Shortcuts' 'Save a web page to Notes').",
        ["share", "notes", "capture"],
        [item("ShareTextTrigger", 1, {})],
        [item("WriteToFileAction", 2, {"m_logText": "{year}-{month_digit}-{dayofmonth} {shared_text}\n",
                                       "m_filename": "notes.txt", "m_append": True, "useAllFilesAccess": True,
                                       "allFilesPath": "/sdcard/OpenMacro"}),
         item("ToastAction", 3, {"m_messageText": "Saved to notes", "m_duration": 2})],
        needs=["All-files access"])

    # ---- IFTTT leftovers ------------------------------------------------------------------
    tpl("ifttt-new-services-alert", "Tell me when IFTTT adds services", "Utilities",
        "Once a day the public IFTTT services list is fetched; if its size changed since the last "
        "check you get a notification (IFTTT: new service published). The first run only records "
        "the baseline.",
        ["ifttt", "services", "notification"],
        [at(1, 10, 0)],
        [item("HttpRequestAction", 2, {"requestConfig": {
            "urlToOpen": "https://ifttt.com/explore/services.json", "requestType": 0,
            "requestTimeOutSeconds": 60, "followRedirects": True, "saveResponseType": 1,
            "responseVariableName": "resp",
            "headerParams": [{"paramName": "User-Agent", "paramValue": "Mozilla/5.0"}]}}),
         item("TextManipulationAction", 3, {"m_text": "{strlen=resp}", "variableName": "newLen",
                                            "m_textManipulation": {"type": "TrimManipulation"}}),
         item("IfConditionAction", 4, constraints=[
             ("CompareValueConstraint", {"type": 1, "value1": "{lv=lastLen}", "value2": "0", "comparisonType": 3}),
             ("CompareValueConstraint", {"type": 1, "value1": "{lv=newLen}", "value2": "{lv=lastLen}",
                                         "comparisonType": 1})]),
         item("NotificationAction", 5, {"m_notificationSubject": "IFTTT",
                                        "m_notificationText": "The IFTTT services list changed - new services may be available"}),
         item("EndIfAction", 6),
         item("SetVariableAction", 7, {"m_variable": var("lastLen", 2), "m_newStringValue": "{lv=newLen}"})],
        variables=[var_str("resp"), var_str("newLen"), var_str("lastLen", "0")],
        needs=["Internet"])
