#!/usr/bin/env python3

import unittest

import export_messages as em


class ExportMessagesTests(unittest.TestCase):
    def test_summarize_content_uses_placeholders(self):
        sender, body = em._summarize_content(3, b"\x00\x01\x02", {}, False)
        self.assertIsNone(sender)
        self.assertEqual(body, "[img]")

        sender, body = em._summarize_content(10002, "ignored", {}, False)
        self.assertEqual(body, "[revoke]")

        sender, body = em._summarize_content(244813135921, b"\x00\x01", {}, False)
        self.assertEqual(body, "[t:244813135921]")

    def test_private_context_collapses_sender_ids_to_me_and_other(self):
        rows = [
            ("message_0.db", 1, 1, 100, 10, 2, "hello", ""),
            ("message_0.db", 2, 1, 101, 20, 4, "hi", ""),
            ("message_0.db", 3, 1, 102, 21, 4, "extra-other", ""),
            ("message_1.db", 4, 1, 103, 30, 2, "older-me", ""),
            ("message_1.db", 5, 1, 104, 40, 4, "older-other", ""),
        ]

        lines, participants = em._build_export_context(
            rows, "wxid_target", {"wxid_target": "对方"}, {}
        )

        self.assertEqual(participants, "1=我 | 2=对方")
        self.assertEqual(
            lines,
            [
                "1970-01-01 08:01:40 1 hello",
                "1970-01-01 08:01:41 2 hi",
                "1970-01-01 08:01:42 2 extra-other",
                "1970-01-01 08:01:43 1 older-me",
                "1970-01-01 08:01:44 2 older-other",
            ],
        )

    def test_group_context_prefers_room_member_name(self):
        rows = [
            ("message_0.db", 1, 1, 100, 7, 3, "ignored", ""),
            ("message_0.db", 2, 47, 101, 8, 3, "ignored", ""),
        ]
        room_members = {
            "room@chatroom": {
                7: "Alice",
                8: "Bob",
            }
        }

        lines, participants = em._build_export_context(
            rows, "room@chatroom", {}, room_members
        )

        self.assertEqual(participants, "1=Alice | 2=Bob")
        self.assertEqual(lines[0], "1970-01-01 08:01:40 1 ignored")
        self.assertEqual(lines[1], "1970-01-01 08:01:41 2 [emoji]")


if __name__ == "__main__":
    unittest.main()
