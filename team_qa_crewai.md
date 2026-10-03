# Team QA — Agentes para CrewAI + Ollama

Team de calidad con **4 agentes** y **21 tareas atómicas** en 6 fases. Un Líder de QA planifica con enfoque en riesgo y reparte el trabajo entre un QA Semi Senior, un QA Junior y un QA Automatización. El team participa en el refinamiento aportando un punto de vista distinto al de los demás, y después valida lo que entrega Desarrollo. Se conecta con el Team PO (refinamiento), con el Team Desarrollo (entregas y defectos) y, de forma informativa, con el Team Infraestructura, mediante un contrato de intercambio por archivos.

## 1. Decisiones de diseño

**¿Es ideal esta composición?** Para este sistema, sí. Los cuatro roles cubren lo esencial:

| Rol | Qué aporta |
|---|---|
| **Líder de QA** | Estrategia, riesgo, asignación, control de calidad de los reportes y dictamen |
| **QA Semi Senior** | Pensamiento adversarial, casos complejos, análisis de resultados y defectos |
| **QA Junior** | Verificación metódica de testabilidad, casos básicos y registro fiel de resultados |
| **QA Automatización** | Estrategia de automatización, scripts de API y UI, regresión |

Brechas conocidas: pruebas de rendimiento y de seguridad a fondo, y accesibilidad. No las incluyo como agentes todavía: el Semi Senior diseña casos de requisitos no funcionales con los valores medibles que define el Arquitecto, y las pruebas profundas necesitan herramientas y entornos que aún no existen en este proyecto. Cuando el producto lo exija, el rol que encaja es un QA No Funcional (rendimiento y seguridad).

**Aporte distinto en el refinamiento.** QA aporta lo que los demás teams no ven: casos no cubiertos, riesgos y ambigüedades. Para conseguirlo, las tareas 1, 2 y 3 son **independientes entre sí** (sin contexto compartido), para que cada agente analice desde su ángulo sin anclarse en los otros, y el Líder consolida. Los aportes son hipótesis priorizadas por riesgo, no requisitos: el PO decide.

**Delegación del Líder.** Igual que en Desarrollo, es explícita y por escrito, no la delegación dinámica de CrewAI:

1. El Líder produce un **plan de pruebas** con ítems de prueba (TP-01, TP-02...), cada uno con tipo, prioridad por riesgo, complejidad, quién lo diseña, si se automatiza y quién lo revisa.
2. Cada agente tiene su tarea que dice "diseña SOLO los ítems asignados a tu nivel; si no tienes, responde *Sin asignaciones*".
3. El Líder revisa los reportes de defecto antes de enviarlos a Desarrollo y emite el dictamen de calidad.

| Rol | Recibe del plan | Autonomía | Lo revisa |
|---|---|---|---|
| **QA Semi Senior** | Casos complejos: negativos, límites, integración, exploratorios, no funcionales, regresión; todo ítem de riesgo Alto | Alta: aplica técnicas de diseño y define el nivel de detalle | Líder (en el reporte y el dictamen) |
| **QA Junior** | Casos básicos: camino feliz, humo, validaciones simples | Baja: sigue la plantilla; registra dudas en lugar de suponer | QA Semi Senior |
| **QA Automatización** | Ítems marcados *Automatizar = Sí*: estables, repetitivos, deterministas y de alto valor | Alta en su área; pide a Desarrollo lo que necesita | Líder |

**Los agentes no ejecutan el software.** Un modelo local sin herramientas no puede abrir una app ni correr un pipeline, y si se le pide un resultado lo inventa. Por eso el flujo separa **preparar**, **ejecutar** y **analizar**:

- Los agentes preparan casos, scripts y la hoja de ejecución.
- Una **persona** (tú, que haces QA) ejecuta los casos manuales y el **pipeline** corre los scripts automatizados; los resultados se pegan en `intercambio/resultados_ejecucion.md`.
- Los agentes analizan esos resultados y reportan defectos.

Regla de todo el team: **nunca inventar resultados de ejecución.** Sin resultados, el estado es "No ejecutado" y el dictamen es "Pendiente de ejecución". Si más adelante les das herramientas de CrewAI para ejecutar pruebas, esa separación se vuelve opcional.

**Tres comunicaciones con otros teams** (cada una con su archivo):

| Interacción | Momento | Para qué |
|---|---|---|
| **QA ↔ PO** | Refinamiento | Testabilidad, riesgos y aportes de calidad antes del sprint |
| **QA ↔ Desarrollo** | Validación y reverificación | Entrega de Desarrollo → defectos de QA → reentrega |
| **QA → Desarrollo e Infra** (informativa) | Planificación de pruebas | Qué necesita QA: entornos, datos, identificadores estables |

## 2. Visión general

| Agente | Responsabilidad | Modelo sugerido |
|---|---|---|
| **Líder de QA** | Consolida el refinamiento, planifica y asigna, controla los reportes, emite el dictamen. | `qwen2.5:14b` |
| **QA Semi Senior** | Aportes de riesgo, casos complejos, revisión de casos del Junior, análisis de resultados y defectos. | `qwen2.5:14b` |
| **QA Junior** | Testabilidad, casos básicos y registro de resultados. | `qwen2.5:7b` |
| **QA Automatización** | Estrategia y scripts de automatización, regresión. | `qwen2.5-coder:14b` |

Los modelos son los mismos que ya usan los otros teams, así que no hay nada nuevo que descargar.

### Flujo completo

```
FASE 1 — REFINAMIENTO (responde al Team PO)            python main.py refinamiento
  [Semi Senior]  1. analizar_historias_riesgos      ┐
  [Junior]       2. revisar_testabilidad            ├ independientes entre sí
  [Automatiz.]   3. evaluar_automatizacion          ┘
  [Líder]        4. consolidar_respuesta_qa ──► intercambio/respuestas_qa.md
        │
        ▼
FASE 2 — PREPARAR PRUEBAS                              python main.py preparar
  [Líder]        5. planificar_pruebas_y_asignar ──► intercambio/plan_pruebas.md
  [Semi Senior]  6. disenar_casos_semi_senior
  [Junior]       7. disenar_casos_junior
  [Semi Senior]  8. revisar_casos_prueba            (revisa los del Junior)
  [Automatiz.]   9. disenar_estrategia_automatizacion
        │
        ▼
  Team Desarrollo ──► intercambio/entrega_a_qa.md
        │
        ▼
FASE 3 — PREPARAR EJECUCIÓN                            python main.py preparar_ejecucion
  [Líder]       10. preparar_ejecucion              (criterios de entrada + hoja)
  [Automatiz.]  11. automatizar_pruebas             (scripts, sin ejecutar)
        │
        ▼
  PERSONA / PIPELINE ejecutan ──► intercambio/resultados_ejecucion.md
        │
        ▼
FASE 4 — VALIDAR                                       python main.py validar
  [Junior]      12. registrar_ejecucion_junior
  [Semi Senior] 13. analizar_resultados_y_defectos
  [Líder]       14. consolidar_reporte_qa ──► intercambio/reporte_qa.md
  [Líder]       15. emitir_dictamen_calidad ──► intercambio/dictamen_qa.md
        │
        ▼
  Team Desarrollo corrige ──► intercambio/reentrega_a_qa.md
        │
        ▼
FASE 5 — PREPARAR REVERIFICACIÓN                       python main.py preparar_reverificacion
  [Líder]       16. planificar_reverificacion
  [Automatiz.]  17. actualizar_automatizacion_regresion
        │
        ▼
  PERSONA / PIPELINE ejecutan ──► intercambio/resultados_reverificacion.md
        │
        ▼
FASE 6 — REVERIFICAR                                   python main.py reverificar
  [Junior]      18. registrar_reverificacion_junior
  [Semi Senior] 19. analizar_reverificacion
  [Líder]       20. consolidar_reporte_reverificacion ──► intercambio/reporte_qa.md
  [Líder]       21. emitir_dictamen_final ──► intercambio/dictamen_qa.md
```

## 3. Estructura de archivos y ejecución

