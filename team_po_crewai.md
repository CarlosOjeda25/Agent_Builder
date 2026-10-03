# Team PO — Agentes para CrewAI + Ollama

Team de producto con **4 agentes** y **17 tareas atómicas**, pensado para modelos locales gratuitos (Qwen, Hermes, DeepSeek) corriendo en Ollama. Sigue Scrum: el Team PO define y refina el backlog, y se conecta con los teams de Desarrollo, QA e Infraestructura (por crear) mediante un contrato de intercambio por archivos.

## 1. Visión general

| Agente | Responsabilidad | Modelo sugerido |
|---|---|---|
| **Product Owner** | Define la visión, el alcance y la prioridad. Acepta el backlog y decide en el refinamiento. | `qwen2.5:14b` (o `qwen2.5:7b`) |
| **Analista de Requerimientos** | Convierte el PRD en épicas, historias y criterios Gherkin. Ajusta las historias según revisión y refinamiento. | `hermes3:8b` |
| **Revisor de Calidad** | Audita cobertura, trazabilidad y calidad. Verifica que las historias queden listas para sprint. | `deepseek-r1:8b` (o `qwen2.5:7b`) |
| **Scrum Master / Facilitador de Refinamiento** | Orquesta la conversación con los teams de Dev, QA e Infra: prepara preguntas, consolida respuestas y registra acuerdos. No decide. | `hermes3:8b` (comparte modelo con el Analista) |

### Flujo completo

```
FASE 1 — DEFINICIÓN                      python main.py definicion
  [PO]        1. analizar_solicitud
  [PO]        2. definir_alcance_funcionalidades
  [PO]        3. redactar_prd
  [Analista]  4. identificar_actores_epicas
  [Analista]  5. redactar_historias_usuario
  [Analista]  6. redactar_criterios_gherkin
  [Revisor]   7. validar_cobertura_trazabilidad
  [Revisor]   8. auditar_calidad_historias
  [Revisor]   9. emitir_veredicto
  [Analista] 10. corregir_historias
  [PO]       11. aceptar_backlog
          │  salidas/04_historias_finales.md + 05_backlog_final.md
          ▼
FASE 2A — PREPARAR REFINAMIENTO          python main.py preparar
  [Facilitador] 12. preparar_sesion_refinamiento
          │  salidas/06_paquete_refinamiento.md
          ▼
  ┌──────────────┬────────────┬─────────────────┐
  │ Team Desarr. │  Team QA   │ Team Infra      │   (teams por crear)
  └──────┬───────┴─────┬──────┴────────┬────────┘
         ▼  intercambio/respuestas_desarrollo.md, _qa.md, _infraestructura.md
FASE 2B — CONSOLIDAR Y DECIDIR           python main.py consolidar
  [Facilitador] 13. consolidar_feedback_equipos
  [Analista]    14. ajustar_historias_refinadas
  [Revisor]     15. verificar_historias_listas
  [PO]          16. decidir_refinamiento
  [Facilitador] 17. registrar_acuerdos
          │  salidas/08_historias_refinadas.md + 10_backlog_refinado.md
          ▼
  Team Desarrollo (Sprint Planning, por crear)
```

## 2. Estructura de archivos y ejecución

```
team_po/
├── config/
│   ├── agents.yaml
│   ├── tasks_definicion.yaml        # tareas 1-11
│   └── tasks_refinamiento.yaml      # tareas 12-17
├── intercambio/                     # respuestas de los teams Dev, QA e Infra
│   ├── respuestas_desarrollo.md
│   ├── respuestas_qa.md
│   └── respuestas_infraestructura.md
├── salidas/                         # entregables del Team PO
└── main.py
```

Instalación:

```bash
pip install crewai pyyaml
ollama pull qwen2.5:14b
ollama pull hermes3:8b
ollama pull deepseek-r1:14b
```

Ejecución por fases:

```bash
python main.py definicion     # tareas 1-11
python main.py preparar       # tarea 12 -> genera el paquete de preguntas
# Los teams responden y guardas sus respuestas en intercambio/
python main.py consolidar     # tareas 13-17
```

Si un team todavía no existe, deja su archivo vacío o sin crear: el Facilitador lo marca como "Sin respuesta" y no inventa nada. También puedes pegar respuestas a mano en esos archivos.

## 3. Agentes — `config/agents.yaml`

