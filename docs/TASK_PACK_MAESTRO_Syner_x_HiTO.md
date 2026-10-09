# TASK PACK MAESTRO
## Syner × HiTO — Transformation Room

### 0. MISIÓN

Construir y desplegar una mini aplicación web privada para acompañar el proyecto de consultoría de **Grupo Syner con HiTO**.

No construir un ERP, CRM ni PM tradicional.

Construir una **Client Advisory & Transformation Room** que funcione como punto central del proyecto y permita a dirección de HiTO y al equipo Syner entender rápidamente:

**Dónde estamos → qué encontramos → qué estamos priorizando → qué se decidió → qué se está ejecutando → qué sigue → qué evidencia existe.**

La aplicación debe ser útil desde la primera semana del acompañamiento y evolucionar conforme avance el proyecto.

---

# 1. PRINCIPIO DE PRODUCTO

El software debe materializar la metodología de Syner.

No queremos que la consultoría termine dispersa entre:

- PowerPoints
- Excel
- correos
- WhatsApp
- minutas
- documentos
- reuniones

La aplicación debe convertirse progresivamente en la **memoria operativa y ejecutiva del engagement**.

Modelo conceptual:

INPUTS
↓
Diagnóstico
↓
Hallazgos
↓
Riesgos / oportunidades
↓
Prioridades
↓
Decisiones
↓
Iniciativas
↓
Acciones
↓
Evidencia
↓
Resultados
↓
Aprendizaje

Toda la información importante deberá mantener trazabilidad.

---

# 2. NOMBRE PROVISIONAL

**Syner × HiTO**
**Transformation Room**

Subtítulo:

> Executive advisory, transformation & decision intelligence.

Alternativas internas:

- Syner Client Room
- HiTO Transformation Office
- Syner Advisory OS
- HiTO Executive Room
- Transformation Control Tower

No usar estos nombres como marcas finales sin aprobación.

---

# 3. USUARIOS

Crear inicialmente tres roles.

### SYNER_ADMIN

Equipo consultor.

Puede:

- crear y editar información;
- registrar hallazgos;
- cargar documentos;
- crear iniciativas;
- actualizar avances;
- registrar reuniones;
- registrar decisiones;
- administrar usuarios;
- modificar roadmap;
- administrar diagnóstico.

### HITO_EXECUTIVE

Alta dirección del cliente.

Puede:

- consultar dashboard;
- revisar hallazgos;
- validar decisiones;
- revisar roadmap;
- consultar documentos;
- revisar avances;
- registrar comentarios.

### HITO_COLLABORATOR

Participante de un workstream.

Puede:

- visualizar información asignada;
- actualizar acciones;
- adjuntar evidencia;
- comentar;
- consultar reuniones relacionadas.

Aplicar RBAC real desde backend.

---

# 4. MVP — EXPERIENCIA PRINCIPAL

## 4.1 HOME / EXECUTIVE COCKPIT

Debe responder en menos de 30 segundos:

- ¿Cuál es el estado del engagement?
- ¿Qué cambió recientemente?
- ¿Dónde existen riesgos?
- ¿Qué necesita decisión?
- ¿Qué estamos haciendo?
- ¿Cuál es el siguiente milestone?

Componentes:

### Engagement Health

Indicador general:

- On Track
- Attention
- At Risk

Mostrar también:

- progreso general;
- iniciativas activas;
- acciones abiertas;
- decisiones pendientes;
- riesgos críticos;
- próximo milestone.

### Executive Summary

Bloque editable por Syner:

**Situación actual**

Resumen ejecutivo de máximo 4–6 líneas.

### This Week

Mostrar:

- avances;
- descubrimientos;
- decisiones;
- bloqueadores.

### Next

Mostrar próximas acciones relevantes.

### Decisions Required

Panel prominente con decisiones que requieren intervención C-level.

---

# 5. MÓDULO DIAGNÓSTICO

Ruta:

`/diagnostic`

Crear un diagnóstico empresarial vivo.

Dimensiones iniciales configurables:

- Estrategia
- Operaciones
- Procesos
- Tecnología
- Datos
- Inteligencia Artificial
- Automatización
- Gobierno
- Riesgos
- Personas y capacidades
- Experiencia del cliente
- Seguridad
- Cumplimiento

Escala sugerida:

1 — Inicial  
2 — Reactivo  
3 — Estandarizado  
4 — Gestionado  
5 — Optimizado

Por dimensión almacenar:

- situación actual;
- score;
- evidencia;
- observaciones;
- riesgos;
- oportunidades;
- estado objetivo;
- brecha;
- recomendación Syner.

