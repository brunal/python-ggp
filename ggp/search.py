import time
from ggp.util import shuffle
from ggp.cache import FIFOCache

class VF:
    """
    Tuple: (value, features)
    """
    def __init__(self, tup):
        self.tup = tup
        
    def __cmp__(self, other):
        return cmp(self.tup[0], other.tup[0])

    def __repr__(self):
        return str(self.tup)

    def v(self):
        return self.tup[0]

    def f(self):
        return self.tup[1]

class SearchResponse:
    """
    Record to store search result along
    with statistics about the search
    """
    def __init__(self, bestMove, value, depth, numHE, numTSE, numSV, time):
        self.bestMove = bestMove
        self.value = value
        self.depth = depth
        self.numHeuristicEvaluations = numHE
        self.numTerminalStateEvaluations = numTSE
        self.numStatesVisited = numSV
        self.time = time

    def __str__(self):
        return 'Move: ' + str(self.bestMove) + \
               ', Value: ' + str(self.value) + \
               ', Depth: ' + str(self.depth) + \
               ', Heuristic Evaluations: ' + str(self.numHeuristicEvaluations) + \
               ', Terminal States: ' + str(self.numTerminalStateEvaluations) + \
               ', Total States: ' + str(self.numStatesVisited) + \
               ', Time: ' + str(self.time)

