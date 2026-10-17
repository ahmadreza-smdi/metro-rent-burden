#!/usr/bin/env python3
"""Download official public ACS table-based files; never request/register API keys."""
import argparse,datetime,hashlib,json,urllib.request
from pathlib import Path

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--year',type=int,default=2024);a=parser.parse_args()
 root=Path(__file__).resolve().parent;raw=root/'raw';raw.mkdir(exist_ok=True)
 base=f'https://www2.census.gov/programs-surveys/acs/summary_file/{a.year}/table-based-SF'
 sources=[(f'{a.year}-b25070.dat',base+f'/data/1YRData/acsdt1y{a.year}-b25070.dat'),(f'{a.year}-geographies.txt',base+f'/documentation/Geos{a.year}1YR.txt')]
 receipts=[]
 for name,url in sources:
  target=raw/name
  if target.exists():data=target.read_bytes();state='existing snapshot retained'
  else:
   with urllib.request.urlopen(url,timeout=40) as response:data=response.read()
   if not data.startswith((b'GEO_ID|',b'FILEID|')):raise ValueError('Unexpected public table response; stop, no retry/key signup')
   target.write_bytes(data);state='downloaded'
  receipts.append({'file':'raw/'+name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'state':state})
 receipt={'accessed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'survey_year':a.year,'product':'ACS1-year detailed tables','table':'B25070','access':'Official public table-based summary file; no key or account','sources':receipts}
 target=root/f'source-{a.year}.json'
 if not target.exists():target.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
