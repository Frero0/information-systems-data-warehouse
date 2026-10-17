import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from analyze import export, kmeans, normalize

class SegmentationTests(unittest.TestCase):
    def test_minmax_handles_constant_features(self):
        scaled, lo, hi = normalize([[2, 7], [4, 7], [6, 7]])
        self.assertEqual(scaled, [[0, 0], [0.5, 0], [1, 0]])
        self.assertEqual((lo, hi), ([2, 7], [6, 7]))

    def test_separated_groups_and_deterministic_restarts(self):
        points = [[0, 0], [0.01, 0], [0.5, 0.5], [0.51, 0.5], [1, 1], [0.99, 1]]
        first = kmeans(points)
        self.assertEqual(first, kmeans(points))
        labels, centers, inertia, iterations = first
        self.assertEqual(labels, [0, 0, 1, 1, 2, 2])
        self.assertLess(inertia, 0.001)
        self.assertLessEqual(iterations, 99)

    def test_degenerate_data_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'distinct'):
            kmeans([[0, 0], [0, 0], [1, 1]])

    def test_nonfinite_features_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize([[1, float('nan')], [2, 3]])

    def test_assignment_matches_nearest_returned_centroid(self):
        points = [[i / 20, (i % 4) / 4] for i in range(20)]
        labels, centers, inertia, _ = kmeans(points, max_iterations=1)
        from analyze import squared_distance
        for point, label in zip(points, labels):
            self.assertEqual(label, min(range(3), key=lambda c: squared_distance(point, centers[c])))
        self.assertAlmostEqual(inertia, sum(squared_distance(p, centers[c]) for p, c in zip(points, labels)))

    def test_export_writes_readable_results_and_svg(self):
        rows = [dict(customer_id=str(i), company_name='Demo < & >', order_count=i,
                     distinct_products=i, gross_spend=i*10, net_spend=i*9,
                     total_quantity=i*3, mean_discount=i/10) for i in range(1, 7)]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            summary = export({'customer_features': rows, 'top_products': [],
                              'rolling_by_product': [], 'rolling_by_product_country': []}, output)
            self.assertEqual(summary['customer_count'], 6)
            self.assertEqual(len(list(output.glob('*.csv'))), 6)
            for svg in output.glob('*.svg'):
                root = ET.parse(svg).getroot()
                circles = root.findall('.//{http://www.w3.org/2000/svg}circle')
                self.assertEqual(len(circles), 9)  # six customers and three legend entries
            for model in summary['models'].values():
                self.assertEqual(sum(model['cluster_sizes']), 6)

if __name__ == '__main__':
    unittest.main()
