import importlib
import unittest


def load_state_module():
    return importlib.import_module("slappaper.state")


class ExecutionStateTests(unittest.TestCase):
    def setUp(self):
        self.state_module = load_state_module()

    def test_auto_refresh_debounces_repeated_finder_activations(self):
        state = self.state_module.ExecutionState(auto_debounce_seconds=1.0)

        self.assertTrue(state.begin_generation("auto", now=10.0))
        state.finish_generation()
        self.assertFalse(state.begin_generation("auto", now=10.5))
        self.assertTrue(state.begin_generation("auto", now=11.2))

    def test_manual_refresh_bypasses_auto_debounce(self):
        state = self.state_module.ExecutionState(auto_debounce_seconds=1.0)

        self.assertTrue(state.begin_generation("auto", now=10.0))
        state.finish_generation()
        self.assertTrue(state.begin_generation("manual", now=10.2))

    def test_generation_in_progress_blocks_all_sources(self):
        state = self.state_module.ExecutionState(auto_debounce_seconds=1.0)

        self.assertTrue(state.begin_generation("manual", now=10.0))
        self.assertFalse(state.begin_generation("auto", now=11.0))


if __name__ == "__main__":
    unittest.main()
