#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'src/data/games.json').read_text(encoding='utf-8'));games=data['juegos'];covers=json.loads((ROOT/'src/data/covers.json').read_text(encoding='utf-8'))
errors=[]
if len(games)<147 or data.get('total')!=len(games):errors.append(f"Catálogo inválido: total declarado {data.get('total')} y {len(games)} registros")
if len({g['id'] for g in games})!=len(games):errors.append('Hay ID duplicados')
appids=[g['steam_appid'] for g in games if g.get('steam_appid')]
if len(set(appids))!=len(appids):errors.append('Hay appid de Steam duplicados')
for g in games:
    m=g['coop']['max_jugadores'];seg=g['coop']['segmento']
    if m is None and seg!='desconocido':errors.append(f"{g['id']}: máximo ausente con segmento {seg}")
    if g['precio_actual']['importe'] is not None and g['precio_actual']['moneda'] not in {'USD','EUR'}:errors.append(f"{g['id']}: moneda no esperada")
    if g.get('steam_appid') and g.get('steam_vr_modo') not in {'obligatorio','opcional'}:errors.append(f"{g['id']}: soporte VR Steam sin clasificar")
    if g.get('tipo_plataforma') not in {'standalone','pcvr','ambos','desconocido'}:errors.append(f"{g['id']}: plataforma inválida")
    if g.get('vr_obligatorio') not in {True,False,'desconocido'}:errors.append(f"{g['id']}: VR obligatorio inválido")
    if g.get('coop_online') not in {True,False,'desconocido'}:errors.append(f"{g['id']}: coop online inválido")
    if g.get('coop_local') not in {True,False,'desconocido'}:errors.append(f"{g['id']}: coop local inválido")
    rel=covers.get(g['id'])
    if rel and not (ROOT/'public/covers'/Path(rel).name).is_file():errors.append(f"{g['id']}: portada declarada inexistente")
if sum(g['coop']['max_jugadores'] is None for g in games)<120:errors.append('Se perdieron máximos desconocidos: deben conservarse al menos los 120 originales')
if errors:print('\n'.join(errors));sys.exit(1)
print(json.dumps({'games':len(games),'real_covers':sum(bool(covers.get(g['id']) or g.get('portada_url')) for g in games),'placeholders':sum(not (covers.get(g['id']) or g.get('portada_url')) for g in games),'unknown_max':sum(g['coop']['max_jugadores'] is None for g in games)},ensure_ascii=False))