Visualización:

Radar de madurez + tarjetas detalladas.

IMPORTANTE:

El gráfico es una visualización ejecutiva.

La información real debe existir como entidades estructuradas en base de datos.

---

# 6. HALLAZGOS

Ruta:

`/findings`

Un hallazgo NO es una tarea.

Cada hallazgo debe contener:

- título;
- descripción;
- contexto;
- categoría;
- área;
- origen;
- impacto;
- severidad;
- evidencia;
- recomendación;
- responsable Syner;
- fecha;
- estado.

Clasificación:

### Tipo

- Opportunity
- Risk
- Gap
- Finding
- Quick Win
- Strategic Insight

### Impacto

- Low
- Medium
- High
- Critical

### Status

- New
- Under Analysis
- Validated
- Converted to Initiative
- Accepted
- Closed

Permitir convertir:

**Finding → Initiative**

sin duplicar información.

---

# 7. STRATEGIC OPPORTUNITIES

Ruta:

`/opportunities`

Aquí registrar oportunidades identificadas durante el acompañamiento.

Categorías:

- Digitalización
- Automatización
- IA
- Datos
- Procesos
- Producto
- Tecnología
- Cost Optimization
- Customer Experience
- Revenue
- Risk Reduction
- Compliance
- Organizational

Cada oportunidad debe mostrar:

### Business value

### Complexity

### Time to Value

### Strategic Fit

### Risk

### Estimated Effort

Crear matriz visual:

**Impact × Effort**

Cuadrantes:

- Quick Wins
- Strategic Bets
- Incremental
- Defer

---

# 8. INITIATIVES / WORKSTREAMS

Ruta:

`/initiatives`

Representan proyectos concretos derivados del diagnóstico.

Ejemplo conceptual:

**Automatización de proceso X**

No asumir iniciativas reales hasta que Syner las registre.

Campos:

- nombre;
- descripción;
- objetivo;
- owner HiTO;
- owner Syner;
- área;
- prioridad;
- estado;
- fecha inicial;
- fecha objetivo;
- progreso;
- impacto esperado;
- KPIs;
- riesgos;
- dependencias.

Estados:

- Discovery
- Design
- Validation
- Execution
- Monitoring
- Completed
- On Hold

Cada iniciativa tendrá su propia página.

---

# 9. INITIATIVE DETAIL

Crear una vista tipo mission control.

Header:

Nombre  
Owner  
Status  
Progress  
Target Date

Después:

### Objective

### Expected Outcome

### Milestones

### Actions

### Decisions

### Risks

### Evidence

### Documents

### Activity

Todo relacionado mediante IDs.

---

# 10. ROADMAP

Ruta:

`/roadmap`

Timeline ejecutiva.

No construir inicialmente un Gantt complejo.

Crear fases:

### Discover
Entender.

### Diagnose
Medir.

### Design
Diseñar.

### Prioritize
Elegir.

### Execute
Implementar.

### Measure
Comprobar.

Cada milestone:

- nombre;
- descripción;
- fecha;
- estado;
- owner;
- workstream;
- entregable asociado.

---

# 11. ACTION REGISTER

Ruta:

`/actions`

Sistema ligero de compromisos.

Campos:

- acción;
- responsable;
- organización;
- iniciativa;
- fecha compromiso;
- prioridad;
- status;
- evidencia;
- comentarios.

Status:

- Open
- In Progress
- Blocked
- Completed
- Cancelled

Debe existir una vista:

**My Actions**

pero NO construir un task manager genérico.

---

# 12. DECISION LOG

Ruta:

`/decisions`

Este será uno de los módulos diferenciadores.

Registrar:

- decisión;
- contexto;
- alternativas consideradas;
- recomendación Syner;
- decisión final;
- responsable;
- participantes;
- fecha;
- impacto;
- iniciativa relacionada;
- documentos/evidencia.

Estados:

- Proposed
- Under Review
- Approved
- Rejected
- Deferred

El dashboard debe destacar:

**Decisions awaiting approval**

---

# 13. RISK REGISTER

Ruta:

`/risks`

Campos:

- riesgo;
- categoría;
- descripción;
- probabilidad;
- impacto;
- nivel;
- owner;
- mitigación;
- contingencia;
- status.

Matriz:

Impact × Probability.

Estados:

- Identified
- Monitoring
- Mitigating
- Escalated
- Closed

---

# 14. MEETINGS

Ruta:

`/meetings`

Cada sesión con HiTO debe convertirse en conocimiento estructurado.

Campos:

