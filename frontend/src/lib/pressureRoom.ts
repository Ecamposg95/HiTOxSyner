/**
 * Motor de la Pressure Room (demo). Todo es un guion determinista tomado del
 * Libro Maestro del Caso Project ORION (docs/HITO_Leadership_Pressure_Room_
 * Project_ORION_Case_Book_ES_v1.0.pdf): personajes, liberaciones 1A–4D y
 * Exhibits. Los personajes, cifras y comunicaciones son ficticios por diseño.
 * Sin backend ni IA real: el "agente" es este reducer.
 */

export type ActId = "I" | "II" | "III" | "IV";

export type ActorKind = "client" | "hito" | "vendor" | "facilitator";

export interface Actor {
  id: string;
  name: string;
  role: string;
  kind: ActorKind;
}

export const ACTORS: Record<string, Actor> = {
  aurea: { id: "aurea", name: "Sofía Navarro", role: "Áurea Capital · Cliente", kind: "client" },
  nova: { id: "nova", name: "NOVA Analytics", role: "Proveedor · IA", kind: "vendor" },
  lucia: { id: "lucia", name: "Lucía Ortega", role: "Dir. Comercial", kind: "hito" },
  alejandro: { id: "alejandro", name: "Alejandro Vega", role: "Dir. Operaciones", kind: "hito" },
  mariana: { id: "mariana", name: "Mariana Solís", role: "Dir. Datos y Tecnología", kind: "hito" },
  ricardo: { id: "ricardo", name: "Ricardo Luna", role: "Dir. Riesgo y Compliance", kind: "hito" },
  sofia: { id: "sofia", name: "Sofía Torres", role: "Líder de Relación con Cliente", kind: "hito" },
  carlos: { id: "carlos", name: "Carlos Meza", role: "Gerente de Proyecto ORION", kind: "hito" },
  elena: { id: "elena", name: "Elena Prado", role: "Analista Senior de Datos", kind: "hito" },
  daniel: { id: "daniel", name: "Daniel Cárdenas", role: "Business Partner de Finanzas", kind: "hito" },
  facilitator: { id: "facilitator", name: "Facilitador Syner", role: "Responsable del Caso", kind: "facilitator" },
};

export type PodTarget = number | "all";

/** Efecto de un evento sobre una mesa. Deltas en pressure; valores absolutos en certainty/evidence. */
export interface Effect {
  pod: PodTarget;
  pressure?: number;
  certainty?: number;
  evidence?: number;
  decided?: boolean;
  deliverable?: string;
  alert?: string;
}

export type EventKind = "release" | "message" | "observer" | "end";

export interface SimEvent {
  id: string;
  /** Minutos de simulación desde el inicio del acto. */
  at: number;
  kind: EventKind;
  text: string;
  actor?: string;
  /** Código de liberación (1A…4D) para kind=release. */
  code?: string;
  title?: string;
  /** Liberación que el Director del caso propone y el facilitador aprueba o frena. */
  gated?: boolean;
  /** Razón que da el Director para proponer la liberación. */
  reason?: string;
  pod?: number;
  effects?: Effect[];
}

export interface Act {
  id: ActId;
  number: number;
  name: string;
  question: string;
  deliverable: string;
  /** Etiqueta del día del caso ("D+3"). */
  day: string;
  /** Hora de inicio en minutos del día. */
  startMinutes: number;
  /** Hora límite en minutos del día. */
  deadlineMinutes: number;
  deadlineLabel: string;
  /** Mezcla de intensidad narrativa (Libro del Caso, sección A). */
  mix: string;
  events: SimEvent[];
}

export interface PodState {
  number: number;
  name: string;
  pressure: number;
  certainty: number;
  evidence: number;
  decidedAt: number | null;
  deliverable: string;
  alerts: string[];
}

export interface SimState {
  actId: ActId;
  clock: number;
  running: boolean;
  speed: 1 | 2 | 4;
  /** Minutos acumulados por "Frenar" (desplazan todo lo no liberado). */
  offset: number;
  fired: string[];
  pending: string | null;
  pods: PodState[];
}

