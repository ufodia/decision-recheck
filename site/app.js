'use strict';

// This viewer never executes bundle content. All imported text is rendered with
// textContent; local artifact verification remains the CLI's responsibility.
const state = { catalog: null, loading: false, snapshot: 'A', audience: 'owner', imported: null, bundle: null };
const roleNames = { owner: 'Product owner', buyer: 'Buyer / user', marketing: 'Marketing / support' };
const roleQuestions = {
  owner: 'What needs a product or documentation review?',
  buyer: 'Does this offer meet the stated requirements?',
  marketing: 'Which promises and answers need qualification?'
};
const byId = (id) => document.getElementById(id);
const safeText = (value, fallback = '') => typeof value === 'string' ? value : fallback;
const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function validateBundle(bundle) {
  if (!isObject(bundle) || bundle.schema_version !== '1.0') throw new Error('Expected a Decision Recheck bundle with schema_version 1.0.');
  const pending = [[bundle, 0]];
  let nodeCount = 0;
  while (pending.length) {
    const [value, depth] = pending.pop();
    if (++nodeCount > 50000 || depth > 30) throw new Error('The bundle structure exceeds the local preview limit.');
    if (typeof value === 'string' && value.length > 200000) throw new Error('A bundle text value exceeds the local preview limit.');
    if (value !== null && typeof value === 'object') {
      for (const child of Object.values(value)) pending.push([child, depth + 1]);
    }
  }
  for (const field of ['run_id', 'title', 'created_at', 'mode', 'status']) {
    if (typeof bundle[field] !== 'string' || bundle[field].length > 2000) throw new Error(`Invalid bundle field: ${field}.`);
  }
  if (!isObject(bundle.scope) || !isObject(bundle.freshness)) throw new Error('The bundle needs scope and freshness records.');
  for (const field of ['sources', 'artifacts', 'tasks', 'findings', 'decisions', 'changes', 'warnings']) {
    if (!Array.isArray(bundle[field]) || bundle[field].length > 1000) throw new Error(`Invalid or oversized bundle list: ${field}.`);
  }
  const allowedRoles = new Set(Object.keys(roleNames));
  for (const field of ['sources', 'artifacts', 'tasks', 'findings', 'decisions']) {
    const ids = new Set();
    for (const record of bundle[field]) {
      if (!isObject(record) || typeof record.id !== 'string' || !record.id || record.id.length > 200 || ids.has(record.id)) throw new Error(`Invalid or duplicate record in ${field}.`);
      ids.add(record.id);
      if (record.evidence_ids !== undefined && (!Array.isArray(record.evidence_ids) || record.evidence_ids.some(id => typeof id !== 'string'))) throw new Error('Invalid evidence references.');
      if (field === 'decisions' && !allowedRoles.has(record.audience)) throw new Error('Unknown report audience.');
      if (field === 'findings' && (!Array.isArray(record.audiences) || record.audiences.some(role => !allowedRoles.has(role)))) throw new Error('Invalid finding audiences.');
    }
  }
  return bundle;
}

function validateCatalog(catalog) {
  if (!isObject(catalog) || catalog.schema_version !== '1.0' || catalog.fictional !== true || !Array.isArray(catalog.snapshots)) throw new Error('The recorded fixture catalog is not valid.');
  for (const id of ['A', 'B', 'C', 'footer']) {
    const snapshots = catalog.snapshots.filter(snapshot => isObject(snapshot) && snapshot.id === id);
    if (snapshots.length !== 1) throw new Error(`Missing or duplicate snapshot ${id}.`);
    validateBundle(snapshots[0].bundle);
  }
  return catalog;
}

function displayTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? 'Capture time unavailable' : date.toISOString().replace('T', ' ').replace('.000Z', ' UTC');
}

function tokenText(value) {
  return safeText(value, 'unknown').replaceAll('_', ' ').toLowerCase();
}

function badge(text, warning = false) {
  return element('span', `mini-status${warning ? ' warning' : ''}`, text);
}

