import ggp.util as util
import tpg
import string

GDL_KEYWORDS = set(['role', 'init', 'true', 'next', 'legal', 'does', 'goal', 'terminal', 'distinct'])
GDL_OPS = set(['not', 'or', 'and', '<='])

class Message:
    def __init__(self, msgType):
        self.msgType = msgType
        self.lastMoves = None

    def __repr__(self):
        return self.msgType + " message"

    def __str__(self):
        if self.msgType == 'start':
            return '(start ' + self.matchID + ' ' + \
                   str(self.role) + ' (' + util.join(self.sents) + ') ' + \
                   str(self.startClock) + ' ' + str(self.playClock) + ')'
        else: # play, replay or stop
            s = '(' + self.msgType + ' ' + self.matchID + ' '
            if self.lastMoves:
                return s + '(' + util.join(self.lastMoves) + '))'
            else:
                return s + 'nil)'

class KIFParser(tpg.Parser):
    r"""
        separator space '\s+' ;
        separator comment ';.*';

        token lparen    '\('    ;
        token rparen    '\)'    ;
        token const     '\w[\w\-_\.]*'   $ self.make_const
        token var       '\?(\w\-*)+' $ self.make_var

        START/l ->              $ l = []
                   ( comment
                   | Sentence/s $ l.append(s)
                   )*
        ;

        Messages/n -> $ n = []
                      ( Message/m  $ n.append(m)
                      )*
        ;

        Message/m -> ( StartMessage/m
                     | PlayMessage/m
                     | ReplayMessage/m
                     | StopMessage/m
                     )
        ;

        StartMessage/m -> lparen 'start' $ m = Message('start')
                          const/c        $ m.matchID = c
                          Relation/r     $ m.role = r
                          lparen START/l rparen $ m.sents = l
                          const/c        $ m.startClock = int(c)
                          const/c        $ m.playClock = int(c)
                          rparen
        ;
                       
        PlayMessage/m -> lparen 'play'  $ m = Message('play')
                         const/c        $ m.matchID = c
                         ( 'nil'        $ m.lastMoves = None
                         | lparen       $ m.lastMoves = []
                           ( Relation/r $ m.lastMoves.append(r)
                           )+ rparen
                         )
                         rparen
        ;

        ReplayMessage/m -> lparen 'replay'  $ m = Message('replay')
                         const/c        $ m.matchID = c
                         ( 'nil'        $ m.lastMoves = None
                         | lparen       $ m.lastMoves = []
                           ( Relation/r $ m.lastMoves.append(r)
                           )+ rparen
                         )
                         rparen
        ;

        StopMessage/m -> lparen 'stop'  $ m = Message('stop')
                         const/c        $ m.matchID = c
                         ( 'nil'        $ m.lastMoves = None
                         | lparen       $ m.lastMoves = []
                           ( Relation/r $ m.lastMoves.append(r)
                           )+ rparen
                         )
                         rparen
        ;

        Sentence/s -> ( Logical/s | Relation/s ) ;

        Relation/r ->                    $ terms = []
                      ( const/c
                        | lparen const/c
                        ( ( Relation/t |
                            var/t )      $ terms.append(t)
                        )*
                        rparen
                      )                  $ r = Struct(c, terms)
        ;
                                
        Relations/n -> $ n = []
                      ( Relation/r  $ n.append(r)
                      )*
        ;

        VizLog/v ->                 $ v = []
                    ( lparen        
                      Relations/n  
                      rparen        $ v.append(n)
                    )*
        ;
                    

        Logical/l ->  lparen       $ sents = []
                      ( 'or'   $ op = 'or'
                      | 'not'  $ op = 'not'
                      | 'and'  $ op = 'and'
                      | '<='   $ op = '<='
                      )
                      ( Sentence/s $ sents.append(s)
                      )+
                      rparen       $ l = LogicalSentence(op, sents)
        ;

    """

    def make_var(self,s):
        return Var(s.strip()[1:])

    def make_const(self,s):
        return s.replace('-', '_').strip()

    def parse(self, start, s):
        return tpg.Parser.parse(self, start, string.lower(s))


class PrologParser(tpg.Parser):
    r"""
        separator space '\s+' ;

        token lparen    '\('    ;
        token rparen    '\)'    ;
        token comma     ','     ;
        token const     '_*[a-z0-9](\w\-*)*' $ self.make_const
        token var       '_*[A-Z](\w\-*)*' $ self.make_var

        START/r ->    const/c            $ terms = []
                      ( 
                        lparen
                        ( ( START/t | var/t )      $ terms.append(t)
                          (
                            comma
                            ( START/t | var/t )    $ terms.append(t)
                          )*
                        )*
                        rparen
                      )?                 $ r = Struct(c, terms)
        ;

    """

    def make_var(self,s):
        return Var(string.lower(string.strip(s)))

    def make_const(self,s):
        name = s.strip()
        if name[:4] == 'ggp_':
            return name[4:]
        else:
            return name
        
    def parse(self, start, s):
        try:
            return tpg.Parser.parse(self, start, string.lower(s))
        except Exception:
            print("Error parsing prolog: " + str(s))
            raise