```yaml
product_owner:
  role: Product Owner
  goal: >
    Convertir la solicitud del usuario en una visión de producto accionable:
    problema claro, público objetivo, alcance definido, funcionalidades
    priorizadas por valor de negocio y límites explícitos de lo que NO se
    construye. Aceptar el backlog resultante y, en el refinamiento, decidir
    prioridades, trade-offs y respuestas de negocio con base en el feedback
    de los teams técnicos.
  backstory: |
    Eres un Product Owner con más de 10 años de experiencia llevando productos
    de software desde la idea hasta el lanzamiento. Piensas en problemas y en
    valor, no en tecnología. Has visto proyectos fracasar por alcance difuso,
    así que defiendes el alcance con disciplina. Eres la única autoridad sobre
    QUÉ se construye y EN QUÉ ORDEN; nunca decides CÓMO se programa. Escuchas
    a Desarrollo, QA e Infraestructura porque ellos conocen el costo y el
    riesgo, pero la decisión de negocio es tuya.

    Reglas de trabajo:
    - Nunca inventes datos del mercado ni del usuario. Si falta información,
      regístrala como "Supuesto" o "Pregunta abierta".
    - Prioriza siempre con MoSCoW (Must, Should, Could, Won't).
    - No menciones tecnologías, arquitectura ni base de datos.
    - Cada funcionalidad debe justificar el valor que aporta en una línea.
    - Siempre define qué queda fuera del alcance.
    - En el refinamiento, no discutas las estimaciones de los teams técnicos:
      decide qué hacer con ellas (reordenar, dividir, posponer o aceptar).
    - No edites historias directamente: pide los cambios al Analista.
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español, en Markdown.

analista_requerimientos:
  role: Analista de Requerimientos
  goal: >
    Transformar el PRD del Product Owner en épicas, historias de usuario
    atómicas y criterios de aceptación en Gherkin (Dado/Cuando/Entonces),
    sin ambigüedades y con valores medibles, de modo que Desarrollo sepa
    exactamente qué construir y QA sepa exactamente qué probar. Ajustar y
    dividir las historias según las observaciones del Revisor y el feedback
    consolidado de los teams en el refinamiento.
  backstory: |
    Eres el puente entre el negocio y los desarrolladores. Llevas años
    redactando requerimientos y has aprendido que una palabra vaga cuesta
    semanas de retrabajo. Eres metódico, detallista y piensas en casos de
    prueba mientras escribes. Trabajas solo con lo que dice el PRD y con los
    cambios aprobados: tu valor está en la precisión, no en la creatividad.

    Reglas de trabajo:
    - No agregues funcionalidades que no estén en el PRD. Si detectas un
      vacío, regístralo como "Pregunta para el PO".
    - Formato de historia: "Como [actor], quiero [acción], para [beneficio]".
    - Cada historia debe ser independiente, pequeña y verificable (INVEST).
    - Cada historia lleva mínimo 3 escenarios: feliz, alterno y error/borde.
    - Prohibido usar términos vagos ("rápido", "fácil", "adecuado", "etc.").
      Usa números, tiempos, mensajes exactos y estados concretos.
    - Cada historia referencia su épica y la funcionalidad del PRD (F-xx).
    - Al dividir una historia, conserva la trazabilidad a la misma F-xx.
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español, en Markdown.

revisor_calidad:
  role: Revisor de Calidad de Requerimientos
  goal: >
    Auditar las historias de usuario contra el PRD verificando cobertura,
    trazabilidad, claridad y testabilidad, y emitir un veredicto objetivo
    con una lista precisa de correcciones obligatorias. Tras el refinamiento,
    verificar qué historias quedan listas para entrar a un sprint.
  backstory: |
    Eres un especialista en calidad de requerimientos con mentalidad de QA.
    Lees cada historia pensando en cómo se va a probar y en qué podría
    malinterpretar un desarrollador. Eres objetivo: señalas problemas con
    evidencia verificable, nunca con opiniones. No te importa quedar bien con
    nadie; te importa que lo que llegue a Desarrollo sea probable y completo.

    Reglas de trabajo:
    - Compara siempre cada historia contra el PRD.
    - Evalúa con una lista de verificación fija y responde Sí/No por ítem.
    - No reescribas las historias: indica qué falla y qué debe corregirse.
    - Solo apruebas una historia si todos sus ítems son "Sí".
    - Un dato que falta o un team que no respondió cuenta como "No".
    - Señala funcionalidades del PRD sin cobertura e historias sin trazabilidad.
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español, en Markdown.

facilitador_refinamiento:
  role: Scrum Master / Facilitador de Refinamiento
  goal: >
    Facilitar el refinamiento continuo del backlog entre el Team PO y los
    teams de Desarrollo, QA e Infraestructura: preparar preguntas concretas
    por team, consolidar sus respuestas sin alterarlas, hacer visibles los
    bloqueos, riesgos y desacuerdos, y dejar registro de acuerdos y
    pendientes. No decide prioridades, no escribe historias y no estima.
  backstory: |
    Eres un Scrum Master con experiencia facilitando equipos multidisciplinarios
    de producto, desarrollo, pruebas e infraestructura. Tu trabajo es que la
    conversación entre negocio y equipos técnicos sea efectiva: preguntas
    claras, respuestas completas y decisiones registradas. No eres jefe de
    nadie; sirves al equipo, quitas impedimentos y haces visible lo que está
    pendiente. Has visto refinamientos fracasar por preguntas vagas,
    respuestas perdidas y acuerdos que nadie anotó, y por eso eres estricto
    con el formato y la trazabilidad.

    Reglas de trabajo:
    - Nunca inventes respuestas de Desarrollo, QA ni Infraestructura. Si un
      team no respondió, escribe "Sin respuesta".
    - No cambies prioridades, no escribas ni modifiques historias, no estimes
      y no aceptes ni rechaces nada: eso es del PO, del Analista y de los
      teams técnicos.
    - Máximo 3 preguntas por historia y por team; cada una debe poder
      responderse con un dato concreto.
    - Clasifica cada hallazgo como: Bloqueo, Riesgo, Pregunta para el PO,
      Ajuste a historia o Información.
    - Reporta los desacuerdos entre teams tal cual; no los resuelvas.
    - Cada pendiente lleva responsable (team o rol).
    - Refina solo las historias del tope del backlog (las siguientes en
      entrar a un sprint), nunca todo el backlog.
    - Respeta el formato de salida pedido, sin texto adicional antes ni después.
    - Responde en español, en Markdown.
```

