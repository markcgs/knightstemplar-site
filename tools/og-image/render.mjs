// Share image (Open Graph / Twitter card) renderer.
// Usage: node tools/og-image/render.mjs [config.json ...]
// Renders each config into a 1200x630 JPEG with the pre-installed Playwright
// Chromium. Not part of the site build: run it when the logo, photo or wording
// changes, then commit the image it writes. Paths in a config are relative to it.
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

// Playwright via require so a global install (NODE_PATH) works too.
const { chromium } = createRequire(import.meta.url)('playwright');
const here = dirname(fileURLToPath(import.meta.url));
const configs = process.argv.slice(2);
if (!configs.length) configs.push(resolve(here, 'config.json'));

const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.avif': 'image/avif' };
const dataUri = (p) => `data:${MIME[extname(p).toLowerCase()]};base64,${readFileSync(p).toString('base64')}`;
const esc = (s = '') => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function html(c, base) {
  const col = { bg: '#1f2a3d', bg2: '#121a28', text: '#ffffff', muted: 'rgba(255,255,255,.82)', accent: '#e3b341', ...c.colors };
  const f = { display: 'Georgia, serif', body: 'Inter, system-ui, sans-serif', ...c.fonts };
  const logo = c.logo ? dataUri(resolve(base, c.logo)) : '';
  const photo = c.photo ? dataUri(resolve(base, c.photo)) : '';
  const layout = c.layout || (photo ? 'split' : 'center');
  const nameSize = c.nameSize || (layout === 'center' ? 64 : 58);
  const logoH = c.logoHeight || (layout === 'center' ? 200 : 120);
  const plate = c.logoPlate ? `${c.logoRadius === 999 ? "aspect-ratio:1/1;" : ""}background:${c.logoPlate};padding:${c.logoPad ?? 18}px;border-radius:${c.logoRadius ?? 18}px;` : '';
  const logoTag = logo ? `<img class="logo" src="${logo}" alt="" style="max-height:${logoH}px;${plate}">` : '';
  const text = `
    ${c.logoInText && logoTag ? logoTag : ''}
    ${c.kicker ? `<div class="kicker">${esc(c.kicker)}</div>` : ''}
    ${c.name ? `<div class="name">${esc(c.name)}</div>` : ''}
    ${c.tagline ? `<div class="tag">${esc(c.tagline)}</div>` : ''}`;
  const foot = `<div class="foot"><span class="rule"></span><span class="dom">${esc(c.domain || '')}</span></div>`;
  let body;
  if (layout === 'split') {
    body = `<div class="panel">${logoTag}<div class="txt">${text}</div>${foot}</div>
      <div class="photo"><div class="stripe"></div></div>`;
  } else if (layout === 'overlay') {
    body = `<div class="full"></div><div class="scrim"></div><div class="panel ov">${logoTag}<div class="txt">${text}</div>${foot}</div>`;
  } else if (layout === 'logo-left') {
    body = `<div class="glow"></div><div class="ll"><div class="llogo">${logoTag}</div><div class="lt"><div class="txt">${text}</div>${foot}</div></div>`;
  } else {
    body = `<div class="glow"></div><div class="center">${logoTag}<div class="txt">${text}</div>${foot}</div>`;
  }
  const pw = c.panelWidth || 640;
  return `<!doctype html><html><head><meta charset="utf-8">
  ${f.css ? `<link rel="stylesheet" href="${f.css}">` : ''}
  <style>
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{width:1200px;height:630px;overflow:hidden}
  body{background:linear-gradient(135deg,${col.bg} 0%,${col.bg2} 100%);color:${col.text};font-family:${f.body};position:relative}
  ${c.texture ? `body::before{content:"";position:absolute;inset:0;background-image:url(${dataUri(resolve(base, c.texture))});background-size:cover;opacity:${c.textureOpacity ?? .12}}` : ''}
  .glow{position:absolute;inset:0;background:radial-gradient(ellipse 60% 70% at ${layout === 'logo-left' ? '26%' : '50%'} 40%,${col.glow || 'rgba(255,255,255,.10)'},transparent 70%)}
  .logo{display:block;max-width:${c.logoMaxWidth || 340}px;object-fit:contain;${c.logoShadow === false ? '' : 'filter:drop-shadow(0 6px 18px rgba(0,0,0,.25));'}}
  .kicker{font-family:${f.body};font-size:${c.kickerSize || 22}px;letter-spacing:.16em;text-transform:uppercase;font-weight:600;color:${col.accent};margin-bottom:14px}
  .name{font-family:${f.display};font-weight:${c.nameWeight || 700};font-size:${nameSize}px;line-height:1.06;letter-spacing:${c.nameTracking || '-.01em'};${c.nameUpper ? 'text-transform:uppercase;' : ''}text-wrap:balance}
  .tag{font-size:${c.tagSize || 27}px;line-height:1.35;color:${col.muted};margin-top:18px;text-wrap:balance}
  .foot{display:flex;align-items:center;gap:16px}
  .rule{display:block;width:56px;height:5px;border-radius:3px;background:${col.accent}}
  .dom{font-size:22px;font-weight:600;letter-spacing:.06em;color:${col.text}}
  .panel{position:absolute;left:0;top:0;bottom:0;width:${pw}px;padding:54px 56px 50px;display:flex;flex-direction:column;justify-content:space-between;gap:20px;z-index:2}
  .panel .txt{margin-top:auto;margin-bottom:auto}
  .photo{position:absolute;right:0;top:0;bottom:0;left:${pw}px;background:url(${photo}) ${c.photoPosition || 'center'}/cover}
  .stripe{position:absolute;left:0;top:0;bottom:0;width:8px;background:${col.accent}}
  .full{position:absolute;inset:0;background:url(${photo}) ${c.photoPosition || 'center'}/cover}
  .scrim{position:absolute;inset:0;background:linear-gradient(90deg,${col.bg} 0%,${col.bg}ee 38%,${col.bg}99 60%,transparent 85%)}
  .panel.ov{width:${c.panelWidth || 720}px}
  .center{position:absolute;inset:0;padding:48px 80px 44px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;text-align:center}
  .center .logo{margin:0 auto}
  .center .txt{margin:auto 0}
  .ll{position:absolute;inset:0;display:flex;align-items:center;padding:56px 64px;gap:56px}
  .llogo{flex:0 0 ${c.logoCol || 380}px;display:flex;justify-content:center}
  .ll .logo{max-height:${c.logoHeight || 400}px;max-width:${c.logoCol || 380}px}
  .lt{flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px;height:100%}
  ${c.css || ''}
  </style></head><body>${body}</body></html>`;
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
for (const file of configs) {
  const path = resolve(file);
  const base = dirname(path);
  const list = [].concat(JSON.parse(readFileSync(path, 'utf8')));
  for (const c of list) {
    await page.setContent(html(c, base), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const out = resolve(base, c.out);
    writeFileSync(out, await page.screenshot({ type: 'jpeg', quality: c.quality || 86 }));
    console.log('wrote', out);
  }
}
await browser.close();
