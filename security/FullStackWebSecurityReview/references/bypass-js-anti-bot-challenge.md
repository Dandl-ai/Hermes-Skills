# Bypassing a multi-step JS anti-bot challenge

Some shared/free hosts (InfinityFree-style) gate the real page behind an iterative **JavaScript challenge**. The homepage returns an HTML body that loads `/aes.js` (a `slowAES` implementation) and runs:

```js
var a=toNumbers("...hex key..."), b=toNumbers("...hex iv..."), c=toNumbers("...hex ciphertext...");
document.cookie="__test="+toHex(slowAES.decrypt(c,2,a,b))+"; ... path=/";
location.href="http://site/?i=1";   // note: i increments each iteration
```

It re-randomises `c` on each hop, so a single solve is not enough — you must loop through the challenge until the body stops being a challenge (i.e. you receive the real page or a 3xx/301 to HTTPS).

## Recognising it
The body contains `slowAES.decrypt` + `toNumbers(...)` + a `__test` cookie + a `location.href=".../?i=N"` redirect.

## Working Node.js solver pattern
Run `aes.js` in a Node `vm` context, then repeatedly: parse `a,b,c`, decrypt, set the cookie, and follow the redirect. Re-run until no challenge pattern matches.

```js
const fs = require('fs'); const vm = require('vm');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('/tmp/aes.js', 'utf8'), ctx);

function toNumbers(d){const e=[];d.replace(/(..)/g,x=>e.push(parseInt(x,16)));return e;}
function toHex(a){let e='';for(const f of a)e+=(16>f?'0':'')+f.toString(16);return e.toLowerCase();}

// get(pagePath, cookie) -> Promise<{status, headers, body}>  (use https for 443)
let cookie=null, res = await get('/');
for (let step=1; step<=20; step++) {
  const m = res.body.match(/a=toNumbers\("([0-9a-f]+)"\),b=toNumbers\("([0-9a-f]+)"\),c=toNumbers\("([0-9a-f]+)"\)/);
  if (!m) { /* no challenge: real page or redirect — done */ break; }
  const [,a,b,c]=m;
  cookie = `__test=${toHex(ctx.slowAES.decrypt(toNumbers(c),2,toNumbers(a),toNumbers(b)))}`;
  const red=(res.body.match(/location\.href="([^"]+)"/)||[])[1];
  res = await get(red || `/?i=${step+1}`, cookie);
}
```

## Pitfalls hit
- The homepage may be HTTP but then **301 to HTTPS** — the solver must follow redirects and switch libraries (the `https` module) with `rejectUnauthorized:false`, because the challenge continues across the redirect.
- **Quoting hell:** building the curl command with a User-Agent containing parentheses broke `/bin/sh`. Prefer Node's built-in `http`/`https` modules over spawning `curl` to avoid shell-escaping bugs.
- Once you hold the `__test` cookie, reuse it (and any `PHPSESSID`) for subsequent page fetches in the same script so you do not re-solve every request.

## Nature of the control
This is a deterrent for naive bots, **not** a security boundary — it is trivially bypassable. Note it in a report as a caveat, never as a real control.