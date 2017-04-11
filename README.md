# SynList
Python classes for managing sets of synonyms

## SynList spec

 * A SynList is a collection of unique terms that map to a smaller collection of items.
   - terms must be .strip()ed of leading + trailing spaces

   - Possible enhancement: at instantiation, a SynList can be made case-insensitive, in which case each term is .lower()ed before adding

 * a single term MAY NOT refer to two items.

 * `SynList.name(term)`: Each item has a canonical name which is ordinarily the first term used to describe it, but can be re-set later
   - the "name" of the name is a class property which defaults to "name"
   - an item's name must be a term referring to that item.

 * a synlist serializes and deserializes to a single json structure containing two keys:
   - the list, whose key is the __class__.__name__
     - entries in the list each have 'name' and 'synonyms' keys
   - 'ignoreCase' which is the case insensitivity boolean

   - enhancement: if the serialization target is a directory, serializes each term into its own file, grouped into subdirectories by the first letter of the canonical name. In this situation, case insensitivity is indicated by the *presence or absence* of a file called 'ignoreCase' in the root directory.

Application Programming Interface:

 * 'SynList.index(term)` each item has an instantiation-specific index which may be used for internal applications to refer to items directly. the index is stable only within the instantiation and is not stable across de/serialization.

 * `SynList.add_term(term)` : if the term is known, return the index of the associated item; otherwise create a new item

 * Adding a synonym requires two terms in any order that are synonyms.
   - If either term exists in the SynList, the other term is added
   - If both exist as separate items, an Inconsistency error is raised
   - if neither exist, a new item is created in which both terms are synonyms and the first is canonical

 * A set of synonyms can be used to create a new group (`.new_set(iterable, name=None)`)
   - if name is None, the first term will be used as the name
   - duplicate entries will be SILENTLY DROPPED.

 * A set of synonyms can be added as a group, which may be more efficient: (`.add_set(iterable, merge=False, name=None)`)
   - all synonyms are checked for membership in the synlist
   - if one item is found:
     - if `merge` is `False`: add non-duplicative terms as a new set
     - if `merge` is `True`: add non-duplicative terms to existing set
   - if multiple items are found, an Inconsistency error is raised
   - if no items are found, a new item is created in which all the terms are synonyms

 * Two sets of synonyms can be merged by supplying two or more terms in sequence (`.merge(dominant, *terms)`)
   - the first term's canonical name is kept
   - the subsequent terms' synonyms are all added to the first
   - (the second term's list entry is deleted; the index will return `None`)
   = if either key is not found, a KeyError is raised
   = if both keys correspond to the same item, then nothing happens and no error is raised

 * 

 * A term can be removed from a set and made into a new item simply by naming it (`.detach(term)`)

 * a term can be moved from one item to another by specifying the term and a term for the new item. (`.move(term, new_term)`)




== Flowables sepc

* Flowables is a SynList in which each item is a substance called a 'flowable'

* Flowables terms are case-sensitive BUT for terms with longer than 3 characters, the .lower() term is also added

* If a CAS number is added, it becomes the canonical name

* A flowable is not allowed to have two CAS numbers: distinct CAS numbers implies distinct flowables.
  (not sure about this- in fact, I am sure there are duplicate CAS numbers- but it seems necessary empirically
   based on my existing collection of synonyms. Best practice seems to be that CAS numbers are 1:1. More insight will come for this as I get some unit tests written.)

