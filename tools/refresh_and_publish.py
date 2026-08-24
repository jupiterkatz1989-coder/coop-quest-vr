#!/usr/bin/env python3
"""Refresca Steam, conserva Meta histórico y publica dist atómicamente."""
from __future__ import annotations
import fcntl,json,os,shutil,subprocess,tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parents[1];LOCK=ROOT/'data/refresh.lock';STATE=ROOT/'data/refresh_state.json'
def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=f'.{path.name}.',suffix='.part',dir=path.parent)
    with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def main():
    LOCK.parent.mkdir(parents=True,exist_ok=True)
    with LOCK.open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 3
        started=datetime.now().astimezone().isoformat(timespec='seconds');state={'status':'running','phase':'Consultando Steam España','started_at':started,'prices_updated':False}
        atomic_json(STATE,state)
        source=ROOT/'src/data/games.json';backup=ROOT/'data/games.before-refresh.json';shutil.copy2(source,backup)
        try:
            subprocess.run(['/usr/bin/python3',str(ROOT/'tools/steam_catalog.py')],cwd=ROOT,check=True)
            state['prices_updated']=True
            state['phase']='Refrescando portadas oficiales';atomic_json(STATE,state)
            subprocess.run(['/usr/bin/python3',str(ROOT/'tools/fetch_covers.py')],cwd=ROOT,check=True)
            subprocess.run(['/usr/bin/python3',str(ROOT/'tools/verify_catalog.py')],cwd=ROOT,check=True)
            state['phase']='Compilando y publicando';atomic_json(STATE,state)
            staging=ROOT/'dist.next';shutil.rmtree(staging,ignore_errors=True)
            subprocess.run(['/usr/bin/npm','run','build','--','--outDir','dist.next'],cwd=ROOT,check=True)
            old=ROOT/'last_valid_dist';shutil.rmtree(old,ignore_errors=True)
            if (ROOT/'dist').exists():os.replace(ROOT/'dist',old)
            os.replace(staging,ROOT/'dist')
            catalog=json.loads(source.read_text());report=json.loads((ROOT/'data/cover_report.json').read_text())['summary'];state.update(status='success',phase='Publicación validada',finished_at=datetime.now().astimezone().isoformat(timespec='seconds'),detail=f"{catalog['total']} juegos; {report['real']} portadas locales más portadas oficiales Steam. Steam actualizado; Meta conserva la captura del 06-06-2026.")
            atomic_json(STATE,state);print(state['detail']);return 0
        except Exception as e:
            if backup.exists():shutil.copy2(backup,source)
            state.update(status='failed',phase='Fallida; última publicación conservada',finished_at=datetime.now().astimezone().isoformat(timespec='seconds'),detail=str(e)[:300]);atomic_json(STATE,state);raise
if __name__=='__main__':raise SystemExit(main())