export type SimAction =
  | { type: "tick"; dt: number }
  | { type: "play" }
  | { type: "pause" }
  | { type: "speed"; speed: 1 | 2 | 4 }
  | { type: "approve" }
  | { type: "hold" }
  | { type: "act"; actId: ActId }
  | { type: "reset" };

export const HOLD_MINUTES = 10;

const POD_NAMES = ["Pod 1 · Norte", "Pod 2 · Centro", "Pod 3 · Bajío", "Pod 4 · Sur"];

const all = (e: Omit<Effect, "pod">): Effect => ({ pod: "all", ...e });
const pod = (n: number, e: Omit<Effect, "pod">): Effect => ({ pod: n, ...e });

export const ACTS: Act[] = [
  {
    id: "I",
    number: 1,
    name: "DECIDIR",
    question: "¿Qué decidimos ahora y qué nos negamos a afirmar hasta contar con evidencia?",
    deliverable: "Registro de Decisión / Firma de Decisión",
    day: "D+3",
    startMinutes: 8 * 60 + 35,
    deadlineMinutes: 10 * 60,
    deadlineLabel: "Comité de inversiones de Áurea",
    mix: "70% información · 30% personas",
    events: [
      { id: "1A", at: 0, kind: "release", code: "1A", title: "Escalamiento del cliente", text: "Exhibits 1, 2 y 3: snapshot de cartera (MXN $12.8B), correo urgente de Áurea y dashboard de conciliación (98.3% verde, MXN $217.6M en ámbar).", effects: [all({ pressure: 55, certainty: 20, evidence: 20, deliverable: "Registro de Decisión · hechos vs. supuestos" })] },
      { id: "m1", at: 0, kind: "message", actor: "aurea", text: "Nuestro archivo de control y la posición preliminar de HITO no concilian. La variación parece material. Necesitamos una explicación clara antes de las 10:00 y saber si existe impacto financiero." },
      { id: "m2", at: 2, kind: "message", actor: "sofia", text: "Áurea pide responsable y hora de la siguiente actualización. ¿Qué les digo?" },
      { id: "m3", at: 4, kind: "message", actor: "lucia", text: "El comité es a las 10. No podemos llegar con \"estamos investigando\".", effects: [all({ pressure: 8 })] },
      { id: "o1", at: 6, kind: "observer", pod: 1, text: "Lucía-rol habla primero durante 3 min. Nadie separa hechos de supuestos todavía.", effects: [pod(1, { certainty: 70, evidence: 25, alert: "Certeza sin evidencia" })] },
      { id: "m4", at: 8, kind: "message", actor: "ricardo", text: "Antes de afirmar impacto necesito saber si la variación mueve efectivo. Nadie lo sabe todavía." },
      { id: "o2", at: 10, kind: "observer", pod: 2, text: "Pod 2 registra su decisión: investigar 60 min, no afirmar impacto, responsable Carlos-rol.", effects: [pod(2, { decided: true, certainty: 35, evidence: 30 }), pod(4, { decided: true, certainty: 85, evidence: 25, alert: "Prometió certeza al cliente" })] },
      { id: "1B", at: 12, kind: "release", code: "1B", title: "Actualización de Operaciones", gated: true, reason: "Pods 2 y 4 ya hicieron explícita su primera decisión.", text: "98.3% de la cartera concilia. El 1.7% restante se concentra en dos códigos de producto. Aún no se confirma si la diferencia modifica efectivo o solo clasificación.", effects: [all({ evidence: 45, pressure: 5 })] },
      { id: "m5", at: 14, kind: "message", actor: "alejandro", text: "98.3% concilia. El 1.7% está en dos códigos de producto. No puedo confirmar si mueve efectivo o solo clasificación." },
      { id: "m6", at: 17, kind: "message", actor: "daniel", text: "Sin datos confiables no firmo ninguna declaración de impacto. MXN $217.6M indicativos no es impacto." },
      { id: "o3", at: 19, kind: "observer", pod: 3, text: "Lenguaje de \"mi área\" en aumento. Riesgo-rol se incorpora tarde a la conversación.", effects: [pod(3, { certainty: 60, alert: "Riesgo involucrado tarde" })] },
      { id: "1C", at: 22, kind: "release", code: "1C", title: "Trazabilidad de Tecnología", gated: true, reason: "Pods 1 y 3 formularon una hipótesis de mapeo.", text: "Una regla de mapeo (product_code 47A, lease_residual) fue modificada 48 horas antes de la puesta en operación. Superó validación técnica; no existe un artefacto que demuestre la revalidación de negocio.", effects: [all({ evidence: 65, pressure: 6 })] },
      { id: "m7", at: 24, kind: "message", actor: "mariana", text: "Confirmo: product_code 47A y lease_residual cambiaron en D-2 19:14. Pasó validación técnica. No encuentro un artefacto de revalidación de negocio." },
      { id: "m8", at: 26, kind: "message", actor: "elena", text: "Yo lo había señalado en D-3. Puedo aislar los registros afectados en 20 minutos si alguien me lo pide." },
      { id: "o4", at: 28, kind: "observer", pod: 1, text: "Expertise de Elena-rol ignorado por estatus: nadie la invitó a hablar.", effects: [pod(1, { alert: "Disenso no invitado" })] },
      { id: "o5", at: 30, kind: "observer", pod: 1, text: "Pod 1 re-decide con la nueva evidencia y baja la certeza proyectada.", effects: [pod(1, { decided: true, certainty: 40 }), pod(3, { decided: true, certainty: 50 })] },
      { id: "1D", at: 34, kind: "release", code: "1D", title: "Presión del cliente", gated: true, reason: "Pod 4 busca certeza en lugar de decidir bajo incertidumbre.", text: "Áurea formula una pregunta binaria: \"¿Existe impacto financiero, sí o no?\" La causa raíz sigue bajo investigación.", effects: [all({ pressure: 15 })] },
      { id: "m9", at: 35, kind: "message", actor: "aurea", text: "¿Existe impacto financiero, sí o no? Necesito la respuesta antes del comité." },
      { id: "m10", at: 37, kind: "message", actor: "lucia", text: "Si decimos \"no sabemos\" perdemos la cuenta. Si decimos \"no\" y luego resulta que sí, la perdemos peor." },
      { id: "o6", at: 40, kind: "observer", text: "Pod 2 cambió su mensaje al cliente con la nueva evidencia. Pod 4 no cambió nada.", effects: [pod(4, { alert: "No actualizó con nueva evidencia" })] },
      { id: "m11", at: 45, kind: "message", actor: "carlos", text: "Propongo: mensaje a Áurea a las 09:30 con hechos verificados, supuestos explícitos y hora del siguiente update." },
      { id: "m12", at: 55, kind: "message", actor: "sofia", text: "Enviado el mensaje del Pod 2. Áurea agradece la claridad sobre lo que NO sabemos.", effects: [pod(2, { pressure: -15 })] },
      { id: "o7", at: 70, kind: "observer", text: "Anclas de debrief listas: ¿qué sabíamos y qué suponíamos? ¿Cuándo la confianza se convirtió en cierre? ¿Qué perspectiva faltó?" },
      { id: "e1", at: 85, kind: "end", text: "Fin del Acto I. Cada pod cierra su Registro de Decisión: antes y después de la nueva evidencia." },
    ],
  },
  {
    id: "II",
    number: 2,
    name: "CONFRONTAR",
    question: "¿Cómo se convirtió una señal conocida en un riesgo no gestionado?",
    deliverable: "Registro de Conversación y Responsabilidad",
    day: "D-2",
    startMinutes: 17 * 60 + 30,
    deadlineMinutes: 19 * 60 + 14,
    deadlineLabel: "El cambio de mapeo entra a producción",
    mix: "50% información · 50% relaciones",
    events: [
      { id: "2A", at: 0, kind: "release", code: "2A", title: "La primera señal · 72 horas antes", text: "Exhibit 5: correo de Elena Prado alertando una anomalía de mapeo. Técnicamente correcto, lenguaje ambiguo (\"puede no ser material\"). Sin responsable ni fecha límite.", effects: [all({ pressure: 40, certainty: 30, evidence: 35, deliverable: "Registro de Conversación · contexto sin juicio" })] },
      { id: "m1", at: 0, kind: "message", actor: "elena", text: "Estoy observando una inconsistencia en product_code 47A y valores en blanco en lease_residual. Puede no ser material, pero recomiendo revisarlo antes de la carga final." },
      { id: "o1", at: 3, kind: "observer", text: "Los pods leen el correo. Nadie nombra que falta responsable ni fecha límite." },
      { id: "2B", at: 6, kind: "release", code: "2B", title: "La presión comercial", gated: true, reason: "Los cuatro pods ya reconstruyeron qué sabía cada parte en D-3.", text: "Exhibit 6: si HITO detiene la liberación esa noche es poco probable cumplir la fecha de puesta en operación. Cada stakeholder interpreta el mensaje de forma distinta.", effects: [all({ pressure: 12 })] },
      { id: "m2", at: 7, kind: "message", actor: "lucia", text: "Si detenemos esta noche, es muy poco probable que cumplamos la fecha comprometida. Áurea ha sido clara: la fecha importa." },
      { id: "m3", at: 9, kind: "message", actor: "carlos", text: "Entendido. Creo que Tecnología está revisando la nota de mapeo. Mantengo la llamada de preparación salvo que alguien diga que paremos." },
      { id: "m4", at: 11, kind: "message", actor: "mariana", text: "Podemos validar la regla técnica. La aceptación de negocio sobre el significado del campo debería corresponder a Operaciones." },
      { id: "m5", at: 13, kind: "message", actor: "alejandro", text: "Mi equipo entendió que el mapeo ya estaba liberado como parte del paquete de carga final. ¿Alguien puede confirmarlo?" },
      { id: "o2", at: 15, kind: "observer", pod: 3, text: "Lenguaje de culpa: \"Tecnología debió cerrarlo\". Defensividad en dos roles.", effects: [pod(3, { certainty: 75, alert: "Culpa en lugar de ownership" })] },
      { id: "2C", at: 18, kind: "release", code: "2C", title: "La brecha de responsabilidad", gated: true, reason: "El debate ya tocó quién creyó qué; toca hacer explícitas las expectativas.", text: "El PM creyó que Tecnología había cerrado el tema. Tecnología creyó que Operaciones haría la validación de negocio. Operaciones creyó que el cambio ya estaba aceptado.", effects: [all({ evidence: 60 })] },
      { id: "m6", at: 20, kind: "message", actor: "ricardo", text: "Me entero ahora. Riesgo no estaba en el hilo. Si el riesgo es un filtro final, siempre llegaré tarde." },
      { id: "o3", at: 24, kind: "observer", pod: 2, text: "Pod 2 distingue intención de impacto y vuelve explícitas las expectativas de cada handoff.", effects: [pod(2, { decided: true, certainty: 45, evidence: 65 })] },
      { id: "2D", at: 28, kind: "release", code: "2D", title: "El checkpoint cancelado", gated: true, reason: "Ya emergió la pregunta \"¿quién era responsable de qué?\".", text: "Exhibit 7: el checkpoint transversal de 20 minutos se canceló porque dos directores no estaban disponibles. Se siguió de forma asíncrona sin registro de decisión.", effects: [all({ pressure: 10, evidence: 75 })] },
      { id: "m7", at: 30, kind: "message", actor: "carlos", text: "Cancelé el checkpoint de 17:30: faltaban dos directores. Moví las actualizaciones a asíncrono." },
      { id: "m8", at: 34, kind: "message", actor: "daniel", text: "¿Alguien registró la decisión de seguir adelante? No encuentro nada." },
      { id: "o4", at: 40, kind: "observer", pod: 4, text: "El debate se vuelve personal en Pod 4. Cue: pausar y regresar a los hechos verificados.", effects: [pod(4, { alert: "Debate personal → volver a hechos" })] },
      { id: "o5", at: 48, kind: "observer", pod: 1, text: "Pod 1 cierra un acuerdo: handoff de mapeo con responsable, fecha y evidencia de cierre.", effects: [pod(1, { decided: true, certainty: 50, evidence: 75 }), pod(3, { decided: true, certainty: 55 })] },
      { id: "o6", at: 55, kind: "observer", text: "Pregunta de cierre: ¿qué necesitaba decirse 72 horas antes que nadie dijo con claridad?", effects: [pod(4, { decided: true, certainty: 55, evidence: 70 })] },
      { id: "e1", at: 70, kind: "end", text: "Fin del Acto II. Cada participante nombra la conversación que debe ocurrir y la evidencia de que quedó cerrada." },
    ],
  },
  {
    id: "III",
    number: 3,
    name: "ALINEAR",
    question: "¿Podemos optimizar para HITO y no para nuestra propia función?",
    deliverable: "Mapa de Flujo y Dependencias",
    day: "Mandato +1",
    startMinutes: 9 * 60,
    deadlineMinutes: 11 * 60 + 30,
    deadlineLabel: "Comité Ejecutivo de HITO",
    mix: "30% información · 70% sistema",
    events: [
      { id: "3A", at: 0, kind: "release", code: "3A", title: "Nuevo mandato · expansión en 30 días", text: "Áurea acepta el plan correctivo y acelera: una segunda subcartera de MXN $2.1B deberá incorporarse en 30 días, con los mismos equipos y sin capa adicional de gestión.", effects: [all({ pressure: 45, certainty: 40, evidence: 40, deliverable: "Mapa de Handoffs Rotos · BLOQUEO / ESPERA / RETRABAJO / VALOR" })] },
      { id: "m1", at: 1, kind: "message", actor: "aurea", text: "Aceptamos el plan correctivo. Segunda subcartera, MXN $2.1B, en 30 días." },
      { id: "m2", at: 3, kind: "message", actor: "alejandro", text: "Con el proceso actual es imposible. Toda excepción material pasa por mí." },
      { id: "3B", at: 8, kind: "release", code: "3B", title: "Vista del proceso · el flujo", gated: true, reason: "Los pods ya listaron las funciones involucradas; necesitan ver el flujo.", text: "Exhibit 8: flujo de incorporación de punta a punta. Ocho handoffs, cuatro aprobaciones formales y dos pasos de validación duplicados.", effects: [all({ evidence: 60 })] },
      { id: "m3", at: 10, kind: "message", actor: "carlos", text: "8 handoffs, 4 aprobaciones de director, 2 validaciones duplicadas. Tiempo típico en cola de excepciones: 6–18 horas." },
      { id: "o1", at: 14, kind: "observer", pod: 1, text: "Pod 1 marca BLOQUEO en la aprobación de excepciones, pero defiende el control de Operaciones.", effects: [pod(1, { certainty: 65 })] },
      { id: "3C", at: 18, kind: "release", code: "3C", title: "Cuello de botella · aprobación de excepciones", gated: true, reason: "Los cuatro mapas ya identificaron la cola de excepciones.", text: "Todas las excepciones materiales requieren aprobación a nivel director, incluidos temas recurrentes ya cubiertos por umbrales. El control reduce riesgo y también genera espera.", effects: [all({ pressure: 8, evidence: 70 })] },
      { id: "m4", at: 20, kind: "message", actor: "ricardo", text: "Los umbrales ya cubren la mayoría de las excepciones recurrentes. ¿Por qué siguen subiendo a director?" },
      { id: "m5", at: 22, kind: "message", actor: "mariana", text: "Validación duplicada: nosotros validamos la regla y Operaciones vuelve a validar el archivo completo." },
      { id: "o2", at: 26, kind: "observer", pod: 3, text: "\"Mi área\" 9 veces vs. \"HITO\" 2 veces. Optimización funcional visible.", effects: [pod(3, { certainty: 80, alert: "Función > empresa" })] },
      { id: "3D", at: 32, kind: "release", code: "3D", title: "Cambio de rol · Empresa > Función", gated: true, reason: "Cada pod ya defendió su óptimo funcional; el apego a la primera respuesta es visible.", text: "Cambia la instrucción: \"Ahora son el Comité Ejecutivo de HITO. Decidan para HITO, no para su función.\"", effects: [all({ pressure: 10, deliverable: "Rediseño del flujo · reducir fricción sin reducir accountability" })] },
      { id: "m6", at: 34, kind: "message", actor: "facilitator", text: "Ahora son el Comité Ejecutivo de HITO. Decidan para HITO, no para su función." },
      { id: "o3", at: 38, kind: "observer", pod: 2, text: "Pod 2 cede optimización local: derecho de decisión por umbral al gerente, director solo fuera de umbral.", effects: [pod(2, { decided: true, certainty: 50, evidence: 75 })] },
      { id: "m7", at: 44, kind: "message", actor: "elena", text: "El conocimiento del mapeo está en los analistas; la autoridad en los directores. Ahí está la espera." },
      { id: "o4", at: 50, kind: "observer", text: "Restricción cumplida en Pods 1 y 2: menos fricción sin menos accountability. Pod 3 aún protege su función.", effects: [pod(1, { decided: true, certainty: 55 }), pod(4, { decided: true, certainty: 60 })] },
      { id: "e1", at: 60, kind: "end", text: "Fin del Acto III. Pod 3 cierra tarde su rediseño. Cada participante identifica una interfase real en HITO donde puede mejorar el flujo.", effects: [pod(3, { decided: true, certainty: 70, evidence: 70 })] },
    ],
  },
  {
    id: "IV",
    number: 4,
    name: "TRANSFORMAR",
    question: "¿Podemos utilizar tecnología sin abdicar del juicio?",
    deliverable: "Charter de Juicio",
    day: "War Room",
    startMinutes: 15 * 60,
    deadlineMinutes: 16 * 60 + 30,
    deadlineLabel: "Decisión sobre NOVA Analytics",
    mix: "40% tecnología · 60% juicio",
    events: [
      { id: "4A", at: 0, kind: "release", code: "4A", title: "Propuesta NOVA Analytics", text: "Exhibit 10: validación 40% más rápida, 60% menos revisiones manuales, scoring automatizado de riesgo. Despliegue amplio en 8 semanas; revisión humana solo en casos de alto riesgo.", effects: [all({ pressure: 35, certainty: 45, evidence: 30, deliverable: "Charter de Juicio · IA puede / IA + humano / responsabilidad humana" })] },
      { id: "m1", at: 1, kind: "message", actor: "nova", text: "Validación 40% más rápida y 60% menos revisión manual. Recomendamos despliegue amplio en ocho semanas para las tres clases de activo." },
      { id: "m2", at: 4, kind: "message", actor: "lucia", text: "Áurea quiere velocidad. Esto resuelve el cuello de botella de Operaciones." },
      { id: "o1", at: 7, kind: "observer", pod: 4, text: "Sesgo de automatización: Pod 4 acepta las cifras del proveedor sin pedir evidencia.", effects: [pod(4, { certainty: 80, alert: "Sesgo de automatización" })] },
      { id: "4B", at: 10, kind: "release", code: "4B", title: "Limitación del modelo · el desempeño varía", gated: true, reason: "Los pods ya construyeron el mejor argumento a favor de la adopción.", text: "Exhibit 11: precisión 94% en consumo, 91% en automotriz y 78% en excepciones de valor residual de arrendamiento. Historial de entrenamiento limitado en esa clase.", effects: [all({ evidence: 55, pressure: 5 })] },
      { id: "m3", at: 12, kind: "message", actor: "mariana", text: "Consumo 94%, automotriz 91%, arrendamiento 78%. El historial de residuales es limitado." },
      { id: "m4", at: 15, kind: "message", actor: "ricardo", text: "78% en la clase donde ya fallamos. ¿Quién es dueño del riesgo del modelo?" },
      { id: "4C", at: 20, kind: "release", code: "4C", title: "Desacuerdo humano · experta vs. modelo", gated: true, reason: "Ya apareció la pregunta por el dueño del riesgo.", text: "Exhibit 12: el modelo clasifica una nueva excepción como de bajo riesgo. Elena Prado sostiene que el patrón se parece a la falla de mapeo de ORION y pide revisión manual.", effects: [all({ pressure: 8, evidence: 65 })] },
      { id: "m5", at: 22, kind: "message", actor: "nova", text: "Score de riesgo: BAJO. Consistente con una discrepancia de clasificación no material observada previamente." },
      { id: "m6", at: 23, kind: "message", actor: "elena", text: "No cerraría esta excepción de forma automática. La secuencia se parece al problema de mapeo previo a la puesta en operación de ORION." },
      { id: "o2", at: 27, kind: "observer", pod: 1, text: "Pod 1 desafía al modelo y a Elena-rol por igual: pide evidencia a ambos.", effects: [pod(1, { decided: true, certainty: 45, evidence: 70 })] },
      { id: "4D", at: 30, kind: "release", code: "4D", title: "Expectativa del cliente · regresa la presión por velocidad", gated: true, reason: "Los pods sostienen posiciones; es momento de rotarlas.", text: "Áurea solicita usar la automatización en la siguiente incorporación de 30 días. El cliente no prescribe cómo debe HITO gobernar la decisión.", effects: [all({ pressure: 15 })] },
      { id: "m7", at: 31, kind: "message", actor: "aurea", text: "Usen la automatización en la siguiente incorporación. El proceso manual actual es demasiado lento." },
      { id: "m8", at: 34, kind: "message", actor: "facilitator", text: "Rotación: ÚSALA → DESAFÍALA → ASÚMANLA. Ningún equipo conserva su posición." },
      { id: "o3", at: 40, kind: "observer", pod: 3, text: "Pod 3 se adhiere a la identidad \"anti-IA\". Forzar la rotación.", effects: [pod(3, { certainty: 85, alert: "Identidad anti-IA" })] },
      { id: "m9", at: 48, kind: "message", actor: "daniel", text: "Opción B: piloto de 90 días con humano en el loop en consumo y automotriz; arrendamiento permanece manual. Trade-off: escalamiento más lento." },
      { id: "o4", at: 55, kind: "observer", text: "Charter de Juicio: Pods 1 y 2 dejan \"aceptación de riesgo\" y \"decisión final\" bajo responsabilidad humana explícita.", effects: [pod(2, { decided: true, certainty: 50, evidence: 75 }), pod(3, { decided: true, certainty: 60 }), pod(4, { decided: true, certainty: 65 })] },
      { id: "e1", at: 70, kind: "end", text: "Fin del Acto IV. Espejo de Liderazgo: ¿qué cambió en el sistema y qué cambió en ti?" },
    ],
  },
];