Los teams comparten la carpeta `intercambio/` en la raíz del proyecto.

```
proyecto/
├── intercambio/                 # compartida por todos los teams
├── team_po/
├── team_desarrollo/
└── team_qa/
    ├── config/
    │   ├── agents.yaml
    │   └── tasks.yaml           # las 21 tareas, con la clave fase
    ├── salidas/
    └── main.py
```

Instalación (los mismos modelos de los otros teams):

```bash
pip install crewai pyyaml
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:14b
```

Ejecución por fases:

```bash
python main.py refinamiento            # tareas 1-4, requiere intercambio/paquete_refinamiento.md
python main.py preparar                # tareas 5-9
# Desarrollo entrega -> intercambio/entrega_a_qa.md
python main.py preparar_ejecucion      # tareas 10-11
# Ejecutas los casos y el pipeline -> intercambio/resultados_ejecucion.md
python main.py validar                 # tareas 12-15
# Desarrollo corrige -> intercambio/reentrega_a_qa.md
python main.py preparar_reverificacion # tareas 16-17
# Ejecutas las repruebas -> intercambio/resultados_reverificacion.md
python main.py reverificar             # tareas 18-21
```

Si un archivo de entrada no existe, el agente lo lee como "SIN DATO" o "SIN RESULTADOS" y no inventa nada. Los casos que el Semi Senior devuelve en la revisión quedan en `salidas/06_revision_casos.md`; al volver a ejecutar `preparar`, el Líder los toma como pendientes y los reasigna primero.

## 4. Agentes — `config/agents.yaml`

```yaml
lider_qa:
  role: Líder de QA
  goal: >
    Coordinar el Team QA: consolidar en una sola respuesta los aportes de
    calidad al refinamiento, planificar las pruebas con enfoque en riesgo y
    asignar cada ítem al agente y nivel adecuados, controlar la calidad de
    los reportes de defecto antes de enviarlos a Desarrollo y emitir el
    dictamen de calidad. Eres la voz del team hacia el Team PO y el Team
    Desarrollo.
  backstory: |
    Eres un Líder de QA con más de 12 años de experiencia. Has visto
    liberaciones fallar por probar mucho lo irrelevante y poco lo crítico, y
    por eso planificas por riesgo: más cobertura donde el impacto y la
    probabilidad de falla son mayores. Sabes que una prueba que nadie
    ejecuta es decoración y que un reporte sin evidencia hace perder tiempo
    a Desarrollo. No escribes casos ni scripts; decides quién hace qué y si
    lo hecho es suficiente. No decides alcance ni prioridades de negocio
    (Product Owner) ni cómo se corrige un defecto (Desarrollo).

    Reglas de trabajo:
    - Planifica con enfoque en riesgo y justifica la prioridad de cada ítem.
    - Asigna: casos básicos al Junior; complejos, exploratorios, no
      funcionales y de regresión al Semi Senior; ítems estables y
      repetitivos al QA Automatización.
    - Todo ítem de riesgo Alto va al Semi Senior, aunque parezca simple.
    - Cada escenario Gherkin de las historias en alcance tiene al menos un
      ítem de prueba.
    - NUNCA inventes resultados de ejecución. Sin resultados, el estado es
      "No ejecutado" y el dictamen es "Pendiente de ejecución".
    - Un defecto sin pasos reproducibles ni evidencia no se envía a
      Desarrollo.
    - No cambies una severidad sin justificarla con el impacto.
    - Hacia el Team PO y el Team Desarrollo responde solo con la plantilla
      acordada. Escribe "SIN DATO" antes que suponer.
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español, en Markdown.

qa_semi_senior:
  role: QA Semi Senior
  goal: >
    Aportar al refinamiento el punto de vista de calidad que los demás no
    ven: riesgos, casos no cubiertos y ambigüedades. Diseñar los casos de
    prueba complejos (negativos, límites, integración, exploratorios, no
    funcionales y de regresión), revisar los casos del QA Junior, analizar
    los resultados de ejecución y reportar defectos con evidencia.
  backstory: |
    Eres un QA con unos 6 años de experiencia y pensamiento adversarial: ante
    cada historia te preguntas cómo se rompe. Dominas las técnicas de diseño
    de pruebas (valores límite, particiones de equivalencia, transiciones de
    estado, tablas de decisión) y sabes distinguir un defecto de un
    requisito faltante. Eres meticuloso con la evidencia: un defecto sin
    pasos claros no existe.

    Reglas de trabajo:
    - Aplica técnicas de diseño de pruebas y nómbralas en cada caso.
    - Tus aportes en el refinamiento son hipótesis priorizadas por riesgo,
      no requisitos: el Product Owner decide el alcance.
    - Cada caso lleva precondiciones y datos, pasos numerados y resultado
      esperado medible (valores y mensajes exactos).
    - Al revisar los casos del Junior, di qué falla y cómo corregirlo; no
      reescribas su trabajo.
    - Un defecto lleva pasos reproducibles, resultado esperado, resultado
      obtenido y evidencia. Nunca inventes evidencia.
    - Si el supuesto defecto es en realidad un requisito ambiguo, regístralo
      como "Pregunta para el PO".
    - NUNCA inventes resultados de ejecución; lo que no aparezca en los
      resultados es "No ejecutado".
    - Solo trabajas los ítems asignados a QA Semi Senior; si no tienes,
      responde exactamente "Sin asignaciones".
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español, en Markdown.

qa_junior:
  role: QA Junior
  goal: >
    Verificar la testabilidad de los criterios de aceptación en el
    refinamiento, diseñar los casos básicos (camino feliz, humo y
    validaciones simples) siguiendo exactamente la plantilla del plan, y
    registrar con fidelidad los resultados de ejecución de los casos
    asignados. Registrar tus dudas en lugar de suponer.
  backstory: |
    Eres un QA con unos 2 años de experiencia. Eres ordenado, sigues la
    plantilla al pie de la letra y no te da pena preguntar. Prefieres decir
    "no ejecutado" antes que registrar un resultado que no viste. Tu
    trabajo siempre lo revisa el QA Semi Senior, así que dejas claro qué no
    tienes seguro.

    Reglas de trabajo:
    - Sigue exactamente la plantilla de caso de prueba del plan.
    - Cada caso tiene un resultado esperado medible, con valores concretos.
    - Al revisar la testabilidad, evalúa cada escenario Gherkin contra los
      cuatro criterios pedidos y no omitas ninguno.
    - Si algo no está claro, no lo adivines: regístralo como "Duda para el
      Semi Senior".
    - NUNCA inventes resultados de ejecución; lo que no aparezca en los
      resultados es "No ejecutado".
    - Solo trabajas los ítems asignados a QA Junior; si no tienes, responde
      exactamente "Sin asignaciones".
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español, en Markdown.

qa_automatizacion:
  role: QA Automatización
  goal: >
    Evaluar en el refinamiento qué historias son automatizables y qué
    necesitan de Desarrollo para serlo; definir la estrategia de
    automatización; escribir scripts de pruebas de API y de UI y de
    regresión, mantenibles y deterministas, ejecutables desde el pipeline;
    y dejar claro qué necesitas de Desarrollo, DevOps e Infraestructura.
  backstory: |
    Eres un ingeniero de automatización de pruebas con más de 7 años de
    experiencia. Sabes que automatizar lo inestable produce pruebas
    inestables y que la automatización es software: se diseña, se revisa y
    se mantiene. Antes de escribir un script te preguntas si vale la pena
    automatizarlo.

    Reglas de trabajo:
    - Automatiza solo lo estable, repetitivo, determinista y de alto valor.
      Nunca lo exploratorio ni lo volátil.
    - Prefiere pruebas de API antes que de UI (más rápidas y estables); la
      UI solo para flujos críticos.
    - Pruebas independientes entre sí, con datos propios y sin esperas
      fijas; usa esperas por condición.
    - Pide a Desarrollo identificadores estables en la interfaz y datos
      semilla; no dependas de textos ni posiciones frágiles.
    - Sin secretos en los scripts: usa variables de entorno.
    - NUNCA afirmes que una prueba pasa. Tus scripts quedan "Sin ejecutar"
      hasta que existan resultados reales.
    - Solo trabajas los ítems marcados Automatizar = Sí; si no tienes,
      responde exactamente "Sin asignaciones".
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español; el código y sus comentarios, en el idioma del proyecto.
```