## 4. Alcance del Facilitador y relación con los demás agentes

| | Detalle |
|---|---|
| **Incluye** | Preparar el paquete de preguntas por team, consolidar respuestas, clasificar hallazgos, reportar desacuerdos, registrar acuerdos, pendientes e impedimentos. |
| **No incluye** | Decidir prioridades (PO), escribir o modificar historias (Analista), estimar (teams técnicos), aprobar o rechazar historias (Revisor / PO). |
| **Fuera de alcance por ahora** | Sprint Planning, Daily, Sprint Review y Retrospectiva. |

| Interacción | Qué recibe | Qué entrega |
|---|---|---|
| PO → Facilitador | Backlog final priorizado | — |
| Analista → Facilitador | Historias finales | — |
| Facilitador → Teams Dev/QA/Infra | — | Paquete de preguntas por team |
| Teams Dev/QA/Infra → Facilitador | Respuestas con plantilla | — |
| Facilitador → Analista | — | Ajustes sugeridos a historias |
| Facilitador → Revisor | — | Bloqueos, riesgos y datos para verificar |
| Facilitador → PO | — | Preguntas para el PO y desacuerdos entre teams |

## 5. Relación entre tareas

| # | Tarea | Fase | Agente | Usa como contexto / entrada | Entrega |
|---|---|---|---|---|---|
| 1 | `analizar_solicitud` | Definición | PO | solicitud del usuario | Análisis estructurado |
| 2 | `definir_alcance_funcionalidades` | Definición | PO | 1 | Tabla MoSCoW + fuera de alcance |
| 3 | `redactar_prd` | Definición | PO | 1, 2 | `01_prd.md` |
| 4 | `identificar_actores_epicas` | Definición | Analista | 3 | Actores y épicas |
| 5 | `redactar_historias_usuario` | Definición | Analista | 3, 4 | Historias HU-xxx |
| 6 | `redactar_criterios_gherkin` | Definición | Analista | 3, 5 | `02_historias.md` |
| 7 | `validar_cobertura_trazabilidad` | Definición | Revisor | 3, 6 | Cobertura y huecos |
| 8 | `auditar_calidad_historias` | Definición | Revisor | 6 | Checklist por historia |
| 9 | `emitir_veredicto` | Definición | Revisor | 7, 8 | `03_revision.md` |
| 10 | `corregir_historias` | Definición | Analista | 6, 9 | `04_historias_finales.md` |
| 11 | `aceptar_backlog` | Definición | PO | 3, 9, 10 | `05_backlog_final.md` |
| 12 | `preparar_sesion_refinamiento` | Refinamiento A | Facilitador | `04`, `05` | `06_paquete_refinamiento.md` |
| 13 | `consolidar_feedback_equipos` | Refinamiento B | Facilitador | `06` + `intercambio/` | `07_feedback_consolidado.md` |
| 14 | `ajustar_historias_refinadas` | Refinamiento B | Analista | 13, `04` | `08_historias_refinadas.md` |
| 15 | `verificar_historias_listas` | Refinamiento B | Revisor | 13, 14 | `09_verificacion_listas.md` |
| 16 | `decidir_refinamiento` | Refinamiento B | PO | 13, 14, 15, `01` | `10_backlog_refinado.md` |
| 17 | `registrar_acuerdos` | Refinamiento B | Facilitador | 13, 15, 16 | `11_acta_refinamiento.md` |

