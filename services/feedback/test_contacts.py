import unittest
from contact_validation import normalize_mobile,normalize_email


class ContactTests(unittest.TestCase):
    def test_mainland_normalization(self):
        for value in ['16600000000','+86 166 0000 0000','8616600000000','１６６００００００００']:
            self.assertEqual(normalize_mobile(value,'CN'),'+8616600000000')

    def test_mainland_invalid(self):
        for value in ['1660000000','166000000000','01234567890','12345678901','+64211234567','166ABCDEFGH']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                normalize_mobile(value,'CN')

    def test_international(self):
        self.assertEqual(normalize_mobile('0211234567','NZ'),'+64211234567')
        self.assertEqual(normalize_mobile('+1 202 555 0123','OTHER'),'+12025550123')
        for value,country in [('02112','NZ'),('+8616600000000','NZ'),('2025550123','OTHER')]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                normalize_mobile(value,country)

    def test_email_normalization(self):
        self.assertEqual(normalize_email(' Student+help@EXAMPLE.COM ','Student+help@example.com'),'Student+help@example.com')
        self.assertEqual(normalize_email("o'connor@example.com","o'connor@example.com"),"o'connor@example.com")

    def test_bad_email(self):
        for value in ['student','student@localhost','student @example.com','student@@example.com','.student@example.com','student..name@example.com','student@-example.com','student@example..com','student@example.com\r\nBcc: other@example.com']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                normalize_email(value,value)
        with self.assertRaises(ValueError):
            normalize_email('student@example.com','different@example.com')


if __name__=='__main__':
    unittest.main(verbosity=2)
