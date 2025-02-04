#define MyAppName "DTR Calculator"
#define MyAppVersion "2.9.25"
#define MyAppPublisher "KCprsnlcc"
#define MyAppURL "https://github.com/KCprsnlcc/DTR-Calculator"
#define MyAppExeName "main.exe"
#define MyAppAssocName MyAppName
#define MyAppAssocExt ".doh"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; General application details
AppId={{813841F4-A474-4402-B0DB-63923C73DC30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation settings to avoid UAC prompts
DefaultDirName=D:\{#MyAppName}
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=

; Additional setup options
LicenseFile=C:\Users\kcper\OneDrive\Documents\OJT Materials\LICENSE.txt
InfoBeforeFile=C:\Users\kcper\OneDrive\Documents\OJT Materials\README.txt
InfoAfterFile=C:\Users\kcper\OneDrive\Documents\OJT Materials\AFTERINSTALL.txt
OutputBaseFilename=dtrsetup
SetupIconFile=C:\xampp\htdocs\DTR Calculator\icon.ico
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Include all necessary application files and directories
Source: "C:\xampp\htdocs\DTR Calculator\build\main\*"; DestDir: "{app}\build\main"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\xampp\htdocs\DTR Calculator\dist\main\*"; DestDir: "{app}\dist\main"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\xampp\htdocs\DTR Calculator\main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\xampp\htdocs\DTR Calculator\main.spec"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\xampp\htdocs\DTR Calculator\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\xampp\htdocs\DTR Calculator\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\xampp\htdocs\DTR Calculator\.gitignore"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\xampp\htdocs\DTR Calculator\dtr_app.log"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\xampp\htdocs\DTR Calculator\dtr_records.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\xampp\htdocs\DTR Calculator\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Create desktop and start menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\dist\main\main.exe"; WorkingDir: "{app}\dist\main"; IconFilename: "{app}\icon.ico"; IconIndex: 0
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\dist\main\main.exe"; WorkingDir: "{app}\dist\main"; IconFilename: "{app}\icon.ico"; IconIndex: 0; Tasks: desktopicon

[Registry]
; Modify registry keys in HKCU instead of HKCR to avoid UAC
Root: HKCU; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\icon.ico"",0"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\dist\main\main.exe"" ""%1"""; Flags: uninsdeletekey

[Run]
; Launch the application after installation
Filename: "{app}\dist\main\main.exe"; Description: "Launch the application"; Flags: nowait postinstall skipifsilent shellexec
