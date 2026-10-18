"""Seed demo: python -m app.seed. Idempotente por slug/email y por módulo. Todo el contenido es ficticio y lleva prefijo [Demo]."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document
from app.models.engagement import Engagement
from app.models.enums import Health, Level, OrganizationKind, Role
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.lab import LabSession
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.organization import Organization
from app.models.user import User
from app.schemas.action import ActionCreate
from app.schemas.comment import CommentCreate
from app.schemas.decision import DecisionCreate
from app.schemas.document import DocumentCreate, DocumentLinkCreate
from app.schemas.finding import FindingCreate
from app.schemas.initiative import InitiativeCreate
from app.schemas.lab import ActionContractCreate, CtaCreate, LabSessionCreate, ParticipantCreate, PodCreate
from app.schemas.meeting import MeetingCreate
from app.schemas.milestone import MilestoneCreate
from app.services import actions as actions_service
from app.services import comments as comments_service
from app.services import decisions as decisions_service
from app.services import documents as documents_service
from app.services import findings as findings_service
from app.services import initiatives as initiatives_service
from app.services import lab as lab_service
from app.services import meetings as meetings_service
from app.services import milestones as milestones_service


def _org(db: Session, name: str, slug: str, kind: OrganizationKind) -> Organization:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        org = Organization(name=name, slug=slug, kind=kind)
        db.add(org)
        db.flush()
    return org


def _user(db: Session, org: Organization, email: str, name: str, role: Role, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(organization_id=org.id, email=email, full_name=name, password_hash=hash_password(password), role=role)
        db.add(user)
        db.flush()
    return user


def _has_rows(db: Session, model, engagement: Engagement) -> bool:
    return db.scalar(select(model).where(model.engagement_id == engagement.id).limit(1)) is not None


def _initiatives(db: Session, engagement: Engagement) -> list[Initiative]:
    return list(db.scalars(select(Initiative).where(Initiative.engagement_id == engagement.id).order_by(Initiative.created_at)))


def _seed_delivery(db: Session, admin: User, collab: User, engagement: Engagement) -> None:
    """Findings, initiatives y actions del plan 1."""
    if _has_rows(db, Finding, engagement):
        return
    findings_data = [
        ("[Demo] Conciliación diaria dependiente de hojas de cálculo", "Quick Win", "Operaciones", Level.HIGH),
        ("[Demo] Reportes a clientes institucionales generados manualmente", "Opportunity", "Operaciones", Level.HIGH),
        ("[Demo] Sin inventario único de procesos críticos", "Gap", "Procesos", Level.MEDIUM),
        ("[Demo] Aprobaciones concentradas en pocas personas", "Risk", "Gobierno", Level.CRITICAL),
        ("[Demo] Datos de cartera replicados en varios sistemas", "Strategic Insight", "Datos", Level.HIGH),
    ]
    for title, ftype, area, impact in findings_data:
        findings_service.create_finding(
            db, user=admin, engagement=engagement,
            data=FindingCreate(title=title, type=ftype, area=area, impact=impact, description="Contenido ficticio de demostración.", recommendation="Recomendación ficticia de demostración."),
        )
    initiatives_data = [
        ("[Demo] Automatización de conciliación diaria", "Execution", 40),
        ("[Demo] Reporting institucional automatizado", "Design", 15),
        ("[Demo] Mapa de procesos críticos", "Discovery", 5),
        ("[Demo] Modelo de gobierno de aprobaciones", "Validation", 25),
    ]
    initiatives = []
    for name, status, progress in initiatives_data:
        initiatives.append(initiatives_service.create_initiative(
            db, user=admin, engagement=engagement,
            data=InitiativeCreate(name=name, status=status, progress_pct=progress, objective="Objetivo ficticio de demostración.", hito_owner="Owner HiTO (demo)", target_date=date.today() + timedelta(days=60)),
        ))
    actions_data = [
        ("[Demo] Levantar inventario de hojas de cálculo", 0, collab.id, 7),
        ("[Demo] Definir reglas de conciliación", 0, None, 14),
        ("[Demo] Validar formato de reporte con cliente piloto", 1, collab.id, 10),
        ("[Demo] Entrevistar responsables de proceso", 2, None, 5),
        ("[Demo] Documentar matriz de aprobaciones actual", 3, collab.id, 12),
        ("[Demo] Proponer umbrales de delegación", 3, None, 20),
        ("[Demo] Revisar fuentes de datos de cartera", 2, None, 18),
        ("[Demo] Preparar sesión de validación con dirección", 1, None, 9),
    ]
    for title, idx, owner_id, days in actions_data:
        actions_service.create_action(
            db, user=admin, engagement=engagement,
            data=ActionCreate(title=title, initiative_id=initiatives[idx].id, owner_user_id=owner_id, owner_name="" if owner_id else "Equipo Syner", organization_side="CLIENT" if owner_id else "SYNER", due_date=date.today() + timedelta(days=days), priority=Level.HIGH if days < 10 else Level.MEDIUM),
        )
    db.commit()


def _is_demo_engagement(initiatives: list[Initiative]) -> bool:
    return len(initiatives) >= 4 and all(i.name.startswith("[Demo]") for i in initiatives)


ORION_DOCUMENTS = [
    ("Executive Leadership Lab — Facilitator Playbook", "0.9", "HITO_Executive_Leadership_Lab_Facilitator_Playbook_v0.9.pdf"),
    ("Project ORION — Leadership Pressure Room Case Book (ES)", "1.0", "HITO_Leadership_Pressure_Room_Project_ORION_Case_Book_ES_v1.0.pdf"),
    ("Project ORION — Participant Handout Master (ES)", "1.0", "HITO_Participant_Handout_Master_Project_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 00: Pre-Work (ES)", "1.0", "HITO_Participant_Packet_00_PreWork_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 01: Lab 01 DECIDIR (ES)", "1.0", "HITO_Participant_Packet_01_Lab01_DECIDIR_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 02: Lab 02 CONFRONTAR (ES)", "1.0", "HITO_Participant_Packet_02_Lab02_CONFRONTAR_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 03: Lab 03 ALINEAR (ES)", "1.0", "HITO_Participant_Packet_03_Lab03_ALINEAR_ORION_ES_v1.0.pdf"),
    ("Project ORION — Participant Packet 04: Lab 04 TRANSFORMAR (ES)", "1.0", "HITO_Participant_Packet_04_Lab04_TRANSFORMAR_ORION_ES_v1.0.pdf"),
]


def _seed_orion_documents(db: Session, admin: User, engagement: Engagement) -> None:
    """Material del Executive Leadership Lab / Project ORION registrado como Documents internos (spec sección 7).

    No es dato demo: se registra siempre, idempotente por nombre. La URL queda vacía porque el primer release
    no integra almacenamiento documental; Syner la completa desde la UI cuando publique los archivos.
    """
    existing = set(db.scalars(select(Document.name).where(Document.engagement_id == engagement.id)))
    for name, version, filename in ORION_DOCUMENTS:
        if name in existing:
            continue
        documents_service.create_document(
            db, user=admin, engagement=engagement,
            data=DocumentCreate(
                name=name, category="Deliverables", version=version, url="", tags=["orion", "leadership-lab"],
                internal_only=True, description=f"Material del Executive Leadership Lab / Project ORION. Archivo fuente: docs/{filename}",
            ),
        )
    db.commit()


def _seed_lab(db: Session, admin: User, engagement: Engagement) -> None:
    """Sesiones, pods, participantes, CTAs y contratos demo del plan 3. Todo ficticio, con prefijo [Demo]."""
    today = date.today()
    if not _is_demo_engagement(_initiatives(db, engagement)):
        print("Seed: el engagement no contiene el set demo de initiatives; se omiten los datos demo del Lab.")
        return
    if _has_rows(db, LabSession, engagement):
        return
    sessions = []
    for number, days, status, attendance in ((1, -20, "Done", 18), (2, -6, "Done", 17), (3, 8, "Planned", None), (4, 22, "Planned", None)):
        sessions.append(lab_service.create_session(
            db, user=admin, engagement=engagement,
            data=LabSessionCreate(number=number, held_on=today + timedelta(days=days), status=status, attendance_count=attendance, syner_notes="[Demo] Notas internas de facilitación." if status == "Done" else ""),
        ))
    pods = [
        lab_service.create_pod(db, user=admin, engagement=engagement, data=PodCreate(number=number, name=f"[Demo] Pod {name}"))
        for number, name in ((1, "Norte"), (2, "Sur"), (3, "Centro"), (4, "Bajío"))
    ]
    areas = ("Operaciones", "Finanzas", "Comercial", "Tecnología", "Personas")
    participants = [
        lab_service.create_participant(
            db, user=admin, engagement=engagement,
            data=ParticipantCreate(full_name=f"[Demo] Participante {i + 1:02d}", area=areas[i % 5], title="Gerente (demo)", pod_id=pods[i % 4].id),
        )
        for i in range(20)
    ]
    ctas = []
    for participant_idx, session_idx, status in ((0, 0, "Evidenced"), (0, 1, "In Progress"), (1, 0, "Evidenced"), (1, 1, "Committed"), (2, 0, "Evidenced"), (3, 0, "In Progress"), (4, 1, "In Progress"), (5, 0, "Dropped")):
        ctas.append(lab_service.create_cta(
            db, user=admin, engagement=engagement,
            data=CtaCreate(
                participant_id=participants[participant_idx].id, session_id=sessions[session_idx].id,
                trigger="[Demo] Situación de presión en comité.", behavior="[Demo] Conducta comprometida de demostración.",
                stakeholder="Equipo directo (demo)", evidence_expected="[Demo] Evidencia esperada.", due_date=today + timedelta(days=14),
                accountability_partner="[Demo] Partner", impact="[Demo] Impacto esperado.", status=status,
                evidence_notes="[Demo] Evidencia registrada." if status == "Evidenced" else "",
            ),
        ))
    lab_service.create_contract(
        db, user=admin, engagement=engagement,
        data=ActionContractCreate(participant_id=participants[0].id, start_date=today - timedelta(days=5), success_signal="[Demo] Señal de éxito observable.", status="Active", cta_ids=[ctas[0].id, ctas[1].id]),
    )
    lab_service.create_contract(
        db, user=admin, engagement=engagement,
        data=ActionContractCreate(participant_id=participants[1].id, success_signal="[Demo] Pendiente de activar.", status="Draft", cta_ids=[ctas[2].id]),
    )
    db.commit()


def _seed_client_room(db: Session, admin: User, collab: User, engagement: Engagement) -> None:
    """Milestones, meetings, decisions, documents y comments del plan 2."""
    today = date.today()
    now = datetime.now(timezone.utc)
    initiatives = _initiatives(db, engagement)
    if not _is_demo_engagement(initiatives):
        print("Seed: el engagement no contiene el set demo de initiatives; se omiten los datos demo del client room.")
        return

    if not _has_rows(db, Milestone, engagement):
        milestones_data = [
            ("[Demo] Entrevistas de discovery completadas", "Discover", -10, "Done", None),
            ("[Demo] Diagnóstico operativo consolidado", "Diagnose", 7, "In Progress", 2),
            ("[Demo] Diseño del modelo de conciliación", "Design", 21, "Planned", 0),
            ("[Demo] Portafolio priorizado con dirección", "Prioritize", 30, "Planned", None),
            ("[Demo] Piloto de conciliación automatizada", "Execute", 60, "Planned", 0),
            ("[Demo] Primer tablero de KPIs de transformación", "Measure", 90, "Planned", None),
        ]
        for name, phase, days, status, idx in milestones_data:
            milestones_service.create_milestone(
                db, user=admin, engagement=engagement,
                data=MilestoneCreate(name=name, phase=phase, due_date=today + timedelta(days=days), status=status, owner="Equipo Syner", initiative_id=initiatives[idx].id if idx is not None else None, deliverable="Entregable ficticio de demostración."),
            )

    meetings = list(db.scalars(select(Meeting).where(Meeting.engagement_id == engagement.id).order_by(Meeting.held_on)))
    if not meetings:
        meetings_data = [
            ("[Demo] Kick-off del engagement", -12, "Alinear objetivos y gobierno del programa."),
            ("[Demo] Comité de transformación #1", -5, "Revisar hallazgos preliminares y acordar prioridades."),
            ("[Demo] Sesión de validación de diagnóstico", 2, "Validar el diagnóstico operativo con dirección."),
        ]
        for title, days, objective in meetings_data:
            meetings.append(meetings_service.create_meeting(
                db, user=admin, engagement=engagement,
                data=MeetingCreate(title=title, held_on=now + timedelta(days=days), participants="Dirección HiTO (demo), Equipo Syner", objective=objective, summary="Resumen ficticio de demostración.", discussion="Discusión ficticia de demostración.", next_steps="Siguientes pasos ficticios de demostración."),
            ))

    if not _has_rows(db, Decision, engagement):
        decisions_data = [
            ("[Demo] Consolidar la conciliación en una sola plataforma", "Proposed", 0, 1, None),
            ("[Demo] Nombrar owner único del reporting institucional", "Under Review", 1, None, None),
            ("[Demo] Aprobar el alcance de la fase de discovery", "Approved", None, 0, today - timedelta(days=10)),
        ]
        for title, status, idx, meeting_idx, decided_on in decisions_data:
            decisions_service.create_decision(
                db, user=admin, engagement=engagement,
                data=DecisionCreate(title=title, status=status, context="Contexto ficticio de demostración.", alternatives="A) Mantener. B) Cambiar.", syner_recommendation="Recomendación ficticia de demostración.", owner_name="Dirección HiTO (demo)", decided_on=decided_on, initiative_id=initiatives[idx].id if idx is not None else None, meeting_id=meetings[meeting_idx].id if meeting_idx is not None else None),
            )

    if not _has_rows(db, Document, engagement):
        documents_data = [
            ("[Demo] Plan de trabajo del engagement", "Strategy", "1.0", False, None),
            ("[Demo] Diagnóstico operativo preliminar", "Assessment", "0.9", False, ("initiative", initiatives[2].id)),
            ("[Demo] Minuta Comité de transformación #1", "Meetings", "1.0", False, ("meeting", meetings[1].id)),
            ("[Demo] Inventario de hojas de cálculo", "Evidence", "1.0", False, ("initiative", initiatives[0].id)),
            ("[Demo] Notas internas del equipo Syner", "Reports", "0.1", True, None),
        ]
        for name, category, version, internal, link in documents_data:
            document = documents_service.create_document(
                db, user=admin, engagement=engagement,
                data=DocumentCreate(name=name, category=category, version=version, url="", doc_date=today - timedelta(days=3), tags=["demo"], internal_only=internal, description="Documento ficticio de demostración."),
            )
            if link is not None:
                documents_service.add_link(db, user=admin, document=document, data=DocumentLinkCreate(entity_type=link[0], entity_id=link[1]))

    if not _has_rows(db, Comment, engagement):
        comments_service.create_comment(db, user=collab, engagement=engagement, data=CommentCreate(entity_type="initiative", entity_id=initiatives[0].id, body="[Demo] Iniciamos el inventario esta semana."))
        comments_service.create_comment(db, user=admin, engagement=engagement, data=CommentCreate(entity_type="initiative", entity_id=initiatives[0].id, body="[Demo] Perfecto, lo revisamos en el próximo comité."))
    db.commit()


def seed(db: Session) -> None:
    settings = get_settings()
    if settings.is_production and (
        settings.seed_syner_password == "syner-demo"
        or settings.seed_exec_password == "exec-demo"
        or settings.seed_collab_password == "collab-demo"
    ):
        raise RuntimeError("En producción define SEED_SYNER_PASSWORD, SEED_EXEC_PASSWORD y SEED_COLLAB_PASSWORD")
    syner = _org(db, "Syner", "syner", OrganizationKind.CONSULTANCY)
    hito = _org(db, "HiTO", "hito", OrganizationKind.CLIENT)
    admin = _user(db, syner, "admin@syner.demo", "Syner Admin", Role.SYNER_ADMIN, settings.seed_syner_password)
    _user(db, hito, "exec@hito.demo", "Dirección HiTO (demo)", Role.HITO_EXECUTIVE, settings.seed_exec_password)
    collab = _user(db, hito, "collab@hito.demo", "Colaborador HiTO (demo)", Role.HITO_COLLABORATOR, settings.seed_collab_password)

    engagement = db.scalar(select(Engagement).where(Engagement.organization_id == hito.id))
    if engagement is None:
        engagement = Engagement(
            organization_id=hito.id,
            name="Syner × HiTO Transformation Program",
            subtitle="Executive advisory, transformation & decision intelligence",
            health=Health.ON_TRACK,
            progress_pct=10,
            executive_summary="[Demo] Fase de discovery en curso. Se han realizado entrevistas iniciales y se está consolidando el diagnóstico.",
            start_date=date.today() - timedelta(days=14),
        )
        db.add(engagement)
        db.flush()
    db.commit()

    _seed_delivery(db, admin, collab, engagement)
    _seed_client_room(db, admin, collab, engagement)
    _seed_lab(db, admin, engagement)
    _seed_orion_documents(db, admin, engagement)


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("Seed completado.")
