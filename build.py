#!/usr/bin/env python3
"""Rebuild point-estimate rent-burden outputs from official ACS summary files."""
import argparse,csv,hashlib,json
from pathlib import Path

def verify_snapshot(root,year):
    """Reject a changed or incomplete saved snapshot before writing outputs."""
    receipt_path=root/f'source-{year}.json'
    if not receipt_path.is_file():raise ValueError('Missing source receipt: '+receipt_path.name)
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt.get('survey_year')!=year:raise ValueError('Source receipt year mismatch')
    expected={f'raw/{year}-b25070.dat',f'raw/{year}-geographies.txt'}
    sources=receipt.get('sources',[])
    if len(sources)!=2 or {s.get('file') for s in sources}!=expected:
        raise ValueError('Source receipt must identify both unique raw files')
    for source in sources:
        path=root/source['file']
        if not path.is_file():raise ValueError('Missing source snapshot: '+source['file'])
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=source.get('sha256'):
            raise ValueError('Source snapshot hash mismatch: '+source['file'])
        if len(data)!=source.get('bytes'):raise ValueError('Source snapshot byte-count mismatch: '+source['file'])

def integer(value):
    """Preserve unavailable/sentinel counts as unknown, never zero."""
    try:n=int(value)
    except (ValueError,TypeError):return None
    return n if n>=0 else None

def measures(row):
    values=[integer(row.get(f'B25070_E{i:03}')) for i in range(1,12)]
    if any(v is None for v in values):return {'status':'unavailable source estimate'}
    total,*bins=values
    if sum(bins)!=total:raise ValueError('Nonadditive B25070 categories: '+row.get('GEO_ID','fixture'))
    not_computed=values[10];denominator=total-not_computed
    count30=sum(values[6:10]);count50=values[9]
    if not (0<=count50<=count30<=denominator):raise ValueError('Invalid threshold nesting')
    return {'status':'ok' if denominator else 'zero computable denominator','renter_units_total':total,'not_computed_units':not_computed,'computable_units':denominator,'rent_30plus_units':count30,'rent_50plus_units':count50,'rent_30plus_pct':100*count30/denominator if denominator else None,'rent_50plus_pct':100*count50/denominator if denominator else None,'not_computed_pct_all_renters':100*not_computed/total if total else None}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--year',type=int,default=2024);args=parser.parse_args()
    root=Path(__file__).resolve().parent;year=args.year
    verify_snapshot(root,year)
    with (root/f'raw/{year}-geographies.txt').open(newline='',encoding='utf-8-sig') as f:geos={r['GEO_ID']:r for r in csv.DictReader(f,delimiter='|')}
    with (root/f'raw/{year}-b25070.dat').open(newline='',encoding='utf-8-sig') as f:raw=list(csv.DictReader(f,delimiter='|'))
    selected=[];excluded=[];national=None
    for row in raw:
        geo=geos[row['GEO_ID']]
        if row['GEO_ID']=='0100000US':national=measures(row)
        if geo['SUMLEVEL']!='310' or geo['COMPONENT']!='00':continue
        if not geo['NAME'].endswith(' Metro Area'):reason='Micropolitan area: outside metropolitan scope'
        elif ', PR Metro Area' in geo['NAME']:reason='Puerto Rico: outside50states/DC scope'
        else:reason=None
        if reason:excluded.append({'geo_id':row['GEO_ID'],'name':geo['NAME'],'reason':reason});continue
        m=measures(row)
        selected.append({'geo_id':row['GEO_ID'],'cbsa_code':geo['CBSA'],'metro_name':geo['NAME'],'survey_year':year,**m,**{k:v for k,v in row.items() if k!='GEO_ID'}})
    selected.sort(key=lambda r:r['metro_name'])
    assert len({r['cbsa_code'] for r in selected})==len(selected),'Duplicate CBSA codes'
    output=root/f'metro-rent-burden-{year}.csv'
    fields=list(selected[0])
    with output.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in selected:w.writerow({k:round(v,6) if isinstance(v,float) else v for k,v in row.items()})
    (root/f'excluded-cbsa-{year}.json').write_text(json.dumps(excluded,indent=2)+'\n',encoding='utf-8',newline='\n')
    summary={'survey_year':year,'metropolitan_areas':len(selected),'excluded_cbsa':len(excluded),'not_computed_total_selected':sum(r['not_computed_units'] for r in selected if 'not_computed_units' in r),'unavailable_rows':sum(r['status']!='ok' for r in selected),'national_50states_dc':national,'chart_selection':'Ten largest computable renter-unit denominators, displayed alphabetically. Not ranked by burden or statistical significance.','chart_rows':sorted(sorted([r for r in selected if r['status']=='ok'],key=lambda r:(-r['computable_units'],r['cbsa_code']))[:10],key=lambda r:r['metro_name']),'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/f'raw/{year}-b25070.dat',root/f'raw/{year}-geographies.txt']},'derived_margins_of_error':'Not calculated. All11source estimate/MOE pairs retained in CSV. No statistical ranking or significance inference.'}
    (root/f'summary-{year}.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['chart_rows','input_sha256']},indent=2))
if __name__=='__main__':main()
