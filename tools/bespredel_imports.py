#!/usr/bin/env python3
"""Imports of the BespredeL/MacroDroid macro collection (MIT, github.com/BespredeL/MacroDroid).

Each entry re-authors one upstream macro as a compact, fully runnable OpenMacro template:
English description, only catalog-validated classes/fields, and the changes needed to make
it work spelled out in the description + `needs`. Attribution: author "BespredeL".

Authoring notes (engine-verified 2026-10-31):
- TriggerThatInvokedConstraint uses m_triggerIndex (0-based position in m_triggerList).
- {vol_music} etc. resolve to percent (0..100) and SetVolume m_variables consumes percent.
- OptionDialog m_actionToRunJson holds one inline action as a JSON object string.
- {lv=var[key]} dictionary navigation is the supported way to read webhook JSON (no JS).
"""

TOGGLE_FLASH_IF_DARK = ("LightLevelConstraint", {"m_option": 0, "m_lightLevel": 50, "m_lightLevelFloat": 50.0})

SCREEN_CONTENT_SKIP = {
    "textToMatch": "Skip", "ignoreCase": True, "packageNameList": ["com.google.android.youtube"],
}
SCREEN_CONTENT_AD_LABEL = {
    "textToMatch": "Visit advertiser", "ignoreCase": True,
    "packageNameList": ["com.google.android.youtube"],
}
YOUTUBE_FOREGROUND = ("ActiveApplicationConstraint", {
    "m_active": True, "m_foreground": True,
    "m_packageNameList": ["com.google.android.youtube"],
})


REJECT_CALL_INLINE = '{"m_classType":"RejectCallAction","m_SIGUID":990001,"m_isDisabled":false,"m_isOrCondition":false}'


