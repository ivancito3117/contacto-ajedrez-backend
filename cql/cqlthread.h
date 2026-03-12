#include "node.h"
void cql_execute(string cqlfilename,int nthreads);
vector<CqlNode*> generateCqlNodes(string filename, int nthreads, bool*ispersistentp);
void thread_exec(CqlNode* cqlnode,
		 QGame*qgame,
		 int threadindex,
		 int nthreads,
		 size_t* ngames,
		 vector<GameSortInfo>* result);
void cqlcheckvalid(vector<CqlNode*>&);
void cql_output_status(int gamenumber,
		       int threadindex,
		       bool matched);
int cql_compute_number_threads(void); // the hardware concurrency