export function getAct(actId: ActId): Act {
  const act = ACTS.find((a) => a.id === actId);
  if (!act) throw new Error(`Acto desconocido: ${actId}`);
  return act;
}

export function initialPods(): PodState[] {
  return POD_NAMES.map((name, i) => ({ number: i + 1, name, pressure: 0, certainty: 0, evidence: 0, decidedAt: null, deliverable: "", alerts: [] }));
}

export function initialState(actId: ActId = "I"): SimState {
  const base: SimState = { actId, clock: 0, running: false, speed: 1, offset: 0, fired: [], pending: null, pods: initialPods() };
  return reduce(base, { type: "tick", dt: 0 });
}

const clamp = (n: number) => Math.max(0, Math.min(100, Math.round(n)));

function applyEffects(pods: PodState[], effects: Effect[] | undefined, clock: number): PodState[] {
  if (!effects?.length) return pods;
  return pods.map((p) => {
    let next = p;
    for (const e of effects) {
      if (e.pod !== "all" && e.pod !== p.number) continue;
      next = {
        ...next,
        pressure: e.pressure === undefined ? next.pressure : clamp(next.pressure + e.pressure),
        certainty: e.certainty === undefined ? next.certainty : clamp(e.certainty),
        evidence: e.evidence === undefined ? next.evidence : clamp(e.evidence),
        decidedAt: e.decided ? clock : e.deliverable ? null : next.decidedAt,
        deliverable: e.deliverable ?? next.deliverable,
        alerts: e.alert && !next.alerts.includes(e.alert) ? [...next.alerts, e.alert] : next.alerts,
      };
    }
    return next;
  });
}

