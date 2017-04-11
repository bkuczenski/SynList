import re


class InconsistentIndices(Exception):
    pass


class SynList(object):
    """
    An ordered list of synonym sets.  The SynList has two components:
     * a list of sets (with unique entries)
     * a dict whose keys are the unique entries, and whose values are the indices into the list

    This allows two types of references:
     - put in a string--> get back a set of synonyms
     - put in an index--> get back a set of synonyms

    This gets easily serialized:
     - JSON list of sets of synonyms

    And de-serialized:
     - from that list, construct the list. boo hoo!
    """
    @classmethod
    def from_json(cls, j):
        s = cls()
        json_string = cls.__name__
        for i in j[json_string]:
            s.add_set(i['synonyms'], name=i['name'])
        return s

    def __init__(self):
        self._name = []
        self._list = []
        self._dict = dict()

    def _new_term(self, term, index):
        term = term.strip()
        self._list[index].add(term)
        self._dict[term] = index

    def _get_index(self, term):
        return self._dict[term.strip()]

    def _set_name(self, index, name):
        self._new_term(name, index)
        self._name[index] = name

    def _new_item(self):
        k = len(self._list)
        self._list.append(set())
        self._name.append(None)
        return k

    def __len__(self):
        """
        Number of (non-None) items in the SynList
        :return:
        """
        return len([x for x in self._list if x is not None])

    def index(self, term):
        """
        internal (non-stable) index for an item corresponding to the given term
        :param term:
        :return:
        """
        return self._get_index(term)

    def all_terms(self):
        """
        dict keys of all terms known to the SynList
        :return:
        """
        return self._dict.keys()

    def name(self, term):
        """
        returns the canonical name for a given term
        :param term:
        :return:
        """
        return self._name[self._get_index(term)]

    def add_term(self, term):
        """
        Given a single term--> return its index, either existing or new
        :param term:
        :return:
        """
        key = term.strip()
        if key not in self._dict.keys():
            index = self._new_item()
            self._new_term(key, index)
        return self._dict[key]

    def find_indices(self, it):
        """
        Return all item indices for terms in the iterable set.
        :param it: an *iterable* of strings to match on-- if the input is a single string, use index()
        :return:
        """
        found = set()
        for i in it:
            try:
                found.add(self._get_index(i))
            except KeyError:
                continue
        return sorted(list(found))

    def _merge_set_with_index(self, it, index):
        for i in it:
            self._new_term(i, index)

    def new_set(self, it, name=None):
        """
        Creates a new synonym set from entries in iterable. SILENTLY IGNORES existing terms.
        :param it:
        :param name:
        :return:
        """
        index = self._new_item()
        for i in it:
            j = i.strip()
            if j not in self._dict:
                self._new_term(j, index)
                if name is None:
                    name = j
        self._set_name(index, name)
        return index

    def add_set(self, it, merge=False, name=None):
        """
        given an iterable of keys:
         - if any of them are found:
          - if they are found in multiple indices, raise an inconsistency error
          - elif they are found in one index, add all to the index
          - elif they are not found at all, add them to a new index
        :param it: an iterable of keys
        :param merge: [False] whether to merge matching keys or to shunt off to a new index
        :param name: shortname for the synonym set
        :return:
        """
        found = self.find_indices(it)
        if len(found) > 1:
            raise InconsistentIndices('Keys found in indices: %s' % found)
        elif len(found) == 1 and merge:
            index = found.pop()
            self._merge_set_with_index(it, index)
        else:
            index = self.new_set(it, name=name)
        return index

    def _merge(self, merge, into):
        print('Merging\n## %s \ninto synonym set containing\n## %s' % (self._list[merge], self._list[into]))
        self._list[into] = self._list[into].union(self._list[merge])
        for i in self._list[into]:
            self._dict[i] = into
        self._list[merge] = None

    def merge(self, dominant, *terms):
        """
        merges the synonyms from two or more terms into one set.
        :param dominant: term for item whose name will remain dominant
        :param terms: one or more terms that should be merged.
        :return:
        """
        merge_into = self._get_index(dominant)
        indices = set([self._get_index(term) for term in terms])
        indices.remove(merge_into)
        for i in indices:
            self._merge(i, merge_into)

    def add_synonyms(self, *terms):
        return self.add_set({terms})

    def synonyms_for(self, term):
        return self.synonym_set(self._get_index(term))

    def search(self, term):
        """
        This is gonna be slow because we don't keep any lexical index
        :param term:
        :return:
        """
        results = set()
        for k in self._dict.keys():
            if bool(re.search(term, k, flags=re.IGNORECASE)):
                results.add(self.index(k))
        return results

    def synonym_set(self, index):
        """
        Access an item via its index.
        :param index:
        :return:
        """
        return self._list[index]

    def __getitem__(self, term):
        return self.synonyms_for(term)

    def _serialize_set(self, index):
        return {"name": self._name[index],
                "synonyms": [k for k in self._list[index]]}

    def serialize(self):
        json_string = self.__name__
        return {
            json_string: [self._serialize_set(i) for i in range(len(self._list))
                          if self._list[i] is not None]
        }