def register(T, A, Template, var_str, var_bool, var_dict, var_dec, item):
    def tg_send(siguid, text, chat_id="{lv=tg[message][chat][id]}"):
        """Telegram sendMessage as a GET with URL-encoded query params (no POST body needed)."""
        return item("HttpRequestAction", siguid, {
            "requestConfig": {
                "urlToOpen": "https://api.telegram.org/bot{lv=botToken}/sendMessage",
                "requestType": 0,
                "requestTimeOutSeconds": 30,
                "followRedirects": True,
                "queryParams": [
                    {"paramName": "chat_id", "paramValue": chat_id},
                    {"paramName": "text", "paramValue": text},
                ],
            }})

    # ---- Gestures / audio -----------------------------------------------------------------
    A(Template(
        "media-volume-hold-mute", "Hold volume button — mute/restore media", "Gestures",
        "Long-press a volume button to mute media instantly; long-press again to restore the "
        "exact level you had (ported from BespredeL's Fast Media Vol.). The current level is "
        "remembered in the 'level' variable, so mute/restore round-trips perfectly.",
        ["volume", "media", "mute", "gesture", "bespredel"],
        [item("VolumeButtonTrigger", 1, {"m_option": 3, "m_dontChangeVolume": True}),
         item("VolumeButtonTrigger", 2, {"m_option": 2, "m_dontChangeVolume": True})],
        [item("IfConditionAction", 3, constraints=[("MacroDroidVariableConstraint", {
            "m_variable": {"m_name": "muted", "m_type": 0}, "m_booleanValue": False})]),
         item("SetVariableAction", 4, {"m_variable": {"m_name": "level", "m_type": 2},
                                       "m_newStringValue": "{vol_music}"}),
         item("SetVolumeAction", 5, {"m_streamIndexArray": [False, True, False, False, False, False, False, False],
                                     "m_streamVolumeArray": [0, 0, 0, 0, 0, 0, 0, 0], "m_volume": -1}),
         item("SetVariableAction", 6, {"m_variable": {"m_name": "muted", "m_type": 0}, "m_newBooleanValue": True}),
         item("ToastAction", 7, {"m_messageText": "Media muted at {lv=level}% — hold a volume button again to restore",
                                 "m_duration": 2}),
         item("ElseIfConditionAction", 8, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "muted", "m_type": 0}, "m_booleanValue": True})]),
         item("SetVolumeAction", 9, {"m_streamIndexArray": [False, True, False, False, False, False, False, False],
                                     "m_streamVolumeArray": [0, 60, 0, 0, 0, 0, 0, 0], "m_volume": -1,
                                     "m_variables": [None, {"m_name": "level", "m_type": 2}, None, None,
                                                     None, None, None, None]}),
         item("SetVariableAction", 10, {"m_variable": {"m_name": "muted", "m_type": 0}, "m_newBooleanValue": False}),
         item("ToastAction", 11, {"m_messageText": "Media volume restored to {lv=level}%", "m_duration": 2}),
         item("EndIfAction", 12)],
        variables=[var_str("level"), var_bool("muted")],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "shake-flashlight-dark", "Shake flashlight (dark only)", "Gestures",
        "Shake the phone to toggle the flashlight — but only when it matters: the macro only "
        "reacts while the screen is on, the device is locked and the phone is not face-down on "
        "a table (ported from BespredeL's Flashlight). In daylight a shake turns the torch "
        "back off so it never burns in your pocket.",
        ["flashlight", "torch", "shake", "gesture", "dark", "bespredel"],
        [item("ShakeDeviceTrigger", 1)],
        [item("VibrateAction", 2, {"m_vibratePattern": 12}),
         item("IfConditionAction", 3, constraints=[TOGGLE_FLASH_IF_DARK]),
         item("CameraFlashLightAction", 4, {"m_state": 2}),
         item("ElseAction", 5),
         item("CameraFlashLightAction", 6, {"m_state": 1}),
         item("EndIfAction", 7)],
        constraints=[("ScreenOnOffConstraint", {"m_screenOn": True}),
                     ("DeviceLockedConstraint", {"m_locked": True}),
                     ("ProximitySensorConstraint", {"m_near": False})],
        needs=["Camera flash unit", "Light sensor"],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "shake-contact-qr", "Shake for contact QR", "Gestures",
        "Shake the phone on your home screen and a QR code with your contact details appears "
        "full-screen — let people scan you instead of dictating numbers (ported from "
        "BespredeL's ShakeContacts). Change the qrText in the action to your number or link: "
        "tel:+10000000000, https://t.me/yourhandle or https://wa.me/10000000000.",
        ["qr", "contact", "share", "shake", "gesture", "bespredel"],
        [item("ShakeDeviceTrigger", 1)],
        [item("VibrateAction", 2, {"m_vibratePattern": 1}),
         item("GenerateQRCodeAction", 3, {"qrText": "tel:+10000000000", "displayMode": 0,
                                          "fullScreenMode": True, "themeMode": 0}),
         item("ToastAction", 4, {"m_messageText": "Edit the QR text in the macro to share your details",
                                 "m_duration": 2})],
        constraints=[("ScreenOnOffConstraint", {"m_screenOn": True}),
                     ("LauncherIsInForegroundConstraint", {"m_inForeground": True})],
        added="2026-10-31", author="BespredeL",
    ))

    # ---- Safety ---------------------------------------------------------------------------
    A(Template(
        "anti-scam-call-guard", "Anti-scam call guard", "Safety",
        "While you are on a call, an incoming SMS or notification that looks like a "
        "verification code (4-8 characters) triggers full scam defense (ported from "
        "BespredeL's Anti-Scam macro): the code notification is wiped from the shade, an "
        "alert SMS goes to a trusted contact, a loud warning appears, and a dialog offers "
        "End call — if nobody touches it for 30 seconds the call hangs up automatically. "
        "Replace the number in the Send SMS action with your trusted contact.",
        ["scam", "fraud", "call", "sms", "security", "bespredel"],
        [item("IncomingSMSTrigger", 1, {"m_option": 3, "m_smsContent": "\\b\\w{4,6}\\b",
                                        "m_exactMatch": False, "enableRegex": True, "ignoreCase": True}),
         item("NotificationTrigger", 2, {"m_option": 0, "m_packageNameList": ["Any Application"],
                                         "m_textContent": "\\b\\w{4,8}\\b", "enableRegex": True,
                                         "ignoreCase": True, "m_ignoreOngoing": True})],
        [item("ClearNotificationsAction", 3, {"m_matchOption": 2, "m_matchText": "\\b\\w{4,6}\\b",
                                              "enableRegex": True, "ignoreCase": True, "m_clearPersistent": True}),
         item("SendSMSAction", 4, {"m_number": "+70000000000",
                                   "m_messageContent": "Possible phone scam: someone on a call may be "
                                                       "trying to get an SMS code from this phone."}),
         item("NotificationAction", 5, {"m_notificationSubject": "Possible phone scam",
                                        "m_notificationText": "A code SMS arrived during a call — do NOT read "
                                                              "the code to the caller!"}),
         item("OptionDialogAction", 6, {"m_title": "Possible phone scam",
                                        "m_message": "Someone on this call may be trying to get an SMS "
                                                     "verification code. Hang up — never share codes.",
                                        "m_buttonNames": ["Ignore", "End call"],
                                        "m_actionToRunJson": [None, REJECT_CALL_INLINE],
                                        "m_actionToRunClassType": [None, "RejectCallAction"],
                                        "m_actionToRunName": [None, "Reject call"],
                                        "m_defaultButton": 2, "m_defaultTimeOutSecs": 30,
                                        "blockNextAction": True})],
        constraints=[("InCallConstraint", {"m_inCall": True})],
        needs=["SMS permission", "Notification listener access", "Phone permission (end call)",
               "Edit the trusted phone number in the Send SMS action"],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "intruder-cam", "Intruder camera on failed unlock", "Safety",
        "After 2 failed unlock attempts within 10 minutes the front camera snaps a photo, GPS "
        "coordinates are captured, and both are saved to /sdcard/OpenMacro/IntruderCam together "
        "with a Google Maps link in a timestamped text file, followed by a notification "
        "(ported from BespredeL's IntruderCam; the rear-camera shot, 30 s video and the "
        "browser-based map viewer of the 89-action original were dropped for the store build).",
        ["intruder", "camera", "security", "failed unlock", "gps", "bespredel"],
        [item("FailedLoginTrigger", 1, {"m_numFailures": 2, "m_timeIndex": 3})],
        [item("SetVariableAction", 2, {"m_variable": {"m_name": "stamp", "m_type": 2},
                                       "m_newStringValue": "{year}-{month_digit}-{dayofmonth}_{hour}_{minute}_{sec}"}),
         item("ForceLocationUpdateAction", 3, {"timeoutSeconds": 20, "blockNextAction": True,
                                               "dictionaryVariableName": "loc"}),
         item("TakePictureAction", 4, {"m_useFrontCamera": True, "useAllFilesAccess": True,
                                       "allFilesPath": "/sdcard/OpenMacro/IntruderCam",
                                       "customFilename": "intruder_{lv=stamp}"}),
         item("WriteToFileAction", 5, {"m_logText": "Failed unlock at {lv=stamp}\nPhoto: intruder_{lv=stamp}.jpg\n"
                                                    "GPS: {lv=loc[latitude]}, {lv=loc[longitude]}\n"
                                                    "Map: https://maps.google.com/?q={lv=loc[latitude]},{lv=loc[longitude]}",
                                       "m_filename": "{lv=stamp}.txt", "overwrite": True,
                                       "useAllFilesAccess": True, "allFilesPath": "/sdcard/OpenMacro/IntruderCam"}),
         item("NotificationAction", 6, {"m_notificationSubject": "IntruderCam",
                                        "m_notificationText": "Failed unlock recorded — photo and GPS saved in "
                                                              "/sdcard/OpenMacro/IntruderCam"})],
        variables=[var_str("stamp"), var_dict("loc")],
        needs=["Camera permission", "Fine location permission", "All-files access"],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "parental-activity-report", "Child device activity reporter", "Safety",
        "Turns a child's phone into a reporter: every call (incoming/missed/outgoing), SMS, "
        "notification, Wi-Fi-free GPS position every 15 minutes and app install/removal is "
        "sent as an HTTP request to your own receiver URL (ported from BespredeL's Parental "
        "Control; the parent-side viewer and offline archive of the 220-action original are "
        "out of scope — the receiver stores what it gets). Fields from triggers that did not "
        "fire arrive as literal {token} text — have the receiver ignore those.",
        ["parental", "monitoring", "gps", "sms", "report", "bespredel"],
        [item("IncomingCallTrigger", 1, {"m_option": 3}),
         item("CallMissedTrigger", 2, {"m_option": 3}),
         item("OutgoingCallTrigger", 3, {"m_option": 3}),
         item("IncomingSMSTrigger", 4, {"m_option": 3, "ignoreCase": True}),
         item("NotificationTrigger", 5, {"m_option": 0, "m_packageNameList": ["Any Application"],
                                         "m_ignoreOngoing": True, "m_supressMultiples": True}),
         item("RegularIntervalTrigger", 6, {"m_seconds": 900, "m_useAlarm": True}),
         item("ApplicationInstalledRemovedTrigger", 7, {"m_installed": True}),
         item("ApplicationInstalledRemovedTrigger", 8)],
        [item("HttpRequestAction", 9, {
            "requestConfig": {
                "urlToOpen": "https://YOUR-RECEIVER.example/report",
                "requestType": 0,
                "requestTimeOutSeconds": 30,
                "followRedirects": True,
                "queryParams": [
                    {"paramName": "time", "paramValue": "{year}-{month_digit}-{dayofmonth} {hour}:{minute}:{sec}"},
                    {"paramName": "call", "paramValue": "{call_number}"},
                    {"paramName": "sms_from", "paramValue": "{sms_number}"},
                    {"paramName": "sms_text", "paramValue": "{sms_message}"},
                    {"paramName": "notification", "paramValue": "{not_app_name}: {not_title} {notification}"},
                    {"paramName": "lat", "paramValue": "{last_loc_lat}"},
                    {"paramName": "lng", "paramValue": "{last_loc_long}"},
                    {"paramName": "app", "paramValue": "{app_package} {app_name}"},
                ],
            }}),
         item("LogAction", 10, {"m_logText": "Activity report sent", "logLevel": 20})],
        needs=["Phone permission", "SMS permission", "Notification listener access",
               "Location permission (GPS reports)", "Your own HTTP receiver (e.g. a small script on your VPS) — "
               "put its URL into the request action"],
        added="2026-10-31", author="BespredeL",
    ))

    # ---- Utilities ------------------------------------------------------------------------
    A(Template(
        "remote-file-server", "LAN file server (JSON API)", "Utilities",
        "Exposes the phone's files to your Wi-Fi: an HTTP endpoint lists a folder as JSON, "
        "deletes a file, or creates a folder — no cloud, LAN only (ported from BespredeL's "
        "Remote Filemanager; the 92-action original serves a full HTML UI, this build is the "
        "JSON API it talks to). Open http://<phone-ip>:<port>/rfm?cmd=list&dir=/sdcard in a "
        "browser or script — the port shows when the macro arms. Add &name=<file> for "
        "delete, or cmd=mkdir to create a folder.",
        ["http", "file server", "lan", "json", "remote", "bespredel"],
        [item("HttpServerTrigger", 1, {"identifier": "rfm", "queryParamsDictionaryName": "q"})],
        [item("IfConditionAction", 2, constraints=[("MacroDroidVariableConstraint", {
            "m_variable": {"m_name": "q", "m_type": 4}, "dictionaryKeys": ["cmd"], "dictionaryType": 2,
            "m_stringValue": "list", "m_stringEqual": True})]),
         item("ClearVariablesAction", 3, {"variableNames": ["files", "filesJson"]}),
         item("FileOperationAllFilesAction", 4, {"option": 4, "fromPath": "{lv=q[dir]}",
                                                 "listFilesVariableName": "files",
                                                 "listFilesSortAscending": True, "waitToComplete": True}),
         item("JsonOutputAction", 5, {"dictionaryVarName": "files", "stringVarName": "filesJson"}),
         item("HttpServerResponseAction", 6, {"option": 0, "text": "{lv=filesJson}", "responseCode": "OK",
                                              "headerParams": [{"paramName": "Content-Type",
                                                                "paramValue": "application/json"}]}),
         item("ElseIfConditionAction", 7, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "q", "m_type": 4}, "dictionaryKeys": ["cmd"], "dictionaryType": 2,
             "m_stringValue": "delete", "m_stringEqual": True})]),
         item("FileOperationAllFilesAction", 8, {"option": 2, "fileOption": 5, "filePattern": "{lv=q[name]}",
                                                 "fromPath": "{lv=q[dir]}", "waitToComplete": True}),
         item("HttpServerResponseAction", 9, {"option": 0, "text": "deleted", "responseCode": "OK"}),
         item("ElseIfConditionAction", 10, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "q", "m_type": 4}, "dictionaryKeys": ["cmd"], "dictionaryType": 2,
             "m_stringValue": "mkdir", "m_stringEqual": True})]),
         item("FileOperationAllFilesAction", 11, {"option": 3, "folderName": "{lv=q[name]}",
                                                  "fromPath": "{lv=q[dir]}"}),
         item("HttpServerResponseAction", 12, {"option": 0, "text": "created", "responseCode": "OK"}),
         item("ElseAction", 13),
         item("HttpServerResponseAction", 14, {"option": 0,
                                               "text": "unknown cmd — use list|delete|mkdir with dir and name",
                                               "responseCode": "OK"}),
         item("EndIfAction", 15)],
        variables=[var_dict("q"), var_dict("files"), var_str("filesJson")],
        needs=["All-files access", "Same Wi-Fi network as the client"],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "wake-pc-wol", "Wake PC (Wake-on-LAN)", "Utilities",
        "Powers on a computer on your network with a Wake-on-LAN magic packet: run the macro "
        "or tap its home-screen widget and the packet goes to the broadcast address on UDP "
        "port 9 (ported from BespredeL's Wake PC; the original's settings scenes are replaced "
        "by three plain variables). Set the 'mac' variable to your PC's MAC and the UDP "
        "action's destination to your network's broadcast (usually your IP with .255 at the "
        "end). The PC must have Wake-on-LAN enabled in its BIOS/UEFI and NIC driver.",
        ["wake-on-lan", "pc", "udp", "remote", "bespredel"],
        [item("EmptyTrigger", 1),
         item("WidgetPressedTrigger", 2, {"m_widgetType": 0, "m_widgetLabel": "Wake PC"})],
        [item("SetVariableAction", 3, {"m_variable": {"m_name": "magicPacket", "m_type": 2},
                                       "m_newStringValue": "FFFFFFFFFFFF"}),
         item("TextManipulationAction", 4, {"m_text": "{lv=mac}",
                                            "m_textManipulation": {"type": "RemoveTextManipulation",
                                                                   "params": [":", "0"]},
                                            "variableName": "macHex"}),
         item("LoopAction", 5, {"m_option": 0, "m_fixedOptionCount": 16}),
         item("SetVariableAction", 6, {"m_variable": {"m_name": "magicPacket", "m_type": 2},
                                       "m_newStringValue": "{lv=magicPacket}{lv=macHex}"}),
         item("EndLoopAction", 7),
         item("UDPCommandAction", 8, {"m_destination": "192.168.1.255", "m_message": "0x{lv=magicPacket}",
                                      "m_port": 9}),
         item("ToastAction", 9, {"m_messageText": "Magic packet sent to {lv=mac} at 192.168.1.255:9",
                                 "m_duration": 2})],
        variables=[var_str("mac", "AA:BB:CC:DD:EE:FF"), var_str("macHex"), var_str("magicPacket")],
        needs=["Wake-on-LAN enabled on the target PC", "Same Wi-Fi network",
               "Edit the 'mac' variable and the UDP destination broadcast address"],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "telegram-device-bot", "Telegram device bot", "Utilities",
        "Controls this phone from a private Telegram chat: /ping answers, /geo replies with a "
        "Google Maps link of the current position, /ring plays a sound at full media volume, "
        "/reject_call ends the current call — anything else prints the command list (ported "
        "from BespredeL's Simple Telegram Bot, trimmed to its core commands; the original's "
        "note-taking, VirusTotal and DeepSeek commands were dropped). Only your Telegram user "
        "id is accepted — put it into the first If condition and your bot token into the "
        "'botToken' variable.",
        ["telegram", "bot", "remote control", "gps", "bespredel"],
        [item("WebHookTrigger", 1, {"identifier": "tgbot", "saveBodyVariableName": "resp"})],
        [item("JsonParseAction", 2, {"stringVarName": "resp", "dictionaryVarName": "tg"}),
         item("IfConditionAction", 3, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "tg", "m_type": 4}, "dictionaryKeys": ["message", "chat", "id"],
             "dictionaryType": 2, "m_stringValue": "REPLACE_WITH_YOUR_USER_ID", "m_stringEqual": False})]),
         tg_send(4, "Not authorized. Your chat id: {lv=tg[message][chat][id]}"),
         item("EndIfAction", 5),
         item("IfConditionAction", 6, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "tg", "m_type": 4}, "dictionaryKeys": ["message", "chat", "id"],
             "dictionaryType": 2, "m_stringValue": "REPLACE_WITH_YOUR_USER_ID", "m_stringEqual": True})]),
         item("IfConditionAction", 7, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "tg", "m_type": 4}, "dictionaryKeys": ["message", "text"],
             "dictionaryType": 2, "m_stringValue": "/ping", "m_stringEqual": True})]),
         tg_send(8, "pong"),
         item("ElseIfConditionAction", 9, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "tg", "m_type": 4}, "dictionaryKeys": ["message", "text"],
             "dictionaryType": 2, "m_stringValue": "/geo", "m_stringEqual": True})]),
         item("ForceLocationUpdateAction", 10, {"timeoutSeconds": 20, "blockNextAction": True,
                                                "dictionaryVariableName": "loc"}),
         tg_send(11, "Location: {lv=loc[latitude]}, {lv=loc[longitude]} — "
                     "https://maps.google.com/?q={lv=loc[latitude]},{lv=loc[longitude]}"),
         item("ElseIfConditionAction", 12, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "tg", "m_type": 4}, "dictionaryKeys": ["message", "text"],
             "dictionaryType": 2, "m_stringValue": "/ring", "m_stringEqual": True})]),
         item("SetVolumeAction", 13, {"m_streamIndexArray": [False, True, False, False, False, False, False, False],
                                      "m_streamVolumeArray": [0, 100, 0, 0, 0, 0, 0, 0], "m_volume": -1}),
         item("PlaySoundAction", 14, {"m_filePath": "Bells", "specifyAudioStream": True,
                                      "audioStream": 3, "staticFilename": True}),
         tg_send(15, "Ringing — follow the sound"),
         item("ElseIfConditionAction", 16, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "tg", "m_type": 4}, "dictionaryKeys": ["message", "text"],
             "dictionaryType": 2, "m_stringValue": "/reject_call", "m_stringEqual": True})]),
         item("RejectCallAction", 17),
         tg_send(18, "Call rejected"),
         item("ElseAction", 19),
         tg_send(20, "Commands: /ping /geo /ring /reject_call"),
         item("EndIfAction", 21),
         item("EndIfAction", 22)],
        variables=[var_str("botToken"), var_str("resp"), var_dict("tg"), var_dict("loc")],
        needs=["Bot token from @BotFather — put it into the 'botToken' variable",
               "Public webhook: OpenMacro webhooks are LAN-only, so forward a port from your VPS "
               "(89.116.128.227) to the phone and set the Telegram webhook to "
               "http://89.116.128.227:<port>/tgbot",
               "Your Telegram user id (ask @userinfobot) in the two If conditions",
               "Location permission (/geo)"],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "telegram-away-secretary", "Telegram away auto-reply", "Utilities",
        "Answers incoming Telegram Business messages when you are away: after a 60-second "
        "grace period (so you can answer manually first) the sender gets your away message "
        "(ported from BespredeL's Telegram Secretary; the AI reply of the original is replaced "
        "by the configurable away text because on-device AI is not built into OpenMacro yet — "
        "to answer with an LLM instead, extend the final branch: POST the message to any "
        "OpenAI-compatible chat endpoint, parse the reply with JsonParse and read "
        "{lv=ai[choices][0][message][content]}). Send /start from your own account once to "
        "register you as the owner.",
        ["telegram", "auto-reply", "away", "business", "bespredel"],
        [item("WebHookTrigger", 1, {"identifier": "tgsec", "saveBodyVariableName": "resp"})],
        [item("JsonParseAction", 2, {"stringVarName": "resp", "dictionaryVarName": "tg"}),
         item("IfConditionAction", 3, constraints=[("MacroDroidVariableConstraint", {
             "m_variable": {"m_name": "tg", "m_type": 4}, "dictionaryKeys": ["message", "text"],
             "dictionaryType": 2, "m_stringValue": "/start", "m_stringEqual": True})]),
         item("SetVariableAction", 4, {"m_variable": {"m_name": "ownerId", "m_type": 2},
                                       "m_newStringValue": "{lv=tg[message][from][id]}"}),
         tg_send(5, "Owner registered — away replies will skip you."),
         item("EndIfAction", 6),
         item("IfConditionAction", 7, constraints=[
             ("MacroDroidVariableConstraint", {"m_variable": {"m_name": "tg", "m_type": 4},
                                               "dictionaryKeys": ["business_message", "text"],
                                               "dictionaryType": 2, "m_stringComparisonType": 1,
                                               "m_stringValue": ""}),
             ("MacroDroidVariableConstraint", {"m_variable": {"m_name": "tg", "m_type": 4},
                                               "dictionaryKeys": ["business_message", "from", "id"],
                                               "dictionaryType": 2, "m_stringValue": "{lv=ownerId}",
                                               "m_stringEqual": False})]),
         item("PauseAction", 8, {"m_delayInSeconds": 60, "m_useAlarm": True}),
         tg_send(9, "Hi! The owner is away right now and will answer you later. "
                    "For urgent matters please call.", chat_id="{lv=tg[business_message][chat][id]}"),
         item("EndIfAction", 10)],
        variables=[var_str("botToken"), var_str("ownerId"), var_str("resp"), var_dict("tg")],
        needs=["Bot token from @BotFather — put it into the 'botToken' variable",
               "Public webhook: OpenMacro webhooks are LAN-only, so forward a port from your VPS "
               "(89.116.128.227) to the phone and set the Telegram webhook to "
               "http://89.116.128.227:<port>/tgsec",
               "Telegram Business connection (business_message updates)",
               "Send /start from your own Telegram account once to register the owner"],
        added="2026-10-31", author="BespredeL",
    ))
    A(Template(
        "youtube-skip-ads", "YouTube ad skipper", "Utilities",
        "While YouTube is in the foreground: when a 'Skip' button appears it is tapped for "
        "you, when an ad's 'Visit advertiser' label shows up media is muted, and when the "
        "label disappears your volume comes back (ported from BespredeL's AutoSkip YouTube "
        "Ads; the Shorts flow and the 79-language detection of the original were dropped — "
        "matched texts are for the English UI, edit them in the triggers for other "
        "languages). Needs the accessibility service for screen reading and tapping.",
        ["youtube", "ads", "skip", "mute", "accessibility", "bespredel"],
        [item("ScreenContentTrigger", 1, dict(SCREEN_CONTENT_SKIP), constraints=[YOUTUBE_FOREGROUND]),
         item("ScreenContentTrigger", 2, dict(SCREEN_CONTENT_AD_LABEL), constraints=[YOUTUBE_FOREGROUND]),
         item("ScreenContentTrigger", 3, dict(SCREEN_CONTENT_AD_LABEL, isOffScreen=True),
              constraints=[YOUTUBE_FOREGROUND])],
        [item("IfConditionAction", 4, constraints=[("TriggerThatInvokedConstraint", {"m_triggerIndex": 0})]),
         item("UIInteractionAction", 5, {"uiInteractionConfiguration": {"type": "Click", "clickOption": "1",
                                                                       "textContent": "Skip", "blocking": "false"}}),
         item("VibrateAction", 6, {"m_vibratePattern": 12}),
         item("ElseIfConditionAction", 7, constraints=[("TriggerThatInvokedConstraint", {"m_triggerIndex": 1})]),
         item("SetVolumeAction", 8, {"m_streamIndexArray": [False, True, False, False, False, False, False, False],
                                     "m_streamVolumeArray": [0, 0, 0, 0, 0, 0, 0, 0], "m_volume": -1}),
         item("ToastAction", 9, {"m_messageText": "Ad muted", "m_duration": 2}),
         item("ElseIfConditionAction", 10, constraints=[("TriggerThatInvokedConstraint", {"m_triggerIndex": 2})]),
         item("SetVolumeAction", 11, {"m_streamIndexArray": [False, True, False, False, False, False, False, False],
                                      "m_streamVolumeArray": [0, 60, 0, 0, 0, 0, 0, 0], "m_volume": -1}),
         item("ToastAction", 12, {"m_messageText": "Volume restored to 60%", "m_duration": 2}),
         item("EndIfAction", 13)],
        needs=["Accessibility service (screen content + taps)", "English YouTube UI — edit the matched texts "
               "in the triggers for other languages"],
        added="2026-10-31", author="BespredeL",
    ))