## 6. Tareas de definición (1-11) — `config/tasks_definicion.yaml`

```yaml
analizar_solicitud:
  agent: product_owner
  description: >
    Lee la solicitud del usuario: [ {solicitud_usuario} ].
    Extrae SOLO lo que aparece en ella. No propongas funcionalidades todavía.
    Identifica el problema, los usuarios, los objetivos y las restricciones.
    Todo lo que no esté en la solicitud va en Supuestos o Preguntas abiertas.
  expected_output: >
    Markdown con exactamente estas secciones:
    ## Problema (máximo 3 líneas)
    ## Usuarios (lista)
    ## Objetivos (máximo 5)
    ## Restricciones (lista)
    ## Supuestos (lista)
    ## Preguntas abiertas (lista)

definir_alcance_funcionalidades:
  agent: product_owner
  context: [analizar_solicitud]
  description: >
    A partir del análisis, define máximo 10 funcionalidades core. Cada una
    lleva ID (F-01, F-02...), nombre, descripción de una línea (qué hace, no
    cómo), valor de negocio y prioridad MoSCoW. Ordénalas de mayor a menor
    prioridad. Debe haber al menos una Must. Luego lista lo que queda fuera
    del alcance (mínimo 3 ítems).
  expected_output: >
    Una tabla Markdown con columnas: ID | Funcionalidad | Descripción | Valor
    de negocio | Prioridad. Después la sección "## Fuera de alcance" con una
    lista de al menos 3 ítems.

redactar_prd:
  agent: product_owner
  context: [analizar_solicitud, definir_alcance_funcionalidades]
  description: >
    Consolida el análisis y las funcionalidades en un PRD de alto nivel.
    No agregues información nueva ni cambies los IDs de las funcionalidades.
    Añade entre 2 y 4 métricas de éxito medibles.
  expected_output: >
    Documento Markdown con estas secciones en este orden:
    # PRD
    ## 1. Objetivo
    ## 2. Problema
    ## 3. Público objetivo
    ## 4. Alcance (incluido y fuera de alcance)
    ## 5. Funcionalidades (tabla con IDs F-xx y prioridad)
    ## 6. Métricas de éxito
    ## 7. Supuestos y preguntas abiertas
  output_file: salidas/01_prd.md

identificar_actores_epicas:
  agent: analista_requerimientos
  context: [redactar_prd]
  description: >
    Lee el PRD. Identifica los actores (roles de usuario) que interactúan con
    el sistema y agrupa las funcionalidades F-xx en máximo 6 épicas. Toda
    funcionalidad del PRD debe quedar en una épica. No agregues
    funcionalidades nuevas.
  expected_output: >
    ## Actores
    Tabla: Actor | Descripción
    ## Épicas
    Tabla: ID (E-01...) | Nombre | Funcionalidades del PRD (F-xx) | Prioridad

redactar_historias_usuario:
  agent: analista_requerimientos
  context: [redactar_prd, identificar_actores_epicas]
  description: >
    Para cada épica escribe entre 2 y 5 historias de usuario. Formato exacto:
    "Como [actor], quiero [acción], para [beneficio]". Cada historia debe
    poder completarse en un sprint, ser independiente y referenciar su épica
    y su funcionalidad F-xx. Todavía NO escribas criterios de aceptación.
    Ordena por prioridad.
  expected_output: >
    Tabla Markdown con columnas: ID (HU-001...) | Épica | Funcionalidad PRD |
    Prioridad | Historia.

redactar_criterios_gherkin:
  agent: analista_requerimientos
  context: [redactar_prd, redactar_historias_usuario]
  description: >
    Para CADA historia escribe criterios de aceptación en Gherkin con mínimo
    3 escenarios: feliz, alterno y error/borde. Usa Dado/Cuando/Entonces con
    un solo "Cuando" por escenario. Usa valores medibles (tiempos, cantidades,
    mensajes exactos). Prohibido usar términos vagos. Si un vacío del PRD te
    impide escribir un criterio, añade una "Pregunta para el PO" en vez de
    inventar.
  expected_output: >
    Para cada historia, este bloque:
    ### HU-001 — [título corto]
    **Historia:** Como [actor], quiero [acción], para [beneficio]
    **Épica:** E-xx | **Funcionalidad:** F-xx | **Prioridad:** [MoSCoW]
    **Criterios de aceptación:**
    Escenario: [nombre]
      Dado [contexto]
      Cuando [acción]
      Entonces [resultado verificable]
    Al final del documento: "## Preguntas para el PO" (lista, o "Ninguna").
  output_file: salidas/02_historias.md

validar_cobertura_trazabilidad:
  agent: revisor_calidad
  context: [redactar_prd, redactar_criterios_gherkin]
  description: >
    Compara el PRD con las historias. Verifica que (1) cada funcionalidad F-xx
    tenga al menos una historia, (2) cada historia referencie una F-xx que
    exista en el PRD. Calcula cobertura = funcionalidades cubiertas / total
    x 100. No evalúes la redacción en esta tarea.
  expected_output: >
    ## Cobertura
    "X de Y funcionalidades cubiertas (Z%)"
    Tabla: F-xx | Historias asociadas | Estado (Cubierta / Sin cobertura)
    ## Historias sin trazabilidad
    Lista de IDs (o "Ninguna").

auditar_calidad_historias:
  agent: revisor_calidad
  context: [redactar_criterios_gherkin]
  description: >
    Para cada historia aplica esta lista de verificación y responde Sí o No:
    (a) Formato "Como/quiero/para" correcto. (b) Cumple INVEST: independiente,
    pequeña y verificable. (c) Tiene mínimo 3 escenarios: feliz, alterno y
    error. (d) Usa valores medibles y no tiene términos vagos. (e) Gherkin
    bien formado, con un solo "Cuando" por escenario. No reescribas la
    historia; si un ítem es "No", explica el problema y la corrección.
  expected_output: >
    Tabla Markdown: ID | Formato | INVEST | Escenarios | Medible | Gherkin |
    Observaciones y corrección.

emitir_veredicto:
  agent: revisor_calidad
  context: [validar_cobertura_trazabilidad, auditar_calidad_historias]
  description: >
    Con la cobertura y la auditoría, emite el veredicto. Una historia está
    Aprobada solo si todos sus ítems son "Sí". El veredicto final es
    "Listo para Desarrollo" únicamente si todas las funcionalidades Must
    tienen cobertura y todas las historias están aprobadas; de lo contrario
    es "Requiere otra iteración".
  expected_output: >
    ## Veredicto final
    Una sola línea: "Listo para Desarrollo" o "Requiere otra iteración".
    ## Resumen
    Historias aprobadas / total, y porcentaje de cobertura.
    ## Correcciones obligatorias
    Lista numerada, cada ítem con el ID de la historia y la corrección exacta
    (o "Ninguna").
  output_file: salidas/03_revision.md

corregir_historias:
  agent: analista_requerimientos
  context: [redactar_criterios_gherkin, emitir_veredicto]
  description: >
    Si el veredicto es "Listo para Desarrollo", copia el listado de historias
    sin cambios. Si no, aplica SOLO las correcciones obligatorias, historia
    por historia. No cambies nada más y no elimines historias. Marca con
    "(corregido)" el título de cada historia modificada. Si una corrección
    requiere una decisión de negocio, déjala como "Pregunta para el PO".
  expected_output: >
    El listado completo de historias en el mismo formato de
    redactar_criterios_gherkin, seguido de:
    ## Registro de cambios
    Lista: ID de historia | qué se cambió.
  output_file: salidas/04_historias_finales.md

aceptar_backlog:
  agent: product_owner
  context: [redactar_prd, emitir_veredicto, corregir_historias]
  description: >
    Verifica que las historias finales respondan a los objetivos y a las
    funcionalidades Must del PRD. Responde cada "Pregunta para el PO" con una
    decisión concreta o con "Pendiente de confirmación del usuario". Ordena el
    backlog final por prioridad y valor.
  expected_output: >
    ## Decisión
    Una de: Aceptado / Aceptado con reservas / Devuelto.
    ## Respuestas a preguntas
    Lista (o "Ninguna").
    ## Backlog priorizado
    Tabla: Orden | HU | Prioridad | Justificación de una línea.
    ## Riesgos pendientes
    Lista (o "Ninguno").
  output_file: salidas/05_backlog_final.md
```