## 5. Relación entre tareas

| # | Tarea | Fase | Agente | Contexto / entradas | Entrega |
|---|---|---|---|---|---|
| 1 | `analizar_historias_riesgos` | Refinamiento | Semi Senior | paquete, historias finales | `01_analisis_riesgos.md` |
| 2 | `revisar_testabilidad` | Refinamiento | Junior | paquete, historias finales | `02_testabilidad.md` |
| 3 | `evaluar_automatizacion` | Refinamiento | Automatización | paquete, historias finales | `03_evaluacion_automatizacion.md` |
| 4 | `consolidar_respuesta_qa` | Refinamiento | Líder | 1, 2, 3, paquete | `intercambio/respuestas_qa.md` |
| 5 | `planificar_pruebas_y_asignar` | Preparar | Líder | historias y backlog refinados, respuesta de QA | `intercambio/plan_pruebas.md` |
| 6 | `disenar_casos_semi_senior` | Preparar | Semi Senior | 5, historias refinadas | `04_casos_semi_senior.md` |
| 7 | `disenar_casos_junior` | Preparar | Junior | 5, 6, historias refinadas | `05_casos_junior.md` |
| 8 | `revisar_casos_prueba` | Preparar | Semi Senior | 5, 6, 7 | `06_revision_casos.md` |
| 9 | `disenar_estrategia_automatizacion` | Preparar | Automatización | 5 | `07_estrategia_automatizacion.md` |
| 10 | `preparar_ejecucion` | Preparar ejecución | Líder | entrega de Desarrollo, plan, revisión de casos | `08_hoja_ejecucion.md` |
| 11 | `automatizar_pruebas` | Preparar ejecución | Automatización | 10, entrega, plan, estrategia, casos | `09_automatizacion.md` |
| 12 | `registrar_ejecucion_junior` | Validar | Junior | 10, resultados de ejecución | `10_ejecucion_junior.md` |
| 13 | `analizar_resultados_y_defectos` | Validar | Semi Senior | 10, 11, 12, resultados de ejecución | `11_resultados_y_defectos.md` |
| 14 | `consolidar_reporte_qa` | Validar | Líder | 10, 13 | `intercambio/reporte_qa.md` |
| 15 | `emitir_dictamen_calidad` | Validar | Líder | 10, 12, 13, 14, plan | `intercambio/dictamen_qa.md` |
| 16 | `planificar_reverificacion` | Preparar reverificación | Líder | reentrega, reporte previo, plan, hoja | `12_hoja_reverificacion.md` |
| 17 | `actualizar_automatizacion_regresion` | Preparar reverificación | Automatización | 16, reentrega, scripts, estrategia | `13_automatizacion_regresion.md` |
| 18 | `registrar_reverificacion_junior` | Reverificar | Junior | 16, resultados de reverificación | `14_reverificacion_junior.md` |
| 19 | `analizar_reverificacion` | Reverificar | Semi Senior | 16, 17, 18, resultados, reporte previo | `15_analisis_reverificacion.md` |
| 20 | `consolidar_reporte_reverificacion` | Reverificar | Líder | 16, 19 | `intercambio/reporte_qa.md` |
| 21 | `emitir_dictamen_final` | Reverificar | Líder | 16, 18, 19, 20, plan, dictamen previo | `intercambio/dictamen_qa.md` |

## 6. Tareas — `config/tasks.yaml`

Cada tarea lleva `fase` y `main.py` ejecuta solo las de esa fase. Las entradas entre llaves las inyecta `main.py` desde los archivos.

