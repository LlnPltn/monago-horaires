"""Horaires Trenitalia côté italien (Taggia → Vintimille), au format compact de MonaGo : {a, d0, n, s, t, maj}.
Source : GTFS Trenitalia de la Regione Liguria (CC BY 4.0). Usage : python3 italie.py <gtfs.zip> <sortie.json> [AAAAMMJJ, par défaut le début de validité]
Même codage que Horaires.java : par gare, arrivée*8 + attente (0-7 min) ; -1 = pas d'arrêt ; -2-code = descente seulement."""
import csv, io, json, sys, zipfile, datetime
GARES = ['830004501', '830004502', '830004503', '830004505', '830004506']   # Vintimille, Vallecrosia, Bordighera, Sanremo, Taggia-Arma
def lire(z, nom):
    return csv.DictReader(io.TextIOWrapper(z.open(nom), 'utf-8-sig'))
def mn(h):
    a = h.strip().split(':'); return int(a[0]) * 60 + int(a[1])
def main(src, dst, d0=None):
    z = zipfile.ZipFile(src); idx = {g: i for i, g in enumerate(GARES)}
    if not d0:   # début de validité du fichier : le résultat ne change que quand la grille change
        try: d0 = next(lire(z, 'feed_info.txt'))['feed_start_date'].strip()
        except Exception: d0 = datetime.date.today().strftime('%Y%m%d')
    pas = {}
    for r in lire(z, 'stop_times.txt'):
        g = idx.get(r['stop_id'])
        if g is None: continue
        pas.setdefault(r['trip_id'], []).append((int(r['stop_sequence']), g, mn(r['arrival_time']), mn(r['departure_time']), 0 if r.get('pickup_type') == '1' else 1))
    garder = {t for t, l in pas.items() if any(x[1] == 0 for x in l) and len(l) >= 2}
    serv = {r['trip_id']: r['service_id'] for r in lire(z, 'trips.txt') if r['trip_id'] in garder}
    t0 = datetime.date(int(d0[:4]), int(d0[4:6]), int(d0[6:])); jours = {}; der = 0
    for r in lire(z, 'calendar_dates.txt'):
        if r['exception_type'].strip() != '1' or r['service_id'] not in set(serv.values()): continue
        d = r['date'].strip(); i = (datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])) - t0).days
        if 0 <= i < 400: jours.setdefault(r['service_id'], []).append(i); der = max(der, i)
    n = der + 1
    if len(garder) < 50 or n < 14: raise SystemExit('données incomplètes')
    bm, num, t = [], {}, []
    for trip in sorted(garder):
        bits = bytearray((n + 7) // 8)
        for i in jours.get(serv.get(trip), []): bits[i >> 3] |= 1 << (i & 7)
        h = bits.hex(); si = num.setdefault(h, len(bm))
        if si == len(bm): bm.append(h)
        ligne = [-1] * len(GARES)
        for _, g, a, d, m in pas[trip]:
            k = a * 8 + min(max(d - a, 0), 7); ligne[g] = k if m else -2 - k
        t.append([si] + ligne)
    json.dump({'a': GARES, 'd0': d0, 'n': n, 's': bm, 't': t, 'maj': d0, 'source': 'Trenitalia, Regione Liguria (CC BY 4.0)'}, open(dst, 'w'), separators=(',', ':'))
    print(dst, len(t), 'trains', n, 'jours')
if __name__ == '__main__':
    main(*sys.argv[1:])
