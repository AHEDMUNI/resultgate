"""Planning scenarios, NOT observed revenue or a provider quote."""
from decimal import Decimal as D
import json

def scenario(calls, collections, hosting=D('15'), variable_per_call=D('0.00002')):
    revenue=D(calls)*D('0.001')
    operations=hosting+D(calls)*variable_per_call
    fees={
        'x402_per_call':D(max(calls-1000,0))*D('0.001'),
        'card_prepaid_20usd':revenue*D('0.029')+D(collections)*D('0.30'),
        'monthly_usage_billing':revenue*D('0.036')+D(collections)*D('0.30'),
    }
    return {'calls':calls,'gross_usd':str(revenue),'modeled_operations_usd':str(operations),
            'rails':{k:{'fee_usd':str(v),'contribution_before_tax_labor_other_usd':str(revenue-v-operations)} for k,v in fees.items()}}

if __name__=='__main__':
    print(json.dumps([scenario(100000,5),scenario(1000000,50)],indent=2))
