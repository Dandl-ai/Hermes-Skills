# KoXo Administrator — Notes de Reconnaissance

## Description

KoXo Administrator est un logiciel Windows professionnel (payant) de gestion de comptes et de stockage pour Active Directory. Edité par KoXo Dev (société francaise).

Site officiel : https://www.koxo.net/

## Fonctionnalités

- Creation de comptes en masse sur Windows Server (AD)
- Gestion des utilisateurs, groupes, quotas, dossiers partages
- Import depuis fichiers XML, CSV, LDAP
- Outils integres : KoXo Computers, KoXo Profiles, KoXo Confserv, KoXo Label
- Support de Windows Server 2003 a 2025, clients Win 7 a 11
- Version actuelle : 4.0.0.2 (Juin 2026), v4 en cours de dev (4.0.0.3)
- Utilise PowerShell pour scripts Office 365
- Detection WOW64, detection PowerShell 5.1 vs 7
- Sauvegardes XML regulieres automatiques
- KoXo Computers Autoplace Service V5.5.0.0

## Stack technique

- App Windows desktop (pas web)
- Interagit avec Active Directory (LDAP, AD)
- Scripts PowerShell integrales
- Fichiers XML/CSV pour l'import/export
- Synchronisation automatique
- Structuration hierarchique a 2 niveaux

## Axes d'audit identifiés (runtime, black-box, user non-admin)

1. **Elevation de privileges** : Le logiciel gere des comptes AD → un user standard peut-il creer/supprimer des comptes ? Modifier son propre grade/role dans la config ?

2. **Manipulation de fichiers de config** : Les fichiers XML sont "modulables" → un user peut-il editer les templates pour injecter des commandes ? Ou sont stockes les fichiers de config ? Permissions filesystem ?

3. **Stockage des secrets** : Comment sont stockes les identifiants AD/PowerShell ? Mots de passe en clair dans des XML/INI/registry ?

4. **Injection de commandes** : Les champs d'import CSV/XML → injection de commandes PowerShell ? Fuzzing des champs de saisie (buffer overflow)

5. **DLL hijacking** : L'app charge-t-elle des DLL depuis des repertoires inscriptibles par un user ?

6. **Communication reseau** : Comment dialogue-t-elle avec l'AD ? LDAP chiffre (LDAPS) ou non ? Communication non chiffree ?

## Contexte d'audit

- Application co-developed avec l'utilisateur (Pollux)
- Fournie sous forme de 2 executables (.exe)
- Audit a faire dans une VM Tiny11 (Windows 11 allégé)
- Perspective : utilisateur de base sans aucun accès Administrateur
- Pas d'acces au code source (black-box runtime)

## Versions

V4 (actuelle) :
- 4.0.0.3 (en dev, xx/xx/2026) : corrections encodage, detection WOW64, PowerShell 5.1
- 4.0.0.2 (25/06/2026) : correction traitement XML doublons
- 4.0.0.0 : mise a jour liste fabricants cartes reseau

V3 :
- Derniere version stable publiee sur le site

V2 :
- Version anterieure, page still available

## Site web

- Site Joomla 4 (croise dans le HTML)
- Pages cles : /produits/koxo-administrator, /produits/koxo-administrator/description/specifications-techniques, /produits/telechargements
- Pas de lien de download direct public visible (compte requis)
