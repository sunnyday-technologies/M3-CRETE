"""Regression checks for units, references, strings and topology preservation."""
import unittest
from step_compact import compact_step_text


class CompactionTests(unittest.TestCase):
    def test_geometry_sharing_preserves_topology_and_literals(self):
        source = """ISO-10303-21;
HEADER;FILE_DESCRIPTION(('label #999; don''t change'),'2;1');ENDSEC;
DATA;
#1=DIRECTION('',(0.,0.,1.));
#2=DIRECTION('',(0.,0.,1.));
#3=VECTOR('',#1,1.E-07);
#4=VECTOR('',#2,1.E-07);
#5=VERTEX_POINT('',#3);
#6=VERTEX_POINT('',#4);
#7=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));
ENDSEC;END-ISO-10303-21;
"""
        result, audit = compact_step_text(source)
        self.assertNotIn('#2=', result)
        self.assertNotIn('#4=', result)
        self.assertIn("#5=VERTEX_POINT('',#3);", result)
        self.assertIn("#6=VERTEX_POINT('',#3);", result)
        self.assertIn("label #999; don''t change", result)
        self.assertIn('SI_UNIT(.MILLI.,.METRE.)', result)
        self.assertIn('1.E-07', result)
        self.assertEqual(audit['passes'], [1, 1])
        self.assertEqual(compact_step_text(result)[0], result)

    def test_no_rounding_or_named_geometry_merge(self):
        text = "#1=DIRECTION('a',(0.,0.,1.));#2=DIRECTION('b',(0.,0.,1.));#3=DIRECTION('a',(0.,0.,1.00000000001));"
        result, audit = compact_step_text(text)
        self.assertEqual(result, text)
        self.assertEqual(audit['passes'], [])

    def test_reject_invalid_references(self):
        for text in ["#1=VECTOR('',#99,1.);", "#1=VERTEX_POINT('',#1);#1=VERTEX_POINT('',#1);",
                     "#1=DIRECTION('',(0.,0.,1.));#1=DIRECTION('',(0.,0.,1.));"]:
            with self.assertRaises(ValueError):
                compact_step_text(text)

    def test_embedded_records_are_rejected(self):
        with self.assertRaises(ValueError):
            compact_step_text("/* #1=DIRECTION('',(0.,0.,1.)); */")


if __name__ == '__main__':
    unittest.main()
