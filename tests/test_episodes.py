"""Unit tests for episode segmentation and outcome labeling."""

import unittest
from brain.adapters.base import RawSession, RawStep
from brain.indexer.episodes import EpisodeSegmenter

class TestEpisodeSegmenter(unittest.TestCase):
    def test_segments_user_boundaries_and_labels_outcome(self):
        steps = [
            RawStep(
                step_index=0,
                source="USER",
                step_type="USER_INPUT",
                status="DONE",
                content="<USER_REQUEST>Fix the database connection error</USER_REQUEST>",
            ),
            RawStep(
                step_index=1,
                source="MODEL",
                step_type="PLANNER_RESPONSE",
                status="DONE",
                thinking="I will inspect postgres",
                tool_calls=[
                    {
                        "tool_name": "run_command",
                        "arguments": {"CommandLine": "systemctl status postgresql"},
                        "output": "Active: failed (Result: exit-code)",
                    }
                ],
            ),
            RawStep(
                step_index=2,
                source="MODEL",
                step_type="PLANNER_RESPONSE",
                status="DONE",
                thinking="Restarting service",
                content="Postgres restarted successfully and connection is verified.",
                tool_calls=[
                    {
                        "tool_name": "run_command",
                        "arguments": {"CommandLine": "systemctl restart postgresql"},
                        "output": "Active: active (running)",
                    }
                ],
            ),
        ]

        session = RawSession(
            id="test-session-123",
            title="Test Session",
            project_id="test-proj",
            model="Gemini",
            steps=steps,
            artifacts=[],
            created_at="2026-10-07T12:00:00Z",
            updated_at="2026-10-07T12:05:00Z",
        )

        episodes = EpisodeSegmenter.segment_session(session)
        self.assertEqual(len(episodes), 1)
        ep = episodes[0]
        self.assertEqual(ep.outcome, "SUCCESS")
        self.assertGreater(ep.outcome_score, 1.0)  # Bonus score for error resolution!
        self.assertIn("systemctl restart postgresql", ep.commands_run)
        self.assertIn("Fix the database connection error", ep.intent)

if __name__ == "__main__":
    unittest.main()
