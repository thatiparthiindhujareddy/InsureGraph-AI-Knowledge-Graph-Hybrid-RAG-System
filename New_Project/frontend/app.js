/* ═══════════════════════════════════════════════════════════════
   InsureGraph AI — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════ */

const API = '';  // Same origin, FastAPI serves frontend

// ── Utilities ─────────────────────────────────────────────────
function toast(msg, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  el.innerHTML = `<span>${icons[type] || ''}</span><span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.style.animation = 'slideOutRight 0.3s ease forwards';
    setTimeout(() => el.remove(), 300);
  }, duration);
}

function fmt(n) { return typeof n === 'number' ? n.toLocaleString() : n; }
function scoreClass(v) {
  if (v >= 0.75) return 'score-high';
  if (v >= 0.45) return 'score-mid';
  return 'score-low';
}
function fmtScore(v) {
  const pct = Math.round(v * 100);
  return `<span class="score-cell ${scoreClass(v)}">${pct}%</span>`;
}

// ── Tab Navigation ─────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  document.getElementById(`tab-${name}`).classList.add('active');
  document.getElementById(`nav-${name}`).classList.add('active');

  const titles = {
    ingest:   ['Policy Ingestion', 'Upload and process P&C insurance documents'],
    query:    ['Policy Intelligence Query', 'Ask questions using hybrid retrieval (vector + graph)'],
    graph:    ['Knowledge Graph', 'Visualize extracted insurance entities and relationships'],
    evaluate: ['Evaluation Harness', 'Automated LLM-as-judge scoring with golden dataset'],
    docs:     ['Ingested Documents', 'Manage processed policy documents'],
  };
  const [title, sub] = titles[name] || ['InsureGraph AI', ''];
  document.getElementById('page-title').textContent = title;
  document.getElementById('page-subtitle').textContent = sub;

  // Load data on tab switch
  if (name === 'graph') loadGraph();
  if (name === 'docs') loadDocuments();
  if (name === 'evaluate') loadGoldenDataset();
}

// ── Health & Stats ─────────────────────────────────────────────
async function loadHealth() {
  try {
    const res = await fetch(`${API}/api/health`);
    const data = await res.json();
    document.getElementById('stat-nodes-val').textContent = fmt(data.graph_nodes || 0);
    document.getElementById('stat-edges-val').textContent = fmt(data.graph_edges || 0);
    document.getElementById('stat-docs-val').textContent = fmt(data.documents_indexed || 0);
    document.getElementById('stat-chunks-val').textContent =
      (data.vector_store || '0 chunks').replace(' chunks', '');
    document.getElementById('health-indicator').className = 'health-dot healthy';
    document.querySelector('.health-text').textContent = 'System Online';
  } catch (e) {
    document.getElementById('health-indicator').className = 'health-dot unhealthy';
    document.querySelector('.health-text').textContent = 'Offline';
  }
}

// ── File Upload / Ingest ───────────────────────────────────────
let selectedFile = null;

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.add('drag-over');
}
function handleDragLeave(e) {
  document.getElementById('upload-zone').classList.remove('drag-over');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.name.endsWith('.pdf')) setFile(file);
  else toast('Please drop a PDF file', 'error');
}
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) setFile(file);
}
function setFile(file) {
  selectedFile = file;
  document.getElementById('selected-file').style.display = 'flex';
  document.getElementById('selected-file-name').textContent = `${file.name} (${(file.size/1024).toFixed(1)} KB)`;
  document.getElementById('ingest-btn').disabled = false;
}

async function ingestDocument() {
  if (!selectedFile) return;
  const btn = document.getElementById('ingest-btn');
  btn.disabled = true;
  btn.innerHTML = `<div class="spinner"></div> Processing...`;

  const progressSection = document.getElementById('progress-section');
  progressSection.style.display = 'block';
  document.getElementById('ingest-result').style.display = 'none';

  const steps = ['step-extract', 'step-embed', 'step-entity', 'step-graph'];
  const progressBar = document.getElementById('ingest-progress');
  let currentStep = 0;

  // Simulate step progression during actual API call
  const progressInterval = setInterval(() => {
    if (currentStep < steps.length) {
      if (currentStep > 0) {
        document.getElementById(steps[currentStep - 1]).className = 'progress-step done';
      }
      document.getElementById(steps[currentStep]).className = 'progress-step active';
      progressBar.style.width = `${(currentStep + 1) * 25}%`;
      currentStep++;
    }
  }, 1200);

  try {
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('document_type', document.getElementById('doc-type').value);
    const policyName = document.getElementById('policy-name').value.trim();
    if (policyName) formData.append('policy_name', policyName);

    const res = await fetch(`${API}/api/ingest/upload`, { method: 'POST', body: formData });
    const data = await res.json();

    clearInterval(progressInterval);
    progressBar.style.width = '100%';
    steps.forEach(id => document.getElementById(id).className = 'progress-step done');

    if (res.ok) {
      showIngestResult(data, 'success');
      toast(`✓ Ingested "${data.policy_name}" successfully`, 'success');
      await loadHealth();
    } else {
      showIngestResult({ message: data.detail || 'Ingestion failed' }, 'error');
      toast('Ingestion failed: ' + (data.detail || 'Unknown error'), 'error');
    }
  } catch (e) {
    clearInterval(progressInterval);
    showIngestResult({ message: `Network error: ${e.message}` }, 'error');
    toast('Connection error. Is the server running?', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg> Process & Ingest Policy`;
  }
}