function publishedArtifactUrl(path) {
  if (state.imported || !['A', 'B', 'C', 'footer'].includes(state.snapshot)) return null;
  if (typeof path !== 'string' || !/^[a-zA-Z0-9._/-]+$/.test(path) || path.startsWith('/') || path.split('/').some(part => part === '.' || part === '..' || !part)) return null;
  return `/data/${state.snapshot}/${path.split('/').map(encodeURIComponent).join('/')}`;
}

function appendEvidenceLinks(container, ids, lookup) {
  if (!Array.isArray(ids) || !ids.length) {
    container.append(element('span', '', 'No evidence references recorded'));
    return;
  }
  for (const id of [...new Set(ids)].slice(0, 15)) {
    const target = lookup.get(id);
    if (target) {
      const link = element('a', '', `${id} ↗`);
      link.href = `#${target}`;
      link.addEventListener('click', () => {
        const detail = byId(target);
        if (detail && detail.tagName === 'DETAILS') detail.open = true;
      });
      container.append(link);
    } else {
      container.append(element('span', '', `${id} · missing from this preview`));
    }
  }
}

function renderEvidence(bundle) {
  const container = byId('evidence-list');
  container.replaceChildren();
  const lookup = new Map();
  const artifacts = new Map(bundle.artifacts.map(artifact => [artifact.id, artifact]));
  const assignedArtifacts = new Set();
  const records = bundle.sources.map(source => ({ kind: 'source', record: source }));
  for (const source of bundle.sources) if (source.artifact_id) assignedArtifacts.add(source.artifact_id);
  for (const artifact of bundle.artifacts) {
    if (!assignedArtifacts.has(artifact.id)) records.push({ kind: 'artifact', record: artifact });
  }
  for (const [index, entry] of records.entries()) {
    const { kind, record } = entry;
    const id = `evidence-record-${index}`;
    lookup.set(record.id, id);
    if (record.artifact_id) lookup.set(record.artifact_id, id);
    const details = element('details', 'evidence-item');
    details.id = id;
    const summary = element('summary');
    summary.append(element('span', '', kind === 'source' ? tokenText(record.kind) : 'Task / local artifact'));
    details.append(summary, element('h4', '', record.id));
    const sourceArtifact = kind === 'source' ? artifacts.get(record.artifact_id) : record;
    if (kind === 'source') {
      details.append(element('p', '', safeText(record.url, 'No public URL recorded')));
      if (isObject(record.values)) {
        const quote = element('blockquote');
        for (const [key, value] of Object.entries(record.values).slice(0, 20)) {
          const row = element('p');
          const label = element('strong', '', `${key.replaceAll('_', ' ')}: `);
          row.append(label, document.createTextNode(typeof value === 'string' ? value : JSON.stringify(value)));
          quote.append(row);
        }
        details.append(quote);
      }
      details.append(element('div', 'evidence-meta', `${tokenText(record.status)} · ${displayTime(record.checked_at)}`));
    }
    const task = bundle.tasks.find(item => Array.isArray(item.evidence_ids) && item.evidence_ids.includes(record.id));
    if (task) {
      lookup.set(task.id, id);
      details.append(element('p', '', `${safeText(task.title)} — ${safeText(task.summary)}`));
      details.append(element('div', 'evidence-meta', `Task execution: ${tokenText(task.execution)}`));
    }
    if (sourceArtifact) {
      details.append(element('div', 'evidence-meta', `Artifact: ${safeText(sourceArtifact.path)}\nSHA-256: ${safeText(sourceArtifact.sha256)}\n${state.imported ? 'Artifact bytes are not included in this metadata preview.' : 'Published fixture capture; verify artifact bytes with the CLI.'}`));
      const artifactUrl = publishedArtifactUrl(sourceArtifact.path);
      if (artifactUrl) {
        const link = element('a', 'artifact-download', 'Download captured artifact ↓');
        link.href = artifactUrl;
        link.download = sourceArtifact.path.split('/').at(-1);
        details.append(link);
      }
    }
    container.append(details);
  }
  if (!records.length) container.append(element('p', 'evidence-empty', 'No evidence artifacts were captured. Conclusions need further review.'));
  return lookup;
}

