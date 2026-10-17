#!/usr/bin/env python3
"""Standalone scientific chart from rebuilt summary; no browser/network needed."""
import argparse,json,textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 p=argparse.ArgumentParser();p.add_argument('--year',type=int,default=2024);args=p.parse_args()
 root=Path(__file__).resolve().parent;d=json.loads((root/f'summary-{args.year}.json').read_text());rows=d['chart_rows']
 fig,ax=plt.subplots(figsize=(14,10),dpi=140);fig.patch.set_facecolor('#f5faf8');ax.set_facecolor('#f5faf8')
 y=list(range(len(rows)));a=[r['rent_30plus_pct'] for r in rows];b=[r['rent_50plus_pct'] for r in rows]
 ax.barh([i-.16 for i in y],a,height=.27,color='#8fcdbb',label='At least 30% of household income')
 ax.barh([i+.16 for i in y],b,height=.27,color='#365f79',label='At least 50% of household income')
 for i,(v,w) in enumerate(zip(a,b)):
  ax.text(v+.7,i-.16,f'{v:.1f}%',va='center',fontsize=10,color='#203c42')
  ax.text(w+.7,i+.16,f'{w:.1f}%',va='center',fontsize=10,color='#203c42')
 labels=['\n'.join(textwrap.wrap(r['metro_name'].removesuffix(' Metro Area'),width=35)) for r in rows]
 ax.set_yticks(y,labels,fontsize=10);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xticks(range(0,101,20));ax.set_xlabel('Share of renter-occupied units with a computable rent-to-income ratio (%)',fontsize=10,labelpad=10)
 ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0,pad=10);ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
 fig.suptitle(f'How much income goes to gross rent? | ACS {args.year}',x=.07,y=.96,ha='left',fontsize=21,color='#203c42',weight='bold')
 fig.text(.07,.914,'Ten largest computable renter-unit denominators, shown alphabetically. Threshold groups overlap.',fontsize=11,color='#365f79')
 ax.legend(loc='lower left',bbox_to_anchor=(-.53,-.16),ncol=2,frameon=False,fontsize=10)
 fig.text(.07,.075,'Source: U.S. Census Bureau, ACS 1-year B25070. Gross rent includes renter-paid utilities and fuels.\nNot-computed units excluded from both denominators. Point estimates; derived margins of error not calculated.\nThis selection is not a statistical ranking or an investment recommendation.',fontsize=10,color='#365f79',linespacing=1.5)
 fig.text(.07,.025,'Ahmadreza Samadi | a-samadi.com | Reproducible source snapshot: 17 October 2026',fontsize=10,color='#203c42')
 fig.subplots_adjust(left=.38,right=.95,top=.87,bottom=.22)
 for ext in ['png','svg']:fig.savefig(root/f'rent-burden-{args.year}.{ext}',facecolor=fig.get_facecolor())
 alt=f'Grouped horizontal bar chart of ACS {args.year} point estimates for10 metropolitan areas selected by the largest computable renter-unit denominators, displayed alphabetically. '
 alt+='; '.join(f"{r['metro_name']}: {r['rent_30plus_pct']:.1f}% at least 30%, {r['rent_50plus_pct']:.1f}% at least 50%" for r in rows)
 alt+='. Both shares exclude not-computed units; threshold groups overlap. Derived margins of error not calculated; no statistical ranking.'
 (root/f'chart-alt-{args.year}.txt').write_text(alt+'\n');print('ChartPNG/SVG and complete alt text saved')
if __name__=='__main__':main()
