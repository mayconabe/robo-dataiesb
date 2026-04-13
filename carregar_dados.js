/**
 * Carregador de dados - SIA/SUS → PostgreSQL
 *
 * Lê os CSVs gerados por robo_sia.js e carrega em:
 *   host    : dataiesb.iesbtech.com.br
 *   database: 2222120008_Maycon
 *   tabela  : sia_producao_ambulatorial
 */

const { Pool } = require('pg');
const fs        = require('fs');
const path      = require('path');

// ─────────────────────────────────────────────
// CONEXÃO
// ─────────────────────────────────────────────
const pool = new Pool({
  host    : 'dataiesb.iesbtech.com.br',
  database: '2222120008_Maycon',
  user    : '2222120008_Maycon',
  password: '2222120008_Maycon',
  port    : 5432,
  ssl     : false,
});

const CONFIG = {
  dadosDir : path.join(__dirname, 'dados'),
  batchSize: 500,
};

// ─────────────────────────────────────────────
// UTILITÁRIOS
// ─────────────────────────────────────────────
function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

function limparNumero(v) {
  if (!v || v.trim() === '' || v.trim() === '-') return null;
  const n = v.replace(/\./g, '').replace(',', '.').trim();
  const num = Number(n);
  return isNaN(num) ? null : num;
}

