import re
from synlist.synlist import SynList, TermFound


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
    A SynList that enforces unique CAS numbers on sets.  Also uses case-insensitive lookup for terms > 3 characters

    The CAS thing requires overloading _new_key and _new_group and just about everything else.
    """

    def __init__(self):
        super(Flowables, self).__init__()
        self._cas = []

    def cas(self, term):
        return self._cas[self._get_index(term)]

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
        try:
            return super(Flowables, self)._get_index(term)
        except KeyError:
            if len(term.strip()) > 3:
                return super(Flowables, self)._get_index(term.lower())

    def _assign_term(self, term, index, force=False):
        if len(term) > 3:
            lterm = term.lower()
        else:
            lterm = term
        if lterm in self._dict:
            if self._dict[lterm] != index:
                if force is False:
                    raise TermFound('%s [%s: %d]' % (term, lterm, self._dict[lterm]))
        self._list[index].add(term)
        self._dict[lterm] = index

    def _new_term(self, term, index):
        term = term.strip()
        if cas_regex.match(term):
            if self._cas[index] is not None and trim_cas(self._cas[index]) != trim_cas(term):
                raise ConflictingCas('Index %d already has CAS %s' % (index, self._cas[index]))
            else:
                term = pad_cas(term)
                self._cas[index] = term
                super(Flowables, self)._new_term(trim_cas(term), index)
        self._assign_term(term, index)
        if self._name[index] is None:
            self._name[index] = term

    def _merge(self, merge, into):
        self._list[into] = self._list[into].union(self._list[merge])
        for i in self._list[into]:
            self._assign_term(i, into, force=True)
        self._list[merge] = None
        self._name[merge] = None
        self._cas[merge] = None

    def merge(self, dominant, *terms, multi_cas=False):
        """
        Flowables.merge first checks for conflicting CAS numbers, then merges as normal. the _merge interior function
        deletes cas numbers from merged entries; then this function sets the (non-conflicting) CAS number for the
        dominant entry.
        :param dominant:
        :param terms:
        :param multi_cas: [False] if True, multiple CAS numbers are allowed as synonyms;
         the first one encountered is kept canonical.
        :return:
        """
        dom = self._get_index(dominant)
        cas = [self._cas[dom]]
        for i in terms:
            cas.append(self._cas[self._get_index(i)])
        the_cas = [k for k in filter(None, cas)]
        if len(the_cas) > 1:
            if multi_cas:
                the_cas = the_cas[:1]
            else:
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
