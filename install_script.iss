; AI Trading Installer - Created for Nedas Miliunas

#define MyAppName "AI Trading"
#define MyAppVersion "1.0"
#define MyAppPublisher "Nedas Miliunas"
#define MyAppExeName "AI_trading.exe"

[Setup]
AppId={{712C455F-7A42-47E6-977A-450DDE581C9E}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=AI_Trading_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "D:\Vynx_AI\RandomProjects\Trading\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Background asset
Source: "D:\Vynx_AI\RandomProjects\Trading\ui\assets\background.jpg"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Optional: README
Source: "D:\Vynx_AI\RandomProjects\Trading\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent