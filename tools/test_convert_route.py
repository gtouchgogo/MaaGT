import unittest
from convert_route import convert


class ConversionTests(unittest.TestCase):
    def record(self, events):
        return {'duration': 2, 'events': events}

    def edge(self, t, key, down):
        return {'t': t, 'kind': 'key', 'vk': key, 'down': down}

    def test_overlap_preserved(self):
        pipeline, report = convert(self.record([
            self.edge(.1,68,True), self.edge(.2,87,True),
            self.edge(1,68,False), self.edge(1.5,87,False)]))
        self.assertEqual([pipeline[f'InsideRoute_{i:03d}']['key'] for i in range(4)], [68,87,68,87])
        self.assertEqual(sum(n['post_delay'] for n in pipeline.values()), 1500)
        self.assertTrue(pipeline['InsideRoute_000']['auto_up'])
        self.assertEqual(report['events'], 4)

    def test_bad_recordings_rejected(self):
        for events in ([self.edge(0,87,True)], [self.edge(0,87,False)],
                       [self.edge(1,87,True), self.edge(.5,87,False)],
                       [self.edge(0,87,True),self.edge(.1,87,True)]):
            with self.assertRaises(ValueError):
                convert(self.record(events))

    def test_ignored_events_reported(self):
        _, report = convert(self.record([{'t':0,'kind':'move'},
            self.edge(.1,87,True),self.edge(.2,87,False),self.edge(.3,69,True)]))
        self.assertEqual(report['ignored'], {'move':1,'key:69':1})


if __name__ == '__main__':
    unittest.main()
