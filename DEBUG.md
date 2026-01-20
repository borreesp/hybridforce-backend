## Diagnóstico Atleta (PRs y Habilidades)

- Flujo real: `POST /athlete/workouts/{id}/result` guarda resultado y ejecución; luego el frontend llama `POST /athlete/workouts/{id}/apply-impact`.
- Problema encontrado:
  - No se creaba ningún PR: el endpoint de resultados nunca insertaba en `user_pr`, ni señalaba `new_pr=True` a misiones.
  - Las habilidades sólo se actualizaban si `athlete_impact` traía claves `skill_*`, pero el análisis base genera únicamente capacidades/fatiga. Resultado: cero filas nuevas en `user_skills`.
- Evidencia rápida:
  - Búsqueda de lógica PR/skill devolvía sólo lecturas (`AthleteService.profile`) y seeds; no había escrituras.
  - Aplicar impacto con WODs ya ejecutados dejaba `skills` y `prs` vacíos en `/athlete/profile` pese a ejecuciones creadas.

## Cambios aplicados
- `POST /athlete/workouts/{id}/result`:
  - Detecta bloques con un único movimiento y registra PR (`user_pr`) si el tiempo mejora el existente (o no hay previo). Si el WOD es de un solo bloque/movimiento y se envía tiempo total, también genera candidato.
  - Propaga `new_pr` a `MissionService.update_progress_for_workout`.
  - Log: `[submit_result][pr] user=<id> workout=<id> new_prs=<n>`.
- `POST /athlete/workouts/{id}/apply-impact`:
  - Log inicial con claves de impacto.
  - Fallback de skills: si el análisis no trae `skill_*`, se infiere un delta mínimo (+2) para movimientos Row/Wall Ball/KB Lunge/BBJO presentes en el WOD y se inserta en `user_skills`.
  - Clamp de skill_score a [0, 100].

## Cómo verificar manualmente
1) Registrar un tiempo en `/workouts/{id}/time` (total o por bloques).  
2) Se dispara `applyImpact` automáticamente: revisar logs en backend (`athlete.apply-impact` y `[submit_result][pr]`).  
3) Abrir `/athlete`: el panel "PRs y tests" debe mostrar el movimiento del bloque (p.ej. Row) con la fecha; "Habilidades" debe listar los movimientos presentes en el WOD con su progreso actualizado.

## Riesgos observados
- PRs se basan en bloques de un solo movimiento; WODs con bloques mixtos no generan PR (intencional para evitar falsos positivos).
- Incremento de skill es heurístico (delta fijo) cuando el análisis no lo provee; si en el futuro el análisis devuelve `skill_*`, tendrá prioridad.
