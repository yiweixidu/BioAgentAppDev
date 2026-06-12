-- database/schema.sql
-- Create database and all tables for BioAgent Research Management System

CREATE DATABASE IF NOT EXISTS bioagent_db
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE bioagent_db;

-- ── Researcher Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS researcher (
    res_id      VARCHAR(10)  PRIMARY KEY,   -- e.g. RES-001
    name        VARCHAR(100) NOT NULL,
    institution VARCHAR(100),
    pi          VARCHAR(100),               -- Principal Investigator
    domain      VARCHAR(50),
    role        VARCHAR(20)  DEFAULT 'researcher',  -- researcher | lab_manager | admin
    email       VARCHAR(100),
    password    VARCHAR(255) DEFAULT ''
);

-- ── Project Table ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project (
    proj_id   VARCHAR(10)  PRIMARY KEY,     -- e.g. PRJ-101
    title     VARCHAR(200) NOT NULL,
    domain    VARCHAR(50),
    grant_src VARCHAR(20),                  -- funding agency e.g. CIHR, NSERC
    pi        VARCHAR(100),
    status    VARCHAR(20)  DEFAULT 'active', -- active | planning | archived
    skill     VARCHAR(50),                  -- assigned AI model
    progress  INT          DEFAULT 0        -- 0 to 100
);

-- ── Hypothesis Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS hypothesis (
    hyp_id     VARCHAR(10)   PRIMARY KEY,
    project_id VARCHAR(10)   NOT NULL,
    text       TEXT          NOT NULL,
    status     VARCHAR(20)   DEFAULT 'pending',
    confidence FLOAT         DEFAULT 0.5,
    pmids      VARCHAR(200)  DEFAULT '',
    note       VARCHAR(500)  DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES project(proj_id)
        ON DELETE CASCADE
);

-- ── Model Skill Table ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_skill (
    skill_id     VARCHAR(10)  PRIMARY KEY,  -- e.g. SK-001
    name         VARCHAR(50)  NOT NULL,     -- DNABERT-2 | ESM-2 | etc.
    project_id   VARCHAR(10)  NOT NULL,
    lora_version VARCHAR(50),               -- fine-tuned adapter version
    threshold    INT          DEFAULT 200,  -- training epoch threshold
    benchmark    VARCHAR(100) DEFAULT 'default_eval',
    status       VARCHAR(20)  DEFAULT 'inactive', -- active | inactive
    loaded       DATE,                      -- date the skill was loaded
    FOREIGN KEY (project_id) REFERENCES project(proj_id)
        ON DELETE CASCADE
);

-- ── Inference History Table ───────────────────────────────
CREATE TABLE IF NOT EXISTS inference_history (
    inf_id         VARCHAR(10)  PRIMARY KEY,  -- e.g. INF-001
    type           VARCHAR(50),               -- DNA Variant | Protein FASTA | etc.
    model          VARCHAR(50),
    project_id     VARCHAR(10),
    input          TEXT,                      -- user-provided input sequence
    result_summary TEXT,                      -- short summary of prediction result
    timestamp      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES project(proj_id)
        ON DELETE SET NULL
);

-- ── Grant Fund Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS grant_fund (
    grant_id   VARCHAR(10)   PRIMARY KEY,   -- e.g. GR-001
    project_id VARCHAR(10)   NOT NULL,
    agency     VARCHAR(50),                 -- funding agency name
    deadline   DATE,                        -- grant submission deadline
    total      DECIMAL(12,2) DEFAULT 0,     -- total budget in CAD
    used       DECIMAL(12,2) DEFAULT 0,     -- amount spent so far
    FOREIGN KEY (project_id) REFERENCES project(proj_id)
        ON DELETE CASCADE
);

-- ── Milestone Table ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS milestone (
    id        INT           AUTO_INCREMENT PRIMARY KEY,
    grant_id  VARCHAR(10)   NOT NULL,
    descr     VARCHAR(300)  NOT NULL,       -- milestone description
    due       DATE,                         -- due date
    completed TINYINT(1)    DEFAULT 0,      -- 0 = not done, 1 = done
    FOREIGN KEY (grant_id) REFERENCES grant_fund(grant_id)
        ON DELETE CASCADE
);

-- ── Audit Trail Table ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_trail (
    id        INT          AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME     DEFAULT CURRENT_TIMESTAMP,
    user      VARCHAR(100),                 -- who performed the action
    action    VARCHAR(50),                  -- CREATE | UPDATE | DELETE | etc.
    entity    VARCHAR(200),                 -- which record was affected
    detail    TEXT                          -- description of the change
);