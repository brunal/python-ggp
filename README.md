Python-GGP
==========

Python framework for General Game Playing.

Python code developed in the course of Gregory Kuhlmann's dissertation work at the University of Texas at Austin.
Imported from SVN hosted on Googlecode.

Dependencies:
  Python: >= 2.6
  SWI-Prolog: install from source
    (Tested with v6.0.2 for x86_64-linux)

To build:
  make

  (If it succeeds, you will see a pyswipl.so file created.)

To run a simple offline match:
  ./offlineplay games/blocks.kif

To run a match with two clients using the test gamemaster:
  1st terminal: ./gameplayer -p 5600
  2nd terminal: ./gameplayer -p 5601
  3rd terminal: ./gamemaster games/ttt.kif 30 15 localhost 5600 localhost 5601


