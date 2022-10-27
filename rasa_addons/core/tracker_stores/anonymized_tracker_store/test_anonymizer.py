import unittest
from rasa_addons.core.tracker_stores.anonymized_tracker_store.text_anonymizer import TextAnonymizer


class TestAnonymizer(unittest.TestCase):

    def setUp(self):
        self.anon = TextAnonymizer()

    def check(self, text, expected):
        result = self.anon.anonymize_text(text)
        self.assertEqual(result, expected, f'Original text: {text}')

    def test_phone_numbers(self):
        # These should be replaced by <phone> tag
        positives = [
            '05012345',
            '050123456',
            '0501234567',
            '050 1234567',
            '050 1234 567',
            '050-1234567',
            '050-1234 567',
            '050-1234-567',
            '+358501234567',
            '(+358)501234567',
            '+358 50 1234567',
            '00358 50 123456',
            '+47 23 34980',
        ]
        for number in positives:
            self.check(number, '<phone>')

    def test_multiple_phone_numbers(self):
        self.check('Numeroni on 050-1234567, 040-654 3210, +358508734987 tai +358 50 8734 987.',
                   'Numeroni on <phone>, <phone>, <phone> tai <phone>.')

    def test_hetus(self):
        # These should be replaced by <hetu> tag
        positives = ['251308A2983',
                     '251308a2983',
                     '251308a2983',
                     '020976-398H',
                     '020976-398h',
                     '122498+9842',
                     '010594Y9021',
                     '020594X903P',
                     '020594X902N',
                     '030594W903B',
                     '030694W9024',
                     '040594V9030',
                     '040594V902Y',
                     '050594U903M',
                     '050594U902L',
                     '010516B903X',
                     '010516B902W',
                     '020516C903K',
                     '020516C902J',
                     '030516D9037',
                     '030516D9026',
                     '010501E9032',
                     '020502E902X',
                     '020503F9037',
                     '020504A902E',
                     '020504B904H',
                     ]
        for hetu in positives:
            self.check(hetu, '<hetu>')

    def test_multiple(self):
        self.check('Numeroni on 040-4667288, hetuni on 120587-763A ja ip on 127.0.0.1.',
                   'Numeroni on <phone>, hetuni on <hetu> ja ip on <ip>.')

    def test_negatives(self):
        # For these strings, anonymizer should do nothing
        negatives = ['25.12.2019',
                     'Aika: 10:23 12.01.2020.',
                     'klo 14.20',
                     '2014-01-01 12:34']
        for text in negatives:
            self.check(text, text)


if __name__ == '__main__':
    unittest.main()