```yaml
# ───────────── FASE 1 — REFINAMIENTO ─────────────

analizar_historias_riesgos:
  fase: refinamiento
  agent: qa_semi_senior
  description: >
    Lee el paquete de refinamiento: [ {paquete_refinamiento} ] y las
    historias finales: [ {historias_finales} ]. Usa SOLO la sección
    "Preguntas para QA" y las historias que aparecen en ella. Analiza cada
    historia con pensamiento adversarial, de forma independiente a lo que
    digan otros teams. Aplica estas heurísticas y nombra la que uses:
    valores límite, particiones de equivalencia, transiciones de estado,
    permisos y roles, datos vacíos o inválidos, concurrencia y repetición de
    operaciones, interrupciones (fallo de red, tiempo de espera), uso
    indebido e impacto sobre funciones existentes. Entrega máximo 5 aportes
    por historia, priorizados por riesgo (impacto por probabilidad), cada uno
    clasificado como: Caso no cubierto, Riesgo, Ambigüedad o Requisito
    posiblemente faltante. Los aportes son hipótesis: no decidas el alcance.
    Evalúa también el riesgo de regresión y responde las preguntas para QA
    que te competan.
  expected_output: >
    Por cada historia este bloque:
    ### HU-001
    Tabla de aportes: ID | Clasificación | Aporte | Riesgo (Alto / Medio / Bajo)
    | Técnica o heurística
    - Riesgo de regresión: [Alto / Medio / Bajo + módulo afectado]
    - Escenarios faltantes: [uno por línea, en una frase, o "Ninguno"]
    - Respuestas a las preguntas: [1) ... 2) ... o "No aplica"]
  output_file: salidas/01_analisis_riesgos.md

revisar_testabilidad:
  fase: refinamiento
  agent: qa_junior
  description: >
    Lee el paquete de refinamiento: [ {paquete_refinamiento} ] y las
    historias finales: [ {historias_finales} ]. Usa SOLO la sección
    "Preguntas para QA" y las historias que aparecen en ella. Para cada
    escenario Gherkin de cada historia responde Sí o No: (a) el resultado
    esperado es verificable, (b) usa valores medibles y no términos vagos,
    (c) los datos de entrada están definidos, (d) tiene una precondición
    clara. Si algo es "No", explica el motivo en una línea. Lista los datos
    de prueba y el entorno que se necesitarían. Responde las preguntas para
    QA que te competan.
  expected_output: >
    Por cada historia este bloque:
    ### HU-001
    Tabla: Escenario | Verificable | Medible | Datos definidos | Precondición |
    Motivo si hay un No
    - ¿Criterios testables?: [Sí si todo es Sí / No + motivo]
    - Datos de prueba requeridos: [lista o "Ninguno"]
    - Entorno requerido: [lista o "Ninguno"]
    - Respuestas a las preguntas: [1) ... 2) ... o "No aplica"]
  output_file: salidas/02_testabilidad.md

evaluar_automatizacion:
  fase: refinamiento
  agent: qa_automatizacion
  description: >
    Lee el paquete de refinamiento: [ {paquete_refinamiento} ] y las
    historias finales: [ {historias_finales} ]. Usa SOLO la sección
    "Preguntas para QA" y las historias que aparecen en ella. Para cada
    historia evalúa si es automatizable: nivel recomendado (API, UI, ambos
    o no automatizar), motivo y esfuerzo relativo (Bajo, Medio, Alto). Indica
    lo que necesitarías de Desarrollo (identificadores estables en la
    interfaz, endpoints, datos semilla), de DevOps (etapa de pruebas en el
    pipeline, reportes) y de Infraestructura (entorno estable, datos).
    Marca como "No automatizar" lo exploratorio, lo volátil o de uso único.
  expected_output: >
    Por cada historia este bloque:
    ### HU-001
    - Automatizable: [Sí / Parcial / No]
    - Nivel: [API / UI / Ambos / No aplica]
    - Motivo: [una línea]
    - Esfuerzo: [Bajo / Medio / Alto]
    - Necesita de Desarrollo: [lista o "Nada"]
    - Necesita de DevOps e Infraestructura: [lista o "Nada"]
  output_file: salidas/03_evaluacion_automatizacion.md

consolidar_respuesta_qa:
  fase: refinamiento
  agent: lider_qa
  context: [analizar_historias_riesgos, revisar_testabilidad, evaluar_automatizacion]
  description: >
    Paquete de refinamiento: [ {paquete_refinamiento} ]. Consolida los tres
    análisis en la respuesta oficial de QA, historia por historia, sin
    alterar su contenido. Une los aportes y deja máximo 5 por historia,
    conservando los de mayor riesgo y su clasificación. "¿Criterios
    testables?" es No si el Junior o el Semi Senior marcaron un problema,
    con el motivo. El riesgo de regresión viene del Semi Senior. Datos y
    entorno: une sin duplicar. "Automatizable" viene del QA Automatización.
    Las dudas de negocio van en "Necesita decisión del PO". Si dos análisis
    se contradicen, repórtalo tal cual en "Aportes de QA" con la etiqueta
    "Desacuerdo interno". No inventes datos.
  expected_output: >
    Por cada historia, exactamente este bloque:
    ## HU-001
    - ¿Criterios testables?: [Sí / No + motivo]
    - Datos de prueba requeridos: [lista o "Ninguno"]
    - Entorno requerido: [lista o "Ninguno"]
    - Riesgo de regresión: [Alto / Medio / Bajo + módulo afectado]
    - Escenarios faltantes: [lista o "Ninguno"]
    - Aportes de QA: [ideas, riesgos o ambigüedades priorizados, o "Ninguno"]
    - Automatizable: [Sí / Parcial / No + nivel]
    - Respuestas a las preguntas: [1) ... 2) ... 3) ...]
    - Necesita decisión del PO: [pregunta o "No"]
  output_file: ../intercambio/respuestas_qa.md

# ───────────── FASE 2 — PREPARAR PRUEBAS ─────────────

planificar_pruebas_y_asignar:
  fase: preparar
  agent: lider_qa
  description: >
    Historias refinadas: [ {historias_refinadas} ]. Backlog refinado:
    [ {backlog_refinado} ]. Tu respuesta de QA del refinamiento:
    [ {respuestas_qa} ]. Revisión de casos previa con ítems devueltos:
    [ {revision_casos} ].
    Selecciona como máximo [ {max_historias} ] historias con estado "Lista
    para sprint", en el orden del backlog (el mismo valor que usa
    Desarrollo, para cubrir las mismas historias). Si hay ítems devueltos
    en la revisión previa, reasígnalos primero con sus observaciones; si
    eran del Junior, súbelos al Semi Senior. Cada escenario Gherkin de las
    historias seleccionadas debe tener al menos un ítem de prueba; añade
    además ítems derivados de los aportes de riesgo Alto. Máximo 10 ítems
    por historia. Asigna quién diseña cada ítem: complejidad Básica (camino
    feliz, humo, validaciones simples de campos y mensajes) al QA Junior;
    Compleja (negativos, valores límite, integración, exploratorios, no
    funcionales con valores medibles, regresión) al QA Semi Senior; todo
    ítem de riesgo Alto al Semi Senior. Marca "Automatizar = Sí" solo si el
    ítem es estable, repetitivo, determinista y de alto valor (humo y
    regresión de flujos críticos, contratos de API); nunca para
    exploratorios. Define criterios de salida medibles; por defecto: 100% de
    los casos de humo pasados, 0 defectos Críticos o Altos abiertos y 100% de
    los casos de prioridad Alta ejecutados. Expresa lo que QA necesita de
    Desarrollo e Infraestructura. Cada ítem del Junior lleva como revisor al
    Semi Senior.
  expected_output: >
    Markdown con exactamente estas secciones:
    # Plan de pruebas
    ## Alcance (tabla: Orden | HU | Título)
    ## Estrategia por tipo de prueba (tabla: Tipo | Aplica (Sí / No) | Enfoque)
    ## Riesgos priorizados (tabla: Riesgo | HU | Impacto | Probabilidad |
    Mitigación)
    ## Criterios de entrada y de salida (dos listas)
    ## Entorno y datos necesarios
    ## Necesidades hacia Desarrollo e Infraestructura (lista)
    ## Plantilla de caso de prueba
    Bloque con estos campos: ID del caso, historia y escenario Gherkin, tipo,
    prioridad, técnica de diseño, precondiciones y datos, pasos numerados,
    resultado esperado medible, automatizar.
    ## Ítems de prueba
    Tabla: ID (TP-01...) | HU | Escenario Gherkin | Tipo (Funcional /
    Negativo / Límite / Integración / Exploratorio / No funcional / Humo /
    Regresión) | Prioridad (Alta / Media / Baja) | Complejidad (Básica /
    Compleja) | Diseña (Junior / Semi Senior) | Automatizar (Sí / No) |
    Revisor
    ## Orden de diseño (lista de IDs)
    ## Ítems reasignados (o "Ninguno")
    ## Carga por agente (tabla: Agente | Número de ítems)
  output_file: ../intercambio/plan_pruebas.md

disenar_casos_semi_senior:
  fase: preparar
  agent: qa_semi_senior
  context: [planificar_pruebas_y_asignar]
  description: >
    Historias refinadas: [ {historias_refinadas} ]. Tienes en tu contexto el
    plan de pruebas. Diseña SOLO los casos de los ítems asignados a QA Semi
    Senior en la columna "Diseña", en el orden del plan. Si no tienes ítems,
    responde exactamente: Sin asignaciones. Usa la plantilla de caso del
    plan y nombra la técnica de diseño de cada caso. El resultado esperado
    debe ser medible, con valores y mensajes exactos. Para los ítems
    exploratorios entrega una carta de exploración: objetivo, alcance, tiempo
    máximo, heurísticas a usar y preguntas a responder; su resultado
    esperado es "Hallazgos registrados".
  expected_output: >
    Si no hay ítems: la frase exacta "Sin asignaciones". Si hay, por cada
    ítem este bloque:
    ### CP-001 (TP-01)
    - Historia: [HU-xxx] | Escenario Gherkin: [nombre]
    - Tipo: [tipo]
    - Prioridad: [Alta / Media / Baja]
    - Técnica de diseño: [nombre de la técnica]
    - Precondiciones y datos: [lista]
    - Pasos: [1) ... 2) ...]
    - Resultado esperado: [medible, con valores y mensajes exactos]
    - Automatizar: [Sí / No]
  output_file: salidas/04_casos_semi_senior.md

disenar_casos_junior:
  fase: preparar
  agent: qa_junior
  context: [planificar_pruebas_y_asignar, disenar_casos_semi_senior]
  description: >
    Historias refinadas: [ {historias_refinadas} ]. Tienes en tu contexto el
    plan de pruebas y los casos del QA Semi Senior como modelo del nivel de
    detalle. Diseña SOLO los casos de los ítems asignados a QA Junior en la
    columna "Diseña", en el orden del plan. Si no tienes ítems, responde
    exactamente: Sin asignaciones. Sigue exactamente la plantilla de caso
    del plan. El resultado esperado debe ser medible, con valores y mensajes
    exactos. Si algo no está claro, no lo adivines: regístralo como "Duda
    para el Semi Senior".
  expected_output: >
    Si no hay ítems: la frase exacta "Sin asignaciones". Si hay, por cada
    ítem este bloque:
    ### CP-010 (TP-08)
    - Historia: [HU-xxx] | Escenario Gherkin: [nombre]
    - Tipo: [tipo]
    - Prioridad: [Alta / Media / Baja]
    - Técnica de diseño: [nombre de la técnica]
    - Precondiciones y datos: [lista]
    - Pasos: [1) ... 2) ...]
    - Resultado esperado: [medible, con valores y mensajes exactos]
    - Automatizar: [Sí / No]
    - Dudas para el Semi Senior: [lista o "Ninguna"]
  output_file: salidas/05_casos_junior.md

revisar_casos_prueba:
  fase: preparar
  agent: qa_semi_senior
  context: [planificar_pruebas_y_asignar, disenar_casos_semi_senior, disenar_casos_junior]
  description: >
    Revisa los casos del QA Junior contra el plan de pruebas. Para cada caso
    responde Sí o No: (a) es trazable a un escenario Gherkin y a una
    historia, (b) los pasos están numerados y otra persona puede
    reproducirlos, (c) el resultado esperado es verificable y medible, (d)
    las precondiciones y los datos están definidos, (e) sigue la plantilla.
    Si un caso es "No", indica el problema y la corrección exacta; no
    reescribas el caso. Un caso es "Aprobado" solo si los cinco son "Sí"; si
    no, "Devuelto". Responde también cada "Duda para el Semi Senior". Si el
    Junior respondió "Sin asignaciones", responde exactamente: Sin casos
    para revisar.
  expected_output: >
    Si no hay casos: la frase exacta "Sin casos para revisar". Si hay:
    Tabla Markdown: Caso | Trazable | Reproducible | Medible | Datos |
    Plantilla | Veredicto (Aprobado / Devuelto) | Problema y corrección.
    ## Respuestas a dudas
    Lista: caso y respuesta (o "Ninguna").
    ## Resumen
    "X de Y casos aprobados".
  output_file: salidas/06_revision_casos.md

disenar_estrategia_automatizacion:
  fase: preparar
  agent: qa_automatizacion
  context: [planificar_pruebas_y_asignar]
  description: >
    Tienes en tu contexto el plan de pruebas. Trabaja SOLO con los ítems
    marcados "Automatizar = Sí". Si no hay, responde exactamente: Sin
    asignaciones. Define la estrategia de automatización: proporción entre
    pruebas de API y de UI (prefiere API), criterio de selección con la
    razón de cada ítem, herramienta con su justificación (si no hay
    restricción del stack, prefiere Playwright para UI y API; si el equipo ya
    usa colecciones de Postman, ejecútalas desde el pipeline con su línea de
    comandos), estructura del proyecto de automatización, convenciones,
    manejo de datos de prueba, integración con el pipeline y formato de
    reportes. Lista los riesgos de inestabilidad y lo que necesitas de
    Desarrollo (identificadores estables, endpoints, datos semilla), de
    DevOps y de Infraestructura.
  expected_output: >
    Si no hay ítems: la frase exacta "Sin asignaciones". Si hay, Markdown con
    exactamente estas secciones:
    # Estrategia de automatización
    ## Ítems a automatizar (tabla: TP | Nivel (API / UI) | Razón)
    ## Herramientas y justificación
    ## Estructura del proyecto
    ## Convenciones y manejo de datos
    ## Integración con el pipeline y reportes
    ## Riesgos de inestabilidad
    ## Necesidades hacia Desarrollo, DevOps e Infraestructura
  output_file: salidas/07_estrategia_automatizacion.md

# ───────────── FASE 3 — PREPARAR EJECUCIÓN ─────────────

preparar_ejecucion:
  fase: preparar_ejecucion
  agent: lider_qa
  description: >
    Entrega de Desarrollo: [ {entrega_qa} ]. Plan de pruebas:
    [ {plan_pruebas} ]. Revisión de casos: [ {revision_casos} ].
    Verifica los criterios de entrada de la entrega: versión indicada,
    historias incluidas listadas, pasos de despliegue, URLs y endpoints,
    datos de prueba y forma de correr las pruebas unitarias. El veredicto de
    la entrega es Aceptada o Rechazada; si es Rechazada, lista los faltantes
    exactos y no armes la hoja. Si es Aceptada, arma la hoja de ejecución solo
    con las historias incluidas en la entrega: primero los casos de humo y
    después por prioridad de Alta a Baja. Excluye los casos "Devuelto" en la
    revisión (quedan pendientes). Cada caso indica el modo (Manual o
    Automatizado) y quién registra su resultado: QA Junior, QA Semi Senior o
    QA Automatización. Recuerda que ningún agente ejecuta: las personas o el
    pipeline ejecutan y los agentes registran y analizan.
  expected_output: >
    Markdown con exactamente estas secciones:
    # Hoja de ejecución
    ## Veredicto de la entrega
    Una línea: "Aceptada" o "Rechazada" y, si es Rechazada, la lista de
    faltantes.
    ## Versión probada
    ## Hoja
    Tabla: Orden | CP | HU | Prioridad | Modo (Manual / Automatizado) |
    Registra (Junior / Semi Senior / Automatización)
    ## Casos excluidos (tabla: CP | Motivo, o "Ninguno")
  output_file: salidas/08_hoja_ejecucion.md

automatizar_pruebas:
  fase: preparar_ejecucion
  agent: qa_automatizacion
  context: [preparar_ejecucion]
  description: >
    Entrega de Desarrollo: [ {entrega_qa} ]. Plan: [ {plan_pruebas} ].
    Estrategia de automatización: [ {estrategia_automatizacion} ]. Casos del
    Semi Senior: [ {casos_semi_senior} ]. Casos del Junior:
    [ {casos_junior} ]. Si la hoja de ejecución indica que la entrega es
    Rechazada, responde exactamente: Sin ejecución: entrega rechazada. Si no,
    escribe los scripts SOLO para los ítems marcados "Automatizar = Sí" que
    estén en la hoja de ejecución, con los pasos y resultados esperados de sus
    casos y los endpoints de la entrega. Cada script es independiente, con
    datos propios, sin esperas fijas y sin secretos (variables de entorno).
    Entrega el código completo por archivo, el mapeo caso a script y el
    comando para ejecutarlos desde el pipeline. No inventes endpoints ni
    selectores que no estén en la entrega: si faltan, regístralos como
    "Necesidad hacia Desarrollo". Todos los scripts quedan como "Sin
    ejecutar".
  expected_output: >
    Si la entrega fue rechazada: la frase exacta "Sin ejecución: entrega
    rechazada". Si no hay ítems: la frase exacta "Sin asignaciones". Si hay:
    ## Scripts
    Cada archivo con su ruta como título y el código en un bloque.
    ## Mapeo caso a script (tabla: CP | Script | Nivel)
    ## Cómo ejecutar (comandos para el pipeline)
    ## Variables de entorno (solo nombres)
    ## Necesidades hacia Desarrollo (lista o "Ninguna")
    ## Estado
    "Sin ejecutar".
  output_file: salidas/09_automatizacion.md

# ───────────── FASE 4 — VALIDAR ─────────────

registrar_ejecucion_junior:
  fase: validar
  agent: qa_junior
  context: [preparar_ejecucion]
  description: >
    Resultados de ejecución: [ {resultados_ejecucion} ]. Tienes en tu
    contexto la hoja de ejecución. Si la hoja indica que la entrega es
    Rechazada, responde exactamente: Sin ejecución: entrega rechazada. Si no,
    registra SOLO los resultados de los casos que la hoja asigna al QA
    Junior. Estados posibles: Pasó, Falló, Bloqueado o No ejecutado. Usa
    únicamente lo que aparece en los resultados; todo caso que no aparezca es
    "No ejecutado". Para la evidencia cita la referencia tal como aparece
    (ruta, captura, log). Nunca inventes resultados ni evidencia. Si no
    tienes casos asignados, responde exactamente: Sin asignaciones.
  expected_output: >
    Si la entrega fue rechazada: la frase exacta "Sin ejecución: entrega
    rechazada". Si no hay casos: la frase exacta "Sin asignaciones". Si hay:
    Tabla Markdown: Caso | HU | Estado | Evidencia | Observaciones
    ## Resumen
    "X de Y casos ejecutados".
  output_file: salidas/10_ejecucion_junior.md

analizar_resultados_y_defectos:
  fase: validar
  agent: qa_semi_senior
  context: [preparar_ejecucion, automatizar_pruebas, registrar_ejecucion_junior]
  description: >
    Resultados de ejecución: [ {resultados_ejecucion} ]. Tienes en tu
    contexto la hoja de ejecución, los scripts y el registro del Junior. Si la
    hoja indica que la entrega es Rechazada, responde exactamente: Sin
    ejecución: entrega rechazada. Si no: (1) registra con el mismo formato
    del Junior los resultados de los casos asignados a Semi Senior y de los
    automatizados, usando solo lo que aparezca en los resultados; lo que no
    aparezca es "No ejecutado". (2) Por cada caso Falló o Bloqueado, del
    Junior, tuyos o automatizados, redacta un reporte de defecto con la
    plantilla acordada; agrupa los duplicados en un solo defecto y numéralos
    BUG-001, BUG-002... (3) Asigna severidad por impacto: Crítica = bloquea el
    flujo principal, pierde datos o falla de seguridad; Alta = funcionalidad
    principal incorrecta sin alternativa; Media = incorrecta pero con
    alternativa; Baja = cosmética. (4) Si el supuesto defecto es en realidad un
    requisito ambiguo, regístralo como Pregunta para el PO. Nunca inventes
    evidencia ni resultados.
  expected_output: >
    Si la entrega fue rechazada: la frase exacta "Sin ejecución: entrega
    rechazada". Si no:
    ## Registro de ejecución (Semi Senior y automatizados)
    Tabla: Caso | HU | Estado | Evidencia | Observaciones
    ## Defectos
    Por cada defecto, exactamente este bloque:
    ### BUG-001
    - Historia: [HU-xxx]
    - Escenario Gherkin afectado: [nombre]
    - Severidad: [Crítica / Alta / Media / Baja]
    - Pasos para reproducir: [lista numerada]
    - Resultado esperado: [texto]
    - Resultado obtenido: [texto]
    - Evidencia: [referencia tal como aparece en los resultados]
    - Versión probada: [versión]
    Si no hay defectos: "Ninguno".
    ## Preguntas para el PO (lista o "Ninguna")
    ## Cobertura de ejecución
    "X de Y casos ejecutados (Z%)".
  output_file: salidas/11_resultados_y_defectos.md

consolidar_reporte_qa:
  fase: validar
  agent: lider_qa
  context: [preparar_ejecucion, analizar_resultados_y_defectos]
  description: >
    Revisa cada reporte de defecto del análisis. Un defecto está "Aprobado
    para enviar" solo si: (a) los pasos son reproducibles, (b) el resultado
    esperado y el obtenido son claros, (c) hay evidencia, (d) la severidad
    está justificada por el impacto, (e) no está duplicado. Los defectos
    aprobados se copian sin cambios a la salida. Los que no cumplen quedan
    retenidos y no se incluyen. Si la entrega fue Rechazada o no hay defectos
    aprobados, responde exactamente: SIN REPORTE.
  expected_output: >
    Solo los defectos aprobados, cada uno exactamente con este bloque y sin
    ningún texto adicional:
    ## BUG-001
    - Historia: [HU-xxx]
    - Escenario Gherkin afectado: [nombre]
    - Severidad: [Crítica / Alta / Media / Baja]
    - Pasos para reproducir: [lista numerada]
    - Resultado esperado: [texto]
    - Resultado obtenido: [texto]
    - Evidencia: [referencia]
    - Versión probada: [versión]
    Si no hay defectos aprobados: la frase exacta "SIN REPORTE".
  output_file: ../intercambio/reporte_qa.md

emitir_dictamen_calidad:
  fase: validar
  agent: lider_qa
  context: [preparar_ejecucion, registrar_ejecucion_junior, analizar_resultados_y_defectos, consolidar_reporte_qa]
  description: >
    Plan de pruebas con sus criterios de salida: [ {plan_pruebas} ]. Emite
    el dictamen de calidad usando solo los resultados registrados. Veredicto
    general: "Apto para aceptación del PO" solo si todos los criterios de
    salida se cumplen; "No apto" si alguno no se cumple o la entrega fue
    Rechazada; "Pendiente de ejecución" si no hay resultados suficientes
    para evaluar. Veredicto por historia: Apta, Con defectos abiertos o No
    validada. Los defectos retenidos son los que aparecen en el análisis y no
    en el reporte enviado. Si la entrega fue Rechazada, lista los
    faltantes. No inventes datos.
  expected_output: >
    Markdown con exactamente estas secciones:
    # Dictamen de calidad
    ## Entrega
    "Aceptada" o "Rechazada" y los faltantes si los hay.
    ## Veredicto general
    Una línea: "Apto para aceptación del PO", "No apto" o "Pendiente de
    ejecución".
    ## Resultado por historia
    Tabla: HU | Casos ejecutados | Pasaron | Fallaron | Defectos abiertos (por
    severidad) | Veredicto (Apta / Con defectos abiertos / No validada)
    ## Criterios de salida
    Tabla: Criterio | Meta | Resultado | Cumple (Sí / No)
    ## Defectos retenidos y motivo (tabla o "Ninguno")
    ## Riesgos residuales (lista o "Ninguno")
    ## Preguntas para el PO (lista o "Ninguna")
  output_file: ../intercambio/dictamen_qa.md

# ───────────── FASE 5 — PREPARAR REVERIFICACIÓN ─────────────

planificar_reverificacion:
  fase: preparar_reverificacion
  agent: lider_qa
  description: >
    Reentrega de Desarrollo: [ {reentrega_qa} ]. Reporte anterior:
    [ {reporte_previo} ]. Plan de pruebas: [ {plan_pruebas} ]. Hoja de
    ejecución anterior: [ {hoja_ejecucion} ]. Verifica que la reentrega
    indique nueva versión y la lista de defectos corregidos y no corregidos;
    si falta algo, el veredicto es Rechazada y listas los faltantes sin armar
    la hoja. Si es Aceptada: para cada defecto corregido define una reprueba
    con el caso que lo detectó; define la regresión con las pruebas que pide
    la reentrega y los casos de las historias afectadas; los defectos no
    corregidos siguen Abiertos con su motivo. Ordena primero las repruebas de
    defectos Críticos y Altos. Asigna lo manual: básico al QA Junior, el resto
    al Semi Senior; lo automatizado, al QA Automatización.
  expected_output: >
    Markdown con exactamente estas secciones:
    # Hoja de reverificación
    ## Veredicto de la reentrega
    "Aceptada" o "Rechazada" y los faltantes si los hay.
    ## Nueva versión
    ## Defectos por estado
    Tabla: BUG | Severidad | Estado en la reentrega (Corregido / No
    corregido) | Motivo
    ## Hoja
    Tabla: Orden | Tipo (Reprueba / Regresión) | BUG o CP | Modo (Manual /
    Automatizado) | Registra (Junior / Semi Senior / Automatización)
  output_file: salidas/12_hoja_reverificacion.md

actualizar_automatizacion_regresion:
  fase: preparar_reverificacion
  agent: qa_automatizacion
  context: [planificar_reverificacion]
  description: >
    Reentrega de Desarrollo: [ {reentrega_qa} ]. Scripts actuales:
    [ {salida_automatizacion} ]. Estrategia: [ {estrategia_automatizacion} ].
    Si la hoja de reverificación indica que la reentrega es Rechazada,
    responde exactamente: Sin ejecución: reentrega rechazada. Si no: para cada
    defecto corregido cuyo caso sea automatizable, escribe un script de
    regresión nuevo que reproduzca el defecto; actualiza solo los scripts
    afectados por los cambios de la reentrega y entrega los archivos
    completos modificados. Mantén las reglas de la estrategia. No inventes
    endpoints ni selectores. Todo queda como "Sin ejecutar".
  expected_output: >
    Si la reentrega fue rechazada: la frase exacta "Sin ejecución: reentrega
    rechazada". Si no hay cambios que automatizar: "Sin asignaciones". Si hay:
    ## Scripts nuevos y modificados
    Cada archivo con su ruta como título y el código en un bloque.
    ## Mapeo defecto a script (tabla: BUG | Script)
    ## Cómo ejecutar (comandos para el pipeline)
    ## Estado
    "Sin ejecutar".
  output_file: salidas/13_automatizacion_regresion.md

# ───────────── FASE 6 — REVERIFICAR ─────────────

registrar_reverificacion_junior:
  fase: reverificar
  agent: qa_junior
  context: [planificar_reverificacion]
  description: >
    Resultados de la reverificación: [ {resultados_reverificacion} ]. Tienes
    en tu contexto la hoja de reverificación. Si la hoja indica que la
    reentrega es Rechazada, responde exactamente: Sin ejecución: reentrega
    rechazada. Si no, registra SOLO los resultados de los ítems que la hoja
    asigna al QA Junior. Estados posibles: Pasó, Falló, Bloqueado o No
    ejecutado. Usa únicamente lo que aparece en los resultados; lo que no
    aparezca es "No ejecutado". Cita la evidencia tal como aparece. Nunca
    inventes resultados ni evidencia. Si no tienes ítems asignados, responde
    exactamente: Sin asignaciones.
  expected_output: >
    Si la reentrega fue rechazada: la frase exacta "Sin ejecución: reentrega
    rechazada". Si no hay ítems: la frase exacta "Sin asignaciones". Si hay:
    Tabla Markdown: BUG o CP | Tipo | Estado | Evidencia | Observaciones
    ## Resumen
    "X de Y ítems ejecutados".
  output_file: salidas/14_reverificacion_junior.md

analizar_reverificacion:
  fase: reverificar
  agent: qa_semi_senior
  context: [planificar_reverificacion, actualizar_automatizacion_regresion, registrar_reverificacion_junior]
  description: >
    Resultados de la reverificación: [ {resultados_reverificacion} ]. Reporte
    anterior: [ {reporte_previo} ]. Si la hoja indica que la reentrega es
    Rechazada, responde exactamente: Sin ejecución: reentrega rechazada. Si
    no: registra los resultados de los ítems asignados a Semi Senior y de los
    automatizados, usando solo lo que aparezca en los resultados. Clasifica
    cada defecto del reporte anterior como: Cerrado (la reprueba pasó, con
    evidencia), Reabierto (la reprueba falló; redacta un nuevo reporte con
    evidencia) o Sin verificar (no hay resultados). Si una prueba de
    regresión falló, redacta un defecto nuevo continuando la numeración
    después del BUG más alto del reporte anterior. Los defectos no
    corregidos por Desarrollo siguen Abiertos. Nunca inventes evidencia ni
    resultados.
  expected_output: >
    Si la reentrega fue rechazada: la frase exacta "Sin ejecución: reentrega
    rechazada". Si no:
    ## Estado de los defectos
    Tabla: BUG | Estado (Cerrado / Reabierto / Sin verificar / Abierto) |
    Evidencia
    ## Registro de ejecución
    Tabla: BUG o CP | Tipo | Estado | Evidencia
    ## Defectos reabiertos y nuevos
    Cada uno con este bloque:
    ### BUG-00X
    - Historia: [HU-xxx]
    - Escenario Gherkin afectado: [nombre]
    - Severidad: [Crítica / Alta / Media / Baja]
    - Pasos para reproducir: [lista numerada]
    - Resultado esperado: [texto]
    - Resultado obtenido: [texto]
    - Evidencia: [referencia]
    - Versión probada: [versión]
    Si no hay: "Ninguno".
  output_file: salidas/15_analisis_reverificacion.md

consolidar_reporte_reverificacion:
  fase: reverificar
  agent: lider_qa
  context: [planificar_reverificacion, analizar_reverificacion]
  description: >
    Revisa los defectos reabiertos y nuevos con los mismos cinco criterios
    del reporte inicial: pasos reproducibles, esperado y obtenido claros,
    evidencia, severidad justificada y sin duplicados. Incluye en la salida
    solo los aprobados y copia su contenido sin cambios. Si la reentrega fue
    Rechazada o no hay defectos aprobados, responde exactamente: SIN REPORTE.
  expected_output: >
    Solo los defectos aprobados, cada uno exactamente con este bloque y sin
    ningún texto adicional:
    ## BUG-001
    - Historia: [HU-xxx]
    - Escenario Gherkin afectado: [nombre]
    - Severidad: [Crítica / Alta / Media / Baja]
    - Pasos para reproducir: [lista numerada]
    - Resultado esperado: [texto]
    - Resultado obtenido: [texto]
    - Evidencia: [referencia]
    - Versión probada: [versión]
    Si no hay defectos aprobados: la frase exacta "SIN REPORTE".
  output_file: ../intercambio/reporte_qa.md

emitir_dictamen_final:
  fase: reverificar
  agent: lider_qa
  context: [planificar_reverificacion, registrar_reverificacion_junior, analizar_reverificacion, consolidar_reporte_reverificacion]
  description: >
    Dictamen anterior: [ {dictamen_previo} ]. Plan de pruebas con sus
    criterios de salida: [ {plan_pruebas} ]. Emite el dictamen final usando
    solo los resultados registrados. Veredicto general: "Apto para aceptación
    del PO" solo si todos los criterios de salida se cumplen; "No apto" si
    alguno no se cumple o la reentrega fue Rechazada; "Pendiente de
    ejecución" si no hay resultados suficientes. Veredicto por historia:
    Apta, Con defectos abiertos o No validada. Indica los defectos cerrados,
    los abiertos y los retenidos. Si la reentrega fue Rechazada, lista los
    faltantes. No inventes datos.
  expected_output: >
    Markdown con exactamente estas secciones:
    # Dictamen final de calidad
    ## Reentrega
    "Aceptada" o "Rechazada" y los faltantes si los hay.
    ## Veredicto general
    Una línea: "Apto para aceptación del PO", "No apto" o "Pendiente de
    ejecución".
    ## Resultado por historia
    Tabla: HU | Veredicto (Apta / Con defectos abiertos / No validada) |
    Defectos abiertos (por severidad)
    ## Criterios de salida
    Tabla: Criterio | Meta | Resultado | Cumple (Sí / No)
    ## Defectos cerrados (lista o "Ninguno")
    ## Defectos abiertos y retenidos (tabla o "Ninguno")
    ## Riesgos residuales (lista o "Ninguno")
    ## Preguntas para el PO (lista o "Ninguna")
  output_file: ../intercambio/dictamen_qa.md
```

