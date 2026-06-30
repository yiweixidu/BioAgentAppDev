-- database/schema.sql
-- Create database and all tables for BioAgent Research Management System
-- Phase 1 schema — includes L0 compliance tables from day one

CREATE DATABASE IF NOT EXISTS bioagent_db
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE bioagent_db;

-- ═══════════════════════════════════════════════════════════════
-- L0 · COMPLIANCE PLANE  (created first — everything depends on it)
-- ═══════════════════════════════════════════════════════════════

-- ── Audit Chain (SHA-256 linked, append-only) ─────────────────
-- Each row's hash covers its own content + previous row's hash.
-- This makes the log tamper-evident: any modification breaks the chain.
CREATE TABLE IF NOT EXISTS audit_chain (
    id            BIGINT        AUTO_INCREMENT PRIMARY KEY,
    timestamp     DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    user_id       VARCHAR(100)  NOT NULL,
    action        VARCHAR(50)   NOT NULL,   -- CREATE|UPDATE|DELETE|INFERENCE|LOGIN
    entity_type   VARCHAR(50)   NOT NULL,   -- project|hypothesis|skill|inference|researcher
    entity_id     VARCHAR(50)   NOT NULL,
    detail        TEXT,
    ip_owner      VARCHAR(20)   NOT NULL DEFAULT 'platform',  -- platform|lab|shared
    project_id    VARCHAR(10),              -- NULL = system-wide action
    payload_hash  CHAR(64)      NOT NULL,   -- SHA-256 of (timestamp+user+action+entity+detail)
    chain_hash    CHAR(64)      NOT NULL,   -- SHA-256 of (payload_hash + prev chain_hash)
    prev_id       BIGINT,                   -- FK to previous row (NULL for first row)
    FOREIGN KEY (prev_id) REFERENCES audit_chain(id)
);

