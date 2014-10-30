#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import math
import itertools

from dedupe.cpredicates import ngrams, initials

words = re.compile(r"[\w']+").findall
integers = re.compile(r"\d+").findall
start_word = re.compile(r"^([\w']+)").match
start_integer = re.compile(r"^(\d+)").match

class Predicate(object) :
    def __iter__(self) :
        yield self
        
    def __repr__(self) :
        return "%s: %s" % (self.type, self.__name__)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other) :
        return repr(self) == repr(other)

class SimplePredicate(Predicate) :
    type = "SimplePredicate"

    def __init__(self, func, field) :
        self.func = func
        self.__name__ = "(%s, %s)" % (func.__name__, field)
        self.field = field

    def __call__(self, record_id, record) :
        column = record[self.field]
        return self.func(column)



class TfidfPredicate(Predicate):
    type = "TfidfPredicate"

    def __init__(self, threshold, field):
        self.__name__ = '(%s, %s)' % (threshold, field)
        self.field = field
        self.canopy = {}
        self.threshold = threshold
        self._index = None

    def __call__(self, record_id, record) :
        centers = self.canopy.get(record_id)

        if centers is not None :
            blocks = [unicode(center) for center in centers]
        else:
            blocks = ()

        return blocks
        
    @property
    def index(self) :
        return self._index
        
    @index.setter
    def index(self, value) :
        self.old_class = self.__class__
        self.__class__ = TfidfIndexPredicate

        self._index = value

    @index.deleter
    def index(self) :
        self.__class__ = self.old_class


    def __getstate__(self):

        result = self.__dict__.copy()

        return {'__name__': result['__name__'],
                'field' : result['field'],
                'threshold' : result['threshold']}

    def __setstate__(self, d) :
        self.__dict__ = d
        self._index = None
        self.canopy = {}

class TfidfIndexPredicate(TfidfPredicate) :

    def __call__(self, record_id, record) :
        centers = self.canopy.get(record_id)

        if centers is None :
            centers = self.index.search(record[self.field], self.threshold)
        
        blocks = [unicode(center) for center in centers]
            
        return blocks

class CompoundPredicate(Predicate) :
    type = "CompoundPredicate"

    def __init__(self, predicates) :
        self.predicates = predicates
        self.__name__ = u'(%s)' % u', '.join([unicode(pred)
                                              for pred in 
                                              predicates])

    def __iter__(self) :
        for pred in self.predicates :
            yield pred

    def __call__(self, record_id, record) :
        predicate_keys = [predicate(record_id, record)
                          for predicate in self.predicates]
        return [u':'.join(block_key)
                for block_key
                in itertools.product(*predicate_keys)]
 

def wholeFieldPredicate(field):
    """return the whole field"""

    if field:
        return (field, )
    else:
        return ()

def tokenFieldPredicate(field):
    """returns the tokens"""
    return set(words(field))

def firstTokenPredicate(field) :
    first_token = start_word(field)
    if first_token :
        return first_token.groups()
    else :
        return ()

def commonIntegerPredicate(field):
    """return any integers"""
    return set(integers(field))

def nearIntegersPredicate(field):
    """return any integers N, N+1, and N-1"""
    ints = integers(field)
    near_ints = set(ints)
    for char in ints :
        num = int(char)
        near_ints.add(unicode(num-1))
        near_ints.add(unicode(num+1))
        
    return near_ints

def firstIntegerPredicate(field) :
    first_token = start_integer(field)
    if first_token :
        return first_token.groups()
    else :
        return ()
    
def commonFourGram(field):
    """return 4-grams"""
    return ngrams(field, 4)

def commonSixGram(field):
    """return 6-grams"""
    return ngrams(field, 6)

def sameThreeCharStartPredicate(field):
    """return first three characters"""
    return initials(field, 3)

def sameFiveCharStartPredicate(field):
    """return first five characters"""
    return initials(field, 5)

def sameSevenCharStartPredicate(field):
    """return first seven characters"""
    return initials(field, 7)

def sortedAcronym(field) :
    return (''.join(sorted(each[0] for each in field.split())),)

def wholeSetPredicate(field_set):
    if field_set :
        return (unicode(field_set),)
    else :
        return ()

def commonSetElementPredicate(field_set):
    """return set as individual elements"""
    if field_set :
        return tuple([unicode(each) for each in field_set])
    else :
        return ()

def lastSetElementPredicate(field_set) :
    try :
        return (unicode(sorted(field_set).pop()), )
    except IndexError :
        return ()


def firstSetElementPredicate(field_set) :
    try :
        return (unicode(sorted(field_set, reverse=True).pop()), )
    except IndexError :
        return ()

def latLongGridPredicate(field, digits=1):
    """
    Given a lat / long pair, return the grid coordinates at the
    nearest base value.  e.g., (42.3, -5.4) returns a grid at 0.1
    degree resolution of 0.1 degrees of latitude ~ 7km, so this is
    effectively a 14km lat grid.  This is imprecise for longitude,
    since 1 degree of longitude is 0km at the poles, and up to 111km
    at the equator. But it should be reasonably precise given some
    prior logical block (e.g., country).
    """
    if any(field) :
        return (unicode([round(dim, digits) for dim in field]),)
    else :
        return ()
