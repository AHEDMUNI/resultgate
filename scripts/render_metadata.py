"""Generate reviewable metadata after the actual GitHub owner is verified. Does not publish."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--owner',required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?',a.owner):
    p.error('invalid GitHub username')
a.output.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[1]
for name in ('server','glama'):
    data=json.loads((root/'release'/f'{name}.template.json').read_text().replace('__GITHUB_OWNER__',a.owner))
    (a.output/f'{name}.json').write_text(json.dumps(data,indent=2)+'\n')
(a.output/'ownership-marker.txt').write_text(f'<!-- mcp-name: io.github.{a.owner}/resultgate -->\n')
print('Metadata generated locally; namespace ownership and package publication still require verification.')
