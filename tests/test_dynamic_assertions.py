"""Real-browser assertions wait for delayed content without inventing a pass."""
from decision_recheck import browser as browser_module
from decision_recheck.policy import Budget
from test_browser_boundaries import installed_browser, browser_brief, attempt


def test_assert_text_waits_for_delayed_literal_content(tmp_path, local_sources, installed_browser):
    local_sources.html('/task', '<div id="result">Loading</div><script>setTimeout(()=>{document.getElementById("result").textContent="a.b [ready]"},650)</script>')
    result, _ = attempt(local_sources, tmp_path, browser_brief(local_sources), [{'action':'assert_text','selector':'#result','value':'a.b [ready]'}])
    assert result['execution'] == 'passed', result
    assert result['steps'][0]['result'] == 'a.b [ready]'


def test_permanent_text_mismatch_is_failed_not_passed_or_blocked(tmp_path, local_sources, installed_browser):
    local_sources.html('/task', '<div id="result">This capability is unavailable</div>')
    result, _ = attempt(local_sources, tmp_path, browser_brief(local_sources), [{'action':'assert_text','selector':'#result','value':'Capability completed'}])
    assert result['execution'] == 'failed', result
    assert result['steps'][0]['matched'] is False


def test_disappearing_assertion_target_is_incomplete(tmp_path, local_sources, installed_browser):
    local_sources.html('/task', '<div id="result">Loading</div><script>setTimeout(()=>document.getElementById("result").remove(),650)</script>')
    result, _ = attempt(local_sources, tmp_path, browser_brief(local_sources), [{'action':'assert_text','selector':'#result','value':'Capability completed'}])
    assert result['execution'] == 'blocked', result


def test_run_deadline_during_assertion_is_incomplete(tmp_path, local_sources, installed_browser):
    local_sources.html('/task', '<div id="result">Loading</div>')
    brief = browser_brief(local_sources)
    budget = Budget({**brief['limits'], 'timeout_seconds': 2})
    result, _ = browser_module.run_task({'id':'deadline','url':local_sources.base_url+'/task','steps':[{'action':'assert_text','selector':'#result','value':'Capability completed'}]}, brief, budget, tmp_path)
    assert result['execution'] == 'blocked', result
    assert result['error_type'] == 'BudgetExceeded'
