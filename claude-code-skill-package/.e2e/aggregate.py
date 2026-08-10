#!/usr/bin/env python3
"""Aggregate all E2E discovery candidates (DeepXiv + WebFetch-on-arXiv) into a deduped list."""
import json
import glob
import os

allhits = {}  # keyed by arxiv_id

# 1. DeepXiv candidates from saved search files
for f in sorted(glob.glob('.e2e/searches/*.json')):
    try:
        d = json.load(open(f, encoding='utf-8'))
        if 'result' in d and 'hits' in d['result']:
            for h in d['result']['hits']:
                aid = h.get('arxiv_id')
                if aid and aid not in allhits:
                    h['_source'] = 'deepxiv'
                    allhits[aid] = h
    except Exception:
        pass

# 2. Gold smoke broad DeepXiv search
gold = r'C:\Users\wushuhong\.claude\projects\c--Users-wushuhong-Desktop-my-search-harness\a1e180ff-cc89-45cb-88ce-b0813f9ef8f6\tool-results\bbmzujm68.txt'
try:
    raw = open(gold, encoding='utf-8').read()
    js = raw[raw.index('{'):]
    d = json.loads(js)
    for h in d['result']['hits']:
        aid = h.get('arxiv_id')
        if aid and aid not in allhits:
            h['_source'] = 'deepxiv'
            allhits[aid] = h
except Exception as e:
    print('gold parse err:', e)

deepxiv_ids = set(allhits.keys())
print(f'Total unique DeepXiv candidates: {len(allhits)}')

# Save with explicit utf-8
with open('.e2e/candidates_deepxiv.json', 'w', encoding='utf-8') as f:
    json.dump(list(allhits.values()), f, ensure_ascii=False, indent=1)

# Print summary
from collections import Counter
years = Counter(h.get('publication_year', '?') for h in allhits.values())
print('DeepXiv by year:', dict(sorted(years.items(), key=lambda x: str(x[0]))))
print(f'DeepXiv unique arxiv_ids: {len(deepxiv_ids)}')
