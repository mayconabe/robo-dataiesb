/**
 * Robô DATASUS - SIA/SUS Produção Ambulatorial
 * Por local de atendimento - a partir de 2008
 *
 * Configuração:
 *   Linha      : Município
 *   Coluna     : Subgrupo proced.
 *   Conteúdo   : Qtd. Aprovada + Valor Aprovado (seleção múltipla, 1 query/mês)
 *   Períodos   : Jan/2024 a Jan/2026 (25 meses)
 *   Formato    : Colunas separadas por ";"  (radio name="formato" value="prn")
 *   Linhas zero: Exibir  (checkbox name="zeradas" value="exibirlz")
 */

const { chromium } = require('playwright');
const fs   = require('fs');
const path = require('path');

// ─────────────────────────────────────────────
// CONFIGURAÇÕES
// ─────────────────────────────────────────────
const CONFIG = {
  url      : 'http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qabr.def',
  outputDir: path.join(__dirname, 'dados'),
  logDir   : path.join(__dirname, 'logs'),
  timeout  : 120_000,  // 2 min por query
  headless : true,     // true = sem interface gráfica
  retries  : 3,
  delayMs  : 3_000,
};

// ─────────────────────────────────────────────
// PERÍODO: Jan/2024 → Jan/2026 (25 meses)
// ─────────────────────────────────────────────
function gerarMeses() {
  const meses = [];
  for (let ano = 2024; ano <= 2026; ano++) {
    const mesMax = ano === 2026 ? 1 : 12;
    for (let mes = 1; mes <= mesMax; mes++) meses.push({ ano, mes });
  }
  return meses;
}

// Valor do arquivo para o período: qabr{AA}{MM}.dbf
// Ex: Jan/2024 → "qabr2401.dbf"
function valorPeriodo(mes, ano) {
  const aa = String(ano).slice(-2);
  const mm = String(mes).padStart(2, '0');
  return `qabr${aa}${mm}.dbf`;
}

// ─────────────────────────────────────────────
// UTILITÁRIOS
// ─────────────────────────────────────────────
function log(msg, nivel = 'INFO') {
  const ts  = new Date().toISOString();
  const txt = `[${ts}] [${nivel}] ${msg}`;
  console.log(txt);
  fs.appendFileSync(
    path.join(CONFIG.logDir, `robo_sia_${hoje()}.log`),
    txt + '\n'
  );
}

function hoje() {
  return new Date().toISOString().slice(0, 10).replace(/-/g, '');
}

function nomeMes(mes, ano) {
  return `${String(mes).padStart(2, '0')}${ano}`;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function garantirDirs() {
  [CONFIG.outputDir, CONFIG.logDir].forEach(d => {
    if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
  });
}

// ─────────────────────────────────────────────
// PREENCHER FORMULÁRIO
// Seletores confirmados pelo descobrir_form.js:
//   Linha      → select[name="Linha"]      value="Município"
//   Coluna     → select[name="Coluna"]     value="Subgrupo_proced."
//   Incremento → select[name="Incremento"] values=["Qtd.aprovada","Valor_aprovado"]
//   Arquivos   → select[name="Arquivos"]   value="qabr{AA}{MM}.dbf"
//   zeradas    → input[name="zeradas"]     value="exibirlz"  (checkbox)
//   formato    → input[name="formato"]     value="prn"       (radio "Colunas sep. ;")
//   mostre     → input[name="mostre"]                        (submit)
// ─────────────────────────────────────────────
async function preencherFormulario(page, mes, ano, conteudoValor) {
  // ── Linha = Município ──────────────────────
  await page.selectOption('select[name="Linha"]', 'Município');
  log('  ✓ Linha = Município');

  // ── Coluna = Subgrupo proced. ──────────────
  // Descobre a opção cujo value/texto contém "Subgrupo"
  const optsColuna = await page.$$eval('select[name="Coluna"] option', os =>
    os.map(o => ({ v: o.value, t: o.text }))
  );
  const subgrupo = optsColuna.find(o => /subgrupo/i.test(o.v + o.t));
  if (!subgrupo) throw new Error('Opção "Subgrupo" não encontrada em Coluna');
  await page.selectOption('select[name="Coluna"]', subgrupo.v);
  log(`  ✓ Coluna = ${subgrupo.v}`);

  // ── Conteúdo (1 por vez) ──────────────────────
  await page.evaluate(v => {
    const sel = document.querySelector('select[name="Incremento"]');
    if (!sel) return;
    Array.from(sel.options).forEach(o => { o.selected = o.value === v; });
  }, conteudoValor);
  log(`  ✓ Conteúdo = ${conteudoValor}`);

  // ── Período ────────────────────────────────
  const periodoVal = valorPeriodo(mes, ano);
  const mesLabel   = ['Jan','Fev','Mar','Abr','Mai','Jun',
                      'Jul','Ago','Set','Out','Nov','Dez'][mes - 1];
  await page.evaluate(v => {
    const sel = document.querySelector('select[name="Arquivos"]');
    if (!sel) return;
    Array.from(sel.options).forEach(o => { o.selected = o.value === v; });
  }, periodoVal);
  log(`  ✓ Período = ${mesLabel}/${ano} (${periodoVal})`);

  // ── Exibir linhas zeradas ──────────────────
  // checkbox name="zeradas" value="exibirlz"
  await page.evaluate(() => {
    const cb = document.querySelector('input[name="zeradas"]');
    if (cb) cb.checked = true;
  });
  const zeradasOk = await page.$eval(
    'input[name="zeradas"]', el => el.checked
  ).catch(() => false);
  log(zeradasOk ? '  ✓ Exibir linhas zeradas = marcado'
                : '  ⚠ Checkbox zeradas não encontrado', zeradasOk ? 'INFO' : 'WARN');

  // ── Formato: Colunas separadas por ";" ─────
  // radio name="formato" value="prn"
  await page.evaluate(() => {
    const r = document.querySelector('input[name="formato"][value="prn"]');
    if (r) { r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true })); }
  });
  const formatoOk = await page.$eval(
    'input[name="formato"][value="prn"]', el => el.checked
  ).catch(() => false);
  log(formatoOk ? '  ✓ Formato = Colunas separadas por ";"'
                : '  ⚠ Radio formato[prn] não encontrado', formatoOk ? 'INFO' : 'WARN');
}