function renderReport(bundle, lookup) {
  const container = byId('report-content');
  container.replaceChildren();
  const decisions = bundle.decisions.filter(decision => decision.audience === state.audience);
  const findings = bundle.findings.filter(finding => finding.audiences.includes(state.audience));
  container.append(element('p', 'report-kicker', `${roleNames[state.audience]} / ${state.imported ? 'local preview' : 'fictional example'}`));
  container.append(element('h3', '', decisions[0] ? safeText(decisions[0].title, roleQuestions[state.audience]) : roleQuestions[state.audience]));
  container.append(element('p', 'report-summary', decisions[0] ? safeText(decisions[0].summary) : 'No decision is recorded for this audience. Review the available evidence and missing work.'));
  const statuses = element('div', 'report-statuses');
  const fits = [...new Set(decisions.map(decision => tokenText(decision.fit)))];
  for (const fit of fits) {
    const count = decisions.filter(decision => tokenText(decision.fit) === fit).length;
    const plural = count === 1 ? 'decision' : 'decisions';
    const labels = {
      fails: `${count} ${plural} ${count === 1 ? 'fails' : 'fail'}`,
      meets: `${count} ${plural} ${count === 1 ? 'meets' : 'meet'} requirements`,
      inconclusive: `${count} inconclusive ${plural}`,
      conditional: `${count} conditional ${plural}`
    };
    const label = decisions.length > 1 ? (labels[fit] || `${fit}: ${count} ${plural}`) : `Fit: ${fit}`;
    statuses.append(badge(label, ['fails', 'inconclusive', 'conditional'].includes(fit)));
  }
  statuses.append(badge(`Source check: ${tokenText(bundle.freshness.state)}`, bundle.freshness.state !== 'CURRENT'));
  statuses.append(badge('Conclusions: proposed'));
  container.append(statuses);
  if (decisions[0]) {
    const primaryEvidence = element('div', 'finding-evidence primary-evidence');
    appendEvidenceLinks(primaryEvidence, decisions[0].evidence_ids, lookup);
    container.append(primaryEvidence);
  }
  if (bundle.changes.length) {
    const changeBox = element('details', 'change-note');
    const changed = bundle.changes.filter(change => isObject(change) && change.kind === 'changed').length;
    changeBox.append(element('summary', '', `Recorded recheck · ${changed} changed dependency record${changed === 1 ? '' : 's'}`));
    changeBox.append(element('p', 'change-explanation', 'Expand the source and task dependency trail below. An unchanged record can reuse scoped fixture evidence; live browser tasks still rerun.'));
    for (const change of bundle.changes.slice(0, 8)) {
      if (!isObject(change)) continue;
      const row = element('p');
      row.append(document.createTextNode(`${safeText(change.source_id, 'Source')}: ${tokenText(change.kind)}`));
      if (Array.isArray(change.affected_ids) && change.affected_ids.length) {
        row.append(document.createTextNode(` · affected: ${change.affected_ids.filter(id => typeof id === 'string').join(', ')}`));
      }
      changeBox.append(row);
    }
    container.append(changeBox);
  }
  const list = element('div', 'finding-list');
  for (const decision of decisions.slice(1)) {
    const article = element('article', 'finding');
    const top = element('div', 'finding-topline');
    top.append(element('h4', '', safeText(decision.title)), element('span', 'finding-label', `Decision · ${tokenText(decision.fit)}`));
    article.append(top, element('p', '', safeText(decision.summary)));
    const links = element('div', 'finding-evidence');
    appendEvidenceLinks(links, decision.evidence_ids, lookup);
    article.append(links);
    list.append(article);
  }
  for (const finding of findings) {
    const article = element('article', 'finding');
    const top = element('div', 'finding-topline');
    top.append(element('h4', '', safeText(finding.title)), element('span', 'finding-label', tokenText(finding.support)));
    article.append(top, element('p', '', safeText(finding.summary)));
    if (safeText(finding.suggestion)) article.append(element('p', '', `Suggested next step: ${finding.suggestion}`));
    const links = element('div', 'finding-evidence');
    appendEvidenceLinks(links, finding.evidence_ids, lookup);
    article.append(links);
    list.append(article);
  }
  if (!decisions.length && !findings.length) list.append(element('p', 'report-summary', 'No audience-specific records are present. This is an evidence gap, not a passing result.'));
  for (const warning of bundle.warnings.slice(0, 10)) {
    const text = typeof warning === 'string' ? warning : JSON.stringify(warning);
    list.append(element('p', 'report-summary', `Run note: ${text}`));
  }
  container.append(list);
}

