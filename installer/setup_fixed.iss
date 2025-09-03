; installer/setup.iss — Compressor & PDF Merger
; Inno Setup 6

#define MyAppName "Compressor & PDF Merger"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KIMovchanin"
#define MyAppURL "https://github.com/KIMovchanin/compressor_and_pdf_merger"
#define MyAppExeName "CompressorAndPDFMerger.exe"
#define MyAppId "59C22CD6-E2C5-44E4-83C1-AD2B71B64023"
#define MyAppMutex "CompressorAndPDFMerger_Mutex"

[Setup]
AppId={{{#MyAppId}}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
WizardStyle=modern
SetupIconFile=..\src\compressor_and_pdf_merger\assets\media_tool_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
RestartApplications=yes
AppMutex={#MyAppMutex}
OutputBaseFilename={#MyAppName}_Setup_{#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\src\compressor_and_pdf_merger\assets\media_tool_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('..\LICENSE'))
Source: "..\LICENSE-AGPL-3.0.txt"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('..\LICENSE-AGPL-3.0.txt'))
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('..\THIRD_PARTY_NOTICES.md'))

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; создаём ярлык на рабочем столе ТЕКУЩЕГО пользователя (а не общего) — никаких прав администратора не требуется
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Type: filesandordirs; Name: "{localappdata}\User\CompressorAndPDFMerger\cache"
; Type: filesandordirs; Name: "{localappdata}\User\CompressorAndPDFMerger\logs"
