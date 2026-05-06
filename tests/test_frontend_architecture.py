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


def test_frontend_covers_pending_email_verification_flow() -> None:
    api = (SRC_ROOT / "api" / "index.ts").read_text(encoding="utf-8")
    pending = (SRC_ROOT / "views" / "PendingApprovalView.vue").read_text(encoding="utf-8")

    assert "/api/users/me/email" in api
    assert "/api/users/me/email/verify" in api
    assert "自动吊销" in pending
    assert "验证码" in pending


def test_frontend_admin_approval_policy_warnings_are_visible() -> None:
    admin_users = (SRC_ROOT / "views" / "admin" / "AdminUsersView.vue").read_text(encoding="utf-8")
    email_settings = (SRC_ROOT / "views" / "admin" / "AdminEmailSettingsView.vue").read_text(
        encoding="utf-8"
    )

    assert "allow_unverified_email" in admin_users
    assert "邮箱未验证" in admin_users
    assert "require_admin_approval_for_registration" in email_settings
    assert "require_verified_email_for_approval" in email_settings
    assert "审批前要求验证邮箱" in email_settings
    assert "关闭管理员审批" in email_settings
    assert "未验证邮箱审批警告" not in email_settings


def test_frontend_admin_users_show_authorization_summary() -> None:
    admin_users = (SRC_ROOT / "views" / "admin" / "AdminUsersView.vue").read_text(encoding="utf-8")

    assert "formatUserAuthorizationSummary" in admin_users
    assert "jwt_exp" in admin_users


def test_frontend_replaces_starter_component() -> None:
    app = (SRC_ROOT / "App.vue").read_text(encoding="utf-8")

    assert "HelloWorld" not in app
    assert not (SRC_ROOT / "components" / "HelloWorld.vue").exists()


def test_dashboard_refresh_uses_qr_api_instead_of_login_redirect() -> None:
    dashboard = (SRC_ROOT / "views" / "DashboardView.vue").read_text(encoding="utf-8")

    assert "authApi.requestQRCode" in dashboard
    assert "authApi.getQRCodeStatus" in dashboard
    assert "authApi.cancelQRCodeSession" in dashboard
    assert "router.navigate('/login')" not in dashboard


def test_dashboard_qr_refresh_uses_dialog() -> None:
    dashboard = (SRC_ROOT / "views" / "DashboardView.vue").read_text(encoding="utf-8")

    assert "@/components/ui/dialog" in dashboard
    assert "qrRefreshDialogOpen" in dashboard
    assert "<Dialog" in dashboard
    assert "<DialogContent" in dashboard


def test_settings_email_changes_use_verification_flow() -> None:
    settings = (SRC_ROOT / "views" / "SettingsView.vue").read_text(encoding="utf-8")
    api = (SRC_ROOT / "api" / "index.ts").read_text(encoding="utf-8")

    assert "userApi.setEmail" in settings
    assert "userApi.verifyEmail" in settings
    assert "验证码" in settings
    assert "email?: string" not in api
