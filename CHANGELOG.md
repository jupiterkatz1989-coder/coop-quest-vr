# Changelog

## 2.1.0 — 2026-08-25

- Portadas recuperadas desde la ruta de assets con hash que Steam usa en las fichas recientes: 861 de 862 juegos con imagen real (antes 776).
- Orden por defecto «Recomendado» con nota ponderada por volumen de reseñas; «Nota» sigue disponible como opción explícita.
- El refresco semanal descarga las portadas de los juegos nuevos y reintegra antes de publicar; primera ejecución real verificada de extremo a extremo.

## 2.0.0 — 2026-08-24

- Descubrimiento reanudable de Steam VR cooperativo mediante las categorías oficiales Co-op, Online Co-op, Shared/Split Screen Co-op y LAN Co-op, caché y ritmo limitado.
- Precios Steam para España con rebaja, fecha y distinción entre fuente comprobada y recotización real; Meta queda marcada como captura histórica.
- Clasificación standalone / PCVR / ambos / desconocido, filtros de VR obligatorio, cooperativo online/local y filtros de calidad.
- Paginación progresiva de 36 tarjetas, carga diferida y portadas oficiales por AppID.
- Workflow semanal de GitHub Actions con puerta de integridad, informe de cambios y despliegue Pages.

## 1.0.0 — 2026-08-24

- Aplicación React/Vite/TypeScript con 147 juegos, galería, filtros, detalle, comparador y mejores opciones.
- Caché local determinista de portadas Steam/VRDB y marcador honesto por título.
- Aviso permanente de captura del 06-06-2026 en USD y tratamiento explícito de incertidumbres.
- Servicio local persistente, refresco manual con bloqueo y publicación atómica, inventario y copia exportable.
- Rollback: conservar `last_valid_dist` y las copias previas de los cuatro ficheros compartidos en `rollback/dashboard-before/`.
