; Script de Inno Setup simplificado para App-Stock
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
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Aplicacion principal
Source: "App-Stock.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "instalar_todo.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "iniciar_app.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "INSTRUCCIONES.txt"; DestDir: "{app}"; Flags: ignoreversion

; Archivos de configuracion
Source: "config.py"; DestDir: "{app}"; Flags: ignoreversion

; Documentacion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Ejecutar configuracion automatica despues de la instalacion
Filename: "{app}\instalar_todo.bat"; Description: "Configurar App-Stock automaticamente"; Flags: postinstall runascurrentuser

; Opcion para ejecutar la aplicacion
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\reportes"
Type: filesandordirs; Name: "{app}\.env"

[Code]
// Funcion para verificar si XAMPP esta instalado
function IsXAMPPInstalled: Boolean;
begin
  Result := DirExists('C:\xampp');
end;

// Funcion para verificar si MySQL esta ejecutandose
function IsMySQLRunning: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('net', 'query mysql', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

// Proceso antes de la instalacion
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Verificar si XAMPP ya esta instalado
  if IsXAMPPInstalled then
  begin
    if MsgBox('XAMPP ya esta instalado en su sistema.' + #13#10 + 
              '¿Desea continuar con la instalacion de App-Stock?', 
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

// Proceso despues de la instalacion
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Crear acceso directo en el escritorio
    CreateShortcut(ExpandConstant('{app}\App-Stock.exe'), 
                   ExpandConstant('{autodesktop}\App-Stock.lnk'), 
                   '', '', '', '', 0, '');
  end;
end;