function render() {
  if (!state.catalog && !state.imported) return;
  const snapshot = state.catalog && state.catalog.snapshots.find(item => item.id === state.snapshot);
  const bundle = state.imported || snapshot?.bundle;
  if (!bundle) return;
  state.bundle = bundle;
  const lookup = renderEvidence(bundle);
  renderReport(bundle, lookup);
  byId('run-status').textContent = `${tokenText(bundle.status)} run`;
  byId('run-status').classList.toggle('warning', bundle.status !== 'complete');
  byId('case-scope').textContent = [bundle.scope.plan, bundle.scope.currency, bundle.scope.billing_period].filter(value => typeof value === 'string').join(' · ') || 'Scope not recorded';
  byId('evidence-mode').textContent = state.imported ? 'Imported metadata' : 'Recorded fixture';
  byId('recorded-time').textContent = `${state.imported ? 'Imported capture' : 'Fixture capture'} · ${displayTime(bundle.created_at)}`;
  byId('download-bundle').disabled = false;
  const reportLink = byId('open-report');
  reportLink.hidden = Boolean(state.imported);
  if (!state.imported) reportLink.href = `/data/${state.snapshot}/report-${state.audience}.html`;
  byId('snapshot-panel').setAttribute('aria-labelledby', state.imported ? 'case-title' : `snapshot-${state.snapshot}`);
  if (state.imported) byId('snapshot-panel').setAttribute('aria-busy', 'false');
  if (state.imported) {
    byId('case-title').textContent = bundle.title;
    document.querySelector('.sidebar-description').textContent = 'Imported evidence metadata. Review the original brief for requirements and budget.';
    document.querySelector('.scope-list div:nth-child(1) dd').textContent = 'See decision records';
    document.querySelector('.scope-list div:nth-child(2) dd').textContent = 'See original brief';
  } else {
    byId('case-title').replaceChildren(document.createTextNode('Can we export'), document.createElement('br'), document.createTextNode('within budget?'));
    document.querySelector('.sidebar-description').textContent = 'A small team needs a usable export without exceeding its monthly limit.';
    document.querySelector('.scope-list div:nth-child(1) dd').textContent = 'CSV export';
    document.querySelector('.scope-list div:nth-child(2) dd').textContent = '$20 / month';
  }
}

function chooseSnapshot(id, focus = false) {
  if (!state.catalog) {
    byId('demo-feedback').textContent = state.loading
      ? 'The recorded example is still loading. Your local preview stays open.'
      : 'The recorded example is unavailable. Retry loading it to switch snapshots; your local preview stays open.';
    return;
  }
  state.snapshot = id;
  state.imported = null;
  for (const button of document.querySelectorAll('[data-snapshot]')) {
    const selected = button.dataset.snapshot === id;
    button.setAttribute('aria-selected', String(selected));
    button.tabIndex = selected ? 0 : -1;
    if (selected && focus) button.focus();
  }
  byId('demo-feedback').textContent = '';
  render();
}

