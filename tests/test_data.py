import tempfile
import unittest
from pathlib import Path
from drive_tool.data import save_parameters, load_parameters, compare_sets

class ParameterDataTests(unittest.TestCase):
    def test_json_round_trip(self):
        rows = [{"number":"99.06", "name":"Motor nominal current", "value":"9.4", "unit":"A", "note":"user entered"}]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "backup.json"
            save_parameters(str(p), rows)
            self.assertEqual(load_parameters(str(p)), rows)

    def test_csv_round_trip(self):
        rows = [{"number":"99.07", "name":"Motor nominal frequency", "value":"50", "unit":"Hz", "note":""}]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "backup.csv"
            save_parameters(str(p), rows)
            self.assertEqual(load_parameters(str(p)), rows)

    def test_compare(self):
        a = [{"number":"1.01", "value":"10"}]
        b = [{"number":"1.01", "value":"11"}]
        self.assertEqual(len(compare_sets(a, b)), 1)

if __name__ == "__main__": unittest.main()