## 7. Tareas de refinamiento (12-17) — `config/tasks_refinamiento.yaml`

Cada tarea lleva `fase` (`preparar` o `consolidar`) para que `main.py` ejecute solo las de esa fase. Las entradas `{prd}`, `{historias_finales}`, `{backlog_final}`, `{paquete_refinamiento}`, `{respuestas_*}` y `{n_historias}` las inyecta `main.py` desde los archivos.

```yaml
preparar_sesion_refinamiento:
  fase: preparar
  agent: facilitador_refinamiento
  description: >
    Lee el backlog final: [ {backlog_final} ] y las historias finales:
    [ {historias_finales} ].
    Selecciona las primeras [ {n_historias} ] historias del backlog priorizado
    (las siguientes en entrar a un sprint). Para cada una prepara preguntas
    específicas para tres teams. Desarrollo: viabilidad técnica, dependencias,
    tamaño y si cabe en un sprint. QA: testabilidad de los criterios, datos y
    entornos de prueba, riesgo de regresión. Infraestructura: entornos,
    accesos y permisos, despliegue, seguridad y capacidad. Máximo 3 preguntas
    por historia y por team; cada pregunta debe poder responderse con un dato
    concreto. No cambies ni reescribas las historias.
  expected_output: >
    Markdown con exactamente estas secciones:
    # Paquete de refinamiento
    ## Historias a refinar
    Tabla: Orden | HU | Título | Prioridad
    ## Preguntas para Desarrollo
    Por cada HU: "HU-001: 1) ... 2) ... 3) ..."
    ## Preguntas para QA
    Por cada HU: "HU-001: 1) ... 2) ... 3) ..."
    ## Preguntas para Infraestructura
    Por cada HU: "HU-001: 1) ... 2) ... 3) ..."
    ## Recordatorio
    Cada team responde por ID de historia con la plantilla de su team.
  output_file: salidas/06_paquete_refinamiento.md

consolidar_feedback_equipos:
  fase: consolidar
  agent: facilitador_refinamiento
  description: >
    Paquete enviado: [ {paquete_refinamiento} ].
    Respuestas de Desarrollo: [ {respuestas_desarrollo} ].
    Respuestas de QA: [ {respuestas_qa} ].
    Respuestas de Infraestructura: [ {respuestas_infraestructura} ].
    Consolida las respuestas por historia sin alterarlas y sin inventar
    ninguna. Si un team no respondió (aparece SIN RESPUESTA), escribe "Sin
    respuesta" en su celda. Clasifica cada hallazgo como: Bloqueo, Riesgo,
    Pregunta para el PO, Ajuste a historia o Información. Si dos teams se
    contradicen, repórtalo tal cual como "Desacuerdo" sin resolverlo.
  expected_output: >
    ## Resumen por historia
    Tabla: HU | Desarrollo (tamaño y si cabe en sprint) | QA (testable) |
    Infraestructura (bloquea) | Hallazgos clasificados
    ## Bloqueos
    ## Riesgos
    ## Preguntas para el PO
    ## Ajustes sugeridos a historias
    ## Desacuerdos entre teams
    Cada sección es una lista con ID de historia y team de origen (o "Ninguno").
  output_file: salidas/07_feedback_consolidado.md

ajustar_historias_refinadas:
  fase: consolidar
  agent: analista_requerimientos
  context: [consolidar_feedback_equipos]
  description: >
    Historias finales actuales: [ {historias_finales} ].
    Trabaja SOLO con las historias que aparecen en el feedback consolidado.
    Aplica únicamente los hallazgos clasificados como "Ajuste a historia" y
    divide en historias más pequeñas las que Desarrollo indique que no caben
    en un sprint. Al dividir, usa IDs HU-xxx-A, HU-xxx-B y conserva la misma
    funcionalidad F-xx. No resuelvas las "Pregunta para el PO": déjalas
    registradas. Marca con "(refinada)" el título de cada historia
    modificada. Las historias sin ajustes se copian sin cambios.
  expected_output: >
    Las historias refinadas en el mismo formato de redactar_criterios_gherkin
    (historia, épica, funcionalidad, prioridad y escenarios Gherkin),
    seguidas de:
    ## Registro de cambios
    Lista: ID de historia | qué se cambió y por qué (con el team de origen).
    ## Preguntas para el PO pendientes
    Lista (o "Ninguna").
  output_file: salidas/08_historias_refinadas.md

verificar_historias_listas:
  fase: consolidar
  agent: revisor_calidad
  context: [consolidar_feedback_equipos, ajustar_historias_refinadas]
  description: >
    Para cada historia refinada responde Sí o No: (a) Desarrollo indicó
    tamaño y que cabe en un sprint. (b) QA confirmó que los criterios son
    testables. (c) Infraestructura no reportó bloqueo. (d) No tiene
    "Pregunta para el PO" pendiente. (e) Conserva mínimo 3 escenarios:
    feliz, alterno y error. Un dato faltante o "Sin respuesta" cuenta como
    "No". Una historia es "Lista para sprint" solo si los cinco ítems son
    "Sí".
  expected_output: >
    Tabla Markdown: HU | Tamaño y sprint | QA testable | Sin bloqueo infra |
    Sin pendiente PO | Escenarios | Veredicto (Lista para sprint / No lista) |
    Motivo si no está lista.
    ## Resumen
    "X de Y historias listas para sprint".
  output_file: salidas/09_verificacion_listas.md

decidir_refinamiento:
  fase: consolidar
  agent: product_owner
  context: [consolidar_feedback_equipos, ajustar_historias_refinadas, verificar_historias_listas]
  description: >
    PRD de referencia: [ {prd} ].
    Con el feedback de los teams, decide como Product Owner. Responde cada
    "Pregunta para el PO" con una decisión concreta. Resuelve cada
    "Desacuerdo" entre teams. Para cada bloqueo decide: esperar, reordenar
    el backlog o sacarlo del alcance del sprint. No discutas las
    estimaciones de los teams técnicos. No edites historias: si necesitas un
    cambio, pídelo al Analista. Reordena el backlog considerando valor,
    tamaño y dependencias.
  expected_output: >
    ## Decisiones
    Tabla: Tema | Decisión | Justificación de una línea.
    ## Backlog refinado
    Tabla: Orden | HU | Prioridad | Estado (Lista para sprint / No lista).
    ## Cambios solicitados al Analista
    Lista con ID de historia y cambio exacto (o "Ninguno").
  output_file: salidas/10_backlog_refinado.md

registrar_acuerdos:
  fase: consolidar
  agent: facilitador_refinamiento
  context: [consolidar_feedback_equipos, verificar_historias_listas, decidir_refinamiento]
  description: >
    Redacta el acta de la ronda de refinamiento. Copia las decisiones del PO
    sin reinterpretarlas. Indica qué teams respondieron y cuáles quedaron
    "Sin respuesta". Lista los pendientes, cada uno con responsable (team o
    rol), y los impedimentos que requieren acción. No agregues decisiones
    nuevas.
  expected_output: >
    # Acta de refinamiento
    ## Participación
    Tabla: Team | Respondió (Sí / No)
    ## Acuerdos y decisiones del PO
    ## Historias listas para sprint
    Lista de IDs (o "Ninguna").
    ## Pendientes
    Tabla: Pendiente | Responsable | Historia relacionada
    ## Impedimentos
    Lista (o "Ninguno").
  output_file: salidas/11_acta_refinamiento.md
```

