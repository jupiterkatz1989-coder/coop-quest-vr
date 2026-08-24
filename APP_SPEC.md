# Coop Quest VR — ficha de aplicación

## Problema

El catálogo cooperativo de Meta Quest existe como datos y hojas incrustadas, pero no permite explorar visualmente, filtrar con precisión ni comparar juegos para decidir qué jugar.

## Usuario

- Uso personal y familiar.
- Frecuencia de uso: consulta recurrente, especialmente desde móvil.
- Contexto: elegir juegos cooperativos compatibles con Quest sin confundir datos verificados con campos desconocidos.

## Entradas

- Fuente inicial: snapshot local de 147 juegos; fuente operativa: `src/data/games.json`.
- Apoyo para portadas: caché local VRDB fechada y portadas oficiales Steam derivadas del AppID.
- Datos del usuario: búsqueda, filtros, orden, selección de 2 a 4 juegos para comparar.
- Datos que no debe tocar: Google Site, hoja maestra, datos profesionales, cuentas, credenciales y fuentes originales.

## Salidas

- Aplicación React + Vite + TypeScript con galería, filtros, ficha, comparador y mejores opciones.
- Portadas guardadas localmente y marcadores honestos cuando no haya portada real.
- Publicación local estable, sitio estático compartible en GitHub Pages y control de actualización en el Dashboard.
- Refresco semanal en GitHub Actions con validación previa y conservación de la última versión buena.
- Código: `projects/coop-quest-vr/`.
- Entregable: `projects/coop-quest-vr/deliverables/`.
- Copia exportable: `exports/apps/coop-quest-vr/`, fuera de la carpeta servida.

## Pantallas o vistas

1. Galería responsive con aviso permanente de procedencia: Steam actualizado para España y Meta como captura del 06-06-2026.
2. Filtros combinables visibles y contador, más ordenación.
3. Ficha completa con evidencia, confianza, fuentes, fechas e incertidumbres.
4. Comparador de 2 a 4 juegos con diferencias destacadas.
5. Mejores opciones con fórmula explícita y criterios combinables.

## Acciones permitidas

- Leer y transformar copias de la fuente canónica.
- Descargar y cachear portadas oficiales; validar antes de publicar de forma atómica.
- Escribir únicamente en el proyecto, sus estados de actualización, inventario y copia exportable.
- No modificar tiendas ni alterar el Google Site/hoja original.

## Integraciones

- Servicio HTTP local en `127.0.0.1` y puerto estable libre.
- Dashboard privado de Jupi: inventario, enlace, estado de copia y actualización manual permitida.
- Actualización manual: consulta Steam con caché y ritmo limitado, valida, refresca portadas y publica atómicamente.

## Criterios de aceptación

1. Conserva los 147 registros iniciales, incorpora todos los candidatos Steam que superan las categorías oficiales y mantiene desconocidos los máximos no verificados.
2. Los filtros combinan y actualizan contador; detalle, comparador y mejores opciones funcionan en escritorio y móvil.
3. Cada imagen corresponde al juego o se muestra un marcador generado; nunca se reutiliza una portada incorrecta.
4. Servidor y enlace del Dashboard responden; actualización usa bloqueo, validación y reemplazo atómico.
5. Existen capturas verificables de galería, filtros, ficha, comparador y móvil.

Si falta un dato, la interfaz muestra «Desconocido» o «Sin dato» y conserva la incertidumbre; no infiere valores.

## Riesgos y límites

- Steam depende de la disponibilidad de la tienda y su taxonomía oficial.
- Meta Quest conserva precios USD de la captura del 06-06-2026; Steam se consulta para España.
- Las portadas de Meta pueden no estar presentes en la caché local; el marcador es el fallback honesto.
- El informe distingue fuente comprobada de precio realmente recotizado.

## Estado y operación

- Estado real: producción local y preparada para publicación en GitHub Pages, con copia exportable y rollback.
- Última prueba: 24-08-2026, Chromium headless contra la URL del servicio persistente.
- Ruta estable: `http://127.0.0.1:8800/coop-quest-vr/`.
- Estrategia de actualización: descubrimiento y recotización Steam semanal, caché, validación, staging y publicación atómica; última versión válida intacta ante fallo.
- Migración alternativa: paquete estático `dist` servible por cualquier servidor HTTP, con fuente y manifiesto verificable.
- Fecha de última prueba: se completará al cierre.