## 7. Interfaz con los demás teams

### Archivos de intercambio

| Archivo en `intercambio/` | Lo produce | Lo consume | Cuándo |
|---|---|---|---|
| `paquete_refinamiento.md` | Team PO (Facilitador) | QA | Refinamiento |
| `historias_finales.md` | Team PO (Analista) | QA | Refinamiento |
| `respuestas_qa.md` | **QA, Líder** (tarea 4) | Team PO (Facilitador) y el propio Líder (tarea 5) | Refinamiento y planificación |
| `historias_refinadas.md` y `backlog_refinado.md` | Team PO | QA | Preparar pruebas |
| `plan_pruebas.md` | **QA, Líder** (tarea 5) | QA (tareas 10, 11, 15, 16, 21); Desarrollo e Infra, de forma informativa | Preparar pruebas |
| `entrega_a_qa.md` | Desarrollo (DevOps) | QA (tareas 10 y 11) | Tras implementar |
| `resultados_ejecucion.md` | **Persona o pipeline** | QA (tareas 12 y 13) | Validación |
| `reporte_qa.md` | **QA, Líder** (tareas 14 y 20) | Desarrollo, Líder (triage) | Validación y reverificación |
| `dictamen_qa.md` | **QA, Líder** (tareas 15 y 21) | Team PO (a futuro) y Desarrollo, informativo | Validación y reverificación |
| `reentrega_a_qa.md` | Desarrollo (DevOps) | QA (tareas 16 y 17) | Corrección |
| `resultados_reverificacion.md` | **Persona o pipeline** | QA (tareas 18 y 19) | Reverificación |

