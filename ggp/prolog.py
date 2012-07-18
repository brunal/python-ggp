import pyswipl
import string

def run(query):
	solutions=[]
	proSolutions=pyswipl.run(query)
	for proSolution in proSolutions:
		bindings={}
		for binding in proSolution:
			i=string.find(binding,'=')
			var=binding[0:i]
			value=binding[i+1:len(binding)]
			bindings[var]=value
		solutions.append(bindings)
	return solutions