class Search:
    """
    General Alpha-Beta pruning search implementation.
    Works with single, double and multi-player games
    with turn-taking or simultaneous decision.
    """
    class TranspositionEntry:
        """
        Record stored for each state in the
        transposition table
        """
        def __init__(self, depth, flags, value, bestMove):
            self.depth = depth
            self.flags = flags
            self.value = value
            self.bestMove = bestMove

    def __init__(self, gd, sim, role, shouldIStop, reportAnswer):
        self.gd = gd
        self.sim = sim
        self.role = role
        self.shouldIStop = shouldIStop
        self.reportAnswer = reportAnswer
        self.tt = None

    def search(self, state, heuristic = None, removeStep=False, maxDepth = -1, maxOppMoves = -1):
        self.heuristic = heuristic
        self.deepenForced = False
        if self.role == 0:
            self.deepenForced = True
        self.tt = FIFOCache() #{} 
        self.maxOppMoves = maxOppMoves
        if heuristic == None:
            self.topLevelSearch(state, -1)
        else:
            depth = 1
            while True:
                if self.topLevelSearch(state, depth):
                    break
                depth += 1
                if depth == maxDepth:
                    break

    def topLevelSearch(self, state, depth):
        if self.heuristic:
            features = dict([(k, 0.0) for k in self.heuristic.features(state)])
        else:
            features = None
        alpha = VF((-float('inf'), features))
        beta = VF((float('inf'), features))

        # Statistics
	self.numHeuristicEvaluations = 0
	self.numTerminalStateEvaluations = 0
	self.numStatesVisited = 0
	self.startTime = time.time()

	# Search from top-level state and gather value
	value = self.alphaBeta(state, depth, alpha, beta)
        if self.shouldIStop(): return True

	# Compute legal moves for this state mostly
	# to be used to find out if this is our turn
	legalMoves = self.sim.computeLegalMoves(state)

	# Reset chosen move
	bestMove = -1

	# Check to see if this state is in 
	# the transposition table.  It should be
	# if it's our turn.
        if state in self.tt:
	    # If the state is in the TT then use the entries
	    # best move as the current best move
	    bestMove = self.tt[state].bestMove
	if bestMove == -1 or \
           self.role not in self.gd.turnTakers(legalMoves):
	    # If the state is NOT in the TT
	    # OR if the entry has a turntaker other than ourself then
	    # just choose the first move (and probably only) move
	    bestMove = set(legalMoves[self.role]).pop()
        if self.shouldIStop(): return True
	
	# Report answer
	searchResponse = SearchResponse(bestMove,#self.gd.moveTerm(bestMove),
                                        value, depth, 
                                        self.numHeuristicEvaluations,
                                        self.numTerminalStateEvaluations,
                                        self.numStatesVisited, time.time()-self.startTime)
	self.reportAnswer(searchResponse)

	# Check if we should continue
	if self.numHeuristicEvaluations == 0 and self.numTerminalStateEvaluations > 0:
            # Nothing left to search
            return True

	# It's possible to keep searching
	return False

    def alphaBeta(self, state, depth, alpha, beta):
        # Increment number of numStatesVisited states for this depth
	self.numStatesVisited += 1

	# Reset best move
	bestMove = -1;
	
	# Check if this is state is already in the
	# transposition table
        if state in self.tt:
            entry = self.tt[state]
            if entry.depth >= depth:
                if entry.flags == 'e':
		    return entry.value
                if entry.flags == 'a' and entry.value <= alpha:
		    return alpha
                if entry.flags == 'b' and entry.value >= beta:
		    return beta
	    bestMove = entry.bestMove
	if self.shouldIStop(): return None

        ############################
	# TERMINAL STATE
        if self.sim.isTerminal(state):
            if self.shouldIStop(): return None, None
	    self.numTerminalStateEvaluations += 1
            goals = self.sim.computeGoals(state)
            if self.heuristic:
                features = self.heuristic.features(state)
            else:
                features = None
	    value = VF((goals[self.role], features))
	    # Put state in transposition table
	    self.tt[state] = self.TranspositionEntry(depth, 'e', value, bestMove)
	    return value

	############################
	# HEURISTIC BOARD EVALUATION
        if depth == 0:
	    self.numHeuristicEvaluations += 1
	    value = VF((self.heuristic.value(state), self.heuristic.features(state)))
            # gjk 
            #if value <= 0 or value >= 100:
            #    raise Exception('bad value: %d' % value)
	    # Put state in transposition table
	    self.tt[state] = self.TranspositionEntry(depth, 'e', value, bestMove)
	    return value

        # Get legal moves
	legalMoves = self.sim.computeLegalMoves(state)
        if self.shouldIStop(): return None

	# Figure out whose turn it is
	turnTakers = self.gd.turnTakers(legalMoves)

        #############################
	# FORCED MOVE FOR EVERYONE
        if len(turnTakers) == 0:
	    moves = []
	    # Get each player's legal move
            for s in legalMoves:
		moves.append(set(s).pop())
            # Return the value of the next state
	    nextState = self.sim.computeNextState(state, moves)
            if self.deepenForced:
                value = self.alphaBeta(nextState, depth, alpha, beta)
            else:
                value = self.alphaBeta(nextState, depth - 1, alpha, beta)
	    return value
	
        ######################
	# TURN-TAKING
        if len(turnTakers) == 1:
	    return self.turnTakingSearch(state, legalMoves, bestMove,
                                         depth, alpha, beta, list(turnTakers).pop())

        ###########################
	# SIMULTANEOUS DECISION
        else:
	    return self.simultaneousSearch(state, legalMoves,
                                           bestMove, depth, alpha, beta)


    def turnTakingSearch(self, state, legalMoves, bestMove, depth, 
                         alpha, beta, turnTaker):
        # Get legal moves for turn taker, putting the best one first
	moveSet = legalMoves[turnTaker]
	moveList = shuffle(list(moveSet))
        if bestMove in moveSet:
	    moveList.remove(bestMove)
            moveList.insert(0, bestMove)

	# MAX: this is a teammate
        if self.role == turnTaker:#self.gd.isTeammate(self.role, turnTaker):
	    return self.maximize(state, legalMoves, bestMove, depth, 
                                 alpha, beta, turnTaker, moveList)
	# MIN: this is an opponent
        else:
	    return self.minimize(state, legalMoves, bestMove, depth,
                                 alpha, beta, turnTaker, moveList)
    

    # Handle MAX node
    def maximize(self, state, legalMoves, bestMove, depth, 
                 alpha, beta, turnTaker, moveList):
	flags = 'a'
	    
	# Iterate through moves
        for move in moveList:
	    # Create move vector for all players
	    moves = [list(x).pop() for x in legalMoves]
            moves[turnTaker] = move

	    # Make move
	    nextState = self.sim.computeNextState(state, moves)
            if self.shouldIStop(): return None
	    
	    # Expand child node
	    value = self.alphaBeta(nextState, depth - 1, alpha, beta)
            if self.shouldIStop(): return None
	    
	    # Check for beta cutoff
            if value >= beta:
		self.tt[state] = self.TranspositionEntry(depth, 'b', beta, move)
		return beta

	    # Check if this is best move
            if value > alpha:
		alpha = value
		bestMove = move
		flags = 'e'

        # No better move found, return alpha
	self.tt[state] = self.TranspositionEntry(depth, flags, alpha, bestMove)
	return alpha


    # Handle MIN node
    def minimize(self, state, legalMoves, bestMove, depth, 
                 alpha, beta, turnTaker, moveList):
	flags = 'b'
	
	# Iterate through moves
        for moveNum, move in enumerate(moveList):
            # If we've reached the maximum number of opponent moves to
            # explore then just move on
            if moveNum == self.maxOppMoves:
                break
            
	    # Create move vector for all players
	    moves = [list(x).pop() for x in legalMoves]
            moves[turnTaker] = move

	    # Make move
	    nextState = self.sim.computeNextState(state, moves)
            if self.shouldIStop(): return None
	    
	    # Expand child node
	    value = self.alphaBeta(nextState, depth - 1, alpha, beta)
            if self.shouldIStop(): return None
	    
	    # Check for alpha cutoff
            if value <= alpha:
		self.tt[state] = self.TranspositionEntry(depth, 'a', alpha, move)
		return alpha

            # Check if this is the best move
            if value < beta:
		beta = value
		bestMove = move
		flags = 'e'

        # No better move found, return beta
	self.tt[state] = self.TranspositionEntry(depth, flags, beta, bestMove)
	return beta

    
    # Handle a node with simultaneous moves
    def simultaneousSearch(self, state, legalMoves, bestMove, depth, 
                           alpha, beta):
        # Hack
        turnTaker = self.role
	moveSet = legalMoves[turnTaker]
	moveList = shuffle(list(moveSet))
        if bestMove in moveSet:
	    moveList.remove(bestMove)
            moveList.insert(0, bestMove)

        return self.maximize(state, legalMoves, bestMove, depth, 
                             alpha, beta, turnTaker, moveList)

