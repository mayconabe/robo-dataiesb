-- ═══════════════════════════════════════════════════════
-- DATASUS SIA/SUS - Produção Ambulatorial
-- Schema SQLite
-- ═══════════════════════════════════════════════════════

-- Tabela principal
CREATE TABLE IF NOT EXISTS sia_producao_ambulatorial (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo               TEXT    NOT NULL,   -- "MM/AAAA"  ex: 01/2024
    ano                   INTEGER NOT NULL,
    mes                   INTEGER NOT NULL,
    municipio             TEXT,               -- Nome do município
    cod_municipio         TEXT,               -- Código IBGE (6 dígitos)
    subgrupo_procedimento TEXT    NOT NULL,   -- Ex: "Ações de Promoção e Prevenção"
    qtd_aprovada          INTEGER,            -- Quantidade aprovada
    valor_aprovado        REAL,               -- Valor aprovado (R$)
    fonte                 TEXT DEFAULT 'SIA/SUS',
    data_carga            TEXT DEFAULT (datetime('now','localtime')),
    arquivo_origem        TEXT                -- Nome do CSV de origem
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_sia_periodo
    ON sia_producao_ambulatorial(periodo);

CREATE INDEX IF NOT EXISTS idx_sia_ano_mes
    ON sia_producao_ambulatorial(ano, mes);

CREATE INDEX IF NOT EXISTS idx_sia_municipio
    ON sia_producao_ambulatorial(municipio);

CREATE INDEX IF NOT EXISTS idx_sia_cod_municipio
    ON sia_producao_ambulatorial(cod_municipio);

CREATE INDEX IF NOT EXISTS idx_sia_subgrupo
    ON sia_producao_ambulatorial(subgrupo_procedimento);

CREATE INDEX IF NOT EXISTS idx_sia_periodo_municipio
    ON sia_producao_ambulatorial(periodo, municipio);


-- ═══════════════════════════════════════════════════════
-- VIEW: resumo por período e subgrupo
-- ═══════════════════════════════════════════════════════
CREATE VIEW IF NOT EXISTS vw_resumo_periodo_subgrupo AS
SELECT
    periodo,
    ano,
    mes,
    subgrupo_procedimento,
    COUNT(DISTINCT municipio)           AS total_municipios,
    SUM(qtd_aprovada)                   AS total_qtd_aprovada,
    SUM(valor_aprovado)                 AS total_valor_aprovado,
    ROUND(AVG(qtd_aprovada), 2)         AS media_qtd_municipio,
    ROUND(AVG(valor_aprovado), 2)       AS media_valor_municipio
FROM sia_producao_ambulatorial
GROUP BY periodo, ano, mes, subgrupo_procedimento
ORDER BY ano, mes, subgrupo_procedimento;


-- ═══════════════════════════════════════════════════════
-- VIEW: ranking de municípios por produção total
-- ═══════════════════════════════════════════════════════
CREATE VIEW IF NOT EXISTS vw_ranking_municipios AS
SELECT
    municipio,
    cod_municipio,
    COUNT(DISTINCT periodo)             AS periodos_com_producao,
    SUM(qtd_aprovada)                   AS total_qtd_aprovada,
    SUM(valor_aprovado)                 AS total_valor_aprovado
FROM sia_producao_ambulatorial
WHERE qtd_aprovada > 0
GROUP BY municipio, cod_municipio
ORDER BY total_qtd_aprovada DESC;


-- ═══════════════════════════════════════════════════════
-- VIEW: série temporal mensal consolidada
-- ═══════════════════════════════════════════════════════
CREATE VIEW IF NOT EXISTS vw_serie_temporal AS
SELECT
    periodo,
    ano,
    mes,
    COUNT(DISTINCT municipio)       AS municipios_ativos,
    SUM(qtd_aprovada)               AS qtd_aprovada_total,
    SUM(valor_aprovado)             AS valor_aprovado_total
FROM sia_producao_ambulatorial
GROUP BY periodo, ano, mes
ORDER BY ano, mes;