class Functor:
    def __init__(self, name, arity):
        self.name = name
        self.arity = arity

    def __repr__(self):
        #if self.arity == 0:
        #    return self.name
        return self.name + '/' + str(self.arity)

    def __eq__(self, func):
        return self.name == func.name and self.arity == func.arity

    def __ne__(self, func):
        return not self.__eq__(func)

    def __hash__(self):
        return self.name.__hash__() ^ self.arity*(self.arity+1)#id(self.arity)
    
    def struct(self, terms = []):
        if len(terms) != self.arity:
            raise Exception('Length of terms: ' + str(len(terms)) +
                            ' does not match arity: ' + str(self.arity))
        return Struct(self.name, terms)

    def relationDomain(self, index):
        return RelationDomain(self, index)

    def relationDomains(self):
        return [self.relationDomain(idx) for idx in range(self.arity)]

    def prolog(self):
        if self.name in GDL_KEYWORDS or util.isint(self.name):
            return self.name + '/' + str(self.arity)
        else:
            return 'ggp_' + self.name + '/' + str(self.arity)


class RelationDomain:
    def __init__(self, functor, index):
        if index >= functor.arity:
            raise Exception('Index ' + str(index) + ' is >= arity of ' +
                            str(functor))
        self.functor = functor
        self.index = index

    def __repr__(self):
        return str(self.functor) + ':' + str(self.index)

    def __eq__(self, rd):
        return self.functor == rd.functor and self.index == rd.index

    def __ne__(self, rd):
        return not self.__eq__(rd)

    def __hash__(self):
        return self.functor.__hash__() ^ self.index*(self.index+1)#id(self.index)

    def name(self):
        return self.functor.name

    def arity(self):
        return self.functor.arity

    def neighbors(self):
        return [RelationDomain(self.functor, i) for i in range(self.functor.arity) \
                if i != self.index]

class Var:
    "KIF Variable"
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '?' + self.name

    def __eq__(self, var):
        return self.name == var.name

    def __ne__(self, var):
        return not self.__eq__(var)

    def __hash__(self):
        return self.name.__hash__()

    def prolog(self):
        return self.name.upper()

    
class Struct:
    "Basic KIF Struct"
    def __init__(self, name, terms = []):
        self.name = name
        self.terms = terms

    def __repr__(self):
        if self.arity() == 0:
            return self.name
        else:
            return '(' + self.name + ' ' + util.join(self.terms) + ')'

    def __eq__(self, struct):
        return struct and self.name == struct.name and self.terms == struct.terms

    def __ne__(self, struct):
        return not self.__eq__(struct)

    def __hash__(self):
        ret = self.name.__hash__()
        for t in self.terms:
            ret ^= t.__hash__()
        return ret
    
    def arity(self):
        return len(self.terms)

    def functor(self):
        return Functor(self.name, self.arity())

    def relationDomain(self, index):
        return self.functor().relationDomain(index)

    def relationDomains(self):
        return self.functor().relationDomains()

    def varOccur(self):
        occur = {}
        for j, t in enumerate(self.terms):
            if t.__class__ == Var:
                util.setMapAdd(occur, t, self.relationDomain(j))
            else:
                util.setMapMerge(occur, t.varOccur())
        return occur

    def prologName(self):
        if self.name in GDL_KEYWORDS or util.isint(self.name):
            return self.name
        else:
            return 'ggp_' + self.name

    def prolog(self):
        if self.arity() == 0:
            return self.prologName()
        elif self.name == 'distinct':
            return self.terms[0].prolog() + ' \\== ' + \
                   self.terms[1].prolog()
        else:
            terms = [x.prolog() for x in self.terms]
            return self.prologName() + '(' + util.join(terms, ',') + ')'


class LogicalSentence:
    "KIF logical sentence"
    def __init__(self, op, sents):
        self.op = op
        self.sents = sents

    def __repr__(self):
        return '(' + str(self.op) + ' ' + util.join(self.sents) + ')'

    def __eq__(self, ls):
        return self.op == ls.op and self.sents == ls.sents

    def __ne__(self, ls):
        return not self.__eq__(ls)
    
    def varOccur(self):
        occur = {}
        for s in self.sents:
            util.setMapMerge(occur, s.varOccur())
        return occur

    def prolog(self):
        head = self.sents[0].prolog()
        if self.op == '<=':
            if len(self.sents) == 1:
                return head
            else:
                cdr = LogicalSentence('and', self.sents[1:])
                return head + " :- " + cdr.prolog()
        elif self.op == 'not':
            return '\\+ ' + head
        elif self.op == 'or':
            clauses = [s.prolog() for s in self.sents]
            return '(' + util.join(clauses, ' ; ') + ')'
        elif self.op == 'and':
            clauses = [s.prolog() for s in self.sents]
            return '(' + util.join(clauses, ',') + ')'
        else:
            raise Exception('Unsupported op: ' + str(self.op))
        