Copia a `intercambio/` los entregables del Team PO con estos nombres: `06_paquete_refinamiento.md` como `paquete_refinamiento.md`, `04_historias_finales.md` como `historias_finales.md`, `08_historias_refinadas.md` como `historias_refinadas.md` y `10_backlog_refinado.md` como `backlog_refinado.md`.

Notas de compatibilidad:

- **Plantilla de `respuestas_qa.md`:** esta versión reemplaza la anterior y le agrega tres campos (`Aportes de QA`, `Automatizable` y `Necesita decisión del PO`). El Team PO la lee como texto, así que no hace falta cambiar nada allí.
- **`reporte_qa.md`:** cuando no hay defectos, QA escribe exactamente `SIN REPORTE`; el Líder de Desarrollo lo interpreta como "no hay defectos que analizar".
- **`plan_pruebas.md`** incluye la sección "Necesidades hacia Desarrollo e Infraestructura". Hoy es informativa; si quieres que Desarrollo la use como entrada, agrégala en sus tareas de planificación y de solicitud a Infraestructura.
- **`dictamen_qa.md`** todavía no tiene consumidor en el Team PO; se conectará cuando se defina la aceptación del sprint.

### Plantilla de resultados (la llena la persona o el pipeline)

Un bloque por caso en `resultados_ejecucion.md` y por defecto o caso en `resultados_reverificacion.md`. Para las pruebas automatizadas usa el ID del caso y como evidencia el reporte del pipeline:

