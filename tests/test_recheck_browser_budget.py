"""Shared prior decisions must not multiply scoped browser revalidation work."""
from decision_recheck import browser as browser_module
from decision_recheck.engine import run_case
from decision_recheck.freshness import FreshnessSession
from decision_recheck.validate import validate_bundle
from test_browser_boundaries import installed_browser


def source_html(value='Alpha'):
    return f'<p id="value">{value}</p><p id="second">Ready</p><p id="third">Docs</p><p id="fourth">Support</p>'


def scoped_brief(server):
    return {
        'case_id': 'shared-browser-source', 'title': 'Shared source recheck',
        'scope': {'product': 'Owned synthetic page'},
        'permissions': {'allowed_hosts': ['127.0.0.1'], 'allow_private_network': True, 'allow_test_writes': False, 'allowed_actions': ['read', 'assert_text']},
        'sources': [{'id': 'landing', 'kind': 'product', 'url': server.base_url + '/source', 'format': 'html', 'fields': {'value': '#value', 'second': '#second', 'third': '#third', 'fourth': '#fourth'}}],
        'requirements': [{'id': f'req{i}', 'label': f'Declared requirement {i}', 'source_id': 'landing', 'field': 'value', 'operator': 'eq', 'expected': 'Alpha'} for i in range(5)],
        'tasks': [{'id': 'read-ui', 'title': 'Read the actual page', 'url': server.base_url + '/source', 'method': 'browser', 'depends_on': ['landing'], 'dependencies_complete': False, 'steps': [
            {'action': 'assert_text', 'selector': '#second', 'value': 'Ready'},
            {'action': 'assert_text', 'selector': '#third', 'value': 'Docs'},
            {'action': 'assert_text', 'selector': '#fourth', 'value': 'Support'},
        ]}],
    }


def track_browser_reads(monkeypatch):
    reads = []
    original = browser_module.read_html_source
    def tracked(source, brief, budget):
        reads.append({'source': source['id'], 'before': budget.browser_actions})
        return original(source, brief, budget)
    monkeypatch.setattr(browser_module, 'read_html_source', tracked)
    return reads


def test_many_prior_decisions_share_one_fresh_capture_per_baseline_batch(tmp_path, local_sources, installed_browser, monkeypatch):
    local_sources.html('/source', source_html())
    reads = track_browser_reads(monkeypatch)
    brief = scoped_brief(local_sources)
    baseline_dir = tmp_path / 'baseline'
    run_case(brief, baseline_dir)
    archive = (baseline_dir / 'artifacts' / 'source-landing.txt').read_bytes()
    before = len(reads)
    result = run_case(brief, tmp_path / 'recheck', baseline=baseline_dir)
    assert result['status'] == 'complete', result['warnings']
    assert result['freshness']['state'] == 'CURRENT'
    assert len(reads) - before == 4, 'Initial capture, selection check, baseline batch and final export each read the live source independently'
    assert result['tasks'][0]['execution'] == 'passed'
    assert result['usage']['browser_actions'] <= 36
    assert (baseline_dir / 'artifacts' / 'source-landing.txt').read_bytes() == archive
    assert validate_bundle(tmp_path / 'recheck') == []


def test_changed_live_field_invalidates_every_dependent_prior_decision(tmp_path, local_sources, installed_browser):
    local_sources.html('/source', source_html())
    brief = scoped_brief(local_sources)
    baseline_dir = tmp_path / 'baseline'
    run_case(brief, baseline_dir)
    local_sources.html('/source', source_html('Beta'))
    result = run_case(brief, tmp_path / 'recheck', baseline=baseline_dir)
    change = next(c for c in result['changes'] if c['source_id'] == 'landing')
    assert change['state'] == 'STALE_SOURCE'
    assert set(change['affected_ids']) == {*(f'decision-buyer-req{i}' for i in range(5)), 'decision-owner-alignment'}
    assert {d['fit'] for d in result['decisions'] if d['audience'] == 'buyer'} == {'fails'}
    assert result['freshness']['state'] == 'CURRENT', 'Freshly captured Beta is current, while old Alpha decisions are stale'
    assert result['status'] == 'complete'


def test_final_guard_rereads_after_baseline_batch_and_blocks_late_drift(tmp_path, local_sources, installed_browser, monkeypatch):
    local_sources.html('/source', source_html())
    brief = scoped_brief(local_sources)
    baseline_dir = tmp_path / 'baseline'
    run_case(brief, baseline_dir)
    original = FreshnessSession.check_baseline
    def change_after_batch(self, baseline):
        result = original(self, baseline)
        local_sources.html('/source', source_html('Changed after baseline validation'))
        return result
    monkeypatch.setattr(FreshnessSession, 'check_baseline', change_after_batch)
    result = run_case(brief, tmp_path / 'recheck', baseline=baseline_dir)
    assert result['status'] == 'partial'
    assert result['freshness']['state'] == 'STALE_REASONING'
    assert any('Current-status export was blocked' in w for w in result['warnings'])
    assert validate_bundle(tmp_path / 'recheck') == []


def test_failed_live_batch_cannot_report_dependent_nodes_current(tmp_path, local_sources, installed_browser, monkeypatch):
    local_sources.html('/source', source_html())
    brief = scoped_brief(local_sources)
    baseline_dir = tmp_path / 'baseline'
    run_case(brief, baseline_dir)
    original = FreshnessSession.check_baseline
    def become_unavailable(self, baseline):
        local_sources.html('/source', '<h1>Temporarily unavailable</h1>', status=503)
        return original(self, baseline)
    monkeypatch.setattr(FreshnessSession, 'check_baseline', become_unavailable)
    result = run_case(brief, tmp_path / 'recheck', baseline=baseline_dir)
    assert result['status'] == 'partial'
    assert result['freshness']['state'] == 'UNVERIFIABLE'
    checks = [r for r in result['freshness']['receipts'] if r.get('purpose') == 'baseline_recheck' and r.get('domain_id', '').startswith('decision-buyer')]
    assert len(checks) == 5
    assert all(r['state'] == 'UNVERIFIABLE' for r in checks)
