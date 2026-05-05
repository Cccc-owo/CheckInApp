from __future__ import annotations

from pathlib import Path


FRONTEND_ROOT = Path(__file__).resolve().parents[1] / "apps" / "frontend"
SRC_ROOT = FRONTEND_ROOT / "src"


def test_frontend_has_business_app_structure() -> None:
    expected_files = [
        "api/client.ts",
        "api/index.ts",
        "api/types.ts",
        "app/router.ts",
        "app/auth.ts",
        "components/AppLayout.vue",
        "components/ui.ts",
        "views/LoginView.vue",
        "views/PendingApprovalView.vue",
        "views/DashboardView.vue",
        "views/TasksView.vue",
        "views/TaskRecordsView.vue",
        "views/RecordsView.vue",
        "views/SettingsView.vue",
        "views/NotFoundView.vue",
        "views/admin/AdminUsersView.vue",
        "views/admin/AdminTemplatesView.vue",
        "views/admin/AdminRecordsView.vue",
        "views/admin/AdminLogsView.vue",
        "views/admin/AdminStatsView.vue",
        "views/admin/AdminEmailSettingsView.vue",
        "utils/format.ts",
    ]

    missing = [path for path in expected_files if not (SRC_ROOT / path).is_file()]

    assert missing == []


def test_frontend_routes_cover_user_and_admin_workflows() -> None:
    router = (SRC_ROOT / "app" / "router.ts").read_text(encoding="utf-8")

    for path in [
        "/login",
        "/pending-approval",
        "/dashboard",
        "/tasks",
        "/tasks/:taskId/records",
        "/records",
        "/settings",
        "/admin/users",
        "/admin/templates",
        "/admin/records",
        "/admin/logs",
        "/admin/stats",
        "/admin/email-settings",
    ]:
        assert path in router


def test_frontend_admin_api_covers_email_settings() -> None:
    api = (SRC_ROOT / "api" / "index.ts").read_text(encoding="utf-8")

    assert "/api/admin/email_settings" in api


def test_frontend_replaces_starter_component() -> None:
    app = (SRC_ROOT / "App.vue").read_text(encoding="utf-8")

    assert "HelloWorld" not in app
    assert not (SRC_ROOT / "components" / "HelloWorld.vue").exists()