/** Minuto efectivo en que dispara un evento, contando los "Frenar" acumulados. */
export function effectiveAt(ev: SimEvent, state: SimState): number {
  return ev.at === 0 ? 0 : ev.at + state.offset;
}

export function unfired(state: SimState): SimEvent[] {
  return getAct(state.actId).events.filter((e) => !state.fired.includes(e.id));
}

export function firedEvents(state: SimState): SimEvent[] {
  const events = getAct(state.actId).events;
  return state.fired.map((id) => events.find((e) => e.id === id)!).filter(Boolean);
}

function fire(state: SimState, ev: SimEvent): SimState {
  return { ...state, fired: [...state.fired, ev.id], pods: applyEffects(state.pods, ev.effects, state.clock) };
}

function advance(state: SimState, dt: number): SimState {
  const target = state.clock + dt;
  let s = state;
  for (const ev of unfired(state)) {
    const at = effectiveAt(ev, s);
    if (at > target) break;
    if (ev.gated && s.pending !== ev.id) {
      // El Director propone; el reloj se detiene hasta que el facilitador decide.
      return { ...s, clock: at, running: false, pending: ev.id };
    }
    s = fire({ ...s, clock: at, pending: null }, ev);
    if (ev.kind === "end") return { ...s, running: false };
  }
  return { ...s, clock: target };
}

