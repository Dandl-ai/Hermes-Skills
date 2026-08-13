---
name: WindowsDesktopRuntimeAudit
description: "Audit runtime black-box d'applications desktop Windows en VM — privileges non-admin, instrumentation process, DLL hijacking, secrets, config."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [Security, Windows, Runtime, Desktop, PrivEsc, DLL, BlackBox]
    triggers:
      - "Auditer une application Windows desktop"
      - "Tester une app Windows en tant qu'utilisateur non-admin"
      - "Audit runtime black-box Windows"
      - "Vérifier la sécurité d'un .exe Windows"
    scope:
      - "Applications desktop Windows (Win 7 à 11)"
      - "Logiciels de gestion (AD, ERP, panels admin)"
      - "Outils système Windows"
    prerequisites:
      - "VM Windows (VirtualBox, VMware, Hyper-V)"
      - "Accès à l'exécutable/installateur de l'app cible"
    related_skills:
      - security-analysis-methodology
      - security-reporting-evidence-pack
      - system-package-setup
---

# Audit Runtime Black-Box — Applications Desktop Windows

Auditer une application desktop Windows en boîte noire (sans code source) depuis la perspective d'un utilisateur **non-administrateur**. L'objectif : identifier les failles permettant à un user standard d'escalader ses privilèges, d'accéder à des données protégées, ou d'exécuter du code arbitraire.

## Différences avec l'audit web

| Aspect | Audit Web | Audit Desktop Windows |
|--------|-----------|----------------------|
| Code source | disponible (SAST) | non disponible (black-box) |
| Interface | HTTP/REST | API Win32, GUI, IPC |
| Accès | distant | local sur la machine |
| Privilèges | contexte web/CPU | utilisateur standard |
| Outils | nmap, sqlmap, ffuf | Process Monitor, AccessEnum, Wireshark |
| Vecteurs | SQLi, XSS, CSRF | DLL hijack, priv esc, secrets en clair |

## When to Use

- L'utilisateur fournit un .exe ou un installateur Windows à auditer
- L'objectif est de tester l'app en tant qu'utilisateur non-admin
- Pas de code source disponible (black-box uniquement)
- L'app interagit avec des services système (AD, PowerShell, registre, fichiers)

## Prérequis — Environnement VM

### 1. Préparer la VM Windows

```bash
# Sur l'hôte Linux (VirtualBox déjà installé)
VBoxManage createvm --name "AuditWin" --ostype Windows11_64 --register
VBoxManage modifyvm "AuditWin" --memory 4096 --cpus 2 --firmware efi \
  --nested-hw-virt on --vram 128 --graphicscontroller vmsvga \
  --boot1 dvd --boot2 disk --nic1 nat
VBoxManage createmedium disk --filename "AuditWin.vdi" --size 40960 --variant Standard
VBoxManage storagectl "AuditWin" --name "SATA" --add sata --controller IntelAhci
VBoxManage storageattach "AuditWin" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "AuditWin.vdi"
```

Voir `system-package-setup` pour l'installation de VirtualBox sur Fedora et la création de VM.

### 2. Créer deux comptes utilisateurs

Après installation de Windows dans la VM :
- **Admin** (`Administrateur` ou compte admin par défaut)
- **User standard** (`auditeur`) — sans droits admin, membre du groupe `Users` uniquement

L'audit se fait **exclusivement depuis le compte user standard**.

### 3. Installer les outils d'audit sur la VM

Voir `references/windows-audit-tools.md` pour la liste complète et les URLs de téléchargement.

