"""Deterministic static cards from the same data used by local MCP."""
import html,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def render(data):
    e=html.escape
    out=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ResultGate — service selection pilot</title><link rel="stylesheet" href="/resultgate-site.css"></head><body><main>',
    '<nav><a href="/">ResultGate</a> · <a href="/browseract">BrowserAct demo</a> · <a href="/referrals.json">Catalog JSON</a> · <a href="/privacy">Privacy</a></nav>',
    '<h1>Choose a service for your agent’s actual task</h1>',
    '<p>Six researched providers; BrowserAct has an account-issued affiliate link and written MCP permission. Provider execution, billing and accounts remain with the provider. ResultGate evaluates fit and prepares a bounded task. Nothing on this page buys or runs a service.</p>',
    '<p>'+e(data['disclosure'])+'</p><p>Sources reviewed '+e(data['checked_on'])+' (America/Chicago). Recheck price and terms before subscribing.</p>',
    '<h2>Try the selection tools without keys or a purchase</h2><ol><li><a href="https://github.com/AHEDMUNI/resultgate/blob/main/docs/referrals/OPERATOR.md">Follow the Cursor setup and ready prompts</a>.</li><li>Call <code>list_referral_providers</code>, then <code>recommend_referral_service</code> with your need and permission flags.</li><li>Use <code>prepare_referral_task</code> for the selected id. Review the free/direct alternative first.</li><li>Only the owner can authorize a provider account or a run. Return output for inspection; no automatic spending or enrollment.</li></ol>',
    '<p>The companion runs locally. Hosted <code>/mcp</code> remains unchanged and does not expose these tools. Local MCP sends no telemetry. Unknown usage is not zero.</p>',
    '<p><strong>Internal evidence:</strong> BrowserAct uses the previously supplied 20-record practice CSV. Firecrawl keyless MCP was exercised on the same public practice homepage. Other provider execution is pending authorized accounts; their local task-contract tests are not provider runs.</p>',
    '<p>'+e(data['ranking_policy'])+'</p>']
    for p in data['providers']:
        out += ['<section id="'+e(p['id'])+'"><h2>'+e(p['name'])+'</h2><p><strong>Need:</strong> '+e(p['use_case'])+'</p>']
        for key,label in [('qualification','Qualification'),('pricing','Price and billing'),('free_alternative','Free/direct option'),('limits','Limits'),('commission_terms','Published commission, not our entitlement'),('attribution','Attribution'),('payout','Payout conditions'),('refunds','Refunds and unresolved terms'),('test_status','Test evidence')]:
            out.append('<p><strong>'+label+':</strong> '+e(p[key])+'</p>')
        if p.get('commercial_blockers'):
            out.append('<p><strong>Commercial verification remaining:</strong> '+e(' '.join(p['commercial_blockers']))+'</p>')
        out += ['<p>'+e(p['cross_device'])+'</p><p><strong>Task:</strong> '+e(p['task'])+'</p>', '<p>Input fields: <code>'+e(', '.join(p['input_fields']))+'</code>. Output fields: <code>'+e(', '.join(p['output_fields']))+'</code>.</p>', '<ol>'+''.join('<li>'+e(x)+'</li>' for x in p['steps'])+'</ol>', '<p><a href="'+e(p['integration']['docs_url'],quote=True)+'" rel="noopener noreferrer">Official integration guide</a> · <a href="'+e(p['handoff_url'],quote=True)+'" rel="noopener noreferrer sponsored">'+('BrowserAct — affiliate link' if p.get('referral_url') else 'Provider pricing — untracked')+'</a></p>', '<p>Sources: '+ ' · '.join('<a href="'+e(url,quote=True)+'">'+e(key)+'</a>' for key,url in p['sources'].items())+'</p></section>']
    out += ['<h2>Support and feedback</h2><p>Operated by ALLUBI Yerba Mate LLC. Live checkout is not currently available.</p><p>Report setup failures via <a href="https://github.com/AHEDMUNI/resultgate/issues/new">GitHub</a> or support@allubiyerbamate.com. Do not include keys, private URLs or customer data. Identify internal/ALLUBI tests separately. No independent users or sales are claimed.</p><p><a href="/terms">Terms</a> · <a href="/refunds">Refunds</a></p></main></body></html>']
    return '\n'.join(out)+'\n'
if __name__=='__main__':
    data=json.loads((ROOT/'resultgate/referral_catalog.json').read_text())
    (ROOT/'web/business/referrals.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'web/business/referrals.html').write_text(render(data))