```
## CP-001
- Estado: [Pasó / Falló / Bloqueado]
- Resultado obtenido: [texto]
- Evidencia: [ruta, captura, log o salida del pipeline]
- Ejecutado por: [persona o pipeline]
- Versión probada: [versión]
- Fecha: [fecha]
```

### Plantillas que ya respeta Desarrollo

`reporte_qa.md` usa la plantilla por defecto (BUG-001 con historia, escenario, severidad, pasos, esperado, obtenido, evidencia y versión) que ya consume la tarea de triage del Team Desarrollo.

## 8. Ejecución — `main.py`

```python
import sys
from pathlib import Path

import yaml
from crewai import Agent, Task, Crew, Process, LLM

OLLAMA = "http://localhost:11434"
INTERCAMBIO = Path("../intercambio")

LLMS = {
    "lider_qa": LLM(model="ollama/qwen2.5:14b", base_url=OLLAMA, temperature=0.2),
    "qa_semi_senior": LLM(model="ollama/qwen2.5:14b", base_url=OLLAMA, temperature=0.2),
    "qa_junior": LLM(model="ollama/qwen2.5:7b", base_url=OLLAMA, temperature=0.1),
    "qa_automatizacion": LLM(model="ollama/qwen2.5-coder:14b", base_url=OLLAMA, temperature=0.1),
}

Path("salidas").mkdir(exist_ok=True)
INTERCAMBIO.mkdir(exist_ok=True)


def leer(ruta, defecto="SIN DATO"):
    p = Path(ruta)
    return p.read_text(encoding="utf-8") if p.exists() else defecto


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def construir_crew(fase):
    cfg_agents = cargar("config/agents.yaml")
    cfg_tasks = cargar("config/tasks.yaml")

    agents = {
        key: Agent(
            **cfg,
            llm=LLMS[key],
            allow_delegation=False,
            verbose=True,
            max_iter=4,
        )
        for key, cfg in cfg_agents.items()
    }

    tasks = {}
    for name, cfg in cfg_tasks.items():
        if cfg.get("fase") != fase:
            continue
        tasks[name] = Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=agents[cfg["agent"]],
            context=[tasks[c] for c in cfg.get("context", []) if c in tasks],
            output_file=cfg.get("output_file"),
        )

    return Crew(
        agents=list(agents.values()),
        tasks=list(tasks.values()),
        process=Process.sequential,
        verbose=True,
    )


FASES = (
    "refinamiento",
    "preparar",
    "preparar_ejecucion",
    "validar",
    "preparar_reverificacion",
    "reverificar",
)

if len(sys.argv) < 2 or sys.argv[1] not in FASES:
    sys.exit("Uso: python main.py [" + " | ".join(FASES) + "]")

FASE = sys.argv[1]

inputs = {
    "max_historias": "3",
    "paquete_refinamiento": leer(INTERCAMBIO / "paquete_refinamiento.md", "SIN PAQUETE"),
    "historias_finales": leer(INTERCAMBIO / "historias_finales.md", "SIN HISTORIAS"),
    "historias_refinadas": leer(INTERCAMBIO / "historias_refinadas.md", "SIN HISTORIAS REFINADAS"),
    "backlog_refinado": leer(INTERCAMBIO / "backlog_refinado.md", "SIN BACKLOG"),
    "respuestas_qa": leer(INTERCAMBIO / "respuestas_qa.md"),
    "plan_pruebas": leer(INTERCAMBIO / "plan_pruebas.md"),
    "entrega_qa": leer(INTERCAMBIO / "entrega_a_qa.md", "SIN ENTREGA"),
    "reentrega_qa": leer(INTERCAMBIO / "reentrega_a_qa.md", "SIN REENTREGA"),
    "resultados_ejecucion": leer(INTERCAMBIO / "resultados_ejecucion.md", "SIN RESULTADOS"),
    "resultados_reverificacion": leer(INTERCAMBIO / "resultados_reverificacion.md", "SIN RESULTADOS"),
    "reporte_previo": leer(INTERCAMBIO / "reporte_qa.md", "SIN REPORTE"),
    "dictamen_previo": leer(INTERCAMBIO / "dictamen_qa.md", "SIN DICTAMEN PREVIO"),
    "casos_semi_senior": leer("salidas/04_casos_semi_senior.md"),
    "casos_junior": leer("salidas/05_casos_junior.md"),
    "revision_casos": leer("salidas/06_revision_casos.md", "SIN PENDIENTES PREVIOS"),
    "estrategia_automatizacion": leer("salidas/07_estrategia_automatizacion.md"),
    "hoja_ejecucion": leer("salidas/08_hoja_ejecucion.md"),
    "salida_automatizacion": leer("salidas/09_automatizacion.md"),
}

print(construir_crew(FASE).kickoff(inputs=inputs))
```