// ─────────────────────────────────────────────
// CRIAR TABELA E ÍNDICES
// ─────────────────────────────────────────────
async function criarTabela(client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS sia_producao_ambulatorial (
      id                    SERIAL PRIMARY KEY,
      periodo               TEXT    NOT NULL,
      ano                   INTEGER NOT NULL,
      mes                   INTEGER NOT NULL,
      municipio             TEXT,
      cod_municipio         TEXT,
      subgrupo_procedimento TEXT    NOT NULL,
      qtd_aprovada          BIGINT,
      valor_aprovado        NUMERIC(18,2),
      fonte                 TEXT    DEFAULT 'SIA/SUS',
      data_carga            TIMESTAMP DEFAULT NOW(),
      arquivo_origem        TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_sia_periodo
      ON sia_producao_ambulatorial(periodo);

    CREATE INDEX IF NOT EXISTS idx_sia_ano_mes
      ON sia_producao_ambulatorial(ano, mes);

    CREATE INDEX IF NOT EXISTS idx_sia_municipio
      ON sia_producao_ambulatorial(municipio);

    CREATE INDEX IF NOT EXISTS idx_sia_subgrupo
      ON sia_producao_ambulatorial(subgrupo_procedimento);

    CREATE INDEX IF NOT EXISTS idx_sia_periodo_municipio
      ON sia_producao_ambulatorial(periodo, municipio);
  `);
  log('Tabela sia_producao_ambulatorial OK.');
}

// ─────────────────────────────────────────────
// PARSE CSV
// ─────────────────────────────────────────────
function parseLinha(linha, sep = ';') {
  const campos = [];
  let atual = '', emAspas = false;
  for (let i = 0; i < linha.length; i++) {
    const c = linha[i];
    if (c === '"') {
      if (emAspas && linha[i + 1] === '"') { atual += '"'; i++; }
      else emAspas = !emAspas;
    } else if (c === sep && !emAspas) {
      campos.push(atual.trim());
      atual = '';
    } else {
      atual += c;
    }
  }
  campos.push(atual.trim());
  return campos;
}

function lerCsv(arquivo) {
  const conteudo  = fs.readFileSync(arquivo, 'utf8').replace(/^\uFEFF/, '');
  const linhas    = conteudo.split(/\r?\n/).filter(l => l.trim());
  if (linhas.length < 2) return { cabecalho: [], dados: [] };
  return {
    cabecalho: parseLinha(linhas[0]),
    dados    : linhas.slice(1).map(l => parseLinha(l)),
  };
}

function inferirTipo(nomeArquivo) {
  const n = nomeArquivo.toLowerCase();
  if (n.includes('qtd'))   return 'qtd_aprovada';
  if (n.includes('valor')) return 'valor_aprovado';
  return 'desconhecido';
}

function extrairPeriodo(nomeArquivo) {
  const m = nomeArquivo.match(/(\d{2})(\d{4})\.csv$/);
  if (!m) return null;
  return {
    mes    : parseInt(m[1], 10),
    ano    : parseInt(m[2], 10),
    periodo: `${m[1]}/${m[2]}`,
  };
}

// ─────────────────────────────────────────────
// CARREGAR UM ARQUIVO
// ─────────────────────────────────────────────
async function carregarArquivo(client, arquivo) {
  const nomeArq  = path.basename(arquivo);
  const tipo     = inferirTipo(nomeArq);
  const periodo  = extrairPeriodo(nomeArq);

  if (!periodo) {
    log(`AVISO: período não identificado em "${nomeArq}" — ignorando.`);
    return 0;
  }

  const { cabecalho, dados } = lerCsv(arquivo);
  if (!cabecalho.length || !dados.length) {
    log(`AVISO: arquivo vazio "${nomeArq}" — ignorando.`);
    return 0;
  }

  const idxPeriodo   = cabecalho.findIndex(c => /^periodo$/i.test(c));
  const idxConteudo  = cabecalho.findIndex(c => /^conteudo$/i.test(c));
  const idxMunicipio = cabecalho.findIndex(c =>
    /municipio|munic/i.test(c) && !/cod|uf|ibge/i.test(c)
  );
  const idxCodMun    = cabecalho.findIndex(c => /cod.*mun|ibge|^codigo$/i.test(c));

  // Colunas de subgrupo = tudo exceto periodo, conteudo, municipio, cod
  const skip = new Set([idxPeriodo, idxConteudo, idxMunicipio, idxCodMun].filter(i => i >= 0));
  const colsSubgrupo = cabecalho
    .map((c, i) => ({ col: c, idx: i }))
    .filter(({ idx }) => !skip.has(idx) && cabecalho[idx]?.trim());

  // Remove registros do mesmo arquivo (idempotente)
  await client.query(
    'DELETE FROM sia_producao_ambulatorial WHERE arquivo_origem = $1',
    [nomeArq]
  );

  let total = 0;
  let batch = [];

  const flush = async () => {
    if (!batch.length) return;

    // Monta INSERT com múltiplas linhas
    const valores = [];
    const params  = [];
    let   p       = 1;

    for (const r of batch) {
      valores.push(`($${p++},$${p++},$${p++},$${p++},$${p++},$${p++},$${p++},$${p++},$${p++})`);
      params.push(
        r.periodo, r.ano, r.mes,
        r.municipio, r.cod_municipio,
        r.subgrupo_procedimento,
        r.qtd_aprovada, r.valor_aprovado,
        r.arquivo_origem
      );
    }

    await client.query(`
      INSERT INTO sia_producao_ambulatorial
        (periodo, ano, mes, municipio, cod_municipio,
         subgrupo_procedimento, qtd_aprovada, valor_aprovado, arquivo_origem)
      VALUES ${valores.join(',')}
      ON CONFLICT DO NOTHING
    `, params);

    batch = [];
  };

  for (const campos of dados) {
    const municipio    = idxMunicipio >= 0 ? campos[idxMunicipio] : null;
    const codMunicipio = idxCodMun    >= 0 ? campos[idxCodMun]   : null;

    for (const { col, idx } of colsSubgrupo) {
      const num = limparNumero(campos[idx] ?? '');

      batch.push({
        periodo              : periodo.periodo,
        ano                  : periodo.ano,
        mes                  : periodo.mes,
        municipio,
        cod_municipio        : codMunicipio,
        subgrupo_procedimento: col,
        qtd_aprovada         : tipo === 'qtd_aprovada'   ? num : null,
        valor_aprovado       : tipo === 'valor_aprovado' ? num : null,
        arquivo_origem       : nomeArq,
      });
      total++;

      if (batch.length >= CONFIG.batchSize) await flush();
    }
  }

  await flush();
  return total;
}

// ─────────────────────────────────────────────
// RELATÓRIO FINAL
// ─────────────────────────────────────────────
async function relatorio(client) {
  const { rows: [total] } = await client.query(
    'SELECT COUNT(*) AS n FROM sia_producao_ambulatorial'
  );
  const { rows: periodos } = await client.query(`
    SELECT periodo, COUNT(*) AS qtd
    FROM   sia_producao_ambulatorial
    GROUP  BY periodo
    ORDER  BY periodo
  `);

  log('─────────────────────────────────────────────');
  log(`Total de registros: ${Number(total.n).toLocaleString('pt-BR')}`);
  log('Registros por período:');
  periodos.forEach(p => log(`  ${p.periodo}: ${Number(p.qtd).toLocaleString('pt-BR')}`));
  log('─────────────────────────────────────────────');
}

// ─────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────
async function main() {
  const arquivos = fs.readdirSync(CONFIG.dadosDir)
    .filter(f => f.endsWith('.csv'))
    .sort()
    .map(f => path.join(CONFIG.dadosDir, f));

  if (!arquivos.length) {
    log('Nenhum CSV encontrado em: ' + CONFIG.dadosDir);
    log('Execute primeiro: node robo_sia.js');
    process.exit(0);
  }

  log(`Conectando ao PostgreSQL...`);
  const client = await pool.connect();

  try {
    await criarTabela(client);

    log(`${arquivos.length} arquivo(s) encontrado(s).`);
    let totalRegistros = 0;

    for (const arq of arquivos) {
      log(`Carregando: ${path.basename(arq)}`);
      const n = await carregarArquivo(client, arq);
      log(`  → ${n.toLocaleString('pt-BR')} registros inseridos`);
      totalRegistros += n;
    }

    log(`Total inserido: ${totalRegistros.toLocaleString('pt-BR')} registros`);
    await relatorio(client);
    log('Carga concluída!');

  } finally {
    client.release();
    await pool.end();
  }
}

main().catch(err => { console.error('ERRO:', err.message); process.exit(1); });
