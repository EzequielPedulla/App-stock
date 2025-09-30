; Script de Inno Setup basico para App-Stock
; Instalador automatico completo

#define MyAppName "App-Stock"
#define MyAppVersion "1.0"
#define MyAppPublisher "App-Stock Solutions"
#define MyAppURL "https://github.com/EzequielPedulla/App-stock"
#define MyAppExeName "App-Stock.exe"

[Setup]
; Informacion basica
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Configuracion del instalador
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=App-Stock-Installer-v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Requisitos del sistema
MinVersion=6.1sp1
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Aplicacion principal
Source: "App-Stock.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "instalar_todo.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "iniciar_app.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "INSTRUCCIONES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Ejecutar configuracion automatica despues de la instalacion
Filename: "{app}\instalar_todo.bat"; Description: "Configurar App-Stock automaticamente"; Flags: postinstall runascurrentuser

; Opcion para ejecutar la aplicacion
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\reportes"
Type: filesandordirs; Name: "{app}\.env"
