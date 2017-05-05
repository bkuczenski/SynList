import re
from collections import defaultdict


class InconsistentIndices(Exception):
    pass


class TermFound(Exception):
    """
    TermFound should never be thrown except in _set_name, where it gets upgraded to NameFound
    """
    pass


class NameFound(Exception):
    pass


class SynList(object):
    """
    An ordered list of synonym sets.  The SynList has two components:
     * a list of sets (with unique entries)
     * a dict whose keys are the unique entries, and whose values are the indices into the list

    Membership in the list is determined by whether it is a key in the dict.  Dict keys are sanitized before being
    added: mainly by stripping whitespace. but this can be overloaded.

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
            s.add_set(i['synonyms'] + [i['name']])
            s.set_name(i['name'])
        return s

    def __init__(self):
        self._name = []
        self._list = []
        self._dict = dict()

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

    @staticmethod
    def _sanitize(key):
        return key.strip()

    def _new_term(self, term, index):
        if term is None:
            return
        key = self._sanitize(term)
        if key in self._dict:
            if self._dict[key] == index:
                return  # nothing to do
            raise TermFound(term)
        self._list[index].add(term)
        self._dict[key] = index
        if self._name[index] is None:
            self._name[index] = term

    def _get_index(self, term):
        if term is None:
            raise KeyError
        if isinstance(term, int):
            if term < len(self._list):
                return term
            raise IndexError('Item index out of range')
        return self._dict[self._sanitize(term)]

    def index(self, term):
        """
        internal (non-stable) index for an item corresponding to the given term
        :param term:
        :return:
        """
        return self._known(term)

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
        try:
            index = self._get_index(term)
        except KeyError:
            index = self._new_item()
            self._new_term(term, index)
        return index

    def find_indices(self, it):
        """
        Match an iterable of terms with indices.
        :param it: an *iterable* of strings to match on-- if the input is a single string, use index()
        :return: a dict whose keys are indices and whose values are sets of terms. If the set includes terms that are
         not known to the synlist, they will be included in the None key.
        """
        found = defaultdict(set)
        for i in it:
            try:
                found[self._get_index(i)].add(i)
            except KeyError:
                found[None].add(i)
        return found

    def _merge_set_with_index(self, it, index):
        for i in it:
            self._new_term(i, index)

    def _new_set(self, it):
        """
        Creates a new synonym set from entries in iterable. SILENTLY IGNORES existing terms.
        :param it:
        :return:
        """
        index = None
        unmatched = []
        for i in it:
            try:
                self._get_index(i)
            except KeyError:
                unmatched.append(i)
        if len(unmatched) > 0:
            index = self._new_item()
            self._merge_set_with_index(unmatched, index)
        return index

    def add_set(self, it, merge=False):
        """
        given an iterable of keys:
         - if any of them are found:
          - if merge is True:
           - if they are found in multiple indices, raise an inconsistency error
           - else they are found in one index, add unmatched terms to the index
          - else, add unmatched terms to a new index
         - else they are not found at all: add all terms to a new index
        :param it: an iterable of terms
        :param merge: [False] whether to merge matching keys or to shunt off to a new index
        :return:
        """
        found = self.find_indices(it)

        try:
            unmatched = found.pop(None)
        except KeyError:
            unmatched = set()
        if len(found) == 0 or merge is False:
            # no matching index found, or don't merge
            index = self._new_set(unmatched)
        elif len(found) > 1:
            # two or more non-None indices -- if merge is false, we can just ignore these
            raise InconsistentIndices('Keys found in indices: %s' % sorted(list(found.keys())))
        else:
            # len(found) == 1 and merge is True:
            index = next(k for k in found.keys())
            self._merge_set_with_index(unmatched, index)
        return index

    def set_name(self, name):
        """
        Make the given term the canonical name of whatever item it belongs to.
        :param name:
        :return: index of named item
        """
        index = self._get_index(name)
        self._name[index] = name
        return index

    def _merge(self, merge, into):
        # print('Merging\n## %s \ninto synonym set containing\n## %s' % (self._list[merge], self._list[into]))
        self._list[into] = self._list[into].union(self._list[merge])
        for i in self._list[into]:
            self._dict[self._sanitize(i)] = into
        self._list[merge] = None
        self._name[merge] = None

    def merge(self, dominant, *terms):
        """
        merges the synonyms from two or more terms into one set.
        :param dominant: term for item whose name will remain dominant
        :param terms: one or more terms that should be merged.
        :return:
        """
        merge_into = self._get_index(dominant)
        indices = set([self._get_index(term) for term in terms])
        for i in indices:
            self._merge(i, merge_into)

    def add_synonym(self, index, term):
        """
        Add term to an item known by index
        :param index:
        :param term:
        :return:
        """
        self._new_term(term, index)

    def add_synonyms(self, *terms):
        return self.add_set(terms, merge=True)

    def _known(self, term):
        if term is None:
            return None
        try:
            in1 = self._get_index(term)
        except KeyError:
            return None
        return in1

    def synonyms_for(self, term):
        inx = self._known(term)
        if inx is None:
            return None
        return self.synonym_set(inx)

    def are_synonyms(self, term1, term2):
        k1 = self._known(term1)
        return k1 == self._known(term2) and k1 is not None

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
