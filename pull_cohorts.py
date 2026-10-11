#!/usr/bin/env python3
"""C-NEW-87 (run-215): arXiv version-drift dataset.
Cohorts: 4 categories x 4 submission windows (2019-10, 2021-10, 2023-10, 2025-10),
100 papers per (category, window). Per paper: v1 + latest title/abstract,
v1->latest divergence, v2 existence + lag (days), casing-only vs substantive split.
arXiv API courtesy: >=3s between calls. Free, no key."""
import urllib.request, urllib.parse, re, time, json, os, sys

CATS = ['cs.CL', 'cs.AI', 'cs.LG', 'math.CO']
WINDOWS = [('2019-10', '201910010000', '201911010000'),
           ('2021-10', '202110010000', '202111010000'),
           ('2023-10', '202310010000', '202311010000'),
           ('2025-10', '202510010000', '202511010000')]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(OUT, exist_ok=True)

def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'pennyforge-research/0.1 (dataset: arxiv version drift; contact: penny.forge.99@gmail.com)'})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(5)

def norm(t):
    return re.sub(r'\s+', ' ', t or '').strip()

def parse_entries(xml):
    out = {}
    for e in re.findall(r'<entry>(.*?)</entry>', xml, re.S):
        m = re.search(r'<id>http://arxiv.org/abs/([^<]+)</id>', e)
        if not m: continue
        aid = m.group(1).split('v')[0]
        ver = int(m.group(1).split('v')[1]) if 'v' in m.group(1) else 1
        title = norm(re.search(r'<title>(.*?)</title>', e, re.S).group(1))
        summ = norm(re.search(r'<summary>(.*?)</summary>', e, re.S).group(1))
        pub = re.search(r'<published>([^<]+)</published>', e)
        upd = re.search(r'<updated>([^<]+)</updated>', e)
        out[(aid, ver)] = {'title': title, 'abstract': summ,
                           'published': pub.group(1) if pub else None,
                           'updated': upd.group(1) if upd else None}
    return out

def batch(versions):
    """versions: list of full versioned ids like 2310.20501v1. Returns {(aid,ver): entry}."""
    res = {}
    for i in range(0, len(versions), 100):
        u = 'http://export.arxiv.org/api/query?' + urllib.parse.urlencode({'id_list': ','.join(versions[i:i+100]), 'max_results': 100})
        res.update(parse_entries(get(u)))
        time.sleep(3.2)
    return res

rows = []
total_ids = 0
for window, lo, hi in WINDOWS:
    ids = []
    for cat in CATS:
        u = 'http://export.arxiv.org/api/query?' + urllib.parse.urlencode({
            'search_query': f'cat:{cat} AND submittedDate:[{lo} TO {hi}]',
            'sortBy': 'submittedDate', 'sortOrder': 'descending', 'max_results': 100})
        xml = get(u)
        got = re.findall(r'<id>http://arxiv.org/abs/([^<]+)</id>', xml)[1:]
        ids += [(g.split('v')[0], cat) for g in got]
        time.sleep(3.2)
    ids = list({a: c for a, c in ids}.items())  # dedupe by base id
    total_ids += len(ids)
    print(f'{window}: {len(ids)} papers', flush=True)
    bases = [a for a, _ in ids]
    cats = {a: c for a, c in ids}
    latest = batch(bases)                       # no version suffix = latest
    v1 = batch([b + 'v1' for b in bases])
    v2 = batch([b + 'v2' for b in bases])       # may 404 -> entry absent
    for b in bases:
        l = latest.get((b, None)) or next((v for (a, ver), v in latest.items() if a == b), None)
        first = v1.get((b, 1))
        second = next((v for (a, ver), v in v2.items() if a == b and ver == 2), None)
        if not l or not first: continue
        t_same = l['title'] == first['title']
        a_same = l['abstract'] == first['abstract']
        # casing/punct-only title change?
        def squash(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())
        t_cosmetic = (not t_same) and squash(l['title']) == squash(first['title'])
        lag_days = None
        if second and second.get('published'):
            try:
                import datetime
                d1 = datetime.datetime.fromisoformat(first['published'].replace('Z', '+00:00'))
                d2 = datetime.datetime.fromisoformat(second['updated'].replace('Z', '+00:00'))
                lag_days = round((d2 - d1).total_seconds() / 86400, 1)
            except Exception:
                lag_days = None
        rows.append({'id': b, 'category': cats[b], 'window': window,
                     'v': max(ver for (a, ver), _ in latest.items() if a == b) if any(a == b for (a, ver) in latest) else 1,
                     'title_changed': not t_same, 'abstract_changed': not a_same,
                     'title_cosmetic_only': t_cosmetic, 'n_versions': max([ver for (a, ver) in latest if a == b] or [1]) if any(a == b for (a, ver) in latest) else 1,
                     'v2_lag_days': lag_days,
                     'v1_title': first['title'][:180], 'latest_title': l['title'][:180]})
    json.dump(rows, open(os.path.join(OUT, 'drift-rows.json'), 'w'), indent=1)
    print(f'  total rows so far: {len(rows)}', flush=True)
json.dump(rows, open(os.path.join(OUT, 'drift-rows.json'), 'w'), indent=1)
print(f'DONE: {len(rows)} rows from {total_ids} ids', flush=True)
