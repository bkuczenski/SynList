"""
Unit Tests for SynList and Flowables

Things to test for:
 - all the problems I ran into when first creating the flowables, in unit form. this can actually be very constructive.
"""

from synlist.synlist import SynList, InconsistentIndices

import unittest
import json


synlist_json = '''\
{
  "SynList": [
    {
      "name": "The Great Houdini",
      "synonyms": [
        "Henry VII",
        "Arthur the Great",
        "Alexander the terrible, horrible, no-good, very-bad"
      ]
    },
    {
      "name": "Zeke",
      "synonyms": [
        "Zeke",
        "zeke",
        "your cousin",
        "your cousin Zeke"
      ]
    }
  ]
}
'''


class SynListTestCase(unittest.TestCase):
    """
    user-facing methods:
     cls.from_json()
     index(term) - return instantiation-specific index for an item
     all_terms - just dict-keys- not very useful to test
     name(term) - the canonical name of an item
     add_term(term) - if term is known, return its index; else create a new and return its index
     find_indices(iterable) - map terms in iterable to sets in a dict; keys are indices
     new_set(iterable, name) - create a new set for all the terms not already known in iterable
     add_set(iterable, merge, name) - add (unknown) terms to existing or new item depending on merge
     merge - squash items together; first one listed keeps its name
     add_synonyms() - add_set
     synonyms_for(term) - return all synonyms for item containing term
     search() - regexp - returns a set of indices
     synonym_set(index) - access an item via its index
     [] - synonyms_for
     serialize - to dict, filter out empty items

    internal methods:
     _get_index
     _new_term
     _
    """
    def setUp(self):
        """
        deserialize, __init__, add_set without merge (=>
        :return:
        """
        self.synlist = SynList.from_json(json.loads(synlist_json))

    def tearDown(self):
        pass

    def test_name(self):
        self.synlist.add_term('bob the builder')
        self.assertEqual(self.synlist.name('bob the builder'), 'bob the builder')

    def test_lookup(self):
        """
        synonyms_for, _get_index
        :return:
        """
        self.assertSetEqual(self.synlist.synonyms_for('zeke'), {'Zeke', 'zeke', 'your cousin', 'your cousin Zeke'})

    def test_find_indices(self):
        """
        find_indices
        :return:
        """
        indices = self.synlist.find_indices(('The Great Houdini', 'Henry VIII'))

        self.assertSetEqual(indices[None], {'Henry VIII'})
        self.assertSetEqual(indices[0], {'The Great Houdini'})

    def test_add_synonyms(self):
        self.assertEqual(self.synlist.add_term('Henry VII'), 0)
        self.assertEqual(self.synlist.add_term('Conan the barbarian'), 2)
        self.assertEqual(self.synlist.add_synonyms('Conan the barbarian', 'your brother steve'), 2)

        with self.assertRaises(InconsistentIndices):
            self.synlist.add_set(('Conan the barbarian', 'Henry VII'))

    def test_add_merge(self):
        self.assertEqual(self.synlist.add_set(('Conan the barbarian', 'bob the builder'), merge=False), 2)
        self.assertEqual(self.synlist.add_set(('bob the builder', 'Nicky "legs" Capote'), merge=False), 3)
        self.assertEqual(self.synlist.add_set(('Jack the Ripper', 'Nicky "legs" Capote'), merge=True), 3)
        with self.assertRaises(InconsistentIndices):
            self.synlist.add_set(('bob the builder', 'Nicky "legs" Capote'))

    def test_new_set(self):
        self.assertEqual(self.synlist.new_set(('Henry VII', 'Marie Antoinette')), 2)
        self.assertSetEqual(self.synlist.synonyms_for('Marie Antoinette'), {'Marie Antoinette'})


if __name__ == '__main__':
    unittest.main()
