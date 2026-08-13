# Outils d'Audit Runtime Windows — Liste et Installation

## Sysinternals Suite (essentiel)

Téléchargement : https://download.sysinternals.com/files/SysinternalsSuite.zip

Outils clés de la suite :

### Process Monitor (procmon)
Capture en temps réel de TOUS les accès filesystem, registry, réseau, process/thread.
- Pas besoin d'admin pour lancer, mais les données sont plus complètes avec admin
- Filtrer : Process Name = `<app>.exe`
- Chercher : ACCESS DENIED, CreateFile PATH_NOT_FOUND, RegSetValue
- Export : File > Save > CSV (pour analyse ultérieure)

### Process Explorer (procexp)
Inspection des processus en cours : DLLs chargées, handles, tokens, integrity level.
- View > Lower Pane View > DLLs → voir toutes les DLLs chargées par l'app
- View > Lower Pane View > Handles → voir les fichiers/registry keys ouverts
- Gérer un process : Properties > Security → voir le token et les privilèges
-détection : Integrity Level (Medium = user standard, High = admin)

### AccessEnum
Scan de permissions sur une arborescence de fichiers ou la registry.
- Cible : `C:\Program Files\<App>`
- Affiche : quels utilisateurs/groupes ont Read / Write / Execute
- Danger : `Users` avec Write dans le dossier d'installation

### Autoruns
Liste tout ce qui s'exécute au démarrage (services, scheduled tasks, drivers, shell extensions).
- Vérifier si l'app installe un service qui tourne en SYSTEM
- Scheduled tasks avec l'app en action

### listDLLs
Liste les DLLs chargées par un processus en ligne de commande.
```cmd
listdlls <app>.exe
```

## Wireshark

Téléchargement : https://www.wireshark.org/download.html

```
Installer Wireshark + Npcap pendant la phase admin.
Npcap enables la capture réseau en user standard.
```

Capture au lancement de l'app :
- Filtrer par port LDAP (389) ou LDAPS (636) pour analyser la comm AD
- Filtrer HTTP/HTTPS : l'app communique-t-elle en clair ?
- Chercher : credentials en clair dans les packets LDAP bind requests

## Outils d'analyse PE

### Resource Hacker
Téléchargement : http://angusj.com/resourcehacker/
- Ouvrir le .exe
- Manifeste : `RT_MANIFEST` → vérifier `requireAdministrator` vs `asInvoker`
- Dialogues : `RT_DIALOG` → identifier les champs de saisie
- Version info : `RT_VERSION` → architecte x86 vs x64

### PEview
Téléchargement : https://www.heaventools.com/pe-viewer.htm
- Sections : .text, .data, .rdata, .rsrc
- Header : Characteristics (GUI vs Console subsystem)
- Data directories : .NET (CLR) header présent = décompilable avec ILSpy

### CFF Explorer
Alternative à PEview, plus complet.
Téléchargement : ntcore.com

## Décompilation .NET (si applicable)

### dnSpy
Téléchargement : https://github.com/dnSpy/dnSpy/releases
Permet de déboguer directement le code source décompilé.

### ILSpy
Téléchargement : https://github.com/icsharpcode/ILSpy/releases
Visualise le code source à partir des binaires .NET.

Procédure :
```cmd
# Vérifier si l'app est .NET :
# Resource Hacker > Manifeste > s'il mentionne .NET
# OU : CFF Explorer > .NET Directory > si présent .NET
# OU : ildasm <app>.exe (si .NET SDK installé) > check IL code

# Ouvrir avec dnSpy
# Le code source apparaît quasi-complet
# Debug : Debug > Start Debug
```

## Resource extraction

### Strings (Sysinternals)
```cmd
strings -accepteula <app>.exe > strings.txt
# Chercher :
#   password / motdepasse / secret / token / key
#   http:// ou https:// (URLs potentielles)
#   -service / -install / -uninstall (arguments CLI)
#   -admin / -supervisor / -debug mode (backdoors?)
```

## Registry snapshot

### regshot
Téléchargement : https://sourceforge.net/projects/regshot/
```cmd
# 1. Snapshot avant installation de l'app
# 2. Installer l'app
# 3. Snapshot après
# 4. Compare → voir quelles keys ont été créées/modifiées
# Chercher : secrets en clair, chemins d'execution, mappages ID-utilisateur
```

## Outils bonus (optionnel)

### TriggerKite / TcpLogView (NirSoft)
Log des connexions TCP établies par chaque application.
Téléchargement : https://www.nirsoft.net/utils/tcp_log_view.html

### FolderChangesView (NirSoft)
Surveille les changements dans un dossier.
Téléchargement : https://www.nirsoft.net/utils/folder_changes_view.html

### RunAsDate (NirSoft)
Lance une app avec une date/heure simulée — tester les licenses d'essai.
