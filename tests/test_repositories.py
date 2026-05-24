"""Tests for database repositories."""

import pytest


class TestUserRepository:
    def test_create_user(self, user_repo):
        from src.auth.security import hash_password
        user = user_repo.create("a@b.com", "alice", hash_password("pw"))
        assert user["email"] == "a@b.com"
        assert user["username"] == "alice"
        assert "id" in user

    def test_get_by_email(self, user_repo, sample_user):
        found = user_repo.get_by_email("test@example.com")
        assert found is not None
        assert found["id"] == sample_user["id"]

    def test_get_by_email_not_found(self, user_repo):
        assert user_repo.get_by_email("nobody@nowhere.com") is None

    def test_get_by_id(self, user_repo, sample_user):
        found = user_repo.get_by_id(sample_user["id"])
        assert found is not None
        assert found["email"] == "test@example.com"

    def test_get_by_username(self, user_repo, sample_user):
        found = user_repo.get_by_username("testuser")
        assert found is not None


class TestHoldingsRepository:
    def test_add_and_list(self, holdings_repo, sample_user):
        holdings_repo.add(sample_user["id"], "AAPL", 10, 150.0)
        holdings_repo.add(sample_user["id"], "GOOGL", 5, 2800.0)

        holdings = holdings_repo.list_by_user(sample_user["id"])
        assert len(holdings) == 2
        tickers = {h["ticker"] for h in holdings}
        assert tickers == {"AAPL", "GOOGL"}

    def test_ticker_uppercased(self, holdings_repo, sample_user):
        h = holdings_repo.add(sample_user["id"], "aapl", 10, 150.0)
        assert h["ticker"] == "AAPL"

    def test_update_holding(self, holdings_repo, sample_user):
        h = holdings_repo.add(sample_user["id"], "AAPL", 10, 150.0)
        updated = holdings_repo.update(h["id"], shares=20)
        assert updated["shares"] == 20

    def test_delete_holding(self, holdings_repo, sample_user):
        h = holdings_repo.add(sample_user["id"], "AAPL", 10, 150.0)
        holdings_repo.delete(h["id"])
        assert holdings_repo.list_by_user(sample_user["id"]) == []


class TestWatchlistRepository:
    def test_crud(self, patched_db, sample_user):
        from src.database.repositories import WatchlistRepository
        repo = WatchlistRepository()

        wl = repo.create(sample_user["id"], "Tech", ["AAPL", "GOOGL"])
        assert wl["name"] == "Tech"
        assert wl["tickers"] == ["AAPL", "GOOGL"]

        updated = repo.update(wl["id"], tickers=["AAPL", "GOOGL", "MSFT"])
        assert len(updated["tickers"]) == 3

        all_wl = repo.list_by_user(sample_user["id"])
        assert len(all_wl) == 1

        repo.delete(wl["id"])
        assert repo.list_by_user(sample_user["id"]) == []


class TestNotificationRepository:
    def test_create_and_list(self, patched_db, sample_user):
        from src.database.repositories import NotificationRepository
        repo = NotificationRepository()

        repo.create(sample_user["id"], "price_alert", "AAPL moved +5%", "AAPL")
        repo.create(sample_user["id"], "milestone", "Portfolio up 10%!")

        notifs = repo.list_by_user(sample_user["id"])
        assert len(notifs) == 2

    def test_mark_read(self, patched_db, sample_user):
        from src.database.repositories import NotificationRepository
        repo = NotificationRepository()

        n = repo.create(sample_user["id"], "test", "msg")
        repo.mark_read(n["id"])

        unread = repo.list_by_user(sample_user["id"], unread_only=True)
        assert len(unread) == 0


class TestLearningProgressRepository:
    def test_complete_step(self, patched_db, sample_user):
        from src.database.repositories import LearningProgressRepository
        repo = LearningProgressRepository()

        repo.complete_step(sample_user["id"], "getting_started", "create_account")
        repo.complete_step(sample_user["id"], "getting_started", "explore_overview")

        progress = repo.get_progress(sample_user["id"])
        assert len(progress) == 2

    def test_idempotent_completion(self, patched_db, sample_user):
        from src.database.repositories import LearningProgressRepository
        repo = LearningProgressRepository()

        repo.complete_step(sample_user["id"], "mod1", "step1")
        repo.complete_step(sample_user["id"], "mod1", "step1")  # duplicate

        progress = repo.get_progress(sample_user["id"])
        assert len(progress) == 1
