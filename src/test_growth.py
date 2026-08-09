from __future__ import annotations

import unittest

from growth import build_plant_state, get_growth_progress, get_growth_stage


class GrowthStageTests(unittest.TestCase):
    def test_growth_stage_boundaries(self) -> None:
        cases = [
            (0, "씨앗", 1, 1),
            (1, "새싹", 2, 3),
            (2, "새싹", 2, 3),
            (3, "어린잎", 3, 6),
            (5, "어린잎", 3, 6),
            (6, "줄기", 4, 10),
            (9, "줄기", 4, 10),
            (10, "꽃", 5, None),
        ]

        for count, stage, level, next_target in cases:
            with self.subTest(count=count):
                growth = get_growth_stage(count)
                self.assertEqual(growth["stage"], stage)
                self.assertEqual(growth["level"], level)
                self.assertEqual(growth["next_target"], next_target)

    def test_negative_count_is_clamped_to_zero(self) -> None:
        growth = get_growth_stage(-3)
        self.assertEqual(growth["stage"], "씨앗")
        self.assertEqual(growth["level"], 1)


class BuildPlantStateTests(unittest.TestCase):
    def test_build_plant_state_with_missing_recommendation_fields(self) -> None:
        state = build_plant_state({}, 2)
        self.assertEqual(state["plant_name"], "식물 친구")
        self.assertEqual(state["plant_id"], "unknown")
        self.assertEqual(state["plant_emoji"], "🌱")
        self.assertEqual(state["growth_stage"]["stage"], "새싹")


class GrowthProgressTests(unittest.TestCase):
    def test_progress_non_max_level(self) -> None:
        progress = get_growth_progress(2)
        self.assertEqual(progress["total_exp"], 1000)
        self.assertEqual(progress["current_level_exp"], 500)
        self.assertEqual(progress["required_level_exp"], 1000)
        self.assertEqual(progress["next_level_total_exp"], 1500)
        self.assertFalse(progress["is_max_level"])

    def test_progress_required_exp_increases_per_level(self) -> None:
        self.assertEqual(get_growth_progress(0)["required_level_exp"], 500)
        self.assertEqual(get_growth_progress(1)["required_level_exp"], 1000)
        self.assertEqual(get_growth_progress(3)["required_level_exp"], 1500)
        self.assertEqual(get_growth_progress(6)["required_level_exp"], 2000)

    def test_progress_max_level(self) -> None:
        progress = get_growth_progress(10)
        self.assertEqual(progress["total_exp"], 5000)
        self.assertTrue(progress["is_max_level"])
        self.assertIsNone(progress["required_level_exp"])


if __name__ == "__main__":
    unittest.main()
