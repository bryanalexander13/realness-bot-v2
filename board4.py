class Board:
    """ a class to represent a connect four game
    """

    def __init__(self, height, width):
        """ The variables of the board
        input height & width: integers
        """

        self.height = height
        self.width = width
        self.slots = [['  ']*width for r in range(height)]

    def __str__(self):
        """ Returns a string representation for a Board object.
        """
        s = ''         # begin with an empty string

        # add one row of slots at a time
        for row in range(self.height):
            s += '|  '   # one vertical bar at the start of the row

            for col in range(self.width):
                s += self.slots[row][col] + '  |  '

            s += '\n'  # newline at the end of the row

        # Add code here for the hyphens at the bottom of the board
        # and the numbers underneath it.

        s += ((2*self.width + 1) * '----')[:-15]

        s += '\n  '

        ref = 0
        
        for i in range(1,2*self.width + 1):
            if i % 2 == 0:
                s += '     '
            else:
                s += str(ref % 10)
                ref += 1
        
        return s
        
    def __repr__(self):
        """ returns the same as the string for the representation 
        """

        return str(self)

    def add_checker(self, checker, col):
        """ adds a specificied checker on the top of the specified collumn
        input checker: string X or O
        input col: collumn number
        """
        
        row = 0
        while self.slots[row][col] == '  ':
            if row < self.height - 1:
                row += 1
            else:
                self.slots[row][col] = checker
                return
        if row == 5 and col == 2:
                t=1
        self.slots[row - 1][col] = checker
        
    def clear(self):
        """ clears the board
        """
        self.slots = [['  ']*self.width for r in range(self.height)]
                

    def add_checkers(self, colnums):
        """ takes in a string of column numbers and places alternating
        checkers in those columns of the called Board object, 
        starting with 'X'.
        """
        checker = 'X'   # start by playing 'X'

        for col_str in colnums:
            col = int(col_str)
            if 0 <= col < self.width:
                self.add_checker(checker, col)

            # switch to the other checker
            if checker == 'x':
                checker = 'o'
            else:
                checker = 'x' 

    def can_add_to(self, col):
        """ checks the collumn for empty space
        input col: collumn number
        """

        if col in range(self.width):
            if self.slots[0][col] == 'o' or self.slots[0][col] == 'x':
                return False
            else:
                return True
        else:
            return False

    def is_full(self):
        """ checks if the board is full
        """

        for i in range(self.width):
            if self.can_add_to(i):
                return False
        return True


    def remove_checker(self, col):
        """ removes a checker from the top of the collumn
        input col: collumn number
        """
        
        row = 0
        while self.slots[row][col] == '  ':
            if row < self.height - 1:
                row += 1
            else:
                break
        if row == 4 and col == 2:
                t=1
        self.slots[row][col] = '  '


    def is_horizontal_win(self, checker):
        """ Checks for a horizontal win for the specified checker.
        """
        for row in range(self.height):
            for col in range(self.width - 3):
                # Check if the next four columns in this row
                # contain the specified checker.
                if self.slots[row][col] == checker and \
                   self.slots[row][col + 1] == checker and \
                   self.slots[row][col + 2] == checker and \
                   self.slots[row][col + 3] == checker:
                    return True

        # if we make it here, there were no horizontal wins
        return False 

    def is_vertical_win(self, checker):
        """ Checks for a vertical win for the specified checker.
        """
        for row in range(self.height - 3):
            for col in range(self.width):
                if self.slots[row][col] == checker and \
                   self.slots[row + 1][col] == checker and \
                   self.slots[row + 2][col] == checker and \
                   self.slots[row + 3][col] == checker:
                    return True
        return False

    def is_up_diagonal_win(self, checker):
        """ Checks for a up diagonal win for the specified checker.
        """
        for row in range(3, self.height):
            for col in range(self.width - 3):
                if self.slots[row][col] == checker and \
                   self.slots[row - 1][col + 1] == checker and \
                   self.slots[row - 2][col + 2] == checker and \
                   self.slots[row - 3][col + 3] == checker:
                    return True
        return False 

    def is_down_diagonal_win(self, checker):
        """ Checks for a down diagonal win for the specified checker.
        """
        for row in range(self.height - 3):
            for col in range(self.width - 3):
                if self.slots[row][col] == checker and \
                   self.slots[row + 1][col + 1] == checker and \
                   self.slots[row + 2][col + 2] == checker and \
                   self.slots[row + 3][col + 3] == checker:
                    return True
        return False 

    def is_win_for(self, checker):
        """ checks for a win in any direction for the specified checker
        """

        if self.is_horizontal_win(checker) or self.is_vertical_win(checker) or \
           self.is_up_diagonal_win(checker) or self.is_down_diagonal_win(checker):
            return True
        else:
            return False