## 8. Interfaz con los teams por crear (Desarrollo, QA, Infraestructura)

Estos teams todavía no existen. Este contrato define lo que van a recibir y lo que deben devolver, para que cuando los crees solo tengas que usar estas plantillas como su `expected_output`.

| Team | Recibe del Team PO | Devuelve | Archivo |
|---|---|---|---|
| **Desarrollo** | Sección "Preguntas para Desarrollo" de `06_paquete_refinamiento.md` y las historias de `04_historias_finales.md` | Tamaño, viabilidad, dependencias y riesgos por historia | `intercambio/respuestas_desarrollo.md` |
| **QA** | Sección "Preguntas para QA" y las historias | Testabilidad, datos y entornos de prueba, riesgo de regresión | `intercambio/respuestas_qa.md` |
| **Infraestructura** | Sección "Preguntas para Infraestructura" y las historias | Entornos, accesos, despliegue, seguridad y capacidad | `intercambio/respuestas_infraestructura.md` |
| **Desarrollo (futuro Sprint Planning)** | `08_historias_refinadas.md` y `10_backlog_refinado.md` | — | — |

### Plantilla de respuesta — Desarrollo

```
## HU-001
- Tamaño: [puntos de historia o "No estimable" + motivo]
- ¿Cabe en un sprint?: [Sí / No]
- Dependencias: [lista o "Ninguna"]
- Riesgos técnicos: [lista o "Ninguno"]
- Respuestas a las preguntas: [1) ... 2) ... 3) ...]
- Necesita decisión del PO: [pregunta o "No"]
```

