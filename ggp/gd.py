from ggp.kif import *
from ggp.util import setMapAdd

ROLE = Functor('role', 1)
INIT = Functor('init', 1)
TRUE = Functor('true', 1)
NEXT = Functor('next', 1)
LEGAL = Functor('legal', 2)
DOES = Functor('does', 2)
GOAL = Functor('goal', 2)
TERMINAL = Functor('terminal', 0)
DISTINCT = Functor('distinct', 2)

class GameDescription:
    "GDL Game Description"
    def __init__(self, filename = ''):
        self.roles = []
        self.rules = []
        self.initRules = []

        self.relationals = {}
        self.domains = {}
        self.sharedDomains = {}

        self.orderings = {}
        self.orderingsInv = {}
        self.loops = {}
        self.orderedStateVars = {}

        self.relations = set()
        self.functions = set()
        self.objects = set()
        self.stateVars = set()
        self.actions = set()
        self.goals = set()

        self.boards = {}

        self.stateTerms = []
        self.moveTerms = []
        self.stateTermsInv = {}
        self.moveTermsInv = {}

        self.statePrologTerms = []
        self.movePrologTerms = []
        self.statePrologTermsInv = {}
        self.movePrologTermsInv = {}

        self.SV = {}
        self.ROT = {}
        self.prologParse = PrologParser()

        self.stepCounter = None

        if filename != '':
            self.loadKIF(filename)


    def loadKIF(self, filename):
        infile = open(filename, 'r')
        text = infile.read()
        self.loadText(text)

    def loadText(self, text):
        parse = KIFParser()
        sents = parse(text)
        self.processKIF(sents)

    def processKIF(self, sents):
        initTerms = []
        varOccur = []
        for s in sents:
            if s.__class__ == Struct:
                functor = s.functor()
                if functor == ROLE:
                    self.roles.append(s.terms[0])
                    self.rules.append(s)
                elif functor == INIT:
                    initTerms.append(s.terms[0])
                    self.initRules.append(s)
                elif functor == DISTINCT or \
                     functor == TRUE or \
                     functor == NEXT:
                    raise Exception('Unexpected functor: ' + str(functor))
                else:
                    if functor != LEGAL and \
                       functor != TERMINAL:
                        setMapAdd(self.relationals, s.functor(), s)
                    self.rules.append(s)
            elif s.__class__ == LogicalSentence:
                varOccur.extend(s.varOccur().values())
                self.rules.append(s)
            self.processFunctions(s)
        self.initialState = State([self.stateIndex(t) for t in initTerms])

        self.domains[RelationDomain(TRUE, 0)] = self.stateVars
        self.domains[RelationDomain(NEXT, 0)] = self.stateVars
        self.domains[RelationDomain(DOES, 1)] = self.actions
        self.domains[RelationDomain(LEGAL, 1)] = self.actions
        self.domains[RelationDomain(GOAL, 1)] = self.goals
        roleNames = set([t.functor() for t in self.roles])
        self.domains[RelationDomain(ROLE, 0)] = roleNames
        self.domains[RelationDomain(DOES, 0)] = roleNames
        self.domains[RelationDomain(LEGAL, 0)] = roleNames
        self.domains[RelationDomain(GOAL, 0)] = roleNames

        for s in varOccur:
            current = set()
            for rd in s:
                if rd in self.domains:
                    current.add(rd)
                    if rd in self.sharedDomains:
                        for rd2 in self.sharedDomains[rd]:
                            current.add(rd2)
            for rd in current:
                self.sharedDomains[rd] = current

        uniqueDomains = []
        for srd in self.sharedDomains.values():
            if srd not in uniqueDomains:
                uniqueDomains.append(srd)
                self.uniteSet(srd)

        self.goals = set([int(f.name) for f in self.domains[RelationDomain(GOAL, 1)]])
            
            
    def uniteSet(self, s):
        union = set()
        for key in s:
            if key in self.domains:
                union = union.union(self.domains[key])
        for key in s:
            if key in self.domains:
                self.domains[key] = union


    def processFunctions(self, s):
        if s.__class__ == LogicalSentence:
            for sent in s.sents:
                self.processFunctions(sent)
        elif s.__class__ == Struct:
            functor = s.functor()
            if functor == INIT or \
               functor == TRUE or \
               functor == NEXT:
                t = s.terms[0]
                if t.__class__ == Struct:
                    self.stateVars.add(t.functor())
            elif functor == DOES or \
                functor == LEGAL:
                t = s.terms[1]
                if t.__class__ == Struct:
                    self.actions.add(t.functor())
            elif functor == GOAL:
                t = s.terms[1]
                if t.__class__ == Struct:
                    self.goals.add(t.functor())
            elif functor == TERMINAL or \
                 functor == DISTINCT or \
                 functor == ROLE:
                pass
            else:
                if functor not in self.relations:
                    if functor in self.functions:
                        raise Exception('Relation exists as function')
                    self.relations.add(functor)
                    for rd in functor.relationDomains():
                        self.domains[rd] = set()
                for i in range(s.arity()):
                    t = s.terms[i]
                    if t.__class__ == Struct:
                        setMapAdd(self.domains, s.relationDomain(i), t.functor())
            for t in s.terms:
                if t.__class__ == Struct:
                    self.processFunctionalTerm(t)


    def processFunctionalTerm(self, ft):
        functor = ft.functor()
        if functor not in self.functions:
            if functor in self.relations:
                raise Exception('Function already exists as relation: ' + str(functor))
            if ft.arity() == 0:
                self.objects.add(functor)
            else:
                self.functions.add(functor)
            for rd in functor.relationDomains():
                self.domains[rd] = set()
        for i, t in enumerate(ft.terms):
            if t.__class__ == Struct:
                setMapAdd(self.domains, ft.relationDomain(i), t.functor())
                self.processFunctionalTerm(t)


    def processRelationals(self):
        for k, v in self.relationals.iteritems():
            self.checkOrdering(k, v)
        

    def checkOrdering(self, functor, sents):
        if functor.arity != 2 or len(sents) < 1:
            return False
        forward = {}
        backward = {}
        for s in sents:
            first = s.terms[0]
            second = s.terms[1]
            if first in forward or \
               second in backward:
                return False
            forward[first] = second
            backward[second] = first
        diff = set(forward.keys()).difference(set(backward.keys()))
        ordering = []
        if len(diff) == 0:
            start = forward.keys().pop()
            while True:
                ordering.append(start)
                if start not in forward:
                    return False
                start = forward[start]
                if start in ordering:
                    break
            if len(ordering) == len(forward):
                self.loops[functor] = forward
                return True
        elif len(diff) == 1:
            start = diff.pop()
            while True:
                ordering.append(start)
                if start not in forward:
                    break
                start = forward[start]
            if len(ordering) == len(forward) + 1:
                self.orderings[functor] = ordering
                invMap = {}
                for i, o in enumerate(ordering):
                    invMap[o] = i
                self.orderingsInv[functor] = invMap
                return True
        return False

    def roleTerm(self, index):
        return self.roles[index]


    def roleIndex(self, r):
        return self.roles.index(r)


    def numRoles(self):
        return len(self.roles)

    def highestReward(self):
        return max(self.goals)

    def averageReward(self):
        return sum(self.goals) / len(self.goals)

    def lowestReward(self):
        return min(self.goals)

    def kifTerms(self, state):
        return map(self.stateTerm, state)

    def stateTerm(self, index):
        return self.stateTerms[index]

    def stateIndex(self, t):
        try:
            return self.stateTermsInv[t]
        except KeyError:
            return self.newStateIndex(t, t.prolog())


    def statePrologTerm(self, index):
        return self.statePrologTerms[index]

    def statePrologIndex(self, tp):
        try:
            return self.statePrologTermsInv[tp]
        except KeyError:
            return self.newStateIndex(self.prologParse(tp), tp)

    def newStateIndex(self, t, tp):
	    self.stateTerms.append(t)
            self.statePrologTerms.append(tp)
	    i = len(self.stateTerms) - 1;
	    self.stateTermsInv[t] = i
            self.statePrologTermsInv[tp] = i
            return i

    def moveTerm(self, index):
        return self.moveTerms[index]

    def moveIndex(self, t):
        try:
            return self.moveTermsInv[t]
        except KeyError:
            return self.newMoveIndex(t, t.prolog())

    def movePrologTerm(self, index):
        return self.movePrologTerms[index]

    def movePrologIndex(self, tp):
        try:
            return self.movePrologTermsInv[tp]
        except KeyError:
            return self.newMoveIndex(self.prologParse(tp), tp)

    def newMoveIndex(self, t, tp):
        self.moveTerms.append(t)
        self.movePrologTerms.append(tp)
        i = len(self.moveTerms) - 1;
        self.moveTermsInv[t] = i
        self.movePrologTermsInv[tp] = i
        return i

    def turnTakers(self, legalMoves):
	turnTakers = []
        for r, s in enumerate(legalMoves):
            if len(s) > 1:
                turnTakers.append(r)
	return turnTakers        



class State(set):
    def __init__(self, initSet=[]):
        set.__init__(self, initSet)
        self.__hash = None
    def __hash__(self):
        if self.__hash:
            return self.__hash
        self.__hash = 1319817
        for x in self:
            self.__hash ^= x*(x+1)#id(x)
        return self.__hash

if __name__ == '__main__':
    main()

    
