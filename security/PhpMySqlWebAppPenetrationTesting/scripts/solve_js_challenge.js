#!/usr/bin/env node
/*
 * Solve an iterative slowAES JS anti-bot challenge (InfinityFree-style free host).
 * Usage: node solve_js_challenge.js <host> [<path>]
 * Feeds the resolved cookie via stdout as "COOKIE=__test=xxxx".
 * Needs /aes.js at the site root. Adjust https.headers / http vs https as needed.
 */
const fs = require('fs');
const vm = require('vm');
const https = require('https');
const http = require('http');

const HOST = process.argv[2] || 'target-app.example.org';
const BASE = process.argv[3] || '/';
const USE_TLS = /^(https|target-app|www|app)/i.test(HOST) ? https : http; // heuristic; override below

const ctx = {};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('/tmp/aes.js', 'utf8'), ctx); // download aes.js from host first

function toNumbers(d) { const e = []; d.replace(/(..)/g, x => e.push(parseInt(x, 16))); return e; }
function toHex(a) { let e = ''; for (const f of a) e += (16 > f ? '0' : '') + f.toString(16); return e.toLowerCase(); }

function get(path, cookie) {
  return new Promise((res, rej) => {
    const mod = USE_TLS ? https : http;
    const req = mod.request({
      host: HOST, port: USE_TLS ? 443 : 80, path, method: 'GET',
      rejectUnauthorized: false,
      headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0', ...(cookie ? { Cookie: cookie } : {}) },
    }, r => { let b = ''; r.on('data', d => b += d); r.on('end', () => res({ status: r.statusCode, body: b })); });
    req.on('error', rej); req.end();
  });
}

(async () => {
  let cookie = null, res = await get(BASE);
  for (let step = 1; step <= 20; step++) {
    const m = res.body.match(/a=toNumbers\("([0-9a-f]+)"\),b=toNumbers\("([0-9a-f]+)"\),c=toNumbers\("([0-9a-f]+)"\)/);
    if (!m) { console.log('COOKIE=' + (cookie || '')); process.exit(0); }
    const [, a, b, c] = m;
    cookie = '__test=' + toHex(ctx.slowAES.decrypt(toNumbers(c), 2, toNumbers(a), toNumbers(b)));
    const red = (res.body.match(/location\.href="([^"]+)"/) || [])[1];
    const next = red ? red.replace(/^https?:\/\/[^/]+/, '') : `/?i=${step + 1}`;
    res = await get(next, cookie);
    console.error(`step ${step}: token -> ${next}`);
  }
  console.error('Max steps');
})();