"""Fail-closed placement regression tests against the authored baseline."""
from pathlib import Path
from types import SimpleNamespace
import unittest
import cadquery as cq
from x_carriage_placement import derive_x_carriage_proposal, WHEEL_PAIRS, PLATES


class XCarriageProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.children = cq.Assembly.importStep(str(Path(__file__).parent/'M3-2_V1.0_baseline.step')).children

    def test_preserves_raw_children_and_only_plans_four_poses(self):
        before=[(id(c),id(c.obj),c.loc.toTuple()) for c in self.children]
        poses,records=derive_x_carriage_proposal(self.children)
        self.assertEqual(set(poses),set(WHEEL_PAIRS))
        self.assertEqual(len(records),4)
        self.assertEqual(before,[(id(c),id(c.obj),c.loc.toTuple()) for c in self.children])
        self.assertTrue(all(r['status']=='reference_placement_owner_confirmed' for r in records))

    def test_missing_raw_identity_is_rejected(self):
        required=set(WHEEL_PAIRS)|set(WHEEL_PAIRS.values())|set(PLATES)
        for name in required:
            with self.subTest(name=name),self.assertRaises(ValueError):
                derive_x_carriage_proposal(c for c in self.children if c.name!=name)

    def test_duplicate_raw_identity_is_rejected_before_bbox_dedup(self):
        required=set(WHEEL_PAIRS)|set(WHEEL_PAIRS.values())|set(PLATES)
        for name in required:
            c=next(c for c in self.children if c.name==name)
            with self.subTest(name=name),self.assertRaises(ValueError):
                derive_x_carriage_proposal([*self.children,c])

    def test_plate_xz_mismatch_does_not_silently_choose_a_datum(self):
        changed=[]
        for c in self.children:
            if c.name==PLATES[1]:
                c=SimpleNamespace(name=c.name,obj=c.obj,loc=cq.Location((1,0,0))*c.loc)
            changed.append(c)
        with self.assertRaisesRegex(ValueError,'share X/Z'):
            derive_x_carriage_proposal(changed)

    def test_wrong_wheel_axis_is_rejected(self):
        changed=[]
        for c in self.children:
            if c.name=='vwheel_123':
                c=SimpleNamespace(name=c.name,obj=c.obj,
                                  loc=cq.Location(cq.Vector(0,0,0),cq.Vector(0,0,1),90)*c.loc)
            changed.append(c)
        with self.assertRaisesRegex(ValueError,'orientation changed'):
            derive_x_carriage_proposal(changed)


if __name__=='__main__':
    unittest.main()
