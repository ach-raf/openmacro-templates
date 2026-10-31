#!/usr/bin/env python3
"""Tier 1 recreations of popular IFTTT applets (ifttt.com/explore/applets) as OpenMacro templates.

Each applet is re-authored with only engine-runnable classes. Services that need an account
API (Weather Underground, Philips Hue cloud, NASA key) are replaced by keyless or local
equivalents: Open-Meteo, the Hue bridge's local REST API, NASA's DEMO_KEY, Yahoo Finance chart feed, Frankfurter.

Engine facts relied on (verified 2026-10-31):
- HttpRequestAction requestType 0=GET 1=POST 2=PUT; saveResponseType 1 = variable, 2 = file
  (plain path + saveResponseUseAllFilesAccess).
- `{lv=dict[a][b]}` navigates parsed JSON; array indexes are avoided on purpose.
- MacroDroidVariableConstraint on a decimal variable: m_intLessThan / m_intGreaterThan + m_doubleValue.
- Trigger extras `{sms_number}` / `{sms_text}` resolve inside actions.
"""

ADDED = "2026-10-31"
DAILY = [True] * 7


def register(T, A, Template, var_str, var_bool, var_dict, var_dec, item):
    def http(siguid, url, **cfg):
        base = {"urlToOpen": url, "requestType": 0, "requestTimeOutSeconds": 30, "followRedirects": True}
        base.update(cfg)
        return item("HttpRequestAction", siguid, {"requestConfig": base})

    def var(name, t):
        return {"m_name": name, "m_type": t}

    def tpl(tid, name, category, description, tags, triggers, actions, **kw):
        A(Template(tid, name, category, description, ["ifttt"] + tags, triggers, actions,
                   added=ADDED, **kw))

    def daily(hour):
        return item("TimerTrigger", 1, {"m_hour": hour, "m_minute": 0, "m_second": 0,
                                        "m_daysOfWeek": DAILY, "m_useAlarm": True})

    # 1. Forward Android SMS to your email inbox
    tpl("sms-to-email", "Forward SMS to email", "Messaging",
        "Every incoming SMS is emailed to you (IFTTT: Forward Android SMS to your Email inbox). "
        "Set your SMTP account in OpenMacro's More tab and put your address in the Send Email action.",
        ["sms", "email", "forward"],
        [item("IncomingSMSTrigger", 1, {"m_option": 3})],
        [item("SendEmailAction", 2, {"sendOption": 1, "m_emailAddress": "you@example.com",
                                     "m_subject": "SMS from {sms_number}", "m_body": "{sms_text}"})],
        needs=["SMS permission", "SMTP account (More tab)", "Internet"])

    # 2. 6:00 AM weather email forecast
    tpl("weather-email-6am", "6 AM weather email", "Utilities",
        "At 6:00 every morning you get an email with the current weather (Open-Meteo, no API key). "
        "Edit the latitude/longitude in the URL and the address in the email action.",
        ["weather", "email", "morning"],
        [daily(6)],
        [http(2, "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41"
                 "&current=temperature_2m,apparent_temperature,precipitation,wind_speed_10m",
              saveResponseType=1, responseVariableName="resp"),
         item("JsonParseAction", 3, {"stringVarName": "resp", "dictionaryVarName": "weather"}),
         item("SendEmailAction", 4, {
             "sendOption": 1, "m_emailAddress": "you@example.com", "m_subject": "Today's weather",
             "m_body": "Temperature {lv=weather[current][temperature_2m]} C, feels like "
                       "{lv=weather[current][apparent_temperature]} C, wind "
                       "{lv=weather[current][wind_speed_10m]} km/h, precipitation "
                       "{lv=weather[current][precipitation]} mm."})],
        variables=[var_str("resp"), var_dict("weather")],
        needs=["Internet", "SMTP account (More tab)"])

    # 3. Stock watcher: ping me when price drops below a point
    tpl("stock-drop-alert", "Stock below price alert", "Finance",
        "Every 15 minutes the price of your stock is fetched (Yahoo Finance chart feed, no key) and you get a "
        "notification once it falls below your limit. Edit the symbol at the end of the URL (AAPL, "
        "MSFT, ...) and the limit in the condition; you are notified once per drop.",
        ["stock", "finance", "price", "alert"],
        [item("RegularIntervalTrigger", 1, {"m_seconds": 900, "m_ignoreReferenceStartTime": True})],
        [http(2, "https://query1.finance.yahoo.com/v8/finance/chart/AAPL", saveResponseType=1,
              responseVariableName="resp",
              headerParams=[{"paramName": "User-Agent", "paramValue": "Mozilla/5.0"}]),
         item("JsonParseAction", 20, {"stringVarName": "resp", "dictionaryVarName": "quote"}),
         item("TextManipulationAction", 3, {"m_text": "{lv=quote[chart][result][0][meta][regularMarketPrice]}",
                                            "variableName": "price",
                                            "m_textManipulation": {"type": "TrimManipulation"}}),
         item("IfConditionAction", 4, constraints=[
             ("MacroDroidVariableConstraint", {"m_variable": var("price", 3), "m_intLessThan": True,
                                               "m_doubleValue": 150.0}),
             ("MacroDroidVariableConstraint", {"m_variable": var("alerted", 0), "m_booleanValue": False})]),
         item("NotificationAction", 5, {"m_notificationSubject": "Stock alert",
                                        "m_notificationText": "Price dropped to {lv=price}"}),
         item("SetVariableAction", 6, {"m_variable": var("alerted", 0), "m_newBooleanValue": True}),
         item("ElseIfConditionAction", 7, constraints=[
             ("MacroDroidVariableConstraint", {"m_variable": var("price", 3), "m_intGreaterThan": True,
                                               "m_doubleValue": 150.0})]),
         item("SetVariableAction", 8, {"m_variable": var("alerted", 0), "m_newBooleanValue": False}),
         item("EndIfAction", 9)],
        variables=[var_str("resp"), var_dict("quote"), var_dec("price"), var_bool("alerted")],
        needs=["Internet"])

    # 4. Daily currency rate logged (CSV instead of Google Sheets)
    tpl("currency-rate-log", "Daily currency rate log", "Finance",
        "Once a day the USD to EUR rate is fetched (Frankfurter, no key) and appended as a line "
        "to /sdcard/OpenMacro/rates.csv, ready to open in any spreadsheet. Change the currency "
        "codes in the URL.",
        ["currency", "exchange", "csv", "log"],
        [daily(9)],
        [http(2, "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR", saveResponseType=1,
              responseVariableName="resp"),
         item("JsonParseAction", 3, {"stringVarName": "resp", "dictionaryVarName": "fx"}),
         item("WriteToFileAction", 4, {"m_logText": "{lv=fx[date]},USD,EUR,{lv=fx[rates][EUR]}\n",
                                       "m_filename": "rates.csv", "m_append": True,
                                       "useAllFilesAccess": True, "allFilesPath": "/sdcard/OpenMacro"})],
        variables=[var_str("resp"), var_dict("fx")],
        needs=["Internet", "All-files access (writes /sdcard/OpenMacro/rates.csv)"])

    # 5. NASA Image of the Day as wallpaper
    tpl("nasa-apod-wallpaper", "NASA picture of the day wallpaper", "Utilities",
        "Each morning the NASA Astronomy Picture of the Day becomes your wallpaper. Uses NASA's "
        "public DEMO_KEY; get a free key at api.nasa.gov for heavy use. Days when NASA posts a "
        "video instead of an image are skipped.",
        ["nasa", "wallpaper", "space", "apod"],
        [daily(8)],
        [http(2, "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", saveResponseType=1,
              responseVariableName="resp"),
         item("JsonParseAction", 3, {"stringVarName": "resp", "dictionaryVarName": "apod"}),
         item("IfConditionAction", 4, constraints=[
             ("MacroDroidVariableConstraint", {"m_variable": var("apod", 4), "dictionaryKeys": ["media_type"],
                                               "dictionaryType": 2, "m_stringValue": "image"})]),
         http(5, "{lv=apod[url]}", saveResponseType=2, saveResponseUseAllFilesAccess=True,
              saveResponseAllFilesAccessPath="/sdcard/OpenMacro/apod.jpg"),
         item("SetWallpaperAction", 6, {"m_option": 0, "m_screenOption": 2,
                                        "m_wallpaperUriString": "/sdcard/OpenMacro/apod.jpg"}),
         item("EndIfAction", 7)],
        variables=[var_str("resp"), var_dict("apod")],
        needs=["Internet", "Storage folder /sdcard/OpenMacro (grant all-files access in Android settings)"])

    # 6/7. Philips Hue on arrive / off leave (local bridge REST API)
    def hue(tid, name, enter, on, text):
        tpl(tid, name, "Location",
            text + " Talks to your Hue bridge on the local network (no cloud, no account). Set the "
            "bridge IP and your API username in the macro variables (press the bridge button, then "
            "POST a devicetype body to http://<bridge>/api to get one) and the home coordinates in "
            "the trigger.",
            ["hue", "lights", "home", "location", "smart-home"],
            [item("LocationTrigger", 1, {"m_enterArea": enter, "m_geofenceId": "home",
                                         "m_newTriggerFromUnknown": 1, "m_latitude": 52.52,
                                         "m_longitude": 13.405, "m_radius": 150})],
            [http(2, "http://{lv=bridge}/api/{lv=hueUser}/groups/0/action", requestType=2,
                  contentType="application/json",
                  contentBodyText='{"on":%s}' % ("true" if on else "false"))],
            variables=[var_str("bridge", "192.168.1.2"), var_str("hueUser", "YOUR-HUE-USERNAME")],
            needs=["Location permission", "Philips Hue bridge on the same Wi-Fi"])

    hue("hue-on-arrive-home", "Hue lights on when I arrive home", True, True,
        "Turns every Philips Hue light on when you arrive home.")
    hue("hue-off-leave-home", "Hue lights off when I leave home", False, False,
        "Turns every Philips Hue light off when you leave home.")
