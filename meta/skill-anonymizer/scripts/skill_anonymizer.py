#!/usr/bin/env python3
"""
Skill Anonymizer Scanner
=========================
Scans a skill directory for identifiers that could de-anonymize the author
or reveal the real target/engagement.

Categories scanned:
  1. Network  — domains, IPs (non-reserved), URLs, custom ports
  2. Secrets  — API keys, bearer tokens, passwords, .env values, SSH fingerprints
  3. Personal — names, emails, usernames, home dirs, real paths
  4. Project  — repo URLs, commit hashes, prefixed IDs (sim_*, report_*, graph_*),
                UUIDs, DB table names, env var names with project prefixes
  5. Temporal — ISO timestamps, Unix timestamps, date references
  6. Linguistic — non-English identifiers (Unicode-aware)
  7. Metadata  — git author config, editor artifacts, file comments with names

Usage:
  python3 skill_anonymizer.py --scan /path/to/skill/
  python3 skill_anonymizer.py --scan --strict /path/to/skill/
  python3 skill_anonymizer.py --scan --allowlist allowlist.txt /path/to/skill/
  python3 skill_anonymizer.py --replace /path/to/skill/   # interactive mode

Exit codes:
  0 — CLEAN (no hits)
  1 — FINDINGS (hits found, review required)
  2 — ERROR (scanner error)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ─── Reserved / safe ranges (excluded from hits) ───────────────────────

RESERVED_IPV4 = {
    # RFC 5737 — TEST-NET-1/2/3
    "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24",
    # RFC 1918 — private
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    # Loopback
    "127.0.0.0/8",
    # Link-local
    "169.254.0.0/16",
    # APIPA / benchmark
    "0.0.0.0/8", "240.0.0.0/4",
}

SAFE_DOMAINS = {
    "example.com", "example.org", "example.net",
    "example-proxy.com", "example-project.com",
    "localhost", "test", "invalid",
    "acme.com", "acme.org",
    "anon.example.com", "anon@example.com",
}

SAFE_PLACEHOLDER_DATES = {
    "2025-01-01", "2025-01-01T00:00:00", "2025-01-01T00:00:00.000000",
    "1700000000",  # safe unix timestamp
}

# Common English placeholder words that should NOT be flagged
COMMON_PLACEHOLDER_WORDS = frozenset({
    "the", "target", "app", "example", "test", "testuser", "anon",
    "placeholder", "your", "here", "acme", "sample", "demo",
    "project", "skill", "model", "config", "service", "backend",
    "frontend", "server", "client", "agent", "user", "admin",
})

# TLD-like strings that are actually method/attribute names or file extensions
# (prevents false positives like path.name, re.search, allowlist.txt)
EXCLUDED_TLDS = frozenset({
    # Python/JS methods
    "name", "split", "search", "compile", "finditer", "group", "start", "end",
    "rfind", "find", "splitlines", "append", "extend", "scan", "path", "strict",
    "allowlist", "json", "stderr", "exit", "rglob", "parts", "dumps", "suffix",
    "startswith", "strip", "items", "keys", "values", "get", "set", "update",
    "read", "write", "open", "close", "readtext", "isdir", "isfile", "exists",
    "sort", "sorted", "lower", "upper", "isalpha", "isdigit", "format",
    "replace", "sub", "match", "fullmatch", "findall",
    "join", "encode", "decode", "issymlink",
    "resolve", "absolute", "relative",
    "clear", "add", "pop", "remove", "discard", "fromkeys",
    "iter", "next", "type", "len", "str", "int", "float", "bool", "list", "dict",
    # File extensions that look like TLDs
    "txt", "py", "js", "sh", "md", "json", "yaml", "yml", "toml",
    "cfg", "ini", "csv", "html", "xml", "sql", "log", "db", "swp",
})
_EXCLUDED_TLDS_ALT = "|".join(sorted(EXCLUDED_TLDS))

# ─── Patterns ───────────────────────────────────────────────────────────

PATTERNS: Dict[str, List[Tuple[str, str, str]]] = {
    # category: [(id, regex, description), ...]
    "Network": [
        ("DOMAIN", r'(?<![a-z])([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)'
                    r'(?!example\.(com|org|net)|acme\.(com|org)|localhost|test'
                    r'|example-proxy\.com|example-project\.com|anon\.example\.com)'
                    r'(?!' + _EXCLUDED_TLDS_ALT + r'\b)'
                    r'[a-z]{2,63}\b', "Domain name"),
        ("IPV4", r'\b(?!192\.0\.2\.|198\.51\.100\.|203\.0\.113\.|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|0\.|169\.254\.|240\.)'
                 r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "Non-reserved IPv4 address"),
        ("IPV6", r'(?<![0-9a-fA-F:])(?!2001:0?db8:)'
                 r'(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}\b'
                 r'|(?<![0-9a-fA-F:])'
                 r'(?:[0-9a-fA-F]{1,4}:){2}::[0-9a-fA-F]{0,4}\b', "Non-reserved IPv6 address"),
        ("CUSTOM_PORT", r':(\d{4,5})\b', "Non-standard port (possible service identifier)"),
    ],
    "Secrets": [
        ("API_KEY_SK", r'\bsk-[a-zA-Z0-9]{20,}\b', "OpenAI-style API key"),
        ("API_KEY_GOOGLE", r'\bAIza[a-zA-Z0-9_-]{35}\b', "Google API key"),
        ("BEARER_TOKEN", r'Bearer\s+[a-zA-Z0-9_.~+/=-]{20,}', "Bearer token"),
        ("JWT", r'\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b', "JWT token"),
        ("PASSWORD_VALUE", r'(?:password|passwd|pwd)\s*[=:]\s*\S+', "Password value"),
        ("ENV_VALUE", r'(?:^|\n)\s*[A-Z][A-Z0-9_]{3,}=(?!\\*\*\\*|your-|example|placeholder|test|anon)[^\s]{4,}',
                       "Env variable with real value"),
        ("SSH_FINGERPRINT", r'SHA256:[a-zA-Z0-9+/=]{43,}', "SSH fingerprint"),
        ("AWS_ACCOUNT", r'\b\d{12}\b', "Possible AWS account ID (12 digits)"),
        ("GCP_PROJECT", r'projects/\d{8,20}/', "GCP project identifier"),
    ],
    "Personal": [
        ("EMAIL", r'\b(?!anon@example\.com|user@example\.com)[a-zA-Z0-9._%+-]+@'
                  r'(?!example\.(com|org|net)|x\.com\b)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
                  "Email address"),
        ("HOME_DIR", r'/home/(?!anon\b)[a-zA-Z][a-zA-Z0-9_-]{1,30}', "Real home directory path"),
        ("WINDOWS_USER", r'(?i)C:\\\\Users\\\\(?!anon|testuser|public)[a-zA-Z][a-zA-Z0-9_-]{1,30}',
         "Windows user path"),
        ("USERNAME_AT", r'@(?!(?:testuser|anon|example|acme)\b)[a-zA-Z][a-zA-Z0-9_]{2,20}\b',
         "Social media handle or @username"),
    ],
    "Project": [
        ("REPO_URL", r'github\.com/[a-zA-Z0-9][a-zA-Z0-9-]*/[a-zA-Z0-9][a-zA-Z0-9._-]*',
         "GitHub repository URL"),
        ("COMMIT_HASH", r'\b(?i:commit\s+|@)?[0-9a-f]{7,40}\b(?!\.)(?<![0-9a-f])'
                        r'(?=.*[a-f])', "Possible git commit hash"),
        ("PREFIXED_ID", r'\b(sim|report|graph|task|run|job|session)_[0-9a-f]{8,}\b',
                        "Prefixed hex ID (simulation/report/graph/etc)"),
        ("UUID", r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',
                 "UUID"),
        ("ENV_VAR_PROJECT", r'\b[A-Z]{2,}_(?:API_KEY|DB_HOST|DB_PASS|SECRET|TOKEN|URL)\b',
                            "Project-specific env var name"),
    ],
    "Temporal": [
        ("ISO_TIMESTAMP", r'\b(?!2025-01-01)[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}'
                           r'(?:\.\d+)?Z?\b', "ISO 8601 timestamp"),
        ("DATE_ONLY", r'\b(?!2025-01-01)[0-9]{4}-[0-9]{2}-[0-9]{2}\b', "Date (YYYY-MM-DD)"),
        ("UNIX_TS", r'\b(?!1700000000\b)1[0-9]{8,9}\b', "Possible Unix timestamp"),
        ("LOG_TS", r'\[[0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}\]',
                   "Log timestamp bracket"),
    ],
    "Linguistic": [
        # CJK characters that look like real org/person names (not common Chinese words)
        ("CJK_NAME", r'[\u4e00-\u9fff]{2,4}(?:[\u4e00-\u9fff]{1,3})?(?=[\s,;。\n]|$)',
                     "CJK identifier (possible Chinese name/org)"),
    ],
    "Metadata": [
        ("GIT_AUTHOR", r'(?i)git\s+(?:config|log).*?(?:user\.name|user\.email|author)',
                       "Git author reference"),
        ("VSCODE_DIR", r'\.vscode[/\\]', "VSCode workspace artifact"),
        ("IDEA_DIR", r'\.idea[/\\]', "IntelliJ workspace artifact"),
        ("DS_STORE", r'\.DS_Store', "macOS file metadata"),
        ("SWP_FILE", r'\.swp\b', "Vim swap file"),
        ("CODE_COMMENT_NAME",
         r'#\s*(?:TODO|FIXME|HACK|XXX)\s*(?:for|by|from)\s+[A-Z][a-z]+',
         "Code comment with potential real name"),
    ],
}

# ─── Strict-mode extra patterns (higher false-positive rate) ─────────────

STRICT_PATTERNS: Dict[str, List[Tuple[str, str, str]]] = {
    "Strict": [
        ("ANY_HEX_8", r'\b[0-9a-f]{8,}\b', "Hex string 8+ chars (possible ID)"),
        ("BASE64_BLOB", r'[A-Za-z0-9+/]{40,}={0,2}', "Base64 blob"),
        ("VERSIONED_PATH",
         r'/[a-z][a-z0-9-]*(?:/(?:src|dist|bin|lib|app|api|core))?/[a-z][a-z0-9._/-]{5,}',
         "Detailed filesystem path (possible real project)"),
        ("DOCKER_TAG",
         r'(?:^|\s)(?:[a-z][a-z0-9-]*/)?[a-z][a-z0-9-]*:[a-z0-9][a-z0-9._-]{2,}',
         "Docker image:tag (possible private image)"),
        ("SEMVER_FILE",
         r'(?i)(?:version|ver|v)\s*[=:]\s*[0-9]+\.[0-9]+\.[0-9]+(?:[-+].+)?',
         "Version string (possible project version)"),
    ],
}

# File extensions to scan
SCAN_EXTENSIONS = {
    ".md", ".py", ".js", ".ts", ".sh", ".bash", ".json", ".yaml", ".yml",
    ".toml", ".cfg", ".ini", ".env", ".txt", ".html", ".css", ".xml",
    ".sql", ".csv", ".jsonl",
}

# Files to always scan (no extension)
SCAN_FILENAMES = {
    "Dockerfile", "Makefile", ".env", "Procfile", "LICENSE",
    ".gitignore", ".dockerignore",
}


def _is_reserved_ipv4(ip: str) -> bool:
    """Check if an IPv4 is in a reserved range."""
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return False
    o = octets
    if o[0] == 0 or o[0] >= 240:
        return True
    if o[0] == 127:
        return True
    if o[0] == 10:
        return True
    if o[0] == 172 and 16 <= o[1] <= 31:
        return True
    if o[0] == 192 and o[1] == 168:
        return True
    if o[0] == 192 and o[1] == 0 and o[2] == 2:
        return True
    if o[0] == 198 and o[1] == 51 and o[2] == 100:
        return True
    if o[0] == 203 and o[1] == 0 and o[2] == 113:
        return True
    if o[0] == 169 and o[1] == 254:
        return True
    return False


def _should_scan(path: Path) -> bool:
    """Determine if a file should be scanned."""
    if path.is_dir() or path.is_symlink():
        return False
    name = path.name
    if name in SCAN_FILENAMES:
        return True
    ext = path.suffix.lower()
    if ext in SCAN_EXTENSIONS:
        return True
    return False


def _load_allowlist(path: str) -> List[str]:
    """Load allowlist patterns (one regex per line, # comments allowed)."""
    patterns = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns


def _is_allowlisted(text: str, allowlist: List[str]) -> bool:
    """Check if a match is in the allowlist."""
    for pattern in allowlist:
        if re.search(pattern, text):
            return True
    return False


def scan_file(
    filepath: Path,
    strict: bool = False,
    allowlist: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Scan a single file. Returns a list of findings:
      {category, pattern_id, description, line_num, match_text, line_text}
    """
    findings = []
    allowlist = allowlist or []

    try:
        raw = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return findings

    lines = raw.splitlines()

    all_patterns = dict(PATTERNS)
    if strict:
        for cat, plist in STRICT_PATTERNS.items():
            all_patterns[f"{cat} (strict)"] = plist

    for category, plist in all_patterns.items():
        for pid, regex, desc in plist:
            compiled = re.compile(regex, re.MULTILINE)
            for match in compiled.finditer(raw):
                match_text = match.group(0)

                # Skip allowlisted matches
                if _is_allowlisted(match_text, allowlist):
                    continue

                # Skip reserved IPs
                if "IPV4" in pid:
                    if _is_reserved_ipv4(match_text):
                        continue

                # Skip safe domains
                if "DOMAIN" in pid:
                    domain = match_text.lower().lstrip(".")
                    if any(s in domain for s in SAFE_DOMAINS):
                        continue
                    # Skip if it's part of a URL that starts with a safe domain
                    parts_before = raw[:match.start()].rstrip().lower()
                    if any(f"://{s}" in parts_before for s in SAFE_DOMAINS):
                        continue

                # Skip safe placeholder dates
                if pid == "ISO_TIMESTAMP" or pid == "DATE_ONLY":
                    if match_text.strip() in SAFE_PLACEHOLDER_DATES:
                        continue

                # Skip AWS account if it's a documented placeholder
                if pid == "AWS_ACCOUNT" and match_text == "123456789012":
                    continue

                # Find line number
                line_start = raw.rfind("\n", 0, match.start()) + 1
                line_num = raw[:match.start()].count("\n") + 1
                line_end = raw.find("\n", match.end())
                if line_end == -1:
                    line_end = len(raw)
                line_text = raw[line_start:line_end].strip()

                # Skip if match is in a code comment that says "example" or "placeholder"
                lower_match = match_text.lower()
                if any(w in lower_match for w in ("example", "placeholder", "your-", "test", "anon")):
                    if pid not in ("ISO_TIMESTAMP", "DATE_ONLY", "ENV_VALUE"):
                        continue

                findings.append({
                    "category": category,
                    "pattern_id": pid,
                    "description": desc,
                    "line_num": line_num,
                    "match_text": match_text[:200],
                    "line_text": line_text[:300] if line_text else "",
                    "file": str(filepath),
                })

    return findings


def scan_directory(
    dirpath: str,
    strict: bool = False,
    allowlist_path: Optional[str] = None,
) -> Tuple[List[Dict], int, int]:
    """
    Scan all files in a directory tree.
    Returns (findings, files_scanned, total_files).
    """
    root = Path(dirpath)
    if not root.is_dir():
        print(f"ERROR: {dirpath} is not a directory", file=sys.stderr)
        return [], 0, 0

    allowlist = _load_allowlist(allowlist_path) if allowlist_path else []

    findings = []
    files_scanned = 0
    total_files = 0

    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        # Skip the allowlist file itself (it contains patterns that match)
        if path.name == "allowlist.txt" or path.name == ".allowlist":
            continue
        if not _should_scan(path):
            continue
        total_files += 1
        file_findings = scan_file(path, strict=strict, allowlist=allowlist)
        findings.extend(file_findings)
        files_scanned += 1

    return findings, files_scanned, total_files


def format_findings(findings: List[Dict]) -> str:
    """Format findings for terminal output."""
    if not findings:
        return "CLEAN — no identifiers found."

    lines = [f"\n{'='*60}", f" {len(findings)} FINDING(S)", f"{'='*60}"]

    # Group by category
    by_cat: Dict[str, List[Dict]] = {}
    for f in findings:
        by_cat.setdefault(f["category"], []).append(f)

    for cat in sorted(by_cat.keys()):
        lines.append(f"\n── {cat} ({len(by_cat[cat])} hit(s)) ──")
        for f in by_cat[cat]:
            lines.append(
                f"  [{f['pattern_id']}] {f['description']}"
                f"\n  {f['file']}:{f['line_num']}"
                f"\n  match: {f['match_text']!r}"
            )
            if f["line_text"]:
                lines.append(f"  line:  {f['line_text'][:200]}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Scan a skill directory for de-anonymizing identifiers."
    )
    parser.add_argument("path", help="Path to the skill directory to scan")
    parser.add_argument("--scan", action="store_true",
                        help="Run a scan (default action)")
    parser.add_argument("--strict", action="store_true",
                        help="Enable strict-mode patterns (higher false-positive rate)")
    parser.add_argument("--allowlist", metavar="FILE",
                        help="Path to an allowlist file (one regex per line, # comments allowed)")
    parser.add_argument("--json", action="store_true",
                        help="Output findings as JSON")
    args = parser.parse_args()

    if not args.scan:
        args.scan = True  # default action

    findings, files_scanned, total_files = scan_directory(
        args.path,
        strict=args.strict,
        allowlist_path=args.allowlist,
    )

    if args.json:
        import json
        print(json.dumps({
            "findings_count": len(findings),
            "files_scanned": files_scanned,
            "total_files": total_files,
            "findings": findings,
        }, indent=2))
    else:
        print(f"\nScanned {files_scanned} file(s) in {args.path}")
        print(format_findings(findings))

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