- título;
- fecha;
- participantes;
- objetivo;
- resumen;
- temas;
- acuerdos;
- decisiones;
- acciones;
- documentos.

Separar explícitamente:

DISCUSSION

DECISIONS

ACTION ITEMS

NEXT STEPS

Permitir que acciones y decisiones creadas desde una reunión se conviertan automáticamente en entidades de sus respectivos módulos.

---

# 15. DOCUMENT ROOM

Ruta:

`/documents`

Repositorio contextual del engagement.

Categorías:

- Discovery
- Assessment
- Strategy
- Process
- Technology
- Data
- AI
- Reports
- Meetings
- Deliverables
- Evidence

Cada documento:

- nombre;
- descripción;
- categoría;
- versión;
- fecha;
- uploader;
- tags;
- relación con iniciativa/hallazgo/reunión.

MVP:

Metadata + enlace al documento.

NO implementar almacenamiento documental empresarial complejo todavía.

Preparar arquitectura para posteriormente integrar:

- Google Drive
- Microsoft SharePoint
- OneDrive
- S3-compatible storage.

---

# 16. DELIVERABLES

Ruta:

`/deliverables`

Debe servir como registro contractual y de ejecución.

Mostrar:

- entregable;
- descripción;
- milestone;
- responsable;
- target date;
- estado;
- versión;
- aprobación;
- archivo/link.

Status:

- Planned
- In Progress
- Internal Review
- Client Review
- Approved
- Delivered

---

# 17. KPI / VALUE TRACKING

Ruta:

`/impact`

Objetivo:

Pasar de:

"hicimos consultoría"

a:

"generamos impacto medible".

Tipos de impacto:

- tiempo ahorrado;
- costos;
- capacidad;
- riesgo mitigado;
- errores reducidos;
- automatización;
- productividad;
- revenue;
- satisfacción;
- compliance;
- adopción tecnológica.

Campos KPI:

- baseline;
- current;
- target;
- unit;
- frequency;
- owner;
- source;
- last updated.

No inventar datos.

Cuando no haya medición:

`Awaiting baseline`

---

# 18. AI OPPORTUNITY MAP

Crear módulo:

`/ai-opportunities`

No presentar IA como chatbot.

Registrar casos de uso posibles.

Campos:

- proceso;
- problema;
- intervención IA;
- tipo;
- datos requeridos;
- impacto;
- complejidad;
- riesgo;
- human oversight;
- prioridad;
- readiness.

Tipo de IA:

- Generative AI
- Agents
- RAG
- Document Intelligence
- Prediction
- Classification
- Optimization
- Automation
- Computer Vision

Crear indicador:

### AI Readiness

Low / Medium / High.

---

# 19. ACTIVITY / AUDIT TRAIL

Registrar automáticamente acciones importantes:

- usuario;
- acción;
- entidad;
- timestamp;
- cambios relevantes.

Ejemplo:

`Syner updated Initiative "X" from Discovery to Design.`

Esto es especialmente importante por tratarse de un cliente del sector financiero.

---

# 20. SEARCH

Agregar búsqueda global sencilla.

Buscar en:

- hallazgos;
- iniciativas;
- decisiones;
- reuniones;
- acciones;
- documentos.

Preparar arquitectura para búsqueda semántica futura.

NO implementar infraestructura vectorial en MVP si no es necesaria.

---

# 21. FUTURE: SYNER CORTEX

La arquitectura debe estar preparada para incorporar posteriormente una capa de inteligencia.

Concepto:

**Syner Cortex**

El sistema podrá utilizar conocimiento acumulado del engagement para responder preguntas como:

- ¿Cuáles son los principales riesgos detectados?
- ¿Qué decisiones siguen pendientes?
- ¿Qué iniciativas están bloqueadas?
- ¿Qué acuerdos surgieron en las últimas reuniones?
- ¿Qué oportunidades de automatización encontramos?
- ¿Dónde existen contradicciones?
- ¿Qué cambió esta semana?
- ¿Cuál debería ser nuestra siguiente prioridad?

NO implementar agentes autónomos en el primer release.

Solo preparar:

- IDs estables;
- timestamps;
- metadata;
- relaciones;
- tags;
- arquitectura API-first.

---

# 22. SEGURIDAD — REQUISITO CRÍTICO

HiTO opera en el sector financiero.

Diseñar bajo principio:

**Minimum Necessary Data**

En el MVP:

NO almacenar:

- cartera crediticia;
- estados de cuenta;
- información financiera sensible;
- PII de acreditados;
- números de cuenta;
- información fiduciaria confidencial;
- bases productivas de HiTO.