export function reduce(state: SimState, action: SimAction): SimState {
  switch (action.type) {
    case "tick":
      if (state.pending) return state;
      return advance(state, action.dt);
    case "play":
      return state.pending || isFinished(state) ? state : { ...state, running: true };
    case "pause":
      return { ...state, running: false };
    case "speed":
      return { ...state, speed: action.speed };
    case "approve": {
      if (!state.pending) return state;
      const ev = getAct(state.actId).events.find((e) => e.id === state.pending);
      if (!ev) return { ...state, pending: null };
      return { ...fire({ ...state, pending: null }, ev), running: true };
    }
    case "hold":
      if (!state.pending) return state;
      return { ...state, pending: null, offset: state.offset + HOLD_MINUTES, running: true };
    case "act":
      return initialState(action.actId);
    case "reset":
      return initialState(state.actId);
  }
}

export function isFinished(state: SimState): boolean {
  return state.fired.some((id) => getAct(state.actId).events.find((e) => e.id === id)?.kind === "end");
}

export function pendingEvent(state: SimState): SimEvent | null {
  return state.pending ? getAct(state.actId).events.find((e) => e.id === state.pending) ?? null : null;
}

/** Siguiente liberación con compuerta todavía no disparada, y en cuántos minutos. */
export function nextRelease(state: SimState): { event: SimEvent; inMinutes: number } | null {
  const ev = unfired(state).find((e) => e.kind === "release");
  return ev ? { event: ev, inMinutes: Math.max(0, effectiveAt(ev, state) - state.clock) } : null;
}

