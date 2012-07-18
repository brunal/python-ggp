from ggp.kif import *
from ggp.gd import *

COMPILED_PREDS = [ROLE, NEXT, LEGAL, GOAL, TERMINAL]

class PrologSimulator:
    import ggp.prolog as prolog

    def __init__(self, gd):
        self.parser = KIFParser()
        self.state = None
        self.moves = None
        self.gd = gd
        for r in self.gd.rules:
            self.assertRule(r)

    def assertRule(self, rule):
        self.prolog.run('assert((' + rule.prolog() + ')).')

    def abolishFunctor(self, func):
        self.prolog.run('abolish(' + str(func) + ').')

    def cleanup(self):
        funcs = list(self.gd.relations)
        funcs.extend(COMPILED_PREDS)
        for func in funcs:
            self.abolishFunctor(func.prolog())

    def assertTrue(self, state):
        if self.state != state:
            self.prolog.run("abolish(true/1).")
            self.state = state
            terms = [self.gd.statePrologTerm(i) for i in state]
            if len(terms) == 0:
                raise Exception('Encountered empty state in assertTrue')
            for t in terms:
                self.prolog.run("assert(true(" + t + ")).")

    def assertDoes(self, moves):
        #gjk
        if True:#self.moves != moves:
            self.moves = moves
            self.prolog.run("abolish(does/2).")
            terms = [self.gd.movePrologTerm(i) for i in moves]
            if len(terms) == 0:
                raise Exception('Encountered empty move set in assertDoes')
            for i, t in enumerate(terms):
                role = self.gd.roleTerm(i)
                self.prolog.run("assert(does(" + role.prolog() + \
                           ", " + t + ")).")

    def isTerminal(self, state):
        self.assertTrue(state)
        result = self.prolog.run("terminal.")
        return result

    def computeGoals(self, state):
        self.assertTrue(state)
        queries = ["goal(" + r.prolog() + ", X)." \
                   for r in self.gd.roles]
        results = [int(self.prolog.run(q)[0]["X"]) \
                   for q in queries]
        return results

    def computeLegalMoves(self, state):
        self.assertTrue(state)
        queries = ["legal(" + r.prolog() + ", X)." \
                   for r in self.gd.roles]
        results = [set() for _ in self.gd.roles]
        for i, q in enumerate(queries):
            for x in self.prolog.run(q):
                results[i].add(self.gd.movePrologIndex(x["X"]))
            results[i] = list(results[i])
        return results
        
    def computeNextState(self, state, moves):
        self.assertTrue(state)
        self.assertDoes(moves)
        results = State()
        for x in self.prolog.run("next(X)."):
            results.add(self.gd.statePrologIndex(x["X"]))
        return results

    def prologQuery(self, q, state=None, moves=None):
        if state:
            self.assertTrue(state)
        if moves:
            self.assertDoes(moves)
        return self.prolog.run("(" + q + ").")

class SimCache:
    class LookupRec:
        def __init__(self):
            self.terminal = None
            self.goals = None
            self.legal = None
            self.next ={}

    class Moves(list):
        def __hash__(self):
            h = 1311743
            for x in self:
                h ^= x*(x+1)
            return h

    def __init__(self, sim):
        self.sim = sim
        from ggp.cache import FIFOCache
        self.lookup = FIFOCache()

    def isTerminal(self, state):
        if state in self.lookup:
            if self.lookup[state].terminal != None:
                return self.lookup[state].terminal
        else:
            self.lookup[state] = self.LookupRec()
        result = self.sim.isTerminal(state)
        self.lookup[state].terminal = result
        return result

    def computeGoals(self, state):
        if state in self.lookup:
            if self.lookup[state].goals != None:
                return self.lookup[state].goals
        else:
            self.lookup[state] = self.LookupRec()
        result = self.sim.computeGoals(state)
        self.lookup[state].goals = result
        return result

    def computeLegalMoves(self, state):
        if state in self.lookup:
            if self.lookup[state].legal != None:
                return self.lookup[state].legal
        else:
            self.lookup[state] = self.LookupRec()
        result = self.sim.computeLegalMoves(state)
        self.lookup[state].legal = result
        return result

    def computeNextState(self, state, m):
        mp = None
        if state not in self.lookup:
            self.lookup[state] = self.LookupRec()
        mp = self.lookup[state].next
        moves = self.Moves(m)
        if moves in mp :
            return mp[moves]
        result = self.sim.computeNextState(state, moves)
        mp[moves] = result
        return result

    def __getattr__(self, attr):
        return getattr(self.sim, attr)


class CachedSimulator(SimCache):
    def __init__(self, gd):
        SimCache.__init__(self, PrologSimulator(gd))
