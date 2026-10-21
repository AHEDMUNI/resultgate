import json
from pathlib import Path
from resultgate.models import ExtractionInput,CitationInput

def inline(value,defs):
    if isinstance(value,dict):
        if '$ref' in value:return inline(defs[value['$ref'].split('/')[-1]],defs)
        return {k:inline(v,defs) for k,v in value.items() if k!='$defs' and not (k=='default' and v is None)}
    if isinstance(value,list):return [inline(v,defs) for v in value]
    return value
spec={'openapi':'3.1.0','info':{'title':'ResultGate authenticated local API','version':'0.2.0'},'servers':[{'url':'http://127.0.0.1:8765'}], 'components':{'securitySchemes':{'bearerAuth':{'type':'http','scheme':'bearer'}}}, 'paths':{}}
for name,model in [('extraction',ExtractionInput),('citations',CitationInput)]:
    schema=model.model_json_schema()
    spec['paths']['/v1/'+name]={'post':{'operationId':'check_'+name,'security':[{'bearerAuth':[]}],'requestBody':{'required':True,'content':{'application/json':{'schema':inline(schema,schema.get('$defs',{}))}}},'responses':{str(k):{'description':v} for k,v in {200:'Contract audit, never a truth guarantee',400:'Invalid Host',401:'Missing or invalid bearer token',403:'Browser Origin rejected',408:'Body timeout',413:'Body too large',415:'Content type must be application/json',422:'Invalid input'}.items()}}}
Path(__file__).resolve().parents[1].joinpath('openapi.json').write_text(json.dumps(spec,indent=2)+'\n')