function showIngestResult(data, type) {
  const el = document.getElementById('ingest-result');
  el.className = `ingest-result ${type}`;
  el.style.display = 'block';

  if (type === 'success') {
    el.innerHTML = `
      <strong>✅ ${data.message || 'Success'}</strong>
      <div class="result-stats">
        <div class="result-stat"><div class="result-stat-val">${fmt(data.chunks_created)}</div><div class="result-stat-lbl">Chunks</div></div>
        <div class="result-stat"><div class="result-stat-val">${fmt(data.entities_extracted)}</div><div class="result-stat-lbl">Entities</div></div>
        <div class="result-stat"><div class="result-stat-val">${fmt(data.graph_nodes)}</div><div class="result-stat-lbl">Graph Nodes</div></div>
        <div class="result-stat"><div class="result-stat-val">${fmt(data.graph_edges)}</div><div class="result-stat-lbl">Graph Edges</div></div>
      </div>
    `;
  } else {
    el.innerHTML = `<strong>❌ Error:</strong> ${data.message}`;
  }
}

// ── Sample Policy Ingestion ────────────────────────────────────
const SAMPLE_POLICIES = {
  commercial_property: {
    name: 'Acme Corp Commercial Property Policy CP-2024',
    type: 'commercial',
    text: `COMMERCIAL PROPERTY INSURANCE POLICY
Policy Number: CP-2024-ACM-001
Policyholder: Acme Corporation
Insured Premises: 1234 Industrial Parkway, Dallas, TX 75201
Policy Period: January 1, 2024 to January 1, 2025
Annual Premium: $18,500 payable quarterly at $4,625

COVERAGE A — BUILDING
Coverage Limit: $2,500,000 per occurrence
Deductible: $10,000 per occurrence (standard)
Wind/Hail Deductible: 2% of building value per occurrence, minimum $5,000
Valuation Basis: Replacement Cost Value

COVERAGE B — BUSINESS PERSONAL PROPERTY (BPP)
Coverage Limit: $500,000
Deductible: $10,000 (same as building deductible per occurrence)

COVERAGE C — BUSINESS INCOME WITH EXTRA EXPENSE
Business Income Limit: $500,000
Extra Expense Sublimit: $100,000
Waiting Period: 72 hours (3 days) from date of direct physical loss
Maximum Indemnity Period: 12 months from date of loss

OUTDOOR SIGNS AND FENCES
Outdoor Signs: $10,000 per sign, $25,000 total
Fences: $15,000 total sublimit

COINSURANCE CLAUSE
Coinsurance Requirement: 80% of replacement cost value
Penalty: Proportional reduction of claim payment if coverage is below 80%

COVERED CAUSES OF LOSS — SPECIAL FORM (OPEN PERILS)
Coverage applies to all direct physical loss unless specifically excluded.
Named covered perils include: Fire, Lightning, Windstorm, Hail, Explosion, Aircraft damage, Vehicles, Smoke, Vandalism, Theft, Collapse, Plumbing water damage, Volcanic action.

EXCLUSIONS
The following losses are NOT covered:
1. FLOOD — Damage from flood, surface water, storm surge, tidal water, overflow of bodies of water, or waterborne material regardless of cause, including named storms.
2. EARTHQUAKE — Damage from earthquake, volcanic eruption, landslide, mudslide, subsidence, or earth sinking.
3. EQUIPMENT BREAKDOWN — Mechanical or electrical breakdown, deterioration, depletion, or failure to maintain machinery.
4. EMPLOYEE THEFT — Dishonest acts by employees, directors, trustees, or authorized representatives.
5. WEAR AND TEAR — Gradual deterioration, wear and tear, obsolescence, or marring.
6. FLOOD — See Exclusion 1 above.
7. GOVERNMENT ACTION — Seizure or destruction of property by government authority.
8. NUCLEAR HAZARD — Loss caused by nuclear reaction, radiation, or radioactive contamination.
9. INTENTIONAL ACTS — Loss caused by the named insured or at the direction of the named insured.

SPECIAL CONDITIONS — MOLD REMEDIATION
Mold remediation is covered when resulting directly from a covered water damage loss, provided:
(a) Loss is reported within 30 days of initial water damage discovery
(b) Remediation begins within 30 days of water damage discovery
Sublimit: $50,000 for mold remediation (does not reduce building limit)
Pre-existing mold conditions are excluded.

DUTIES OF THE INSURED AFTER LOSS
Upon occurrence of loss, the insured must:
1. Notify the insurer as soon as practicable
2. Notify police if loss involves theft or vandalism  
3. Protect property from further damage (reasonable costs covered)
4. Complete a full inventory of all damaged property
5. Submit signed sworn proof of loss within 60 days of insurer's written request
6. Submit to examination under oath if requested
7. Cooperate fully with the insurer's investigation
8. Authorize release of financial records for business income claims

CANCELLATION PROVISIONS
Non-payment of premium: 10-day written notice required
All other reasons: 30-day written notice required
After first 60 days: Insurer may only cancel for non-payment, material misrepresentation, or substantial increase in hazard
Premium return on cancellation: Pro-rata if insurer cancels; short-rate if insured cancels`
  },
  general_liability: {
    name: 'Acme Corp Commercial General Liability Policy CGL-2024',
    type: 'liability',
    text: `COMMERCIAL GENERAL LIABILITY INSURANCE POLICY
Policy Number: CGL-2024-ACM-002
Policyholder: Acme Corporation
Policy Period: January 1, 2024 to January 1, 2025
Annual Premium: $12,200

COVERAGE LIMITS
Each Occurrence Limit: $1,000,000 (Bodily Injury and Property Damage combined)
General Aggregate Limit: $2,000,000
Products-Completed Operations Aggregate: $2,000,000
Personal and Advertising Injury Limit: $1,000,000 per occurrence
Medical Payments: $10,000 per person
Damage to Premises Rented to You: $100,000 per occurrence

COVERAGE A — BODILY INJURY AND PROPERTY DAMAGE LIABILITY
We will pay those sums that the insured becomes legally obligated to pay as damages for bodily injury or property damage to which this insurance applies. The occurrence must take place in the coverage territory during the policy period.

COVERAGE B — PERSONAL AND ADVERTISING INJURY LIABILITY  
Coverage applies for personal injury arising from false arrest, malicious prosecution, wrongful eviction, libel, slander, or copyright infringement in advertising.

COVERAGE C — MEDICAL PAYMENTS
We will pay medical expenses regardless of fault for bodily injury caused by accident on premises the insured owns or rents, or because of the insured's operations. Medical expenses must be incurred within one year of the accident.

PRODUCTS-COMPLETED OPERATIONS COVERAGE
Coverage applies to bodily injury or property damage arising from goods, products, or completed work sold or manufactured by the insured. Claims may arise years after the products were sold. The products-completed operations aggregate limit of $2,000,000 applies.

ADDITIONAL INSURED PROVISIONS
Additional insureds may be added by endorsement only. Required endorsements: ISO CG 20 10 (ongoing operations) or CG 20 37 (completed operations). A written contract between the insured and the additional insured must exist prior to loss. Coverage for additional insureds is limited to liability arising from the named insured's operations.

PUNITIVE DAMAGES
Coverage for punitive damages depends on applicable state law. In states where insurability of punitive damages is permitted by law, the policy covers punitive damages up to the occurrence limit. A punitive damages exclusion endorsement applies only where required by law.

EXCLUSIONS
1. Expected or intended injury from the standpoint of the insured
2. Contractual liability (except insured contracts)
3. Liquor liability (for businesses in the liquor trade)
4. Workers' compensation obligations  
5. Pollution
6. Aircraft, auto, or watercraft
7. Mobile equipment
8. War
9. Professional liability/errors and omissions

CLAIM REPORTING REQUIREMENTS
Claims or suits must be reported to the insurer immediately upon receipt. Voluntary payments by the insured without insurer consent may void coverage. The insurer has the right and duty to defend.`
  },
  homeowners: {
    name: 'Johnson Family Homeowners Policy HO3-2024',
    type: 'homeowners',
    text: `HOMEOWNERS POLICY HO-3 (SPECIAL FORM)
Policy Number: HO3-2024-JHN-042
Policyholder: Robert and Susan Johnson
Insured Premises: 567 Maple Drive, Austin, TX 78701
Policy Period: March 1, 2024 to March 1, 2025
Annual Premium: $2,850

SECTION I — PROPERTY COVERAGE

COVERAGE A — DWELLING
Coverage Limit: $450,000 replacement cost
Deductible: $2,500 per occurrence
Wind/Hail Deductible: 1% of Coverage A ($4,500 minimum)

COVERAGE B — OTHER STRUCTURES (Detached garage, fence, shed)
Coverage Limit: $45,000 (10% of Coverage A)
Deductible: Same as Coverage A

COVERAGE C — PERSONAL PROPERTY
Coverage Limit: $225,000 (50% of Coverage A)
Valuation: Actual Cash Value (unless replacement cost endorsement added)
Special Limits: Jewelry $1,500; Firearms $2,500; Electronics $5,000; Cash $200; Securities $1,500

COVERAGE D — LOSS OF USE (Additional Living Expenses)
Coverage Limit: $90,000 (20% of Coverage A)
Maximum Duration: 24 months

COVERED CAUSES OF LOSS — OPEN PERILS ON DWELLING (HO-3)
The dwelling (Coverage A and B) is covered on an open perils basis.
Personal property (Coverage C) is covered for named perils only:
Fire, Lightning, Windstorm, Hail, Explosion, Riot, Aircraft, Vehicles, Smoke, Vandalism, Theft, Falling Objects, Weight of Ice/Snow, Accidental Water Discharge, Sudden Tearing of Appliances, Freezing of Plumbing, Electrical Damage.

SECTION I EXCLUSIONS
1. Flood — water damage from surface water, sewer backup without endorsement
2. Earthquake — earth movement of any kind
3. Neglect — failure to protect property after loss
4. Business pursuits — property used for business purposes
5. Intentional loss
6. Ordinance or law (unless endorsed)
7. Power failure
8. War and nuclear hazard
9. Faulty construction or design

SECTION II — LIABILITY COVERAGE

COVERAGE E — PERSONAL LIABILITY
Coverage Limit: $300,000 per occurrence
Applies to bodily injury and property damage for which an insured is legally liable

COVERAGE F — MEDICAL PAYMENTS TO OTHERS
Coverage Limit: $5,000 per person
No-fault coverage for guests injured on premises (regardless of negligence)

SECTION II EXCLUSIONS
1. Business activities conducted on premises
2. Professional services
3. Intentional acts
4. Watercraft over 50 horsepower
5. Motorized vehicles not used for home maintenance

POLICY CONDITIONS
Insured duties after loss: Notify insurer promptly, protect property, prepare inventory, submit proof of loss within 60 days of request, cooperate with investigation.
Cancellation: 10 days for non-payment; 30 days for other reasons.`
  }
};

