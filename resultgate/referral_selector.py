"""Read-only provider selection and handoff. Never executes, enrolls or charges."""
import json
from importlib.resources import files
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Provider = Literal['browseract','searchapi','pdfco','make','apify','firecrawl']
Need = Literal['browser_interaction','search_results','document_extraction','app_workflow','specialized_actor','web_to_markdown']

def catalog():
    return json.loads(files('resultgate').joinpath('referral_catalog.json').read_text(encoding='utf-8'))

class Selection(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    need: Need
    sources_permitted: bool = False
    sensitive_or_login_required: bool = False
    existing_solution_sufficient: bool = False
    local_solution_sufficient: bool = True
    recurring_need: bool = False
    maximum_monthly_budget_usd: int = Field(default=0, ge=0, le=100000)


def select(request: Selection):
    data=catalog()
    decision='prepare_free_evaluation'
    if not request.sources_permitted or request.sensitive_or_login_required:
        decision='reject'
    elif request.existing_solution_sufficient:
        decision='use_existing_solution'
    elif request.local_solution_sufficient:
        decision='use_local_first'
    matched=[p for p in data['providers'] if p['need']==request.need]
    # Capability matching only. No affiliate rate or payout field is read here.
    candidates=[] if decision in ('reject','use_existing_solution') else matched
    return {'decision':decision,'reason':{
        'reject':'This limited pilot requires permitted, non-sensitive inputs and no third-party login tasks.',
        'use_existing_solution':'An existing solution is sufficient; avoid a new subscription.',
        'use_local_first':'Try the local/direct alternative before connecting another provider.',
        'prepare_free_evaluation':'Exact capability match. Evaluate with free allowance first; paid fit is not yet established.'}[decision],
        'candidates':candidates,'requested_budget_usd':request.maximum_monthly_budget_usd,
        'budget_is_authorization':False,'paid_plan_recommended':False,
        'execution_started':False,'commercial_referral_enabled':False,
        'ranking_policy':data['ranking_policy'],
        'next_step':'Stop.' if not candidates else 'Call prepare_referral_task with the provider id; review its free example and official integration steps.'}

class Preparation(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    provider_id: Provider
    sources_permitted: bool = False
    sensitive_data: bool = False


def prepare(request: Preparation):
    if not request.sources_permitted or request.sensitive_data:
        return {'status':'rejected','execution_started':False,'reason':'Use only permitted public or synthetic, non-sensitive inputs.'}
    p=next(p for p in catalog()['providers'] if p['id']==request.provider_id)
    return {'status':'instructions_only','provider':p['name'],'task':p['task'],
        'input_fields':p['input_fields'],'example_inputs':p['example'],'output_fields':p['output_fields'],
        'steps':p['steps'],'integration':p['integration'],'free_alternative':p['free_alternative'],
        'handoff':{'url':p['handoff_url'],'tracking':'none','affiliate_link':False},
        'qualification':p['qualification'],'test_status':p['test_status'],
        'ai_mcp_eligibility':p['ai_mcp_eligibility'],
        'commercial_blockers':p.get('commercial_blockers', ['Provider qualification and issued link remain pending.']),
        'disclosure':catalog()['disclosure'],'execution_started':False,'purchase_authorized':False,
        'approval_boundary':'Owner reviews provider terms, any account registration, OAuth scopes and maximum cost. ResultGate accepts no credentials; never infer spending consent from this task.',
        'evidence_to_keep':['provider run id if available','input hash','output with errors','actual UTC time','credit consumption shown by provider'],
        'attribution_warning':'API calls and clicks are not attributed sales. No active commercial link is supplied.'}


def register(mcp):
    @mcp.tool()
    def list_referral_providers() -> dict:
        """List six researched provider cards and unresolved eligibility, prices and payout terms. Not contracted sellers; no execution or tracked links."""
        return catalog()
    @mcp.tool()
    def recommend_referral_service(request: Selection) -> dict:
        """Match an explicit need to capability; reject unsafe scope, prefer existing/local/free. Budget is not authorization. No commission-based ranking."""
        return select(request)
    @mcp.tool()
    def prepare_referral_task(request: Preparation) -> dict:
        """Return provider-specific task, example, output fields and official connection steps. No execution, account creation, secrets, purchase or attribution."""
        return prepare(request)
