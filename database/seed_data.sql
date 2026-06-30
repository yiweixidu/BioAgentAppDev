-- database/seed_data.sql
-- Insert initial test data into bioagent_db

USE bioagent_db;

-- ── Researchers ───────────────────────────────────────────
INSERT INTO researcher
    (res_id, name, institution, pi, domain, role, email)
VALUES
    ('RES-001', 'Dr. Liwei Rong',
     'Vanier College', 'Dr. Lefrançois',
     'flu_bnab',       'researcher',
     'liwei.rong@vanier.ca'),

    ('RES-002', 'Dr. Ana Cardinal',
     'Vanier College', 'Dr. Lefrançois',
     'noncoding_dna',  'lab_manager',
     'ana.cardinal@vanier.ca');

-- ── Projects ──────────────────────────────────────────────
INSERT INTO project
    (proj_id, title, domain, grant_src, pi, status, skill, progress)
VALUES
    ('PRJ-101',
     'H5N1 bnAb Broad neutralization',
     'flu_bnab',      'CIHR',
     'Dr. Lefrançois', 'active',
     'ESM-2',          75),

    ('PRJ-102',
     'KRAS G12C Resistance',
     'oncology',      'NSERC',
     'Dr. Liwei Rong', 'active',
     'DNABERT-2',      48),

    ('PRJ-103',
     'Noncoding DNA CRISPR Screening',
     'noncoding_dna',  'MITACS',
     'Dr. Ana Cardinal','planning',
     NULL,              90);

-- ── Hypotheses ────────────────────────────────────────────
INSERT INTO hypothesis
    (hyp_id, project_id, text, status, confidence, pmids, note)
VALUES
    ('H3',  'PRJ-101',
     'IL-6 correlates with bnAb breadth in H5N1 challenge',
     'supported', 0.87, 'PMID:38201847',
     'Confirmed ELISA 2026-05-14'),

    ('H14', 'PRJ-102',
     'KRAS G12C dual inhibition improves PFS',
     'refuted', 0.32, 'PMID:36521447',
     'IC50 unchanged in SPR assay'),

    ('H21', 'PRJ-103',
     'Noncoding CpG methylation silences interferon-beta',
     'pending', 0.65, 'PMID:37123890',
     'Awaiting second replicate');

-- ── Model Skills ──────────────────────────────────────────
INSERT INTO model_skill
    (skill_id, name, project_id, lora_version,
     threshold, benchmark, status, loaded, owner, lab_share_pct)
VALUES
    ('SK-001', 'DNABERT-2',     'PRJ-102',
     'oncology-somatic-v2',
     200, 'BRCA_eval',         'active',   '2026-05-01', 'shared', 60),

    ('SK-002', 'ESM-2',         'PRJ-101',
     'flu-ha-v3',
     150, 'HA_binding_eval',   'active',   '2026-05-01', 'shared', 60),

    ('SK-003', 'PPI Predictor', 'PRJ-101',
     'ppi-base-v1',
     100, 'Antibody_PPI_eval', 'inactive', '2026-04-20', 'lab',   100);

-- ── Inference History ─────────────────────────────────────
INSERT INTO inference_history
    (inf_id, type, model, project_id,
     input, result_summary, timestamp, ip_owner)
VALUES
    ('INF-001',
     'DNA Variant',   'LocalLLM-DNABERT-2', 'PRJ-102',
     'chr12:25398284 A>T hg38',
     'score -1.83 · pathogenic · PMID:38201847',
     '2026-05-14 10:23:00', 'platform'),

    ('INF-002',
     'Protein FASTA', 'LocalLLM-ESM-2',     'PRJ-101',
     '>Ab_VH EVQLVESGGG',
     'deltaG=-12.4 kcal/mol · Kd=2.3 nM · PDB:6XR8',
     '2026-05-14 14:15:00', 'platform');

-- ── Grant Funds ───────────────────────────────────────────
INSERT INTO grant_fund
    (grant_id, project_id, grant_type, deadline, total, used)
VALUES
    ('GR-001', 'PRJ-101', 'CIHR',  '2026-08-30', 120000, 42000),
    ('GR-002', 'PRJ-102', 'NSERC', '2026-07-15',  85000, 25500);

-- ── Milestones ────────────────────────────────────────────
INSERT INTO milestone
    (grant_id, descr, due, completed)
