class FIFOCache:
    """
    First-in / First-out cache
    to speed up key-value lookups
    """
    class __Node:
        def __init__(self):
            self.key = None
            self.val = None
        def __repr__(self):
            return '(key: ' + str(self.key) + ', ' + \
                   'val: ' + str(self.val) + ')'

    def __init__(self, capacity=4096):
        self.capacity = capacity
        self.current = 0
        self.__keys = {}
        self.__nodes = [self.__Node() for _ in range(capacity)]

    def __len__(self):
        return len(self.__nodes)

    def __contains__(self, key):
        return self.__keys.has_key(key)

    def __setitem__(self, key, obj):
        if self.__keys.has_key(key):
            self.__nodes[self.__keys[key]].val = obj
        else:
            node = self.__nodes[self.current]
            if node.key and node.key in self.__keys:
                del self.__keys[node.key]
            node.key = key
            node.val = obj
            self.__keys[key] = self.current
            self.current += 1
            if self.current == self.capacity:
                # Empty cache when full
                self.current = 0
        
    def __getitem__(self, key):
        return self.__nodes[self.__keys[key]].val

    def __iter__(self):
        for k in self.__keys:
            yield k
        raise StopIteration
