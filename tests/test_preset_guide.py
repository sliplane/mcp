import json
import unittest

from preset_guide import PRESETS, get_preset_guide


class PresetGuideTest(unittest.TestCase):
    def test_catalog_contains_all_unique_presets(self):
        preset_ids = [preset["settings"]["presetId"] for preset in PRESETS]

        self.assertEqual(len(preset_ids), 76)
        self.assertEqual(len(set(preset_ids)), 76)
        catalog = get_preset_guide()
        for preset_id in preset_ids:
            self.assertIn(f"`{preset_id}`", catalog)

    def test_lookup_accepts_id_and_display_name(self):
        by_id = get_preset_guide("postgres")
        by_name = get_preset_guide("PostgreSQL")

        self.assertIn('"presetId": "postgres"', by_id)
        self.assertIn('"externalDockerImage": "docker.io/library/postgres:18.1"', by_id)
        self.assertEqual(by_id, by_name)

    def test_every_preset_exposes_complete_service_settings(self):
        required = {
            "presetId",
            "name",
            "serverId",
            "envs",
            "cmd",
            "volumes",
            "public",
            "deploySource",
            "externalDockerImage",
        }

        for preset in PRESETS:
            self.assertTrue(required.issubset(preset["settings"]))
            self.assertEqual(preset["settings"]["serverId"], "<SERVER_ID>")
            create_input = preset["createServiceInput"]
            self.assertEqual(create_input["projectId"], "<PROJECT_ID>")
            self.assertEqual(create_input["serverId"], "<SERVER_ID>")
            self.assertEqual(
                create_input["deployment"]["url"],
                preset["settings"]["externalDockerImage"],
            )
            self.assertEqual(create_input["env"], preset["settings"]["envs"])

    def test_frontend_volume_fields_are_mapped_to_public_api(self):
        postgres = next(
            preset
            for preset in PRESETS
            if preset["settings"]["presetId"] == "postgres"
        )

        self.assertEqual(
            postgres["createServiceInput"]["volumes"],
            [
                {
                    "name": "postgres-data-<RANDOM_SUFFIX>",
                    "mountPath": "/var/lib/postgresql",
                }
            ],
        )
        self.assertNotIn("presetId", postgres["createServiceInput"])
        self.assertNotIn("externalDockerImage", postgres["createServiceInput"])

    def test_all_returns_valid_json_payload(self):
        response = get_preset_guide("all")
        payload = response.rsplit("```json\n", 1)[1].removesuffix("```\n")

        self.assertEqual(len(json.loads(payload)), 76)

    def test_unknown_preset_lists_available_ids(self):
        response = get_preset_guide("does-not-exist")

        self.assertIn("Unknown preset", response)
        self.assertIn("postgres", response)
        self.assertIn("ssh", response)


if __name__ == "__main__":
    unittest.main()
