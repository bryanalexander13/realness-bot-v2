from play4 import *
import random

class AIPlayer(Player):
    """
    """

    def __init__(self, checker, tiebreak, lookahead):
        """
        """

        Player.__init__(self, checker)

        self.tiebreak = tiebreak
        self.lookahead = lookahead

    def __str__(self):
        """
        """

        return Player.__str__(self) + ' (' + str(self.tiebreak) + ', '+ str(self.lookahead) + ')'


    def max_score_column(self, scores):
        """
        """

        ind = []

        for i in range(len(scores)):
            if scores[i] == max(scores):
                ind += [i]
        
        if self.tiebreak == 'LEFT':
            return ind[0]
        elif self.tiebreak == 'RIGHT':
            return ind[-1]
        else:
            return random.choice(ind)

    def scores_for(self, board):
        """
        """

        scores = [50] * board.width

        for col in range(board.width):
            if not board.can_add_to(col):
                scores[col] = -1
            elif board.is_win_for(self.checker):
                scores[col] = 100
            elif board.is_win_for(self.opponent_checker()):
                scores[col] = 0
            elif self.lookahead == 0:
                scores[col] = 50
            else:
                board.add_checker(self.checker, col)
                opp = AIPlayer(self.opponent_checker(), self.tiebreak, self.lookahead - 1)
                opp_scores = opp.scores_for(board)
                if max(opp_scores) == 0:
                    scores[col] = 100
                elif max(opp_scores) == 50:
                    scores[col] = 50
                elif max(opp_scores) == 100:
                    scores[col] = 0
                board.remove_checker(col)
                
        return scores
    
    def next_move(self, board, user_id = None, user_name = None, user2_id = None, user2_name = None):
        """
        """

        self.num_moves += 1
        return self.max_score_column(self.scores_for(board))