async function loadSamplePolicy(type) {
  const policy = SAMPLE_POLICIES[type];
  if (!policy) return;

  const resultEl = document.getElementById('sample-result');
  resultEl.style.display = 'block';
  resultEl.innerHTML = `<div class="eval-progress"><div class="spinner"></div> Ingesting sample policy...</div>`;

  try {
    const formData = new FormData();
    formData.append('text', policy.text);
    formData.append('policy_name', policy.name);
    formData.append('document_type', policy.type);

    const res = await fetch(`${API}/api/ingest/text`, { method: 'POST', body: formData });
    const data = await res.json();

    if (res.ok) {
      resultEl.innerHTML = `
        <div style="color: var(--green); margin-top: 12px;">
          <strong>✅ ${data.policy_name} loaded!</strong><br/>
          <span style="font-size:0.8rem; color: var(--text-muted)">
            ${data.chunks_created} chunks · ${data.entities_extracted} entities · ${data.graph_nodes} graph nodes
          </span>
        </div>`;
      toast(`Sample policy "${data.policy_name}" loaded`, 'success');
      await loadHealth();
    } else {
      resultEl.innerHTML = `<span style="color:var(--red)">Error: ${data.detail}</span>`;
    }
  } catch (e) {
    resultEl.innerHTML = `<span style="color:var(--red)">Error: ${e.message}. Is the server running?</span>`;
  }
}

