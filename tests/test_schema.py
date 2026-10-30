import unittest

from literature_rag.schema import numeric_scale_values, rating_scale_inventory


class RatingSchemaTests(unittest.TestCase):
    def test_iclr_text_enums_keep_their_nonuniform_scale(self):
        field = {"value": {"param": {"type": "string", "enum": [
            "1: reject", "3: reject", "5: below threshold", "6: above threshold",
            "8: accept", "10: strong accept",
        ]}}}
        self.assertEqual(numeric_scale_values(field), [1, 3, 5, 6, 8, 10])
        self.assertEqual(numeric_scale_values({"param": {"enum": ["4 excellent", "3 good"]}}),
                         [3, 4])

    def test_neurips_object_enums_read_value_not_dictionary_representation(self):
        field = {"value": {"param": {"type": "integer", "enum": [
            {"value": value, "description": f"Description for {value}"}
            for value in range(10, 0, -1)
        ]}}}
        self.assertEqual(numeric_scale_values(field), list(range(1, 11)))

    def test_missing_or_non_numeric_options_are_not_invented_as_zero(self):
        for options in ([], [True, False], ["yes", "no"], [1, "not applicable"]):
            self.assertIsNone(numeric_scale_values({"param": {"enum": options}}))

    def test_distinct_conference_scales_stay_separate(self):
        def invitation(name, options):
            return {"id": name, "edit": {"note": {"content": {
                "rating": {"value": {"param": {"enum": options}}},
            }}}}
        snapshot = {
            "venues": [
                {"id": "iclr", "review_invitations": {"i": "paper1"},
                 "rating_fields": ["rating"]},
                {"id": "neurips", "review_invitations": {"n": "paper2"},
                 "rating_fields": ["rating"]},
            ],
            "raw_invitations": [invitation("i", ["1: low", "3: high"]),
                                invitation("n", [{"value": 1}, {"value": 2}])],
        }
        inventory, unresolved = rating_scale_inventory(snapshot)
        self.assertEqual(inventory["iclr"]["rating"], [[1, 3]])
        self.assertEqual(inventory["neurips"]["rating"], [[1, 2]])
        self.assertEqual(unresolved, [])
        snapshot["raw_invitations"] = []
        with self.assertRaisesRegex(ValueError, "Brak oryginalnego schematu"):
            rating_scale_inventory(snapshot)
