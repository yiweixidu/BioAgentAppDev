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
     threshold, benchmark, status, loaded)
VALUES
    ('SK-001', 'DNABERT-2',     'PRJ-102',
     'oncology-somatic-v2',
     200, 'BRCA_eval',         'active',   '2026-05-01'),

    ('SK-002', 'ESM-2',         'PRJ-101',
     'flu-ha-v3',
     150, 'HA_binding_eval',   'active',   '2026-05-01'),

    ('SK-003', 'PPI Predictor', 'PRJ-101',
     'ppi-base-v1',
     100, 'Antibody_PPI_eval', 'inactive', '2026-04-20');

-- ── Inference History ─────────────────────────────────────
INSERT INTO inference_history
    (inf_id, type, model, project_id,
     input, result_summary, timestamp)
VALUES
    ('INF-001',
     'DNA Variant',   'DNABERT-2', 'PRJ-102',
     'chr12:25398284 A>T hg38',
     'score -1.83 · pathogenic · PMID:38201847',
     '2026-05-14 10:23:00'),

    ('INF-002',
     'Protein FASTA', 'ESM-2',     'PRJ-101',
     '>Ab_VH EVQLVESGGG',
     'deltaG=-12.4 kcal/mol · Kd=2.3 nM · PDB:6XR8',
     '2026-05-14 14:15:00');

-- ── Grant Funds ───────────────────────────────────────────
INSERT INTO grant_fund
    (grant_id, project_id, agency, deadline, total, used)
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

-- ── Audit Trail ───────────────────────────────────────────
INSERT INTO audit_trail
    (timestamp, user, action, entity, detail)
VALUES
    ('2026-05-14 09:12:00',
     'Dr. Liwei Rong', 'CREATE',
     'Project PRJ-101',
     'New project registered'),

    ('2026-05-14 10:01:00',
     'Dr. Lefrançois',  'ASSIGN_SKILL',
     'SK-002 -> PRJ-101',
     'ESM-2 flu-ha-v3 activated'),

    ('2026-05-14 14:32:00',
     'Dr. Liwei Rong',  'UPDATE',
     'Hypothesis H14',
     'PENDING -> REFUTED (IC50 unchanged in SPR assay)');