La plataforma administra principalmente información del **engagement de consultoría**.

Implementar:

- autenticación;
- autorización backend;
- RBAC;
- tenant isolation;
- HTTPS;
- secrets únicamente mediante environment variables;
- password hashing;
- JWT;
- logs;
- timestamps;
- audit trail;
- validación de input;
- rate-limit preparado;
- protección de endpoints.

Nunca confiar en ocultamiento frontend como mecanismo de seguridad.

---

# 23. MULTI-TENANCY

Aunque el primer tenant será HiTO:

NO hardcodear HiTO en la arquitectura.

Modelo:

Organization
↓
Engagement
↓
Users
↓
Entities

Ejemplo:

Organization:
HiTO

Engagement:
Syner × HiTO Transformation Program

Esto permitirá posteriormente desplegar la misma plataforma para otros clientes Syner.

Toda entidad relevante debe asociarse a:

`organization_id`

y cuando corresponda:

`engagement_id`.

---

# 24. STACK

Seguir arquitectura moderna API-first.

## Backend

Python 3.11+

FastAPI

SQLAlchemy 2

Pydantic v2

PostgreSQL

Alembic

JWT authentication

pytest

## Frontend

React 18

TypeScript

Vite

React Router

Zustand

Axios

Tailwind CSS

Recharts

## Infrastructure

Railway

PostgreSQL Railway

GitHub

Environment variables

Single deployment permitido:

FastAPI puede servir build `/frontend/dist`.

---

# 25. ESTRUCTURA BACKEND

Crear aproximadamente:

app/

main.py  
database.py  
dependencies.py

core/

config.py  
security.py

models/

user.py  
organization.py  
engagement.py  
finding.py  
diagnostic.py  
initiative.py  
milestone.py  
action.py  
decision.py  
risk.py  
meeting.py  
document.py  
deliverable.py  
kpi.py  
ai_opportunity.py  
activity.py

schemas/

routers/

services/

crud/

utils/

No crear arquitectura artificialmente compleja.

---

# 26. API

Todos los endpoints:

`/api/*`

Ejemplo:

`POST /api/auth/login`

`GET /api/dashboard`

`GET /api/findings`

`POST /api/findings`

`GET /api/initiatives`

`GET /api/initiatives/{id}`

`GET /api/actions`

`GET /api/decisions`

`GET /api/risks`

`GET /api/meetings`

`GET /api/documents`

`GET /api/deliverables`

`GET /api/kpis`

`GET /api/ai-opportunities`

Aplicar authorization y organization scope en backend.

---

# 27. FRONTEND

Layout principal:

### Sidebar

Overview

Diagnostic

Findings

Opportunities

Initiatives

Roadmap

Actions

Decisions

Risks

Meetings

Documents

Deliverables

Impact

AI Opportunities

---

Header:

Engagement selector

Search

Notifications placeholder

User

---

# 28. LOOK & FEEL

NO crear apariencia genérica de SaaS.

Inspiración:

- Palantir
- Linear
- Stripe
- Bloomberg institucional
- McKinsey / BCG digital products
- banca de inversión
- enterprise intelligence platforms

Pero utilizar identidad visual propia.

Sensación:

**financial intelligence + consulting + control + trust**

Visualmente:

- fondos claros;
- blanco;
- grises muy suaves;
- tipografía limpia;
- alto uso de espacio negativo;
- líneas finas;
- cards discretas;
- data visualization profesional;
- mínima decoración;
- números y métricas prominentes.

Evitar:

- gradientes excesivos;
- glassmorphism;
- ilustraciones infantiles;
- iconografía innecesaria;
- dashboards saturados;
- colores neón.

---

# 29. IDENTIDAD SYNER × HITO

La aplicación debe comunicar colaboración.

Header/login:

SYNER × HiTO

No hacer que parezca que Syner intenta sustituir la identidad de HiTO.

Mantener interfaz neutral e institucional.

El producto debe sentirse como una **war room compartida**.

---

# 30. LOGIN

Pantalla extremadamente limpia.

SYNER × HiTO

Transformation Room

Email

Password

Sign in

Texto:

`Private advisory workspace`

No permitir registro público.

Los usuarios serán creados por administración.

---

# 31. SEED DATA

Crear seed demo únicamente con información ficticia.

Organization:

HiTO

Engagement:

Syner × HiTO Transformation Program

Crear:

- 5 hallazgos;
- 4 iniciativas;
- 8 acciones;
- 3 decisiones;
- 3 riesgos;
- 3 reuniones;
- 5 documentos;
- 4 oportunidades IA;
- algunos milestones.

