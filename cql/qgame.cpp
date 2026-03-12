#include "qgame.h"
#include "markboard.h"
#include "commentstack.h"
#include "cqlglobals.h"
#include <cstring>

const TagSection* QGame::getTagSection() const{
  uassert(theTagSection.isInitialized,"tag section const is not initialized");
  return &theTagSection;
}

TagSection* QGame::getTagSection(){
  uassert(theTagSection.isInitialized,"tag section is not initialized");
  return &theTagSection;
}

QGame::QGame(PgnSource* pgnsource,bool variations):pgnSource(pgnsource){
  game=new Game;
  uassert(pgnSource,"QGame: bad pgnsource");
  searchVariations=variations;
  thePgnParser=new PgnParser();
  pgnUseSource=true;
  theGameNumber=0;
  for (auto&c:pgnBuffer)c=0; //for repeatability
}

bool QGame::parseNextGame(){
  //should of course delete the old root here!
  root=NULL;
  nextQPosIndex=0;
  if(pgnUseSource)
    return pgnParseNextGame();
  uassert(false, "parseNextGame: unexpected pgnUseSource is false");
  return false;
}

QPos* QGame::getQPos(int index)const{
  uassert(index>=0&&index<(int)(allQPos.size()),"getqpos arg");
  return allQPos[index];
}

int QGame::nQPos(){
  return (int)(allQPos.size());
}


//Verify everything starting with the root
void QGame::verifyRoot(){
  if(0)
    root->verifyDescendants();
}
/* push the comments to the scid game stuff
  this is the version from 9.250 and earlier, restored from
  an earlier version that used more complex comments to support
  smart settag, but smart settag was a mistake
*/

void QGame::mergeComments(){
  for(int i=0;i<theComments.size();++i){
    CommentEntry& entry=theComments.at(i);
    QPos*qpos=entry.qpos;
    qpos->appendCommentLocally(entry.message);
  }
  MarkBoard::gameMoveToPly(game,0);
  root->mergeComments();
  theTagSection.merge(this);
}
/* Later: destructor*/
/*
void QGame::clear(){
  if(root) root->clear();
}
*/  

QPos* QGame::getNewQPos(){
  if(nextQPosIndex>=QPosPoolSize-10){
    stringstream s;
    s<<"getNewQpos(): too many positions in game number: "
     << theGameNumber
     << " (limit is: "
     <<QPosPoolSize
     <<" positions)";
    uassert(false,s.str());
  }
  return &QPosPool.at(nextQPosIndex++);
}

bool QGame::pgnParseNextGame(){
  theGameNumber=0;
  uassert(pgnUseSource,"pgnParseNextGame: internal");
  int charsread{0};
  int linesstart{0};
  bool sourceflag=pgnSource->nextGame(pgnBuffer,
				   pgnBufferCapacity,
				   &theGameNumber,
				   &charsread,
				   &linesstart);
  if(!sourceflag)return false;
  foundCook= (std::strstr((const char*)pgnBuffer,"<cook")!=NULL);
  foundCookValid=true;
  thePgnParser->Init(pgnBuffer);
  bool parseret=(thePgnParser->ParseGame(game)!=ERROR_NotFound);
  if(!parseret)return false;
  ++pgnGamesRead;
  MarkBoard::gameMoveToPly(game,0);
  game->SetNumber(theGameNumber);
  root=QPos::createRoot(this,searchVariations);
  theTagSection.initialize(this);
  theRegexHistory.clear();
  /////////WARNING: before changing this make sure it is synced to parseNextGame()
  allQPos.clear();
  theComments.clear();
  QPos::visitRoot(root,searchVariations,allQPos);
  uassert(allQPos.size(),"qg bad allQPos");
  return true;
}

void QGame::registerRegexMatch(const std::smatch& sm){
  theRegexHistory.registerMatch(sm);
}

void QGame::clearRegexHistory(){
  theRegexHistory.clear();
}

void QGame::pushComment(QPos*qpos,const string&message){
  CommentEntry entry(qpos,message);
  theComments.push(entry);
}

void QGame::doSetTag(const string&name, const string&value){
  theTagSection.setValue(name,value);
}

int QGame::markComments(){
  return theComments.markComments();
}

void QGame::deleteComments(int start,int stop){
  theComments.deleteComments(start,stop);
}

void QGame::restoreComments(int top){
  return theComments.restoreComments(top);
}


