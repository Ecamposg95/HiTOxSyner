"""Seed demo: python -m app.seed. Idempotente por slug/email. Todo el contenido es ficticio y lleva prefijo [Demo]."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.engagement import Engagement
from app.models.enums import Health, Level, OrganizationKind, Role
from app.models.finding import Finding
from app.models.organization import Organization
from app.models.user import User
from app.schemas.action import ActionCreate
from app.schemas.finding import FindingCreate
from app.schemas.initiative import InitiativeCreate
from app.services import actions as actions_service
from app.services import findings as findings_service
from app.services import initiatives as initiatives_service


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


def seed(db: Session) -> None:
    settings = get_settings()
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

    if db.scalar(select(Finding).where(Finding.engagement_id == engagement.id)) is not None:
        return

    findings_data = [
        ("[Demo] Conciliación diaria dependiente de hojas de cálculo", "Quick Win", "Operaciones", Level.HIGH),
        ("[Demo] Reportes a clientes institucionales generados manualmente", "Opportunity", "Operaciones", Level.HIGH),
        ("[Demo] Sin inventario único de procesos críticos", "Gap", "Procesos", Level.MEDIUM),
        ("[Demo] Aprobaciones concentradas en pocas personas", "Risk", "Gobierno", Level.CRITICAL),
        ("[Demo] Datos de cartera replicados en varios sistemas", "Strategic Insight", "Datos", Level.HIGH),
    ]
    findings = []
    for title, ftype, area, impact in findings_data:
        findings.append(findings_service.create_finding(
            db, user=admin, engagement=engagement,
            data=FindingCreate(title=title, type=ftype, area=area, impact=impact, description="Contenido ficticio de demostración.", recommendation="Recomendación ficticia de demostración."),
        ))

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


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("Seed completado.")
