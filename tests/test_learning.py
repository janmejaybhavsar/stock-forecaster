"""Tests for learning path modules."""


class TestLearningModules:
    def test_modules_defined(self):
        from src.learning.modules import MODULES
        assert len(MODULES) == 7

    def test_all_modules_have_steps(self):
        from src.learning.modules import MODULES
        for m in MODULES:
            assert len(m.steps) > 0, f"Module {m.id} has no steps"
            assert m.title
            assert m.icon
            assert m.badge

    def test_total_steps(self):
        from src.learning.modules import total_steps
        assert total_steps() == 21

    def test_get_module(self):
        from src.learning.modules import get_module
        m = get_module("getting_started")
        assert m is not None
        assert m.title == "Getting Started"

    def test_get_module_not_found(self):
        from src.learning.modules import get_module
        assert get_module("nonexistent") is None

    def test_get_all_step_ids(self):
        from src.learning.modules import get_all_step_ids
        ids = get_all_step_ids()
        assert len(ids) == 21
        assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in ids)

    def test_unique_module_ids(self):
        from src.learning.modules import MODULES
        ids = [m.id for m in MODULES]
        assert len(ids) == len(set(ids))

    def test_unique_step_ids_within_module(self):
        from src.learning.modules import MODULES
        for m in MODULES:
            step_ids = [s.id for s in m.steps]
            assert len(step_ids) == len(set(step_ids)), f"Duplicate step IDs in {m.id}"

    def test_steps_have_required_fields(self):
        from src.learning.modules import MODULES
        for m in MODULES:
            for s in m.steps:
                assert s.id
                assert s.title
                assert s.description
                assert s.action_text