function chooseAudience(audience, focus = false) {
  state.audience = audience;
  for (const button of document.querySelectorAll('[data-role]')) {
    const selected = button.dataset.role === audience;
    button.setAttribute('aria-selected', String(selected));
    button.tabIndex = selected ? 0 : -1;
    if (selected && focus) button.focus();
  }
  byId('report-panel').setAttribute('aria-labelledby', `role-${audience}`);
  render();
}

function wireTabs(selector, choose, field) {
  const buttons = [...document.querySelectorAll(selector)];
  for (const [index, button] of buttons.entries()) {
    button.addEventListener('click', () => choose(button.dataset[field]));
    button.addEventListener('keydown', (event) => {
      let next;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % buttons.length;
      if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + buttons.length) % buttons.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = buttons.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        choose(buttons[next].dataset[field], true);
      }
    });
  }
}

wireTabs('[data-snapshot]', chooseSnapshot, 'snapshot');
wireTabs('[data-role]', chooseAudience, 'role');
byId('explore-changed-offer').addEventListener('click', () => {
  // Remember the intended example even if the initial catalog request is pending.
  if (state.catalog) chooseSnapshot('B');
  else state.snapshot = 'B';
});
byId('retry-fixture').addEventListener('click', loadDemo);
byId('download-bundle').addEventListener('click', () => {
  if (!state.bundle) return;
  const blob = new Blob([`${JSON.stringify(state.bundle, null, 2)}\n`], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = element('a');
  link.href = url;
  link.download = `decision-recheck-${state.imported ? 'imported' : state.snapshot}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
byId('bundle-file').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    if (file.size > 2 * 1024 * 1024) throw new Error('Choose a bundle JSON smaller than 2 MB.');
    state.imported = validateBundle(JSON.parse(await file.text()));
    for (const button of document.querySelectorAll('[data-snapshot]')) button.setAttribute('aria-selected', 'false');
    render();
    byId('demo-feedback').textContent = 'Opened locally. This is a metadata preview; no artifact integrity or live-source verification has run in this browser. Choose a snapshot tab to return to the fictional example.';
  } catch (error) {
    byId('demo-feedback').textContent = `Could not open that bundle. ${error.message}`;
  }
  event.target.value = '';
});

async function loadDemo() {
  if (state.loading) return;
  state.loading = true;
  byId('retry-fixture').disabled = true;
  byId('retry-fixture').textContent = 'Loading example…';
  byId('snapshot-panel').setAttribute('aria-busy', String(!state.imported));
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch('/data/demo.json', { credentials: 'omit', signal: controller.signal });
    if (!response.ok) throw new Error('The recorded fixture is temporarily unavailable.');
    const text = await response.text();
    if (text.length > 2 * 1024 * 1024) throw new Error('The fixture catalog exceeds the viewer limit.');
    state.catalog = validateCatalog(JSON.parse(text));
    byId('retry-fixture').hidden = true;
    if (state.imported) render();
    else chooseSnapshot(state.snapshot);
  } catch (error) {
    if (!state.imported) {
      byId('run-status').textContent = 'Fixture unavailable';
      byId('run-status').classList.add('warning');
      byId('report-content').replaceChildren(element('p', 'loading-text', 'The recorded example could not load. Retry below, open a local bundle JSON, or run the example from the repository.'));
      byId('open-report').hidden = true;
    }
    const reason = error.name === 'AbortError' ? 'The request timed out.' : error.message;
    byId('demo-feedback').textContent = `Could not load the example. ${reason} ${state.imported ? 'Your imported preview remains available.' : 'You can still open your own bundle.'}`;
    byId('retry-fixture').hidden = false;
  } finally {
    clearTimeout(timeout);
    state.loading = false;
    byId('retry-fixture').disabled = false;
    byId('retry-fixture').textContent = 'Retry loading example';
    byId('snapshot-panel').setAttribute('aria-busy', 'false');
  }
}
loadDemo();