/** Personaje cuyo siguiente mensaje está a menos de 2 minutos: "escribiendo…". */
export function typingActor(state: SimState): Actor | null {
  if (state.pending || !state.running) return null;
  const ev = unfired(state).find((e) => e.kind === "message");
  if (!ev?.actor) return null;
  return effectiveAt(ev, state) - state.clock <= 2 ? ACTORS[ev.actor] ?? null : null;
}

export function formatClock(minutesOfDay: number): string {
  const m = ((Math.floor(minutesOfDay) % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}

export function caseClock(state: SimState): string {
  return formatClock(getAct(state.actId).startMinutes + state.clock);
}

/** Minutos que faltan para la hora límite del acto (negativo si ya pasó). */
export function minutesToDeadline(state: SimState): number {
  const act = getAct(state.actId);
  return act.deadlineMinutes - (act.startMinutes + state.clock);
}

export function formatCountdown(minutes: number): string {
  const sign = minutes < 0 ? "−" : "";
  const abs = Math.abs(Math.floor(minutes));
  return `${sign}${Math.floor(abs / 60)}:${String(abs % 60).padStart(2, "0")}`;
}

export type PressureLevel = "low" | "mid" | "high";

export function pressureLevel(pressure: number): PressureLevel {
  return pressure >= 70 ? "high" : pressure >= 45 ? "mid" : "low";
}

/** Códigos de liberación del acto con su estado para el mapa de liberación. */
export function releaseMap(state: SimState): { code: string; title: string; status: "fired" | "pending" | "next" | "later" }[] {
  const releases = getAct(state.actId).events.filter((e) => e.kind === "release");
  let nextSeen = false;
  return releases.map((e) => {
    let status: "fired" | "pending" | "next" | "later" = "later";
    if (state.fired.includes(e.id)) status = "fired";
    else if (state.pending === e.id) status = "pending";
    else if (!nextSeen) { status = "next"; nextSeen = true; }
    return { code: e.code ?? e.id, title: e.title ?? "", status };
  });
}
