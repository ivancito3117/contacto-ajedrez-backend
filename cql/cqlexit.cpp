#include <stdio.h>
#include "cqlexit.h"
#ifndef INTEGRATED  
#include "cqlglobals.h"
void cql_gui_exit(string message, int linenumber, int columnnumber){
  printf("\n%s linenumbererror %d\n%s columnnumbererror %d\n%s%s%s\n",
	 CqlGuiVariable,
	 linenumber,
	 CqlGuiVariable,
	 columnnumber,
	 CqlGuiErrorStart,
	 message.c_str(),
	 CqlGuiErrorStop
);
  exit(1);
}
void cql_exit(string message){
  if(message.empty())message="BAD CQL_EXIT ARGUMENT";
  printf("\n%s\n",message.c_str());
  if(CqlGui)
    printf("%s %s %s\n",CqlGuiErrorStart,message.c_str(),CqlGuiErrorStop);
  CqlIsExiting=true; //technically this should be atomic but if a race only a bad error message. Added 9.324
  //std::abort(); fails because "abort" message output
  if (CqlRunningThreads) //9.353
    std::abort();
  else
    exit(1);
  //std::_Exit(1); // 9.350 and reverted
}

void cql_exit(int i){
  exit(i);
}

void cql_exit(){
  exit(0);
}
#endif



