import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import ContractStatus, CtaStatus, LabSessionStatus, LabSessionTheme
from app.models.lab import ActionContract, ActionContractCta, Cta, LabSession, Participant, Pod


def _common(world, engagement):
    return dict(organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=world.admin.id)


def test_lab_models_persist_with_defaults_and_contract_exposes_cta_ids(db, world):
    common = _common(world, world.eng_a)
    session = LabSession(number=1, name="The Brain Under Pressure", theme=LabSessionTheme.DECIDIR, **common)
    pod = Pod(number=1, name="Pod Norte", **common)
    db.add_all([session, pod])
    db.flush()
    participant = Participant(full_name="Ana Ruiz", pod_id=pod.id, **common)
    db.add(participant)
    db.flush()
    cta = Cta(participant_id=participant.id, session_id=session.id, behavior="Dar feedback directo", **common)
    db.add(cta)
    db.flush()
    contract = ActionContract(participant_id=participant.id, **common)
    contract.ctas.append(ActionContractCta(cta_id=cta.id))
    db.add(contract)
    db.commit()
    for obj in (session, participant, cta, contract):
        db.refresh(obj)
    assert session.status == LabSessionStatus.PLANNED
    assert session.held_on is None and session.attendance_count is None and session.syner_notes == ""
    assert participant.is_active is True and participant.area == "" and participant.title == ""
    assert cta.status == CtaStatus.COMMITTED and cta.trigger == "" and cta.evidence_notes == "" and cta.due_date is None
    assert contract.status == ContractStatus.DRAFT
    assert contract.start_date is None and contract.review_30_date is None and contract.review_60_date is None
    assert contract.cta_ids == [cta.id]


def test_session_and_pod_numbers_are_unique_per_engagement(db, world):
    a = _common(world, world.eng_a)
    b = _common(world, world.eng_b)
    db.add_all([
        LabSession(number=1, name="S", theme=LabSessionTheme.DECIDIR, **a),
        LabSession(number=1, name="S", theme=LabSessionTheme.DECIDIR, **b),
        Pod(number=1, name="P", **a),
        Pod(number=1, name="P", **b),
    ])
    db.commit()
    db.add(LabSession(number=1, name="dup", theme=LabSessionTheme.DECIDIR, **a))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    db.add(Pod(number=1, name="dup", **a))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