Outils essentiels (tous gratuits, pas besoin d'admin pour la plupart) :
- **Sysinternals Suite** (Process Monitor, Process Explorer, AccessEnum, Autoruns)
- **Wireshark** (capture réseau, nécessite admin pour Npcap — installer avant de passer en user standard)
- **Strings** (recherche de chaînes dans les binaires)
- **Resource Hacker** (inspection des ressources PE : manifests, dialogs, icons)
- **PEview** ou **CFF Explorer** (analyse des en-têtes PE)

## Méthodologie — 6 Phases

### Phase 1 — Reconnaissance de l'application

Identifier l'architecture et les caractéristiques de l'app **avant** de l'installer :

```powershell
# Sur la VM, depuis le compte admin (avant passage en user standard)
file <app>.exe          # ou : vérifier avec PEview
# Architecture : 32-bit (x86) ou 64-bit (x64) ?
# Est-ce un .NET assembly ? (.NET = facile à décompiler avec ILSpy/dnSpy)
# Est-ce un installateur (MSI, Inno Setup, NSIS) ou un exécutable standalone ?
```

Actions :
- [ ] Noter l'architecture (x86 vs x64) — utile pour le type de DLL hijacking possible
- [ ] Vérifier si l'app demande l'UAC à chaque lancement
- [ ] Vérifier le manifeste embarqué (Resource Hacker) — `requireAdministrator` ? `asInvoker` ?
- [ ] Extraire les strings avec `strings <app>.exe` — secrets, chemins, URLs
- [ ] Identifier le framework (.NET, Electron, Qt, MFC, Delphi...)

### Phase 2 — Analyse du système de fichiers et de la registry

Après installation, **depuis le compte user standard** :

```powershell
# Où l'app s'installe-t-elle ?
dir "C:\Program Files\<App>"
dir "C:\Program Files (x86)\<App>"
dir "%LOCALAPPDATA%\<App>"
dir "%APPDATA%\<App>"

# Permissions sur le dossier d'installation
icacls "C:\Program Files\<App>"
# Chercher : Users:(W) ou Users:(M) = inscriptible par un user standard = DANGER

# Registry — où l'app stocke sa config
reg query "HKLM\SOFTWARE\<App>" /s    # config machine (peut nécessiter admin)
reg query "HKCU\SOFTWARE\<App>" /s    # config user (accessible)
```

Points critiques :
- [ ] Le dossier d'installation est-il inscriptible par `Users` ? → DLL hijacking possible
- [ ] Les fichiers de config (.ini, .xml, .json) sont-ils dans `%APPDATA%` (user-writable) ?
- [ ] La registry `HKLM` contient-elle des secrets en clair ? (mots de passe, clés)
- [ ] Y a-t-il des fichiers de log dans `%LOCALAPPDATA%` ou `%TEMP%` avec des données sensibles ?

### Phase 3 — Analyse des processus et privilèges

Lancer l'app depuis le compte user standard et observer :

```powershell
# Process Monitor (Sysinternals) — capture TOUS les accès
# Filtrer par Process Name = <app>.exe
# Chercher :
#   - ACCESS DENIED (l'app tente d'accéder à des ressources admin)
#   - CreateFile sur des répertoires inscriptibles
#   - RegSetValue sur HKLM (nécessite admin — l'app peut échouer ou contourner)

# Process Explorer — vérifier les privilèges du process
# View > Lower Pane > Handles et DLLs
# Noter : Integrity Level (Medium = user standard, High = admin)
# Noter : quels tokens/privilèges le process possède

# Vérifier si l'app lance des sous-process avec élévation
wmic process where "name='<app>.exe'" get CommandLine /format:list
```

Points critiques :
- [ ] L'app lance-t-elle des process enfants avec `runas` / UAC ?
- [ ] L'app s'exécute-t-elle avec une integrity level supérieure au user (High vs Medium) ?
- [ ] Y a-t-il un service Windows associé ? (`sc query <service_name>`) — tourne-t-il en SYSTEM ?

### Phase 4 — Recherche de secrets et credentials

```powershell
# L'app stocke-t-elle des mots de passe en clair ?
# Fichiers de config
findstr /s /i "password passwort motdepasse secret key token" "C:\Program Files\<App>\*.ini" "C:\Program Files\<App>\*.xml" "C:\Program Files\<App>\*.json" "%APPDATA%\<App>\*"

# Registry
reg query HKCU\SOFTWARE\<App> /s | findstr /i "password secret key token"

# DPAPI — l'app utilise-t-elle DPAPI pour stocker des secrets ?
# (DPAPI = sécurisé, mais check si l'app stocke quand-même en clair à côté)

# Wireshark — capturer le trafic réseau au lancement de l'app
# Chercher : LDAP en clair (port 389 sans TLS), HTTP sans TLS, credentials en clair
```

Points critiques :
- [ ] Mots de passe en clair dans les fichiers de config
- [ ] Credentials dans la registry en clair
- [ ] Communication LDAP non chiffrée (LDAPS port 636 vs LDAP port 389)
- [ ] Tokens de session/d'auth transmis en HTTP (non TLS)

### Phase 5 — DLL Hijacking et Path Vulnerabilities

Le vecteur de DLL hijacking le plus courant et le plus exploitable pour un user non-admin :

```powershell
# 1. Identifier les DLL chargées par l'app
# Process Explorer > Lower Pane View > DLLs
# OU : listdlls <app>.exe (Sysinternals)

# 2. Vérifier les chemins de chargement de DLL
# L'app charge-t-elle des DLL depuis un répertoire inscriptible par l'user ?
#   - C:\Program Files\<App> si Users:(W) permis
#   - %CURRENT_DIR% (répertoire de travail)
#   - %PATH% (répertoires user-writable)

# 3. Test pratique :
#    a. Copier une DLL malveillante (msfvenom ou custom) avec le nom d'une DLL recherchée
#    b. La placer dans le répertoire inscriptible
#    c. Relancer l'app → si la DLL est chargée = code exécuté dans le contexte de l'app

# 4. Vérifier le PATH
echo %PATH%
# Y a-t-il des répertoires user-writable avant les répertoires système ?
```

Points critiques :
- [ ] DLL recherchées par l'app non présentes sur le système → planting possible
- [ ] Répertoire d'installation inscriptible par `Users`
- [ ] PATH contenant des répertoires user-writable en priorité haute
- [ ] L'app charge-t-elle des DLL depuis `%TEMP%` ou `%APPDATA%` ?

### Phase 6 — Fuzzing et injection

```powershell
# Fuzzing des champs de saisie
# - Buffer overflow : entrer des chaînes très longues (10000+ chars) dans les champs
# - Caractères spécials : < > " ' & | ; ` $() {} dans les champs texte
# - Null bytes : \x00 dans les champs
# - Unicode : caractères bidirectionnels, homoglyphes

# Injection de commandes
# Si l'app exécute des commandes système (PowerShell, cmd) :
# - Chercher des champs qui semblent être passés à un shell
# - Essayer : ; calc.exe   |   & calc.exe   |   $(calc.exe)
# - Observer avec Process Monitor si cmd.exe / powershell.exe est lancé

# Injection XML
# Si l'app importe du XML ( configs, templates) :
# - Essayer des XXE : <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]>
# - Essayer des bombs XML (billion laughs)

# Manipulation de fichiers de config
# Depuis le compte user standard :
# - Modifier un fichier .xml/.json/.ini dans %APPDATA%
# - Lancer l'app et observer le comportement
# - Injecter des valeurs malveillantes (paths, commandes, XML)
```

## Outils — Synoptique

| Outil | Rôle | Nécessite admin ? |
|-------|------|-------------------|
| Process Monitor | Capture tous les accès (FS, registry, IPC) | Non (mais limité sans admin) |
| Process Explorer | Inspection des process, DLLs, handles, tokens | Non |
| AccessEnum | Scan de permissions sur fichiers/registry | Non |
| Autoruns | Ce qui s'exécute au démarrage | Non |
| Wireshark | Capture réseau | Oui (Npcap pour l'installation) |
| Strings | Recherche de chaînes dans les binaires | Non |
| Resource Hacker | Inspection des ressources PE | Non |
| PEview / CFF Explorer | Analyse des en-têtes PE | Non |
| ILSpy / dnSpy | Décompilation .NET | Non |
| regshot | Snapshot registry avant/après install | Non |

## Format de finding

```markdown
## [AUDIT-NNN] Titre
**Sévérité** : Critique / Majeur / Mineur
**Vecteur** : DLL Hijacking / Secret en clair / Priv Esc / Injection / ...
**Localisation** : C:\Program Files\<App>\config.xml
**Privilèges requis** : Utilisateur standard (non-admin)
**Preuve** : [screenshot Process Monitor / extrait config / commande de test]
**Impact** : [ce que l'user standard peut faire]
**Remédiation** : [fix recommandé]
```

## Pitfalls

- **Installer les outils Sysinternals AVANT de passer en user standard**. Download et extraction possibles sans admin, mais mieux vaut tout préparer en admin d'abord.
- **Wireshark nécessite Npcap** qui demande admin pour l'installation. Installer Wireshark + Npcap pendant la phase admin, puis capturer en user standard (le service Npcap tourne en arrière-plan).
- **Ne pas tester sur la machine hôte**. Toujours dans une VM isolée. Les payloads DLL peuvent crasher l'app ou le système.
- **Vérifier l'integrity level du process**. Si l'app s'exécute en High integrity (UAC elevated) malgré l'utilisateur standard, le compte rendu doit le noter — l'app contourne l'isolation.
- **Process Monitor génère énormément d'événements**. Toujours filtrer par Process Name avant d'analyser. Sinon, le log devient illisible en quelques secondes.
- **Les fichiers .NET sont facilement décompilables**. Si l'app est en .NET (check avec `file` ou PEview : CLR header présent'), utiliser ILSpy/dnSpy pour récupérer quasi le code source — ça transforme un audit black-box en audit grey-box.
- **Snapshot VM avant chaque test destructif**. Permettre un rollback rapide si un payload crash le système.

## Vérification

- Chaque finding doit avoir une preuve : screenshot Process Monitor, extrait de config, commande reproductible
- Confirmer que le test a été fait depuis le compte **user standard** (pas admin)
- Vérifier que l'integrity level du processus est bien Medium (pas High)
- Si une élévation de privilèges est trouvée, documenter le chemin complet : user standard → action → impact

## Références

- `references/windows-audit-tools.md` — Liste complète des outils avec URLs de téléchargement et procédures d'installation
- `references/dll-hijacking-procedure.md` — Procédure détaillée de test DLL hijacking étape par étape
- `references/koxo-admin-recon.md` — Notes de reconnaissance sur KoXo Administrator (app cible de la session initiale)
