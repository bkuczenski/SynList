import re
from synlist.synlist import SynList


class ConflictingCas(Exception):
    pass


class ConfoundedCas(Exception):
    pass


cas_regex = re.compile('^[0-9]{,6}-[0-9]{2}-[0-9]$')


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
                self._cas[index] = term
        super(Flowables, self)._new_term(term, index)
        if len(term) > 3:
            super(Flowables, self)._new_term(term.lower(), index)  # controversial?

    def _merge(self, merge, into):
        super(Flowables, self)._merge(merge, into)
        if self._cas[merge] is not None:
            if self._cas[into] is not None:
                # this should not happen because test for conflicting CAS was already performed
                raise ConfoundedCas('this should not happen')
            self._cas[into] = self._cas[merge]
            self._cas[merge] = None

    def merge(self, dominant, *terms):
        """
        Flowables.merge first checks for conflicting CAS numbers, then merges as normal
        :param dominant:
        :param terms:
        :return:
        """
        dom_cas = self._cas[dominant]
        k = []
        if dom_cas is not None:
            k.append(dom_cas)
        for i in terms:
            if self._cas[self._dict[i]] is not None:
                k.append((i, self._cas[i]))
        if len(k) > 1:
            raise ConflictingCas('Indices have conflicting CAS numbers: %s' % k)
        super(Flowables, self).merge(dominant, *terms)

    def _merge_set_with_index(self, it, index):
        cas = find_cas(it)
        if cas is not None:
            if self._cas[index] is not None and trim_cas(self._cas[index]) != trim_cas(cas):
                print('Conflicting CAS: incoming %s; existing [%s] = %d' % (cas, self._cas[index], index))
                raise ConflictingCas('Incoming set has conflicting CAS %s' % cas)
        super(Flowables, self)._merge_set_with_index(it, index)
