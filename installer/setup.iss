
; setup.iss — Inno Setup script for "Compressor & PDF Merger"
; Place this file in your project's "installer" folder and compile with Inno Setup.
; One script supports both PyInstaller onefile and onedir builds — toggle #define OneFile.

#define MyAppName "Compressor & PDF Merger"
#define MyAppExeName "CompressorAndPDFMerger.exe"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KIMovchanin"
#define MyAppURL "https://github.com/KIMovchanin/compressor_and_pdf_merger"

; IMPORTANT: Keep AppId constant across versions to allow upgrades over existing install.
#define MyAppId "{59C22CD6-E2C5-44E4-83C1-AD2B71B64023}"

; If you built PyInstaller as ONEFILE, keep this define. For ONEDIR, comment it out.
#define OneFile

[Setup]
AppId={#MyAppId}
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

; Let non-admin users choose per-user install; will show UAC dialog if needed.
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=admin

WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
; The checkbox text will be localized automatically
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
#ifdef OneFile
; PyInstaller ONEFILE — single exe
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
#else
; PyInstaller ONEDIR — entire folder
Source: "..\dist\CompressorAndPDFMerger\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch app right after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
