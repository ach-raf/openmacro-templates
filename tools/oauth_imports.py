#!/usr/bin/env python3
"""Tier 3: templates that call account APIs through OpenMacro's built-in OAuth.

Connect the provider once in More > Accounts (your own free developer app, redirect
http://127.0.0.1:48765/callback); a macro then sends `Authorization: Bearer {oauth=<id>}`.
Provider ids: google, spotify, todoist, github.

Not possible even with OAuth (so not shipped): Spotify Discover Weekly archive (Spotify closed
algorithmic playlists to new developer apps), Evernote (API closed), Facebook tags and Instagram
(no third-party API), Tumblr legacy OAuth1.
"""

ADDED = "2026-10-31"


def register(T, A, Template, var_str, var_bool, var_dict, var_dec, item):
    def var(name, t):
        return {"m_name": name, "m_type": t}

    def bearer(provider):
        return [{"paramName": "Authorization", "paramValue": "Bearer {oauth=%s}" % provider}]

    def call(siguid, url, provider, method=0, body=None, query=None, save=None, accept_json=True):
        cfg = {"urlToOpen": url, "requestType": method, "requestTimeOutSeconds": 30, "followRedirects": True,
               "headerParams": bearer(provider)}
        if body is not None:
            cfg["contentType"] = "application/json"
            cfg["contentBodyText"] = body
        if query:
            cfg["queryParams"] = [{"paramName": k, "paramValue": v} for k, v in query.items()]
        if save:
            cfg["saveResponseType"] = 1
            cfg["responseVariableName"] = save
        return item("HttpRequestAction", siguid, {"requestConfig": cfg})

    def tpl(tid, name, category, description, tags, triggers, actions, **kw):
        needs = ["Internet"] + kw.pop("needs", [])
        A(Template(tid, name, category, description, ["oauth"] + tags, triggers, actions,
                   needs=needs, added=ADDED, **kw))

    def every(siguid, seconds):
        return item("RegularIntervalTrigger", siguid, {"m_seconds": seconds, "m_ignoreReferenceStartTime": True})

    def changed(siguid, new_var, last_var):
        return item("IfConditionAction", siguid, constraints=[
            ("MacroDroidVariableConstraint", {"m_variable": var(new_var, 2), "m_stringComparisonType": 0,
                                              "m_stringEqual": False, "m_stringValue": "{lv=%s}" % last_var}),
            ("MacroDroidVariableConstraint", {"m_variable": var(new_var, 2), "m_stringComparisonType": 2,
                                              "m_stringValue": "{lv="})])

    # Spotify: new liked song -> a playlist
    tpl("spotify-liked-to-playlist", "Spotify: liked songs into a playlist", "Music",
        "Every 5 minutes your newest liked Spotify song is checked; a new one is added to the "
        "playlist whose id you set in the playlistId variable (the part of the playlist link after "
        "/playlist/). Connect Spotify in More > Accounts first. Only the newest like is checked, so "
        "keep the interval short.",
        ["spotify", "playlist", "music"],
        [every(1, 300)],
        [call(2, "https://api.spotify.com/v1/me/tracks?limit=1", "spotify", save="liked"),
         item("JsonParseAction", 3, {"stringVarName": "liked", "dictionaryVarName": "likedDict"}),
         item("TextManipulationAction", 4, {"m_text": "{lv=likedDict[items][0][track][uri]}", "variableName": "newUri",
                                            "m_textManipulation": {"type": "TrimManipulation"}}),
         changed(5, "newUri", "lastUri"),
         call(6, "https://api.spotify.com/v1/playlists/{lv=playlistId}/tracks", "spotify", method=1,
              query={"uris": "{lv=newUri}"}),
         item("SetVariableAction", 7, {"m_variable": var("lastUri", 2), "m_newStringValue": "{lv=newUri}"}),
         item("EndIfAction", 8)],
        variables=[var_str("liked"), var_dict("likedDict"), var_str("newUri"), var_str("lastUri"),
                   var_str("playlistId", "YOUR_PLAYLIST_ID")],
        needs=["Spotify connected (More > Accounts)"])

    # Todoist: share text -> task
    tpl("todoist-task-from-share", "Todoist: share to a new task", "Utilities",
        "Share any text or link to OpenMacro and it becomes a Todoist task in your Inbox. Connect "
        "Todoist (or paste your personal API token) in More > Accounts. Avoid double quotes in shared text.",
        ["todoist", "tasks", "share"],
        [item("ShareTextTrigger", 1, {})],
        [call(2, "https://api.todoist.com/rest/v2/tasks", "todoist", method=1, body='{"content":"{shared_text}"}'),
         item("ToastAction", 3, {"m_messageText": "Added to Todoist", "m_duration": 2})],
        needs=["Todoist connected (More > Accounts)"])

    # Google Tasks: share text -> task
    tpl("google-task-from-share", "Google Tasks: share to a new task", "Utilities",
        "Share text to OpenMacro and it is added to your default Google Tasks list "
        "(IFTTT: Add Google Task). Connect Google in More > Accounts.",
        ["google", "tasks", "share"],
        [item("ShareTextTrigger", 1, {})],
        [call(2, "https://tasks.googleapis.com/tasks/v1/lists/@default/tasks", "google", method=1,
              body='{"title":"{shared_text}"}'),
         item("ToastAction", 3, {"m_messageText": "Added to Google Tasks", "m_duration": 2})],
        needs=["Google connected (More > Accounts)"])

    # Google Sheets: daily currency rate row
    tpl("sheets-currency-log", "Google Sheets: daily currency rate", "Finance",
        "Once a day the USD to EUR rate is appended as a new row to your Google Sheet (IFTTT: log "
        "daily currency exchange rates to Google Sheets). Put the sheet id (from its URL) in the "
        "sheetId variable. Connect Google in More > Accounts.",
        ["google", "sheets", "currency", "finance"],
        [item("TimerTrigger", 1, {"m_hour": 9, "m_minute": 0, "m_second": 0, "m_daysOfWeek": [True] * 7,
                                  "m_useAlarm": True})],
        [item("HttpRequestAction", 2, {"requestConfig": {
            "urlToOpen": "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR", "requestType": 0,
            "requestTimeOutSeconds": 30, "followRedirects": True, "saveResponseType": 1, "responseVariableName": "resp"}}),
         item("JsonParseAction", 3, {"stringVarName": "resp", "dictionaryVarName": "fx"}),
         call(4, "https://sheets.googleapis.com/v4/spreadsheets/{lv=sheetId}/values/Sheet1!A1:append", "google",
              method=1, query={"valueInputOption": "USER_ENTERED"},
              body='{"values":[["{lv=fx[date]}","USD","EUR",{lv=fx[rates][EUR]}]]}')],
        variables=[var_str("resp"), var_dict("fx"), var_str("sheetId", "YOUR_SHEET_ID")],
        needs=["Google connected (More > Accounts)"])

    # Google Sheets: log incoming SMS
    tpl("sheets-sms-log", "Google Sheets: log every SMS", "Messaging",
        "Each incoming text is appended to a Google Sheet as time, sender and message. Set sheetId "
        "to your sheet's id. Connect Google in More > Accounts.",
        ["google", "sheets", "sms", "log"],
        [item("IncomingSMSTrigger", 1, {"m_option": 3})],
        [call(2, "https://sheets.googleapis.com/v4/spreadsheets/{lv=sheetId}/values/Sheet1!A1:append", "google",
              method=1, query={"valueInputOption": "USER_ENTERED"},
              body='{"values":[["{year}-{month_digit}-{dayofmonth} {hour}:{minute}","{sms_number}","{sms_text}"]]}')],
        variables=[var_str("sheetId", "YOUR_SHEET_ID")],
        needs=["SMS permission", "Google connected (More > Accounts)"])

    # Google Contacts: new contact -> email
    tpl("google-contacts-new-email", "Email me new Google Contacts", "Utilities",
        "Every 30 minutes the most recently changed Google contact is checked; when it is a new "
        "one you get an email with its name and number (IFTTT: Email new Google Contacts details). "
        "Needs SMTP (More tab) and Google connected in More > Accounts.",
        ["google", "contacts", "email"],
        [every(1, 1800)],
        [call(2, "https://people.googleapis.com/v1/people/me/connections", "google",
              query={"personFields": "names,phoneNumbers,emailAddresses", "sortOrder": "LAST_MODIFIED_DESCENDING",
                     "pageSize": "1"}, save="resp"),
         item("JsonParseAction", 3, {"stringVarName": "resp", "dictionaryVarName": "people"}),
         item("TextManipulationAction", 4, {"m_text": "{lv=people[connections][0][resourceName]}",
                                            "variableName": "newId",
                                            "m_textManipulation": {"type": "TrimManipulation"}}),
         changed(5, "newId", "lastId"),
         item("SendEmailAction", 6, {
             "sendOption": 1, "m_emailAddress": "you@example.com", "m_subject": "New contact",
             "m_body": "{lv=people[connections][0][names][0][displayName]}\n"
                       "{lv=people[connections][0][phoneNumbers][0][value]}\n"
                       "{lv=people[connections][0][emailAddresses][0][value]}"}),
         item("SetVariableAction", 7, {"m_variable": var("lastId", 2), "m_newStringValue": "{lv=newId}"}),
         item("EndIfAction", 8)],
        variables=[var_str("resp"), var_dict("people"), var_str("newId"), var_str("lastId")],
        needs=["SMTP account (More tab)", "Google connected (More > Accounts)"])

    # GitHub: newest notification -> phone notification
    tpl("github-notification-alert", "GitHub notification alert", "Utilities",
        "Every 10 minutes your newest unread GitHub notification is shown as a phone notification "
        "once. Connect GitHub (or paste a personal access token with the notifications scope) in "
        "More > Accounts.",
        ["github", "notifications", "developer"],
        [every(1, 600)],
        [call(2, "https://api.github.com/notifications", "github", query={"per_page": "1"}, save="resp"),
         item("JsonParseAction", 3, {"stringVarName": "resp", "dictionaryVarName": "n"}),
         item("TextManipulationAction", 4, {"m_text": "{lv=n[entries][0][id]}", "variableName": "newId",
                                            "m_textManipulation": {"type": "TrimManipulation"}}),
         changed(5, "newId", "lastId"),
         item("NotificationAction", 6, {"m_notificationSubject": "GitHub: {lv=n[entries][0][repository][full_name]}",
                                        "m_notificationText": "{lv=n[entries][0][subject][title]}"}),
         item("SetVariableAction", 7, {"m_variable": var("lastId", 2), "m_newStringValue": "{lv=newId}"}),
         item("EndIfAction", 8)],
        variables=[var_str("resp"), var_dict("n"), var_str("newId"), var_str("lastId")],
        needs=["GitHub connected (More > Accounts)"])