Marcar claramente los datos como:

`Demo / placeholder`

NO inventar información real sobre la operación interna de HiTO.

---

# 32. DASHBOARD MVP

Prioridad máxima.

La primera pantalla debe mostrar:

SYNER × HiTO

Transformation Program

---

ENGAGEMENT HEALTH

On Track

---

PROGRESS

XX%

---

ACTIVE INITIATIVES

X

---

OPEN ACTIONS

X

---

DECISIONS REQUIRED

X

---

CRITICAL RISKS

X

---

Después:

### Executive Summary

### Transformation Roadmap

### Active Initiatives

### Decisions Required

### Key Findings

### Recent Activity

### Next Milestones

---

# 33. RESPONSIVE

Desktop-first.

Debe funcionar correctamente en:

1440px  
1280px  
1024px  
tablet  
mobile

El dashboard ejecutivo debe poder revisarse desde teléfono.

---

# 34. FASES DE DESARROLLO

## PHASE 0 — FOUNDATION

Repository  
FastAPI  
React  
PostgreSQL  
Railway  
Authentication  
Organizations  
Engagements  
RBAC  
Layout

---

## PHASE 1 — CLIENT ROOM MVP

Dashboard  
Findings  
Initiatives  
Actions  
Decisions  
Meetings  
Roadmap  
Documents

Objetivo:

**ponerlo en manos del cliente.**

---

## PHASE 2 — CONSULTING OS

Diagnostic  
Risks  
Opportunities  
Deliverables  
KPIs  
Impact tracking

---

## PHASE 3 — INTELLIGENCE

Global search  
Semantic search  
Document ingestion  
Meeting intelligence  
Syner Cortex  
RAG  
Executive briefs

---

## PHASE 4 — AGENTIC ADVISORY

No implementar todavía.

Arquitectura futura:

Meeting Agent

Research Agent

Risk Agent

PMO Agent

Executive Brief Agent

Opportunity Agent

Cada agente debe operar con autorización, herramientas limitadas y Human-in-the-Loop.

---

# 35. QUICK WIN

No esperar a terminar todos los módulos.

El primer release funcional debe permitir:

1. login;
2. entrar al proyecto HiTO;
3. ver dashboard;
4. consultar roadmap;
5. registrar hallazgos;
6. crear iniciativas;
7. registrar acuerdos;
8. registrar decisiones;
9. consultar siguientes acciones.

Ese producto ya debe poder utilizarse durante una reunión real.

---

# 36. DEFINITION OF DONE — MVP

Considerar el MVP listo cuando:

- aplicación desplegada en Railway;
- PostgreSQL funcionando;
- autenticación funcional;
- aislamiento por organización;
- dashboard operativo;
- CRUD principales funcionando;
- RBAC backend;
- responsive básico;
- errores manejados;
- seed demo;
- README completo;
- `.env.example`;
- migrations reproducibles;
- tests mínimos backend;
- health endpoint;
- deploy reproducible desde GitHub.

---

# 37. REGLA DE INGENIERÍA

No construir funcionalidad porque "podría ser útil".

Cada feature debe responder:

**¿Ayuda a Syner y HiTO a entender, decidir, ejecutar o medir mejor el engagement?**

Si la respuesta es no:

NO construirla todavía.

---

# 38. FILOSOFÍA

Esta aplicación no es solamente un portal.

Debe convertirse progresivamente en:

**System of Record**
para el engagement.

Después:

**System of Intelligence**
para la consultoría.

Finalmente:

**System of Action**
para la transformación.

La evolución deseada es:

CONSULTING
↓
DIGITAL CONSULTING
↓
CONTINUOUS ADVISORY
↓
INTELLIGENCE PLATFORM
↓
AGENTIC ADVISORY

---

# 39. INSTRUCCIÓN PARA EL AGENTE DE DESARROLLO

Antes de escribir código:

1. inspecciona completamente el repositorio;
2. identifica arquitectura existente;
3. no destruyas funcionalidad funcional;
4. genera un implementation plan;
5. identifica models y migrations requeridas;
6. identifica endpoints;
7. define componentes React;
8. comienza por foundation + vertical slice;
9. prueba backend;
10. prueba build frontend;
11. realiza deployment check.

Implementar verticalmente, no módulo por módulo sin integración.

Primer vertical slice:

`login → dashboard → finding → initiative → action → dashboard update`

Una vez estable, continuar con los demás módulos.

Priorizar:

security  
traceability  
maintainability  
UX  
speed of delivery

sobre complejidad innecesaria.
