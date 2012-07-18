import random

class RandomPlayer:
    """
    Player makes completely random moves
    """
    def __init__(self, role):
        self.role = role

    def act(self, state, legal):
        return random.choice(legal[self.role])

    def processReward(self, rewards):
        pass

class BFSPlayer:
    """
    Breadth-first search player for 
    single-player games
    """
    def __init__(self, gd, sim):
        if gd.numRoles() > 1:
            raise Exception('BFSPlayer only works on single player games')
        self.gd = gd
        self.sim = sim
        self.solution = []

    def begin(self):
        import Queue
        self.q = Queue.Queue()

    def addChild(self, node):
        self.q.put(node)

    def getNext(self):
        if self.q.empty():
            return None
        return self.q.get()
    
    def retrieveSolution(self, node):
        while node['move'] != None:
            self.solution.append(node['move'])
            node = node['parent']

    def act(self, state, legal):
        if len(self.solution) == 0:
            self.begin()
            closed = set()
            node = {'parent': None, 'move': None, 'state': state}
            while True:
                state = node['state']
                if state not in closed:
                    closed.add(state)
                    if self.sim.isTerminal(state):
                        if self.sim.computeGoals(state)[0] == self.gd.highestReward():
                            self.retrieveSolution(node)
                            break
                    else:
                        legal = self.sim.computeLegalMoves(state)[0]
                        util.shuffle(legal)
                        for move in legal:
                            next = self.sim.computeNextState(state, [move])
                            child = {'parent': node, 'move': move, 'state': next}
                            self.addChild(child)
                node = self.getNext()
                if node == None: raise Exception('No solution found')
        return self.solution.pop()
        
    def processReward(self, rewards):
        pass

class DFSPlayer(BFSPlayer):
    """
    Depth-first search player 
    for single-player games
    """
    def begin(self):
        self.stack = []

    def addChild(self, node):
        self.stack.append(node)

    def getNext(self):
        if len(self.stack) == 0:
            return None
        return self.stack.pop()

class AlphaBetaPlayer:
    """
    Minimax player with Alpha-Beta pruning
    for mutiplayer games.  Makes "paranoid assumption"
    if number of players > 2.

    Most of the work is done in search.py
    """
    def __init__(self, gd, sim, role, heuristic=None, maxDepth=-1):
        from ggp.search import Search
        self.gd = gd
        self.sim = sim
        self.role = role
        self.heuristic = heuristic
        self.maxDepth = maxDepth
        self.move = None
        self.search = Search(gd, sim, role, self.shouldIStop, self.processResponse)

    def processResponse(self, sr):
        self.move = sr.bestMove

    def shouldIStop(self):
        return False

    def act(self, state, legal):
	self.move = legal[self.role][0]
	self.search.search(state, self.heuristic, maxDepth=self.maxDepth)
	return self.move

    def processReward(self, rewards):
        # Clear out transposition table at end of match
        self.search.tt = None
        