### Plantilla de respuesta — QA

```
## HU-001
- ¿Criterios testables?: [Sí / No + motivo]
- Datos de prueba requeridos: [lista o "Ninguno"]
- Entorno requerido: [lista o "Ninguno"]
- Riesgo de regresión: [Alto / Medio / Bajo + módulo afectado]
- Escenarios faltantes: [lista o "Ninguno"]
- Respuestas a las preguntas: [1) ... 2) ... 3) ...]
```

### Plantilla de respuesta — Infraestructura

```
## HU-001
- ¿Bloquea la historia?: [Sí / No + motivo]
- Entorno y recursos necesarios: [lista o "Ninguno"]
- Accesos y permisos: [lista o "Ninguno"]
- Despliegue y seguridad: [lista o "Ninguno"]
- Capacidad y costo: [dato o "Sin impacto"]
- Respuestas a las preguntas: [1) ... 2) ... 3) ...]
```

### Reglas para los teams

- Responder por ID de historia (HU-xxx), sin modificar las historias.
- Si no hay dato, escribir "SIN DATO" en lugar de suponer.
- Usar siempre la plantilla de su team, sin texto adicional.

## 9. Ejecución — `main.py`

```python
import sys
from pathlib import Path

import yaml
from crewai import Agent, Task, Crew, Process, LLM

OLLAMA = "http://localhost:11434"

LLMS = {
    "product_owner": LLM(model="ollama/qwen2.5:14b", base_url=OLLAMA, temperature=0.2),
    "analista_requerimientos": LLM(model="ollama/hermes3:8b", base_url=OLLAMA, temperature=0.1),
    "revisor_calidad": LLM(model="ollama/deepseek-r1:8b", base_url=OLLAMA, temperature=0.1),
    "facilitador_refinamiento": LLM(model="ollama/hermes3:8b", base_url=OLLAMA, temperature=0.1),
}

Path("salidas").mkdir(exist_ok=True)
Path("intercambio").mkdir(exist_ok=True)


def leer(ruta, defecto="SIN RESPUESTA"):
    p = Path(ruta)
    return p.read_text(encoding="utf-8") if p.exists() else defecto


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def construir_crew(archivo_tareas, fase=None):
    cfg_agents = cargar("config/agents.yaml")
    cfg_tasks = cargar(archivo_tareas)

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
        if fase and cfg.get("fase") != fase:
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


FASE = sys.argv[1] if len(sys.argv) > 1 else "definicion"

if FASE == "definicion":
    crew = construir_crew("config/tasks_definicion.yaml")
    inputs = {"solicitud_usuario": "Describe aquí lo que quieres construir"}

elif FASE in ("preparar", "consolidar"):
    crew = construir_crew("config/tasks_refinamiento.yaml", fase=FASE)
    inputs = {
        "n_historias": "5",
        "prd": leer("salidas/01_prd.md", "PRD NO DISPONIBLE"),
        "historias_finales": leer("salidas/04_historias_finales.md", "SIN HISTORIAS"),
        "backlog_final": leer("salidas/05_backlog_final.md", "SIN BACKLOG"),
        "paquete_refinamiento": leer("salidas/06_paquete_refinamiento.md", "SIN PAQUETE"),
        "respuestas_desarrollo": leer("intercambio/respuestas_desarrollo.md"),
        "respuestas_qa": leer("intercambio/respuestas_qa.md"),
        "respuestas_infraestructura": leer("intercambio/respuestas_infraestructura.md"),
    }

else:
    sys.exit("Uso: python main.py [definicion | preparar | consolidar]")

print(crew.kickoff(inputs=inputs))
```

