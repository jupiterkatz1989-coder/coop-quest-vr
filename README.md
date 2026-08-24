# Coop Quest VR

Aplicación React/Vite/TypeScript para explorar y comparar el catálogo cooperativo VR de Steam y Meta Quest.

## Datos y honestidad

Steam se descubre mediante la búsqueda oficial filtrada por soporte VR y solo se acepta cuando `appdetails` declara una categoría oficial Co-op (9, 38 o 39) y soporte VR obligatorio/opcional (54/53). Los precios Steam se consultan para España en EUR.

Meta Quest no ofrece una API pública equivalente: sus precios se identifican siempre como captura histórica del 06-06-2026. Los máximos de jugadores desconocidos siguen siendo desconocidos.

## Operación

- Compilar: `npm run build`
- Validar: `npm run verify:data`
- Refrescar Steam y publicar localmente de forma atómica: `npm run refresh`
- Servir: `python3 server.py` en `http://127.0.0.1:8800/coop-quest-vr/`

El refresco usa caché en disco, peticiones espaciadas, bloqueo no bloqueante y validación. Conserva `last_valid_dist` y el dataset anterior para rollback. Las portadas Steam usan su CDN oficial por AppID; si no existe una imagen válida, la interfaz muestra un marcador honesto.

## Publicación

El sitio está preparado para GitHub Pages bajo `/coop-quest-vr/`. GitHub Actions vuelve a descubrir y recotizar Steam cada lunes a las 05:17 UTC, registra altas, bajas, precios y fallos, compila y solo despliega si supera las puertas de integridad. No necesita secretos distintos del `GITHUB_TOKEN` automático con permisos de Pages y contenido.

## Restauración y migración

Instalar dependencias, ejecutar el refresco y servir `dist` con cualquier servidor HTTP bajo el prefijo `/coop-quest-vr/`. Para rollback local, sustituir `dist` por `last_valid_dist` y restaurar `data/games.before-refresh.json` como `src/data/games.json`.
