; setup_fixed.iss — corrected AppId escaping
#define MyAppName "Compressor & PDF Merger"
#define MyAppExeName "CompressorAndPDFMerger.exe"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KIMovchanin"
#define MyAppURL "https://github.com/KIMovchanin/compressor_and_pdf_merger"
; Store GUID *without* braces
#define MyAppId "59C22CD6-E2C5-44E4-83C1-AD2B71B64023"

; If you built PyInstaller as ONEFILE, keep this define. For ONEDIR, comment it out.
#define OneFile

[Setup]
; IMPORTANT: Use triple braces here so resulting value has literal braces and isn't treated as a {constant}
AppId={{{#MyAppId}}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
LicenseFile=..\LICENSE
OutputDir=Output
OutputBaseFilename={#MyAppName}_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
SetupIconFile=..\src\compressor_and_pdf_merger\assets\media_tool_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
#ifdef OneFile
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
#else
Source: "..\dist\CompressorAndPDFMerger\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
