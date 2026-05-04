from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.exceptions import ResourceConflictError
from backend.models import Base, CheckInTask, User
from backend.schemas.task import TaskCreate, TaskUpdate
from backend.services import scheduler_service
from backend.services.task_service import TaskService


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def add_user(db_session, alias: str) -> User:
    user = User(alias=alias)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def payload(thread_id: str, **extra: Any) -> str:
    return json.dumps({"ThreadId": thread_id, **extra}, ensure_ascii=False)


def test_create_task_persists_thread_id_identity(db_session) -> None:
    user = add_user(db_session, "alice")

    task = TaskService.create_task(
        user.id,
        TaskCreate(
            payload_config=payload("thread-1", Signature="sig"),
            name="Morning",
            cron_expression="0 8 * * *",
        ),
        db_session,
    )

    assert task.thread_id == "thread-1"
    assert task.payload_config == payload("thread-1", Signature="sig")
    assert task.cron_expression == "0 8 * * *"


def test_same_user_duplicate_thread_id_is_structured_conflict(db_session) -> None:
    user = add_user(db_session, "alice")
    first = TaskCreate(payload_config=payload("thread-1"), name="First")
    duplicate = TaskCreate(payload_config=payload("thread-1"), name="Duplicate")

    TaskService.create_task(user.id, first, db_session)

    with pytest.raises(ResourceConflictError) as exc_info:
        TaskService.create_task(user.id, duplicate, db_session)

    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "TASK_IDENTITY_CONFLICT"


def test_different_users_can_share_thread_id(db_session) -> None:
    alice = add_user(db_session, "alice")
    bob = add_user(db_session, "bob")

    alice_task = TaskService.create_task(
        alice.id, TaskCreate(payload_config=payload("shared-thread")), db_session
    )
    bob_task = TaskService.create_task(
        bob.id, TaskCreate(payload_config=payload("shared-thread")), db_session
    )

    assert alice_task.thread_id == "shared-thread"
    assert bob_task.thread_id == "shared-thread"
    assert alice_task.user_id != bob_task.user_id


def test_update_task_rejects_duplicate_thread_id(db_session) -> None:
    user = add_user(db_session, "alice")
    first = TaskService.create_task(
        user.id, TaskCreate(payload_config=payload("thread-1")), db_session
    )
    second = TaskService.create_task(
        user.id, TaskCreate(payload_config=payload("thread-2")), db_session
    )

    with pytest.raises(ResourceConflictError):
        TaskService.update_task(
            second.id,
            TaskUpdate(payload_config=payload("thread-1")),
            db_session,
        )

    db_session.refresh(first)
    db_session.refresh(second)
    assert first.thread_id == "thread-1"
    assert second.thread_id == "thread-2"


def test_task_enrichment_uses_stored_thread_id(db_session) -> None:
    user = add_user(db_session, "alice")
    task = CheckInTask(
        user_id=user.id,
        thread_id="stored-thread",
        payload_config=payload("payload-thread"),
        name="Task",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    enriched = TaskService.enrich_task_with_check_in_info(task, db_session)

    assert enriched["thread_id"] == "stored-thread"


def test_template_created_duplicate_task_preserves_structured_conflict(db_session) -> None:
    from backend.models import TaskTemplate
    from backend.services.template_service import TemplateService

    user = add_user(db_session, "alice")
    template = TaskTemplate(name="Daily", field_config="{}", is_active=True)
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)

    TemplateService.create_task_from_template(
        template_id=template.id,
        thread_id="thread-1",
        field_values={},
        user_id=user.id,
        task_name="First",
        db=db_session,
    )

    with pytest.raises(ResourceConflictError) as exc_info:
        TemplateService.create_task_from_template(
            template_id=template.id,
            thread_id="thread-1",
            field_values={},
            user_id=user.id,
            task_name="Duplicate",
            db=db_session,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "TASK_IDENTITY_CONFLICT"


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: dict[str, object] = {}
        self.added: list[str] = []
        self.removed: list[str] = []

    def get_job(self, job_id: str):
        return self.jobs.get(job_id)

    def remove_job(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)
        self.removed.append(job_id)

    def add_job(self, **kwargs) -> None:
        job_id = kwargs["id"]
        self.jobs[job_id] = kwargs
        self.added.append(job_id)


def test_scheduler_sync_skips_invalid_cron_and_removes_existing_job(monkeypatch) -> None:
    fake_scheduler = FakeScheduler()
    fake_scheduler.jobs["task_12"] = object()
    monkeypatch.setattr(scheduler_service, "scheduler", fake_scheduler)
    task = CheckInTask(id=12, thread_id="thread-1", payload_config=payload("thread-1"))
    task.is_active = True
    task.cron_expression = "invalid cron"

    scheduled = scheduler_service.sync_scheduled_task(task)

    assert scheduled is False
    assert fake_scheduler.added == []
    assert fake_scheduler.removed == ["task_12"]


def test_scheduler_sync_is_noop_when_scheduler_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(scheduler_service, "scheduler", None)
    task = CheckInTask(id=12, thread_id="thread-1", payload_config=payload("thread-1"))
    task.is_active = True
    task.cron_expression = "0 8 * * *"

    assert scheduler_service.sync_scheduled_task(task) is False


def test_datetime_normalization_does_not_access_unmapped_properties(
    db_session, monkeypatch
) -> None:
    user = add_user(db_session, "alice")
    user_id = user.id
    db_session.expunge_all()

    def explode(self):
        raise RuntimeError("unmapped property accessed")

    monkeypatch.setattr(User, "explosive_property", property(explode), raising=False)

    loaded = db_session.query(User).filter(User.id == user_id).one()

    assert loaded.created_at.tzinfo is not None


@pytest.mark.asyncio
async def test_task_route_preserves_structured_service_errors(monkeypatch, db_session) -> None:
    from backend.api.tasks import get_tasks

    user = User(id=1, alias="alice")

    def raise_conflict(*args, **kwargs):
        raise ResourceConflictError("duplicate", error_code="TASK_IDENTITY_CONFLICT")

    monkeypatch.setattr(TaskService, "get_user_tasks", raise_conflict)

    with pytest.raises(ResourceConflictError):
        await get_tasks(current_user=user, db=db_session)
