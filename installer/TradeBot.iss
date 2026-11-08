; TradeBot per-user installer (self-contained — no Python required on target PC)
; Built by build_setup.ps1 → setup-v0.2.1.exe (onedir layout)

#define MyAppName "TradeBot"
#define MyAppVersion "0.2.1"
#define MyAppPublisher "TradeBot"
#define MyAppExeName "TradeBot.exe"
#define MyAppId "{{A7E3C2B1-4D5F-6A78-9B0C-1D2E3F4A5B6C}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..
OutputBaseFilename=setup-v{#MyAppVersion}
SetupIconFile=assets\art.ico
WizardImageFile=assets\wizard.bmp
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PyInstaller onedir: TradeBot.exe + _internal\ (no TEMP extract on start)
Source: "..\dist\TradeBot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Colibri runtime (no model weights — downloaded later via HuggingFace)
Source: "payload\colibri\*"; DestDir: "{app}\colibri"; Flags: ignoreversion recursesubdirs createallsubdirs
; Portable CPython for coli setup/serve
Source: "payload\python\*"; DestDir: "{app}\runtime\python"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DeleteUserData: Boolean;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  DeleteUserData := False;
  if not UninstallSilent then
  begin
    if MsgBox(
         'Also remove TradeBot data under AppData\Local\TradeBot?'#13#10 +
         '(API keys, HuggingFace token, config, logs, caches, and Colibri models)',
         mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      DeleteUserData := True;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if (CurUninstallStep = usPostUninstall) and DeleteUserData then
  begin
    DataDir := ExpandConstant('{localappdata}\TradeBot');
    if DirExists(DataDir) then
      DelTree(DataDir, True, True, True);
  end;
end;
