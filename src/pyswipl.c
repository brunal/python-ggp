#include "Python.h"
#include "SWI-Prolog.h"


static PyObject* pyswipl_run(PyObject* self_Py, PyObject* args_Py) {
char* goalString;
char* answer;
int answerCount;

PyObject* answerList_Py;
PyObject* answerString_Py;
PyObject* bindingList_Py;
PyObject* binding_Py;

term_t swipl_args;
term_t swipl_goalCharList;
term_t swipl_bindingList;
term_t swipl_head;
term_t swipl_list;
predicate_t swipl_predicate;
qid_t swipl_qid;
fid_t swipl_fid;


	/**********************************************************/
	/* The queryString_C should be a python string represting */
	/* the query to be executed on the prolog system.         */
	/**********************************************************/
	if(!PyArg_ParseTuple(args_Py, "s", &goalString))
		return NULL;
	else {

		/**********************************************************/
		/* Create a Python list to hold the lists of bindings.    */
		/**********************************************************/
	  //if ( answerList_Py != NULL )
	  // Py_DECREF(answerList_Py);
	  answerList_Py=PyList_New(0);

		/**********************************************************/
		/* Open a foreign frame and initialize the term refs.     */
		/**********************************************************/
		swipl_fid=PL_open_foreign_frame();
		swipl_head=PL_new_term_ref();		/* Used in unpacking the binding List       */
		swipl_args=PL_new_term_refs(2);		/* The compound term for arguments to run/2 */
		swipl_goalCharList=swipl_args;		/* Alias for arg 1                          */
		swipl_bindingList=swipl_args+1;         /* Alias for arg 2                          */

		/**********************************************************/
		/* Pack the query string into the argument compund term.  */
		/**********************************************************/
		PL_put_list_chars(swipl_goalCharList,goalString);

		/**********************************************************/
		/* Generate a predicate to pyrun/2                        */
		/**********************************************************/
		swipl_predicate=PL_predicate("pyrun",2,NULL);

		/**********************************************************/
		/* Open the query, and iterate through the solutions.     */
		/**********************************************************/
		swipl_qid=PL_open_query(NULL,PL_Q_NORMAL,swipl_predicate, swipl_args);
		while(PL_next_solution(swipl_qid)) {

			/**********************************************************/
			/* Create a Python list to hold the bindings.             */
			/**********************************************************/
			bindingList_Py=PyList_New(0);

			/**********************************************************/
			/* Step through the bindings and add each to the list.    */
			/**********************************************************/
			swipl_list=PL_copy_term_ref(swipl_bindingList);
			while(PL_get_list(swipl_list, swipl_head, swipl_list)) {
				PL_get_chars(swipl_head, &answer, CVT_ALL|CVT_WRITE|BUF_RING);
				answerString_Py = PyString_FromString(answer);
				PyList_Append(bindingList_Py, answerString_Py);
				Py_DECREF(answerString_Py);
			}

			/**********************************************************/
			/* Add this binding list to the list of all solutions.    */
			/**********************************************************/
			PyList_Append(answerList_Py, bindingList_Py);
			Py_DECREF(bindingList_Py); 
		}

		/**********************************************************/
		/* Free this foreign frame...                             */
		/* Added by Nathan Denny, July 18, 2001.                  */
		/* Fixes a bug with running out of global stack when      */
		/* asserting _lots_ of facts.                             */
		/**********************************************************/
		PL_close_query(swipl_qid);
		PL_discard_foreign_frame(swipl_fid);
	
		/**********************************************************/
		/* Return the list of solutions.                          */
		/**********************************************************/
		return answerList_Py;	
	}
}

static PyMethodDef pyswiplMethods[] = {
	{"run", pyswipl_run, METH_VARARGS},
	{NULL,NULL}
};

void initpyswipl() {
char *plargs[3];
term_t swipl_load;
fid_t swipl_fid;

	/**********************************************************/
	/* Initialize the prolog kernel.                          */
	/* The kernel is embedded (linked in) so I am setting the */
	/* the startup path to be the current directory. Also,    */
	/* I'm sending the -q flag to supress the startup banner. */
	/**********************************************************/
	plargs[0]="./";
	plargs[1]="-q";
	plargs[2]="-nosignals";
	PL_initialise(3,plargs);

	/**********************************************************/
	/* Load the pyrun predicate.                              */
	/* The pyrun.pl file has to be in the current working     */
	/* directory.                                             */
	/**********************************************************/
	swipl_fid=PL_open_foreign_frame();
	swipl_load=PL_new_term_ref();

	/**********************************************************/
	/* Changed by Nathan Denny July 18, 2001                  */
	/* No longer necessary to include pyrun.pl                */
	/**********************************************************/
	/*PL_chars_to_term("consult('pyrun.pl')", swipl_load);*/
	PL_chars_to_term("assert(pyrun(GoalString,BindingList):-(atom_codes(A,GoalString),atom_to_term(A,Goal,BindingList),call(Goal))).", swipl_load);

	PL_call(swipl_load,NULL);
	PL_discard_foreign_frame(swipl_fid);

	/**********************************************************/
	/* Call the Python module initializer.                    */
	/**********************************************************/
	(void) Py_InitModule("pyswipl",pyswiplMethods);
}
