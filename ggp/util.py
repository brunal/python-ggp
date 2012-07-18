# Utility functions
import random

def isint(s):
    """ Is the given string an integer?"""
    try:
        i = int(s)
    except ValueError:
        return False
    return True

def join(lst, sep = ' '):
    lst = list(lst)
    if len(lst) == 0: return ''
    elif len(lst) == 1: return str(lst[0])
    return reduce(lambda x,y: str(x) + sep + str(y), lst)

def xor(lst, initial = 0):
    for x in lst:
        initial ^= x
    return initial

def groupAdd(grp, key):
    if key in grp:
        grp[key] += 1
    else:
        grp[key] = 1
    return grp

def listMapAdd(lm, key, item):
    l = []
    if key in lm:
        l = lm[key]
    l.append(item)
    lm[key] = l
    return lm

def setMapAdd(sm, key, item):
    s = set()
    if key in sm:
        s = sm[key]
    s.add(item)
    sm[key] = s
    return sm

def setMapMerge(dst, src):
    for k, v in src.iteritems():
        for item in v:
            setMapAdd(dst, k, item)
    
def mapMax(mp):
    val = max(mp.values())
    s = []
    for k in mp.keys():
        if mp[k] == val:
            s.append(k)
    return random.choice(s), val

def allmax(l):
    m = max(l)
    return [i for i, x in enumerate(l) if x == m]

def argmax(l):
    m = max(l)
    s = [i for i, x in enumerate(l) if x == m]
    return random.choice(s)

def argmin(l):
    m = min(l)
    s = [i for i, x in enumerate(l) if x == m]
    return random.choice(s)

def shuffle(lst):
    random.shuffle(lst)
    return lst

def joinfuncs(funcs):
    return lambda *x: [func(*x) for func in funcs]

            
        