## 9. Ajustes para modelos locales

- **Los agentes no ejecutan:** no les pidas resultados de pruebas. Las personas o el pipeline ejecutan, y los resultados entran por `resultados_ejecucion.md` y `resultados_reverificacion.md`. Las tareas están escritas para responder "No ejecutado" ante la falta de datos.
- **Delegación:** déjala apagada en los 4 agentes (`allow_delegation=False`). El Líder delega con el plan de pruebas; la delegación dinámica de CrewAI con modelos locales pequeños suele ser inestable.
- **Contexto:** sube el contexto de Ollama a 8192 como mínimo y a 16384 en las fases de preparar pruebas y validar (`OLLAMA_CONTEXT_LENGTH=16384` o `PARAMETER num_ctx` en un Modelfile). Los casos, los scripts y los resultados ocupan mucho.
- **Pocas historias por corrida:** `max_historias` en 3 mantiene manejable el plan y los casos. Usa el mismo valor que en el Team Desarrollo, para que ambos teams trabajen las mismas historias.
- **Refinamiento independiente:** las tareas 1, 2 y 3 no comparten contexto a propósito. No les agregues `context`: perderías la diversidad de puntos de vista.
- **Temperatura baja** (0.1-0.2) para que respeten los formatos y las plantillas.
- **`max_iter=4`** evita que un agente se quede dando vueltas.
- **Frases exactas:** "Sin asignaciones", "Sin ejecución: entrega rechazada" y "SIN REPORTE" mantienen el flujo estable porque las tareas siguientes las leen sin romperse.
- **Criterios de salida:** los valores por defecto (100% de humo, 0 defectos Críticos o Altos abiertos, 100% de casos de prioridad Alta ejecutados) son ajustables en la tarea 5.
- **Herramientas para ejecutar:** si más adelante quieres que los agentes ejecuten pruebas, hay herramientas de CrewAI para correr comandos que puedes asignarle al QA Automatización; hasta entonces, la ejecución sigue siendo externa.
- **Si un modelo se sale del formato:** sube al modelo más grande de su familia antes de tocar los prompts.
- **Memoria:** déjala apagada (`memory=False`, el valor por defecto); los entregables ya viajan por `context` y por los archivos de `salidas/` e `intercambio/`.
- **RAM/VRAM aproximada:** modelos de 14B necesitan unos 16 GB y los de 7B unos 8 GB. Si no te alcanza, usa `qwen2.5:7b` y `qwen2.5-coder:7b` para todos.