// ─────────────────────────────────────────────
// SUBMETER E AGUARDAR RESULTADOS
// ─────────────────────────────────────────────
async function submeterFormulario(page) {
  const [popup] = await Promise.all([
    page.context().waitForEvent('page', { timeout: 8_000 }).catch(() => null),
    page.click('input[name="mostre"]'),
  ]);

  const resultPage = popup ?? page;
  await resultPage.waitForLoadState('domcontentloaded', { timeout: CONFIG.timeout });

  // Verifica erro real do TabNet (página sem dados e sem tabela/pre)
  const temConteudo = await resultPage.$('pre, table').catch(() => null);
  if (!temConteudo) {
    const bodyText = await resultPage.evaluate(() => document.body?.innerText ?? '');
    throw new Error(`TabNet não retornou dados: ${bodyText.slice(0, 300)}`);
  }

  return resultPage;
}

// ─────────────────────────────────────────────
// EXTRAIR CSV DA PÁGINA DE RESULTADOS
// Como selecionamos formato "prn" (sep=";"), o TabNet já retorna
// o resultado como texto PRN separado por ";"
// ─────────────────────────────────────────────
async function extrairCSV(resultPage) {
  // Aguarda conteúdo carregar
  await resultPage.waitForSelector('pre, table', { timeout: CONFIG.timeout });

  // Formato "prn" → conteúdo em <pre> ou texto puro
  const preTexto = await resultPage.$eval('pre', el => el.innerText).catch(() => null);
  if (preTexto && preTexto.includes(';')) {
    log('  → Dados extraídos via <pre> (formato prn)');
    return preTexto.trim();
  }

  // Fallback: o TabNet pode exibir em nova janela com texto puro
  const bodyTexto = await resultPage.evaluate(() => document.body?.innerText ?? '');
  if (bodyTexto.includes(';')) {
    log('  → Dados extraídos via body text');
    return bodyTexto.trim();
  }

  // Último fallback: parse da tabela HTML → CSV com ";"
  log('  → Fallback: parse de tabela HTML', 'WARN');
  return await extrairTabelaComoCSV(resultPage);
}

async function extrairTabelaComoCSV(page) {
  await page.waitForSelector('table', { timeout: CONFIG.timeout });

  const linhas = await page.evaluate(() => {
    const tabelas = Array.from(document.querySelectorAll('table'));
    const tabela  = tabelas.reduce((a, b) => a.rows.length > b.rows.length ? a : b);
    return Array.from(tabela.rows).map(tr =>
      Array.from(tr.cells).map(td => td.innerText.replace(/\n/g, ' ').trim())
    );
  });

  return linhas.map(cols =>
    cols.map(c => (c.includes(';') || c.includes('"'))
      ? `"${c.replace(/"/g, '""')}"` : c
    ).join(';')
  ).join('\n');
}

