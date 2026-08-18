; Script de Inno Setup para App-Stock
; La app usa SQLite (un archivo local, sin servidor), por lo que instalar
; App-Stock.exe es el único paso: no hay base de datos externa que configurar.

#define MyAppName "App-Stock"
#define MyAppVersion "1.0"
#define MyAppPublisher "App-Stock Solutions"
#define MyAppURL "https://github.com/EzequielPedulla/App-stock"
#define MyAppExeName "App-Stock.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=App-Stock-Installer-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

MinVersion=6.1sp1
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "App-Stock.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; La base de datos vive en %LOCALAPPDATA%\App-Stock, fuera de la carpeta de
; instalación, así que desinstalar la app no borra el inventario/ventas.
Type: filesandordirs; Name: "{app}\reportes"
