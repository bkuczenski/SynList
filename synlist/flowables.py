import re
from synlist.synlist import SynList


class ConflictingCas(Exception):
    pass


class NotACas(Exception):
    pass


cas_regex = re.compile('^[0-9]{,6}-[0-9]{2}-[0-9]$')
cas_strict = re.compile('^[0-9]{6}-[0-9]{2}-[0-9]$')


def find_cas(syns):
    found = set()
    for i in syns:
        if bool(cas_regex.match(i)):
            found.add(i)
    if len(found) > 1:
        raise ConflictingCas('Multiple CAS numbers found: %s' % found)
    if len(found) == 0:
        return None
    return found.pop()


def pad_cas(cas):
    if not bool(cas_regex.match(cas)):
        raise NotACas(cas)
    while not bool(cas_strict.match(cas)):
        cas = '0' + cas
    return cas


def trim_cas(cas):
    return re.sub('^(0*)', '', cas)


class Flowables(SynList):
    """
    A SynList that enforces unique CAS numbers on sets.  Also introduces a new policy (controversial!) that adds
    both key and key.lower() for every key longer than 3 characters.

    The CAS thing requires overloading _new_key and _new_group and just about everything else.
    """

    def __init__(self):
        super(Flowables, self).__init__()
        self._cas = []

    def cas(self, index):
        return self._cas[index]

    def name(self, term):
        """
        returns the [[trimmed???]] cas number if it exists; otherwise the canonical name
        :param term:
        :return:
        """
        ind = self._get_index(term)
        if self._cas[ind] is not None:
            return trim_cas(self._cas[ind])
        return self._name[ind]

    def _new_item(self):
        k = super(Flowables, self)._new_item()
        self._cas.append(None)
        return k

    def _get_index(self, term):
        term = term.strip()
        try:
            return self._dict[term]
        except KeyError:
            if len(term) > 3:
                return self._dict[term.lower()]

    def _new_term(self, term, index):
        if cas_regex.match(term):
            if self._cas[index] is not None and trim_cas(self._cas[index]) != trim_cas(term):
                raise ConflictingCas('Index %d already has CAS %s' % (index, self._cas[index]))
            else:
                term = pad_cas(term)
                self._cas[index] = term
                super(Flowables, self)._new_term(trim_cas(term), index)
        super(Flowables, self)._new_term(term, index)
        if len(term) > 3:
            super(Flowables, self)._new_term(term.lower(), index)  # controversial?

    def _merge(self, merge, into):
        super(Flowables, self)._merge(merge, into)
        self._cas[merge] = None

    def merge(self, dominant, *terms):
        """
        Flowables.merge first checks for conflicting CAS numbers, then merges as normal. the _merge interior function
        deletes cas numbers from merged entries; then this function sets the (non-conflicting) CAS number for the
        dominant entry.
        :param dominant:
        :param terms:
        :return:
        """
        dom = self._get_index(dominant)
        cas = [self._cas[dom]]
        for i in terms:
            cas.append(self._cas[self._get_index(i)])
        the_cas = [k for k in filter(None, cas)]
        if len(the_cas) > 1:
            raise ConflictingCas('Indices have conflicting CAS numbers: %s' % the_cas)
        super(Flowables, self).merge(dominant, *terms)
        if len(the_cas) == 1:
            self._cas[dom] = the_cas[0]

    def _merge_set_with_index(self, it, index):
        cas = find_cas(it)
        if cas is not None:
            if self._cas[index] is not None and trim_cas(self._cas[index]) != trim_cas(cas):
                print('Conflicting CAS: incoming %s; existing [%s] = %d' % (cas, self._cas[index], index))
                raise ConflictingCas('Incoming set has conflicting CAS %s' % cas)
        super(Flowables, self)._merge_set_with_index(it, index)
