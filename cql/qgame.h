#pragma once
#include "qpos.h"
#include "pathstatus.h"
#include "pgnsource.h"
#include "commentstack.h"
#include "tagsection.h"
#include "regexhistory.h"
#include <regex>
class PathNode; // used for PathLastMatched;
class QGame{
 public:
  QPos* getNewQPos();
  QGame(PgnSource*source,bool searchvariations);
  //  QGame(Game*game,bool variations);
  //  ~QGame();
  Game*game{NULL};
  /*PgnSource stuff*/
  bool pgnUseSource{false};
  PgnSource* pgnSource{NULL};
  static const int pgnBufferCapacity{1000000};
  char pgnBuffer[pgnBufferCapacity];
  int pgnGamesRead{0};
  TagSection* getTagSection();
  const TagSection* getTagSection()const;

  QPos*root{NULL};
  vector<QPos*>allQPos; // in topologically sorted order
  PgnParser* thePgnParser{NULL};
  QPos*getQPos(int index)const;
  bool parseNextGame();
  bool searchVariations{false};
  MFile * theMFile;
  void print();
  void verifyRoot();
  int theGameNumber{0};
  bool foundCook{false}; // whether this game has a substring "<cook"
  bool foundCookValid{false}; //whether foundCook has been computed
  QPos*getRoot(){return root;}
  void mergeComments();
  int getGameNumber()const{return theGameNumber;}
  int nQPos();
  bool pgnParseNextGame();
  CommentStack* getCommentStack(){return &theComments;}
  void pushComment(QPos*,const string&);
  int markComments();
  void restoreComments(int); // exclusive
  void deleteComments(int start, int stop);
  void doSetTag(const string&name, const string& value);
  void registerRegexMatch(const std::smatch&);
  void clearRegexHistory();
  RegexHistory* getRegexHistory(){return &theRegexHistory;}
  const RegexHistory* getRegexHistory()const{return &theRegexHistory;}
 private:
  //QPos pool
  static const int QPosPoolSize{50000};
  std::array<QPos,QPosPoolSize> QPosPool;
  int nextQPosIndex{0};
  CommentStack theComments;
  TagSection theTagSection;
  RegexHistory theRegexHistory;
public:
  //Path stuff
  PathStatus thePathStatus;
  PathStatus getPathStatus()const{return thePathStatus;}
  void setPathStatus(PathStatus s){thePathStatus=s;}
  QGame*clone()const; // for anticipate
  
};
