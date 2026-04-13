/**
 * Utilitário: Descoberta da estrutura do formulário TabNet
 *
 * Acessa a página do DATASUS, inspeciona todos os elementos
 * do formulário e salva o resultado em logs/form_discovery.json
 *
 * Uso: node descobrir_form.js
 */

const { chromium } = require('playwright');
const fs   = require('fs');
const path = require('path');

const URL      = 'http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qabr.def';
const LOG_DIR  = path.join(__dirname, 'logs');
const OUT_FILE = path.join(LOG_DIR, 'form_discovery.json');

async function main() {
  if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: false });
  const page    = await browser.newPage();

  console.log(`Acessando: ${URL}`);
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60_000 });
  await page.waitForTimeout(3000);

  const estrutura = await page.evaluate(() => {
    const resultado = {};

    // ── Selects ───────────────────────────────
    resultado.selects = Array.from(document.querySelectorAll('select')).map(sel => ({
      name    : sel.name,
      id      : sel.id,
      multiple: sel.multiple,
      options : Array.from(sel.options).map(o => ({
        value   : o.value,
        text    : o.text.trim(),
        selected: o.selected,
      })),
    }));

    // ── Inputs ────────────────────────────────
    resultado.inputs = Array.from(document.querySelectorAll('input')).map(inp => ({
      type : inp.type,
      name : inp.name,
      id   : inp.id,
      value: inp.value,
    }));

    // ── Form ──────────────────────────────────
    const form = document.querySelector('form');
    resultado.form = form
      ? { action: form.action, method: form.method, id: form.id }
      : null;

    // ── Título da página ─────────────────────
    resultado.titulo = document.title;

    return resultado;
  });

  fs.writeFileSync(OUT_FILE, JSON.stringify(estrutura, null, 2));
  console.log(`\nEstrutura salva em: ${OUT_FILE}`);

  // Mostra resumo
  console.log('\n── SELECTS ──');
  estrutura.selects.forEach(s => {
    console.log(`  name="${s.name}" id="${s.id}" (${s.options.length} opções, multiple=${s.multiple})`);
    s.options.slice(0, 5).forEach(o => console.log(`    value="${o.value}" → "${o.text}"`));
    if (s.options.length > 5) console.log(`    ... +${s.options.length - 5} mais`);
  });

  console.log('\n── BOTÕES / INPUTS SUBMIT ──');
  estrutura.inputs
    .filter(i => ['submit', 'button', 'checkbox', 'radio'].includes(i.type))
    .forEach(i => console.log(`  type="${i.type}" name="${i.name}" value="${i.value}"`));

  await page.screenshot({
    path    : path.join(LOG_DIR, 'formulario.png'),
    fullPage: true,
  });
  console.log(`\nScreenshot: ${path.join(LOG_DIR, 'formulario.png')}`);

  await browser.close();
}

main().catch(err => { console.error(err); process.exit(1); });
