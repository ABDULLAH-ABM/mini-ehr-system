import unittest
import mini_ehr as ehr


class EHRTests(unittest.TestCase):
    def setUp(self):
        self.conn = ehr.connect(":memory:")
        ehr.seed_demo(self.conn)

    def test_receptionist_cannot_read_records(self):
        with self.assertRaises(PermissionError):
            ehr.list_records(self.conn, "reception_demo", 1)

    def test_doctor_can_add_and_read_record(self):
        ehr.add_record(self.conn, "dr_demo", 1, "Common cold", "Rest")
        self.assertEqual(len(ehr.list_records(self.conn, "dr_demo", 1)), 1)

    def test_unknown_user_denied(self):
        with self.assertRaises(PermissionError):
            ehr.list_patients(self.conn, "nobody")

    def test_denied_attempts_are_audited(self):
        with self.assertRaises(PermissionError):
            ehr.add_record(self.conn, "nurse_demo", 1, "x")
        log = ehr.audit_log(self.conn, "admin1")
        self.assertTrue(any(r["allowed"] == 0 and r["username"] == "nurse_demo" for r in log))

    def test_unknown_patient(self):
        with self.assertRaises(ValueError):
            ehr.add_appointment(self.conn, "dr_demo", 99, "Dr Demo", "2026-12-01 10:00")


if __name__ == "__main__":
    unittest.main()
