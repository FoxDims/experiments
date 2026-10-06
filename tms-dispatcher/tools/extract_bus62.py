"""Извлекает трассы и остановки маршрутов из HAR-записей сайта bus62.ru.

python3 tools/extract_bus62.py data/routes.json file1.har [file2.har ...]

Берёт:
  getRouteNodes      — трасса направления маршрута (rid);
  getVehiclesMarkers — соответствие rid → номер маршрута;
  getVehicleForecasts — остановки (название, координаты) по ходу автобуса.
Госномера и позиции реальных автобусов не сохраняются.
"""
import json, math, re, sys, collections

def dist(a, b):
    return math.hypot((a[0]-b[0])*111320, (a[1]-b[1])*111320*math.cos(math.radians(54.63)))

def seg_proj(p, a, b):
    kx = math.cos(math.radians(54.63))
    ax, ay, bx, by, px, py = a[1]*kx, a[0], b[1]*kx, b[0], p[1]*kx, p[0]
    vx, vy = bx-ax, by-ay; l2 = vx*vx+vy*vy or 1e-18
    t = max(0, min(1, ((px-ax)*vx+(py-ay)*vy)/l2))
    q = (ay+vy*t, (ax+vx*t)/kx)
    return t, dist(p, q)

def project(path, cum, p):
    best = (1e18, 0)
    for i in range(len(path)-1):
        t, d = seg_proj(p, path[i], path[i+1])
        if d < best[0]: best = (d, cum[i] + (cum[i+1]-cum[i])*t)
    return best

def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dmax, idx = 0, 0
    for i in range(1, len(pts)-1):
        d = seg_proj(pts[i], a, b)[1]
        if d > dmax: dmax, idx = d, i
    if dmax <= eps: return [a, b]
    return rdp(pts[:idx+1], eps)[:-1] + rdp(pts[idx:], eps)

out_path, hars = sys.argv[1], sys.argv[2:]
rid2num, vid2rid, nodes, stops = {}, {}, {}, collections.defaultdict(dict)
entries = []
for f in hars:
    entries += json.load(open(f, encoding='utf-8'))['log']['entries']
for e in entries:
    u = e['request']['url']; t = e['response'].get('content', {}).get('text') or ''
    if 'getVehiclesMarkers' in u and t.strip().startswith('{'):
        for a in json.loads(t).get('anims', []):
            rid2num[a['rid']] = a['rnum']; vid2rid[a['id']] = a['rid']
for e in entries:
    u = e['request']['url']; t = e['response'].get('content', {}).get('text') or ''
    if 'getRouteNodes' in u and t.strip().startswith('['):
        rid = int(re.search(r'rid=(\d+)', u).group(1))
        nodes[rid] = [(n['lat']/1e6, n['lng']/1e6) for n in json.loads(t)]
    if 'getVehicleForecasts' in u and t.strip().startswith('['):
        rid = vid2rid.get(re.search(r'vid=(\d+)', u).group(1))
        for s in json.loads(t):
            stops[rid][s['stid']] = (s['stname'].strip(), (int(s['lat0'])/1e6, int(s['lng0'])/1e6))

by_num = collections.defaultdict(list)
for rid in nodes:
    if rid in rid2num: by_num[rid2num[rid]].append(rid)

routes = []
for num, rids in sorted(by_num.items(), key=lambda x: int(re.sub(r'\D', '', x[0]) or 0)):
    rid = max(rids, key=lambda r: len(nodes[r]))
    path = nodes[rid]
    cum = [0]
    for i in range(1, len(path)): cum.append(cum[-1] + dist(path[i-1], path[i]))
    cand = {}
    for r, st in stops.items():
        if rid2num.get(r) != num: continue
        cand.update(st)
    found = []
    for sid, (name, ll) in cand.items():
        off, d = project(path, cum, ll)
        if off < 60: found.append((d, name, ll))
    found.sort()
    clean = []
    for d, name, ll in found:
        if clean and (clean[-1][1] == name or d - clean[-1][0] < 120): continue
        clean.append((d, name, ll))
    simp = rdp(path, 4)
    routes.append({
        'id': num, 'rid': rid,
        'path': [[round(a, 6), round(b, 6)] for a, b in simp],
        'stops': [{'name': n, 'll': [round(a, 6), round(b, 6)]} for _, n, (a, b) in clean],
        'lengthM': round(cum[-1])
    })
    print(f"М{num}: rid {rid}, {len(path)}→{len(simp)} точек, {cum[-1]/1000:.1f} км, остановок {len(clean)}"
          + (f" ({clean[0][1]} … {clean[-1][1]})" if clean else ''))

json.dump({'source': 'bus62.ru', 'routes': routes}, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