-- ── RBAC: Roles & Permissions (Casbin-style, stored in SQL) ───
CREATE TABLE IF NOT EXISTS rbac_role (
    role_id     VARCHAR(30) PRIMARY KEY,   -- admin|pi|lab_manager|researcher|viewer
    description VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS rbac_permission (
    id          INT         AUTO_INCREMENT PRIMARY KEY,
    role_id     VARCHAR(30) NOT NULL,
    resource    VARCHAR(50) NOT NULL,   -- project|hypothesis|skill|inference|grant|audit
    action      VARCHAR(20) NOT NULL,   -- read|write|delete|run|manage
    UNIQUE KEY uq_role_res_act (role_id, resource, action),
    FOREIGN KEY (role_id) REFERENCES rbac_role(role_id)
);

-- ── IP Ownership Registry ──────────────────────────────────────
-- Every skill/model asset has a declared owner from the start.
CREATE TABLE IF NOT EXISTS ip_registry (
    asset_id      VARCHAR(50)  PRIMARY KEY,   -- skill_id or model identifier
    asset_type    VARCHAR(20)  NOT NULL,      -- base_model|skill|adapter
    owner         VARCHAR(20)  NOT NULL,      -- platform|lab|shared
    project_id    VARCHAR(10),                -- NULL for platform-owned base models
    lab_share_pct TINYINT      DEFAULT 0,     -- 0-100, lab's share when owner='shared'
    registered_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes         TEXT
);

-- ── Loi25 Consent Records (Quebec privacy law) ────────────────
CREATE TABLE IF NOT EXISTS loi25_consent (
    id            INT          AUTO_INCREMENT PRIMARY KEY,
    researcher_id VARCHAR(10)  NOT NULL,
    project_id    VARCHAR(10)  NOT NULL,
    data_type     VARCHAR(50)  NOT NULL,   -- clinical|genomic|private_lab
    consented     TINYINT(1)   NOT NULL DEFAULT 0,
    consented_at  DATETIME,
    expires_at    DATETIME,
    version       VARCHAR(10)  NOT NULL DEFAULT 'v1'
);

-- ═══════════════════════════════════════════════════════════════
-- CORE DOMAIN TABLES
-- ═══════════════════════════════════════════════════════════════

-- ── Researcher Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS researcher (
    res_id      VARCHAR(10)  PRIMARY KEY,   -- e.g. RES-001
    name        VARCHAR(100) NOT NULL,
    institution VARCHAR(100),
    pi          VARCHAR(100),               -- Principal Investigator
    domain      VARCHAR(50),
    role        VARCHAR(20)  NOT NULL DEFAULT 'researcher',  -- researcher | lab_manager | admin
    email       VARCHAR(100),
    password    VARCHAR(255) DEFAULT ''
);

-- ── Project Table ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project (
    proj_id   VARCHAR(10)  PRIMARY KEY,     -- e.g. PRJ-101
    title     VARCHAR(200) NOT NULL,
    domain    VARCHAR(50),
    grant_src VARCHAR(20),                  -- funding grant_type e.g. CIHR, NSERC
    pi        VARCHAR(100),
    status    VARCHAR(20)  NOT NULL DEFAULT 'active',   -- active | planning | archived
    skill     VARCHAR(50),                  -- assigned AI model
    progress  INT          NOT NULL DEFAULT 0,          -- 0 to 100
    profile_yaml_path VARCHAR(255)          -- path to ProjectProfile.yaml
);

-- ── Hypothesis Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS hypothesis (
    hyp_id     VARCHAR(10)   PRIMARY KEY,
    project_id VARCHAR(10)   NOT NULL,
    text       TEXT          NOT NULL,
    status     VARCHAR(20)   NOT NULL DEFAULT 'pending',
    confidence FLOAT         NOT NULL DEFAULT 0.5,
    pmids      VARCHAR(200)  DEFAULT '',
    note       VARCHAR(500)  DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES project(proj_id) ON DELETE CASCADE
);

-- ── Model Skill Table ─────────────────────────────────────
-- name column stores the fine-tuning method (LoRA, QLoRA, etc.)
CREATE TABLE IF NOT EXISTS model_skill (
    skill_id     VARCHAR(10)  PRIMARY KEY,          -- e.g. SK-001
    name         VARCHAR(50)  NOT NULL,             -- DNABERT-2 | ESM-2 | etc.
    project_id   VARCHAR(10)  NOT NULL,
    lora_version VARCHAR(50),                       -- fine-tuned adapter version
    threshold    INT          NOT NULL DEFAULT 200, -- training epoch threshold
    benchmark    VARCHAR(100) NOT NULL DEFAULT 'default_eval',
    status       VARCHAR(20)  NOT NULL DEFAULT 'inactive',  -- active | inactive
    loaded       DATE,                              -- date the skill was loaded
    owner        VARCHAR(20)  NOT NULL DEFAULT 'lab',       -- platform|lab|shared
    lab_share_pct TINYINT     NOT NULL DEFAULT 100,         -- lab's IP share %
    FOREIGN KEY (project_id) REFERENCES project(proj_id) ON DELETE CASCADE
);

-- ── Inference History Table ───────────────────────────────
CREATE TABLE IF NOT EXISTS inference_history (
    inf_id         VARCHAR(10) PRIMARY KEY,   -- e.g. INF-001
    type           VARCHAR(50) NOT NULL,      -- DNA Variant | Protein FASTA | etc.
    model          VARCHAR(50) NOT NULL,
    project_id     VARCHAR(10),
    input          TEXT,                      -- user-provided input sequence
    result_summary TEXT,                      -- short summary of prediction result
    result_full    LONGTEXT,                  -- full structured result as JSON
    confidence     FLOAT,
    ip_owner       VARCHAR(20)  NOT NULL DEFAULT 'platform',
    timestamp      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES project(proj_id) ON DELETE SET NULL
);

-- ── Grant Fund Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS grant_fund (
    grant_id   VARCHAR(10)   PRIMARY KEY,       -- e.g. GR-001
    project_id VARCHAR(10)   NOT NULL,
    grant_type     VARCHAR(50),                 -- funding grant_type name
    deadline   DATE,                            -- grant submission deadline
    total      DECIMAL(12,2) NOT NULL DEFAULT 0,     -- total budget in CAD
    used       DECIMAL(12,2) NOT NULL DEFAULT 0,     -- amount spent so far
    FOREIGN KEY (project_id) REFERENCES project(proj_id) ON DELETE CASCADE
);

-- ── Milestone Table ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS milestone (
    id        INT           AUTO_INCREMENT PRIMARY KEY,
    grant_id  VARCHAR(10)   NOT NULL,
    descr     VARCHAR(300)  NOT NULL,               -- milestone description
    due       DATE,                                 -- due date
    completed TINYINT(1)    NOT NULL DEFAULT 0,     -- 0 = not done, 1 = done
    FOREIGN KEY (grant_id) REFERENCES grant_fund(grant_id) ON DELETE CASCADE
);

-- ── Audit_trail Table ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_trail (
    id        INT          AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME     DEFAULT CURRENT_TIMESTAMP,
    user      VARCHAR(100),
    action    VARCHAR(50),
    entity    VARCHAR(200),
    detail    TEXT
);

-- ── Options Table ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_options (
    id         INT          AUTO_INCREMENT PRIMARY KEY,
    category   VARCHAR(50)  NOT NULL,   -- 'domain' | 'grant' | 'role' | 'status'
    value      VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_cat_val (category, value)
);