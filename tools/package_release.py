#!/usr/bin/env python3
import hashlib,json,tarfile,tempfile,os
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables';VERSION='2.0.0';PACKAGE=OUT/f'coop-quest-vr-{VERSION}.tar.gz'
INCLUDE=['dist','src','public','tools','server.py','README.md','ATTRIBUTIONS.md','package.json','pnpm-lock.yaml','vite.config.ts','tsconfig.json','tsconfig.app.json','tsconfig.node.json','.github','data/steam_refresh_report.json','data/steam_changes.json']

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def ignore(info):
 parts=Path(info.name).parts
 return None if not any(x in {'__pycache__','steam_cache','node_modules'} or x.endswith('.pyc') for x in parts) else None

OUT.mkdir(parents=True,exist_ok=True)
fd,tmp=tempfile.mkstemp(prefix=f'.{PACKAGE.name}.',suffix='.part',dir=OUT);os.close(fd)
with tarfile.open(tmp,'w:gz') as tar:
 for rel in INCLUDE:
  p=ROOT/rel
  if p.exists():tar.add(p,arcname=Path('coop-quest-vr')/rel,recursive=True,filter=lambda i: None if any(x in {'__pycache__','steam_cache','node_modules'} or x.endswith('.pyc') for x in Path(i.name).parts) else i)
os.replace(tmp,PACKAGE)
report=json.loads((ROOT/'data/cover_report.json').read_text())['summary'];catalog=json.loads((ROOT/'src/data/games.json').read_text())
manifest={'schema_version':2,'app':'coop-quest-vr','version':VERSION,'created_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'public_path':'/coop-quest-vr/','source':'incluida en el paquete','artifact':PACKAGE.name,'artifact_sha256':sha(PACKAGE),'dataset_games':catalog['total'],'covers':report,'freshness':'Steam España con fecha por ficha; Meta captura 06-06-2026','restore':['extraer el paquete','npm install','npm run build','python3 server.py','verificar /health y la URL'],'rollback':'restaurar el artefacto de la versión anterior','migration':'cualquier servidor HTTP o GitHub Pages; mantener base /coop-quest-vr/'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
