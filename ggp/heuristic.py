class ConstantHeuristic:
    def __init__(self, val):
        self.val = val

    def value(self, state):
        return self.val

    def features(self, state):
        return {0: 1.0}

    def __str__(self):
	return 'Constant: ' + str(self.val)

class GoalHeuristic:
    def __init__(self, s, role):
        self.s = s
        self.role = role

    def value(self, state):
        return self.s.computeGoals(state)[self.role]

    def __str__(self):
	return 'Goal Heuristic'


class MaxHeuristic:
    def __init__(self, feature, gd):
        self.feature = feature
        self.gd = gd
        self.min_goal = gd.lowestReward()
        self.range = gd.highestReward() - gd.lowestReward() - 2

    def value(self, state):
        val = self.feature.scaledValue(state)
        return 1 + self.min_goal + self.range * val

    def __str__(self):
        return 'Max: ' + str(self.feature)


class MinHeuristic:
    def __init__(self, feature, gd):
        self.feature = feature
        self.gd = gd
        self.min_goal = gd.lowestReward()
        self.range = gd.highestReward() - gd.lowestReward() - 2

    def value(self, state):
        val = self.feature.scaledValue(state)
        return 1 + self.min_goal + self.range * (1-val)

    def __str__(self):
        return 'Min: ' + str(self.feature)
