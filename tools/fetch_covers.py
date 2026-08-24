#!/usr/bin/env python3
"""Cachea portadas oficiales de Steam y las referenciadas por el snapshot VRDB.

Es reejecutable: valida ficheros existentes, solo descarga los que faltan y
publica el manifiesto de forma atómica. No asigna nunca una imagen por título.
"""
from __future__ import annotations
import argparse, json, os, re, tempfile, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'src/data/games.json'
VRDB=Path(os.environ['COOPQUEST_VRDB_CACHE']) if os.environ.get('COOPQUEST_VRDB_CACHE') else None
COVERS=ROOT/'public/covers'; DATA=ROOT/'src/data'
UA='CoopQuestVR/1.0 (personal local catalog)'

def valid(path:Path)->bool:
    if not path.is_file() or path.stat().st_size<1500:return False
    head=path.read_bytes()[:16]
    return head.startswith((b'\xff\xd8\xff',b'\x89PNG',b'RIFF'))
def fetch(url:str,path:Path)->bool:
    if valid(path):return True
    try:
        req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'image/avif,image/webp,image/*'})
        with urllib.request.urlopen(req,timeout=25) as r:data=r.read(12_000_000)
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix=f'.{path.name}.',suffix='.part',dir=path.parent)
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        candidate=Path(tmp)
        if not valid(candidate):candidate.unlink(missing_ok=True);return False
        os.replace(candidate,path);return True
    except Exception:return False
def atomic_json(path:Path,data:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=f'.{path.name}.',suffix='.part',dir=path.parent)
    with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def meta_image(appid:str)->str|None:
    if VRDB is None:return None
    p=VRDB/f'game_{appid}.html'
    if not p.exists():return None
    text=p.read_text(encoding='utf-8',errors='ignore')
    m=re.search(r'<meta\s+(?:property|name)="og:image"\s+content="([^"]+)"',text,re.I)
    return m.group(1).replace('&amp;','&') if m else None

def run(allow_network:bool=True)->dict:
    games=json.loads(SOURCE.read_text(encoding='utf-8'))['juegos'];manifest={};details={}
    for g in games:
        gid=g['id'];choices=[];record={'quest':False,'steam_header':False,'steam_library':False}
        for p in g['plataformas']:
            qm=re.search(r'/experiences/(?:[^/]+/)?(\d+)',p['url'])
            if qm:
                url=meta_image(qm.group(1));dest=COVERS/f'{gid}-quest.webp'
                ok=valid(dest) or bool(allow_network and url and fetch(url,dest));record['quest']|=ok
                if ok:choices.append(dest)
            sm=re.search(r'/app/(\d+)',p['url'])
            if sm:
                appid=sm.group(1);header=COVERS/f'{gid}-steam-header.jpg';library=COVERS/f'{gid}-steam-library.jpg'
                hok=valid(header) or bool(allow_network and fetch(f'https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg',header))
                lok=valid(library) or bool(allow_network and fetch(f'https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg',library))
                if not lok:lok=bool(allow_network and fetch(f'https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg',library))
                # Las fichas recientes no publican la ruta clasica; el snapshot ya guarda la URL con hash.
                if not hok:
                    declared=g.get('portada_url') or ''
                    if f'/apps/{appid}/' in declared:hok=bool(allow_network and fetch(declared,header))
                record['steam_header']|=hok;record['steam_library']|=lok
                if lok:choices.append(library)
                elif hok:choices.append(header)
        if choices:
            # Prefer Quest landscape art for native titles; otherwise library capsule.
            chosen=next((p for p in choices if p.name.endswith('-quest.webp')),choices[0])
            manifest[gid]=f'/coop-quest-vr/covers/{chosen.name}'
        details[gid]=record
    summary={'total':len(games),'real':len(manifest),'placeholder':len(games)-len(manifest),'quest_files':sum(x['quest'] for x in details.values()),'steam_headers':sum(x['steam_header'] for x in details.values()),'steam_libraries':sum(x['steam_library'] for x in details.values())}
    atomic_json(DATA/'covers.json',manifest);atomic_json(ROOT/'data/cover_report.json',{'summary':summary,'games':details})
    print(json.dumps(summary,ensure_ascii=False));return summary
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--offline',action='store_true');args=ap.parse_args();run(not args.offline)
