#!/usr/bin/env python3
"""Print catalog-schema param entries for the classes the BespredeL ports need."""
import json
import sys

sys.path.insert(0, r"D:\PycharmProjects\openmacro-templates\tools")
s = json.load(open(r"D:\PycharmProjects\openmacro-templates\tools\catalog-schema.json", encoding="utf-8"))

CLASSES = [
    # triggers
    "IncomingSMSTrigger", "NotificationTrigger", "MacroEnabledTrigger", "ScreenContentTrigger",
    "VolumeButtonTrigger", "ApplicationLaunchedTrigger", "EmptyTrigger", "FailedLoginTrigger",
    "DeviceUnlockedTrigger", "HttpServerTrigger", "GPSEnabledTrigger", "WebHookTrigger",
    "DataOnOffTrigger", "VariableTrigger", "IncomingCallTrigger", "CallMissedTrigger",
    "OutgoingCallTrigger", "WifiConnectionTrigger", "RegularIntervalTrigger",
    "ApplicationInstalledRemovedTrigger", "ShakeDeviceTrigger", "WidgetPressedTrigger",
    "MacroDroidIconLongPressShortcutTrigger",
    # actions
    "IfConditionAction", "MessageDialogAction", "SetVariableAction", "EndIfAction",
    "ElseIfConditionAction", "ElseAction", "ClearNotificationsAction", "SendSMSAction",
    "LoopAction", "EndLoopAction", "NotificationAction", "PauseAction", "OptionDialogAction",
    "SeparatorAction", "ActionGroupAction", "ActionGroupEndAction", "VibrateAction",
    "ToastAction", "SetVolumeAction", "UIInteractionAction", "CheckTextOnScreenAction",
    "CancelActiveMacroAction", "CameraFlashLightAction", "TakePictureAction",
    "RecordVideoAction", "SetLocationModeAction", "WriteToFileAction",
    "FileOperationAllFilesAction", "ReadFileAction", "SendIntentAction", "DisableTriggerAction",
    "OpenWebPageAction", "ForceLocationUpdateAction", "ClearDictionaryArrayEntryAction",
    "TextManipulationAction", "JsonParseAction", "JsonOutputAction", "HttpRequestAction",
    "HttpServerResponseAction", "IterateDictionaryAction", "ClearVariablesAction",
    "MakeCallAction", "RejectCallAction", "PlaySoundAction", "SpeakTextAction",
    "UDPCommandAction", "ConnectivityCheckAction", "SelectionDialogAction",
    "GenerateQRCodeAction", "ShareTextAction", "LogAction", "BreakFromLoopAction",
    "CustomSceneAction", "MacroDroidSettingAction", "AuthenticateUserAction",
    # constraints
    "InCallConstraint", "MusicActiveConstraint", "ActiveApplicationConstraint",
    "ScreenOnOffConstraint", "DeviceLockedConstraint", "ProximitySensorConstraint",
    "LightLevelConstraint", "DeviceOrientationConstraint", "LauncherIsInForegroundConstraint",
    "WifiConstraint", "GPSEnabledConstraint", "MacroDroidVariableConstraint",
    "CompareValueConstraint", "TriggerThatInvokedConstraint", "LogicConstraint",
    "VolumeLevelConstraint", "InvocationMethodConstraint",
]

for kind in ("triggers", "actions", "constraints"):
    for c in CLASSES:
        p = s["params"][kind].get(c)
        if p is None:
            continue
        print(f"\n== {kind[:-1].upper()}: {c}")
        for f in p:
            e = f.get("e")
            print(f"   {f['n']}" + (f"  enum={e}" if e else ""))
runnable = s["runnable"]
missing = []
for kind in ("triggers", "actions", "constraints"):
    for c in CLASSES:
        if c in runnable[kind] and s["params"][kind].get(c) is None:
            missing.append((kind, c))
        if c not in runnable[kind] and s["params"][kind].get(c) is not None:
            missing.append((kind + " NOT-RUNNABLE-but-has-params", c))
print("\n-- missing/quirks:", missing if missing else "none")
