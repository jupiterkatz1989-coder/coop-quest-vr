// Recuperación de la fuente embebida en el último artefacto Vite validado.
import fs from 'node:fs'
import path from 'node:path'
const root=path.resolve(import.meta.dirname,'..')
const asset=fs.readdirSync(path.join(root,'dist/assets')).find(x=>x.endsWith('.js'))
const source=fs.readFileSync(path.join(root,'dist/assets',asset),'utf8')
const marker='{schema_version:'
const start=source.indexOf(marker)
if(start<0)throw new Error('Dataset no encontrado')
let depth=0,quote='',escaped=false,end=-1
for(let i=start;i<source.length;i++){
  const c=source[i]
  if(quote){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c===quote)quote='';continue}
  if(c==='"'||c==="'"||c==='`'){quote=c;continue}
  if(c==='{')depth++
  if(c==='}'&&--depth===0){end=i+1;break}
}
if(end<0)throw new Error('Objeto incompleto')
const data=Function(`"use strict"; return (${source.slice(start,end)})`)()
if(data.total!==147||data.juegos.length!==147)throw new Error('El artefacto no contiene 147 juegos')
for(const dest of ['src/data/games.json','../../tasks/vr_coop_site/vr_coop_games.json']){
  const file=path.resolve(root,dest),tmp=file+'.recovered'
  fs.writeFileSync(tmp,JSON.stringify(data,null,2)+'\n',{encoding:'utf8',mode:0o600});fs.renameSync(tmp,file)
}
console.log(JSON.stringify({recovered:data.juegos.length}))