VALUES
    ('GR-001',
     'Hemagglutinin ELISA optimization',
     '2026-06-01', 0),

    ('GR-002',
     'CRISPR library design',
     '2026-05-10', 0);

-- ── IP Registry seed (base platform models) ─────────────
INSERT IGNORE INTO ip_registry
    (asset_id, asset_type, owner, project_id, lab_share_pct, notes)
VALUES
    ('LocalLLM-DNABERT-2', 'base_model', 'platform', NULL, 0,  'BioAgent exclusive — DNABERT-2 base'),
    ('LocalLLM-ESM-2',     'base_model', 'platform', NULL, 0,  'BioAgent exclusive — ESM-2 base'),
    ('LocalLLM-PPI',       'base_model', 'platform', NULL, 0,  'BioAgent exclusive — PPI Predictor base'),
    ('LocalLLM-RAG',       'base_model', 'platform', NULL, 0,  'BioAgent exclusive — LLaMA RAG base'),
    ('SK-001', 'skill', 'shared', 'PRJ-102', 60, 'DNABERT-2 oncology-somatic-v2 — lab data contributed'),
    ('SK-002', 'skill', 'shared', 'PRJ-101', 60, 'ESM-2 flu-ha-v3 — lab data contributed'),
    ('SK-003', 'skill', 'lab',    'PRJ-101', 100,'PPI ppi-base-v1 — lab owned');

-- ── App Options ───────────────────────────────────────────
INSERT INTO app_options (category, value) VALUES
('domain', 'flu_bnab'),
('domain', 'noncoding_dna'),
('domain', 'antibiotic_resistance'),
('domain', 'oncology'),
('domain', 'general'),
('grant',  'CIHR'),
('grant',  'NSERC'),
('grant',  'MITACS'),
('grant',  'Génome Québec'),
('grant',  'FRQS'),
('role',   'researcher'),
('role',   'lab_manager'),
('role',   'admin'),
('status', 'active'),
('status', 'planning'),
('status', 'archived');

-- ═══════════════════════════════════════════════════════════════
-- L0 SEED: RBAC roles and permissions
-- ═══════════════════════════════════════════════════════════════

INSERT IGNORE INTO rbac_role (role_id, description) VALUES
('admin',       'Full system access'),
('pi',          'Principal Investigator — manage own projects'),
('lab_manager', 'Manage researchers and skills'),
('researcher',  'Run inference, manage hypotheses'),
('viewer',      'Read-only access');

-- admin: everything
INSERT IGNORE INTO rbac_permission (role_id, resource, action) VALUES
('admin','project','read'),('admin','project','write'),('admin','project','delete'),
('admin','hypothesis','read'),('admin','hypothesis','write'),('admin','hypothesis','delete'),
('admin','skill','read'),('admin','skill','write'),('admin','skill','delete'),
('admin','inference','read'),('admin','inference','run'),
('admin','grant','read'),('admin','grant','write'),
('admin','audit','read'),('admin','rbac','manage');

-- pi: own project full access
INSERT IGNORE INTO rbac_permission (role_id, resource, action) VALUES
('pi','project','read'),('pi','project','write'),
('pi','hypothesis','read'),('pi','hypothesis','write'),('pi','hypothesis','delete'),
('pi','skill','read'),('pi','skill','write'),
('pi','inference','read'),('pi','inference','run'),
('pi','grant','read'),('pi','grant','write');

-- lab_manager
INSERT IGNORE INTO rbac_permission (role_id, resource, action) VALUES
('lab_manager','project','read'),('lab_manager','project','write'),
('lab_manager','hypothesis','read'),('lab_manager','hypothesis','write'),
('lab_manager','skill','read'),('lab_manager','skill','write'),
('lab_manager','inference','read'),('lab_manager','inference','run'),
('lab_manager','grant','read');

-- researcher
INSERT IGNORE INTO rbac_permission (role_id, resource, action) VALUES
('researcher','project','read'),
('researcher','hypothesis','read'),('researcher','hypothesis','write'),
('researcher','skill','read'),
('researcher','inference','read'),('researcher','inference','run');

-- viewer
INSERT IGNORE INTO rbac_permission (role_id, resource, action) VALUES
('viewer','project','read'),('viewer','hypothesis','read'),
('viewer','skill','read'),('viewer','inference','read'),
('viewer','grant','read');