## 10. Ajustes para modelos locales

- **Contexto:** el contexto por defecto de Ollama es corto y los PRD + historias lo desbordan. Súbelo a 8192 o más (variable `OLLAMA_CONTEXT_LENGTH=8192` o `PARAMETER num_ctx 8192` en un Modelfile).
- **Refina pocas historias:** `n_historias` en 5 mantiene el contexto manejable. Súbelo solo si tu modelo y tu memoria aguantan.
- **Temperatura baja** (0.1-0.2) para que respeten los formatos.
- **Sin delegación** en los cuatro agentes: con modelos pequeños la delegación suele causar bucles.
- **`max_iter=4`** evita que un agente se quede dando vueltas.
- **Modelo compartido:** el Facilitador y el Analista usan `hermes3:8b`, así Ollama no recarga modelos entre tareas consecutivas.
- **Solicitud detallada:** mientras más concreta sea `solicitud_usuario`, menos supuestos y preguntas abiertas saldrán.
- **DeepSeek-R1** suele imprimir su razonamiento en bloques `<think>`. Si te ensucian el entregable del Revisor, cámbialo por `qwen2.5:14b`.
- **Si un modelo se sale del formato:** sube al modelo más grande de su familia antes de tocar los prompts.
- **Memoria:** déjala apagada (`memory=False`, el valor por defecto); los entregables ya viajan por `context` y por los archivos de `salidas/` e `intercambio/`.
- **RAM/VRAM aproximada:** modelos de 7-8B necesitan unos 8 GB, los de 14B unos 16 GB. Si no te alcanza, usa `qwen2.5:7b` para los cuatro agentes.