// ── Query / Chat ───────────────────────────────────────────────
function setQuestion(q) {
  document.getElementById('query-input').value = q;
  document.getElementById('query-input').focus();
}

function handleQueryKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    submitQuery();
  }
}

async function submitQuery() {
  const input = document.getElementById('query-input');
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  const sendBtn = document.getElementById('send-btn');
  sendBtn.disabled = true;

  // Hide welcome screen
  const welcome = document.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  // Add user message
  appendMessage('user', question);

  // Show typing indicator
  const typingId = addTypingIndicator();

  const useGraph = document.getElementById('use-graph-toggle').checked;
  const maxHops = parseInt(document.getElementById('max-hops').value);

  try {
    const res = await fetch(`${API}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, use_graph: useGraph, max_hops: maxHops }),
    });
    const data = await res.json();

    removeTypingIndicator(typingId);

    if (res.ok) {
      appendMessage('assistant', data.answer, {
        confidence: data.confidence_score,
        model: data.model_used,
        time: data.processing_time_s,
      });
      displaySources(data.sources, data.graph_context);
    } else {
      appendMessage('assistant', `❌ Error: ${data.detail || 'Query failed'}`);
    }
  } catch (e) {
    removeTypingIndicator(typingId);
    appendMessage('assistant', `❌ Connection error: ${e.message}. Is the server running?`);
  } finally {
    sendBtn.disabled = false;
  }
}

function appendMessage(role, text, meta = null) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg ${role}`;

  const avatarHtml = role === 'assistant'
    ? `<div class="msg-avatar">🛡️</div>`
    : '';

  let metaHtml = '';
  if (meta) {
    metaHtml = `<div class="msg-meta">
      <span>${meta.model || ''}</span>
      <span>${meta.time || ''}s</span>
      <span class="confidence-pill">Confidence: ${Math.round((meta.confidence || 0) * 100)}%</span>
    </div>`;
  }

  div.innerHTML = `
    ${role === 'assistant' ? avatarHtml : ''}
    <div>
      <div class="msg-bubble">${formatMarkdown(text)}</div>
      ${metaHtml}
    </div>
    ${role === 'user' ? `<div class="msg-avatar" style="background:rgba(100,100,120,0.2); border: 1px solid var(--border);">👤</div>` : ''}
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function formatMarkdown(text) {
  // Simple markdown rendering
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, `<code style="background:var(--bg-elevated);padding:2px 5px;border-radius:3px;font-family:var(--font-mono);font-size:0.85em">$1</code>`)
    .replace(/\n/g, '<br/>');
}

function addTypingIndicator() {
  const id = 'typing-' + Date.now();
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.id = id;
  div.className = 'msg assistant';
  div.innerHTML = `
    <div class="msg-avatar">🛡️</div>
    <div class="msg-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
      </div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function displaySources(sources, graphCtx) {
  const panel = document.getElementById('sources-panel');
  const list = document.getElementById('sources-list');
  const countBadge = document.getElementById('sources-count');
  panel.style.display = 'flex';

  countBadge.textContent = (sources || []).length;
  list.innerHTML = (sources || []).map(s => `
    <div class="source-item">
      <div class="source-header">
        <span class="source-policy">${s.policy_name || 'Policy'}</span>
        ${s.page_number ? `<span class="source-page">p.${s.page_number}</span>` : ''}
        <span class="method-badge method-${s.retrieval_method || 'hybrid'}">${s.retrieval_method || 'hybrid'}</span>
        <span class="source-score">${Math.round(s.relevance_score * 100)}%</span>
      </div>
      <div class="source-text">${s.chunk_text}</div>
    </div>
  `).join('');

  // Graph context
  const graphSection = document.getElementById('graph-ctx-section');
  if (graphCtx && graphCtx.entities_found && graphCtx.entities_found.length > 0) {
    graphSection.style.display = 'block';
    document.getElementById('graph-entities').innerHTML =
      graphCtx.entities_found.slice(0, 8).map(e => `<span class="entity-chip">${e}</span>`).join('');
    document.getElementById('graph-rels').innerHTML =
      (graphCtx.relationships || []).slice(0, 6)
        .map(r => `<div class="rel-item">${r.from} <span style="color:var(--blue-lt)">→[${r.relationship}]→</span> ${r.to}</div>`)
        .join('');
  } else {
    graphSection.style.display = 'none';
  }
}

// ── Knowledge Graph Visualization ─────────────────────────────
let graphSimulation = null;
let graphData = { nodes: [], links: [] };
let allGraphData = { nodes: [], links: [] };

const ENTITY_COLORS = {
  'Policy':          '#3b82f6',
  'Policyholder':    '#8b5cf6',
  'Coverage':        '#06b6d4',
  'CoverageLimit':   '#0ea5e9',
  'Deductible':      '#f59e0b',
  'Exclusion':       '#ef4444',
  'Premium':         '#10b981',
  'Peril':           '#f97316',
  'Condition':       '#84cc16',
  'Endorsement':     '#ec4899',
  'Insurer':         '#a78bfa',
  'Claim':           '#fb923c',
  'LossEvent':       '#f43f5e',
  'InsuredProperty': '#38bdf8',
};

function getNodeColor(type) {
  return ENTITY_COLORS[type] || '#64748b';
}

async function loadGraph() {
  try {
    const res = await fetch(`${API}/api/graph?max_nodes=300`);
    const data = await res.json();

    if (!data.nodes || data.nodes.length === 0) {
      document.getElementById('graph-empty').style.display = 'flex';
      return;
    }
    document.getElementById('graph-empty').style.display = 'none';

    allGraphData = {
      nodes: data.nodes.map(n => ({
        id: n.id, label: n.label, type: n.entity_type,
        properties: n.properties, docId: n.document_id,
      })),
      links: data.edges.map(e => ({
        source: e.source, target: e.target,
        type: e.relationship_type,
      })),
    };

    renderGraph(allGraphData);
  } catch (e) {
    console.error('Graph load error:', e);
    document.getElementById('graph-empty').style.display = 'flex';
  }
}

function filterGraph(query) {
  const q = (typeof query === 'string' ? query : document.getElementById('graph-search')?.value || '').toLowerCase();
  const typeFilter = document.getElementById('graph-type-filter')?.value || '';

  if (!q && !typeFilter) {
    renderGraph(allGraphData);
    return;
  }

  const filteredNodes = allGraphData.nodes.filter(n => {
    const matchesQ = !q || n.label.toLowerCase().includes(q) || (n.type || '').toLowerCase().includes(q);
    const matchesType = !typeFilter || n.type === typeFilter;
    return matchesQ && matchesType;
  });

  const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
  const filteredLinks = allGraphData.links.filter(
    l => filteredNodeIds.has(typeof l.source === 'object' ? l.source.id : l.source) &&
         filteredNodeIds.has(typeof l.target === 'object' ? l.target.id : l.target)
  );

  renderGraph({ nodes: filteredNodes, links: filteredLinks });
}

function renderGraph(data) {
  const container = document.querySelector('.graph-canvas-wrap');
  const svg = d3.select('#graph-canvas');
  svg.selectAll('*').remove();

  const W = container.clientWidth || 800;
  const H = container.clientHeight || 500;
  svg.attr('width', W).attr('height', H);

  // Zoom container
  const g = svg.append('g').attr('class', 'graph-root');

  svg.call(d3.zoom()
    .scaleExtent([0.1, 6])
    .on('zoom', (event) => g.attr('transform', event.transform))
  );

  // Arrow markers
  const defs = svg.append('defs');
  Object.entries(ENTITY_COLORS).forEach(([type, color]) => {
    defs.append('marker')
      .attr('id', `arrow-${type.replace(/[^a-zA-Z]/g, '_')}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 18).attr('refY', 0)
      .attr('markerWidth', 6).attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', color)
      .attr('opacity', 0.6);
  });

  // Clone data to avoid mutation
  const nodes = data.nodes.map(n => ({ ...n }));
  const links = data.links.map(l => ({ ...l }));

  // Force simulation
  if (graphSimulation) graphSimulation.stop();
  graphSimulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(120).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide().radius(30));

  // Links
  const link = g.append('g').selectAll('line')
    .data(links).enter().append('line')
    .attr('class', 'graph-link')
    .attr('marker-end', d => {
      const tgtType = nodes.find(n => n.id === (typeof d.target === 'object' ? d.target.id : d.target))?.type || '';
      const key = tgtType.replace(/[^a-zA-Z]/g, '_');
      return ENTITY_COLORS[tgtType] ? `url(#arrow-${key})` : 'none';
    });

  // Edge labels (shown on hover)
  const edgeLabel = g.append('g').selectAll('text')
    .data(links).enter().append('text')
    .attr('class', 'graph-edge-label')
    .text(d => d.type || '')
    .style('opacity', 0);

  // Node groups
  const node = g.append('g').selectAll('g')
    .data(nodes).enter().append('g')
    .attr('class', 'graph-node')
    .call(d3.drag()
      .on('start', (event, d) => { if (!event.active) graphSimulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on('drag',  (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on('end',   (event, d) => { if (!event.active) graphSimulation.alphaTarget(0); d.fx = null; d.fy = null; })
    )
    .on('click', (event, d) => showNodeDetail(d))
    .on('mouseover', function(event, d) {
      // Highlight connected links
      link.attr('opacity', l =>
        (typeof l.source === 'object' ? l.source.id : l.source) === d.id ||
        (typeof l.target === 'object' ? l.target.id : l.target) === d.id ? 1 : 0.1
      );
      edgeLabel.style('opacity', l =>
        (typeof l.source === 'object' ? l.source.id : l.source) === d.id ||
        (typeof l.target === 'object' ? l.target.id : l.target) === d.id ? 0.9 : 0
      );
    })
    .on('mouseout', function() {
      link.attr('opacity', 0.5);
      edgeLabel.style('opacity', 0);
    });

  node.append('circle')
    .attr('class', 'graph-node-circle')
    .attr('r', 12)
    .attr('fill', d => getNodeColor(d.type) + '33')
    .attr('stroke', d => getNodeColor(d.type))
    .style('filter', d => `drop-shadow(0 0 4px ${getNodeColor(d.type)}88)`);

  node.append('text')
    .attr('class', 'graph-label')
    .attr('dy', 24)
    .attr('text-anchor', 'middle')
    .text(d => d.label?.length > 20 ? d.label.slice(0, 18) + '…' : d.label);

  // Update positions
  graphSimulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);

    edgeLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2);

    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  link.attr('opacity', 0.5);
}

function showNodeDetail(node) {
  const panel = document.getElementById('node-detail');
  document.getElementById('nd-type').textContent = node.type || '?';
  document.getElementById('nd-type').style.background = getNodeColor(node.type) + '22';
  document.getElementById('nd-type').style.color = getNodeColor(node.type);
  document.getElementById('nd-label').textContent = node.label || node.id;

  const props = node.properties || {};
  const propsHtml = Object.entries(props).length > 0
    ? Object.entries(props).map(([k, v]) => `
        <div class="prop-row">
          <span class="prop-key">${k}</span>
          <span class="prop-val">${typeof v === 'object' ? JSON.stringify(v) : v}</span>
        </div>`).join('')
    : '<div style="color:var(--text-muted);font-size:0.78rem">No properties</div>';

  document.getElementById('nd-props').innerHTML = propsHtml;
  panel.style.display = 'block';
}

function closeNodeDetail() {
  document.getElementById('node-detail').style.display = 'none';
}

function refreshGraph() { loadGraph(); }

function resetGraphZoom() {
  const svg = d3.select('#graph-canvas');
  svg.transition().duration(400).call(
    d3.zoom().transform,
    d3.zoomIdentity
  );
}

// ── Evaluation ─────────────────────────────────────────────────
async function loadGoldenDataset() {
  try {
    const res = await fetch(`${API}/api/evaluate/dataset`);
    const data = await res.json();
    const grid = document.getElementById('dataset-grid');
    grid.innerHTML = (data.questions || []).map(q => `
      <div class="dataset-item">
        <div class="dataset-item-header">
          <span class="qid-badge">${q.id}</span>
          <span class="cat-badge">${q.category}</span>
          <span class="diff-badge diff-${q.difficulty}">${q.difficulty}</span>
        </div>
        <div class="dataset-q">${q.question}</div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Dataset load error:', e);
  }
}

async function runEvaluation() {
  const btn = document.getElementById('eval-run-btn');
  const progress = document.getElementById('eval-progress');
  const count = document.getElementById('eval-count').value;
  const category = document.getElementById('eval-category').value;

  btn.disabled = true;
  progress.style.display = 'flex';
  document.getElementById('eval-progress-text').textContent = `Evaluating ${count} questions with LLM judge...`;
  document.getElementById('eval-results-card').style.display = 'none';
  document.getElementById('eval-individual-card').style.display = 'none';

  try {
    let url = `${API}/api/evaluate/run?max_questions=${count}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;

    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();

    if (res.ok) {
      displayEvaluationResults(data);
      toast(`Evaluation complete! F1: ${Math.round(data.aggregate_metrics.f1_score * 100)}%`, 'success');
    } else {
      toast('Evaluation error: ' + (data.detail || 'Unknown'), 'error');
    }
  } catch (e) {
    toast('Connection error during evaluation', 'error');
  } finally {
    btn.disabled = false;
    progress.style.display = 'none';
  }
}

function displayEvaluationResults(report) {
  const card = document.getElementById('eval-results-card');
  const indCard = document.getElementById('eval-individual-card');
  card.style.display = 'block';
  indCard.style.display = 'block';
  document.getElementById('eval-result-badge').textContent =
    `${report.total_questions} Qs · ${report.processing_time_s}s`;

  const m = report.aggregate_metrics;
  const METRICS = [
    { key: 'faithfulness',     label: 'Faithfulness',     color: '#06b6d4' },
    { key: 'answer_relevance', label: 'Ans. Relevance',   color: '#10b981' },
    { key: 'context_precision',label: 'Ctx Precision',    color: '#8b5cf6' },
    { key: 'context_recall',   label: 'Ctx Recall',       color: '#f59e0b' },
    { key: 'f1_score',         label: 'Token F1',         color: '#3b82f6' },
    { key: 'precision',        label: 'Precision',        color: '#f97316' },
    { key: 'recall',           label: 'Recall',           color: '#ec4899' },
  ];

  document.getElementById('metrics-grid').innerHTML = METRICS.map(mt => `
    <div class="metric-card" style="--metric-color: ${mt.color}">
      <div class="metric-val" style="color:${mt.color}">${Math.round(m[mt.key] * 100)}%</div>
      <div class="metric-lbl">${mt.label}</div>
    </div>
  `).join('');

  // Radar chart via canvas
  drawRadar(m);

  // Individual results table
  const tbody = document.getElementById('results-tbody');
  tbody.innerHTML = (report.individual_results || []).map(r => `
    <tr>
      <td><span class="qid-badge">${r.question_id}</span></td>
      <td style="max-width:300px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap" title="${r.question}">${r.question}</td>
      <td>${fmtScore(r.metrics.faithfulness)}</td>
      <td>${fmtScore(r.metrics.answer_relevance)}</td>
      <td>${fmtScore(r.metrics.context_precision)}</td>
      <td>${fmtScore(r.metrics.context_recall)}</td>
      <td>${fmtScore(r.metrics.f1_score)}</td>
    </tr>
  `).join('');
}

function drawRadar(metrics) {
  const canvas = document.getElementById('radar-chart');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R = Math.min(W, H) * 0.38;

  ctx.clearRect(0, 0, W, H);

  const labels = ['Faithfulness', 'Ans Relevance', 'Ctx Precision', 'Ctx Recall', 'F1', 'Precision', 'Recall'];
  const values = [
    metrics.faithfulness, metrics.answer_relevance, metrics.context_precision,
    metrics.context_recall, metrics.f1_score, metrics.precision, metrics.recall
  ];
  const N = labels.length;
  const angles = labels.map((_, i) => (i / N) * Math.PI * 2 - Math.PI / 2);

  // Grid circles
  ctx.strokeStyle = 'rgba(55,80,130,0.3)';
  ctx.lineWidth = 1;
  [0.2, 0.4, 0.6, 0.8, 1.0].forEach(r => {
    ctx.beginPath();
    angles.forEach((a, i) => {
      const x = cx + Math.cos(a) * R * r;
      const y = cy + Math.sin(a) * R * r;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.closePath(); ctx.stroke();
  });

  // Axis lines
  angles.forEach(a => {
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(a) * R, cy + Math.sin(a) * R);
    ctx.strokeStyle = 'rgba(55,80,130,0.4)'; ctx.stroke();
  });

  // Data polygon
  ctx.beginPath();
  angles.forEach((a, i) => {
    const r = values[i] * R;
    const x = cx + Math.cos(a) * r;
    const y = cy + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = 'rgba(59,130,246,0.18)';
  ctx.fill();
  ctx.strokeStyle = '#3b82f6';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Data points
  angles.forEach((a, i) => {
    const r = values[i] * R;
    const x = cx + Math.cos(a) * r;
    const y = cy + Math.sin(a) * r;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#60a5fa';
    ctx.fill();
  });

  // Labels
  ctx.fillStyle = 'rgba(148,163,184,0.85)';
  ctx.font = '11px Inter, sans-serif';
  ctx.textAlign = 'center';
  angles.forEach((a, i) => {
    const r = R + 20;
    const x = cx + Math.cos(a) * r;
    const y = cy + Math.sin(a) * r + 4;
    ctx.fillText(labels[i], x, y);
  });
}

// ── Documents Management ────────────────────────────────────────
async function loadDocuments() {
  try {
    const res = await fetch(`${API}/api/ingest/documents`);
    const data = await res.json();
    const grid = document.getElementById('docs-grid');

    if (!data.documents || data.documents.length === 0) {
      grid.innerHTML = `<div class="docs-empty"><div class="empty-icon">📂</div><p>No documents ingested yet.</p></div>`;
      return;
    }

    grid.innerHTML = data.documents.map(d => `
      <div class="doc-card" id="doc-${d.document_id}">
        <div class="doc-card-header">
          <div style="display:flex; align-items:center; gap:10px">
            <div class="doc-icon">📄</div>
            <div>
              <div class="doc-name">${d.policy_name}</div>
              <span class="doc-type-chip">${d.document_type}</span>
            </div>
          </div>
        </div>
        <div class="doc-stats">
          <div class="doc-stat">📦 ${d.chunks_count} chunks</div>
          <div class="doc-stat">🕸️ ${d.entities_count} entities</div>
          <div class="doc-stat">💾 ${(d.file_size_bytes / 1024).toFixed(1)} KB</div>
        </div>
        <div class="doc-meta">Ingested: ${new Date(d.upload_time).toLocaleString()}</div>
        <div class="doc-actions">
          <button class="btn btn-secondary btn-sm" onclick="queryWithDoc('${d.document_id}', '${d.policy_name}')">Query</button>
          <button class="btn btn-danger btn-sm" onclick="deleteDocument('${d.document_id}', '${d.policy_name}')">Delete</button>
        </div>
      </div>
    `).join('');

    document.getElementById('stat-docs-val').textContent = fmt(data.total_count);
  } catch (e) {
    console.error('Load docs error:', e);
  }
}

function queryWithDoc(docId, policyName) {
  switchTab('query');
  document.getElementById('query-input').value = `What are the main coverages and exclusions in the ${policyName}?`;
}

async function deleteDocument(docId, policyName) {
  if (!confirm(`Delete "${policyName}" from the knowledge base?`)) return;
  try {
    const res = await fetch(`${API}/api/ingest/documents/${docId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      toast(`Deleted "${policyName}"`, 'success');
      document.getElementById(`doc-${docId}`)?.remove();
      await loadHealth();
    } else {
      toast('Delete failed: ' + data.detail, 'error');
    }
  } catch (e) {
    toast('Delete error: ' + e.message, 'error');
  }
}

// ── Initialization ──────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  await loadHealth();
  setInterval(loadHealth, 30000);  // Refresh stats every 30s

  // Handle window resize for graph
  window.addEventListener('resize', () => {
    if (document.getElementById('tab-graph').classList.contains('active')) {
      loadGraph();
    }
  });
});