// Conteúdos a extrair (1 por vez)
const CONTEUDOS = [
  { valor: 'Qtd.aprovada',    nome: 'qtd_aprovada'   },
  { valor: 'Valor_aprovado',  nome: 'valor_aprovado'  },
];

// ─────────────────────────────────────────────
// PROCESSAR UM MÊS + CONTEÚDO (com retry)
// ─────────────────────────────────────────────
async function processarMes(browser, mes, ano, conteudo, tentativa = 1) {
  const mesLabel = ['Jan','Fev','Mar','Abr','Mai','Jun',
                    'Jul','Ago','Set','Out','Nov','Dez'][mes - 1];
  const rotulo  = `${mesLabel}/${ano} [${conteudo.nome}]`;
  const arquivo = path.join(CONFIG.outputDir, `sia_${conteudo.nome}_${nomeMes(mes, ano)}.csv`);

  if (fs.existsSync(arquivo)) {
    log(`SKIP ${rotulo} → já existe: ${path.basename(arquivo)}`);
    return { ok: true, arquivo, pulado: true };
  }

  const ctx  = await browser.newContext();
  const page = await ctx.newPage();

  try {
    log(`─── ${rotulo} (tentativa ${tentativa}) ───`);

    await page.goto(CONFIG.url, { waitUntil: 'domcontentloaded', timeout: CONFIG.timeout });

    await preencherFormulario(page, mes, ano, conteudo.valor);

    const resultPage = await submeterFormulario(page);

    const csvTexto = await extrairCSV(resultPage);
    if (!csvTexto || csvTexto.split('\n').length < 2) {
      throw new Error(`Nenhum dado retornado para ${rotulo}`);
    }

    const periodoStr = `${String(mes).padStart(2, '0')}/${ano}`;
    const linhas     = csvTexto.split('\n');
    const comPeriodo = linhas.map((l, i) =>
      i === 0 ? `periodo;conteudo;${l}` : `${periodoStr};${conteudo.nome};${l}`
    ).join('\n');

    fs.writeFileSync(arquivo, '\uFEFF' + comPeriodo, 'utf8');
    log(`  ✓ Salvo: ${path.basename(arquivo)}  (${linhas.length - 1} linhas)`);

    return { ok: true, arquivo, linhas: linhas.length - 1 };

  } catch (err) {
    log(`  ✗ ERRO ${rotulo}: ${err.message}`, 'ERROR');

    try {
      const ss = path.join(CONFIG.logDir, `erro_${conteudo.nome}_${nomeMes(mes,ano)}_t${tentativa}.png`);
      await page.screenshot({ path: ss, fullPage: true });
      log(`  Screenshot: ${path.basename(ss)}`, 'WARN');
    } catch (_) {}

    if (tentativa < CONFIG.retries) {
      log(`  Retry ${tentativa + 1}/${CONFIG.retries}...`, 'WARN');
      await sleep(CONFIG.delayMs * 2);
      return processarMes(browser, mes, ano, conteudo, tentativa + 1);
    }

    return { ok: false, rotulo, erro: err.message };

  } finally {
    await ctx.close();
  }
}

// ─────────────────────────────────────────────
// LOOP PRINCIPAL
// ─────────────────────────────────────────────
async function main() {
  garantirDirs();

  log('═══════════════════════════════════════════════');
  log('Robô DATASUS SIA/SUS - Produção Ambulatorial');
  log('Período: Jan/2024 → Jan/2026 (25 meses)');
  log('Conteúdo: Qtd.aprovada + Valor_aprovado');
  log('Formato: Colunas separadas por ";"');
  log('═══════════════════════════════════════════════');

  const meses   = gerarMeses();
  const erros   = [];
  const browser = await chromium.launch({ headless: CONFIG.headless });

  try {
    for (const { ano, mes } of meses) {
      for (const conteudo of CONTEUDOS) {
        const resultado = await processarMes(browser, mes, ano, conteudo);
        if (!resultado.ok) erros.push(resultado);
        await sleep(CONFIG.delayMs);
      }
    }

    log('═══════════════════════════════════════════════');
    log(`Concluído! Arquivos em: ${CONFIG.outputDir}`);

    if (erros.length) {
      log(`ATENÇÃO: ${erros.length} erro(s):`, 'WARN');
      erros.forEach(e => log(`  ✗ ${e.rotulo}: ${e.erro}`, 'WARN'));
      fs.writeFileSync(
        path.join(CONFIG.logDir, `erros_${hoje()}.json`),
        JSON.stringify(erros, null, 2)
      );
    }

  } finally {
    await browser.close();
  }
}

main().catch(err => { console.error('FALHA CRÍTICA:', err); process.exit(1); });
