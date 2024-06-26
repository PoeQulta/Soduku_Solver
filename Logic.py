import random
import timeit
def time_usage(func):
    def wrapper(*args, **kwargs):
        beg_ts = timeit.default_timer()
        retval = func(*args, **kwargs)
        end_ts = timeit.default_timer()
        print("elapsed time: %f" % (end_ts - beg_ts))
        return retval
    return wrapper
class GridVariable():
    def __init__(self,i,j,val=None) -> None:
        self.i = i
        self.j = j
        self.readOnly = False
        if val:
            self.domain = set([val])
            
        else:
            self.domain = set([1,2,3,4,5,6,7,8,9])
        self.val = val
    def __hash__(self) -> int:
        return hash((self.i,self.j))
    def __repr__(self) -> str:
         return str((self.i,self.j))
    def update_lock(self,readOnly):
        if self.val and len(self.domain)>0:
            self.readOnly = readOnly
    def set_val(self,val):
        if self.readOnly:
            return
        if val:
            self.val = val
            self.domain = set([val])
    def update_domain(self,val):
        if self.readOnly:
            return
        self.domain.remove(val)
class Board():
    def __init__(self,notifyUI) -> None:
        self.vars = [[GridVariable(i,j) for j in range(9)] for i in range(9)]
        self.arcs = dict()
        self.notifyUI = notifyUI
        self.init_arcs()
    def init_arcs(self) -> None:
        for i in range(9):
            for j in range(9):
                x = self.vars[i][j]
                self.arcs[x] = self.get_arcs(x)
    def reset_var(self,i,j):
        active_var = self.vars[i][j]
        if active_var.readOnly:
            return
        active_var.val = None 
        for row in self.vars:
            for var in row:
                if var.val == None:
                    var.domain = set([1,2,3,4,5,6,7,8,9])
        self.force_consistency()
    def get_arcs(self,var) -> set:
                arcs = set()
                i = var.i
                j = var.j
                bigGrid_i = (i//3)*3
                bigGrid_j = (j//3)*3 
                for k in range(9):
                    arcs.add(self.vars[i][k])
                    arcs.add(self.vars[k][j])
                for k in range(3):
                     for l in range(3):
                          arcs.add(self.vars[bigGrid_i+k][bigGrid_j+l])
                arcs.remove(var)
                return arcs
    def get_unsatisfiable_vars(self):
        unsats = set()
        for i in range(9):
            for j in range(9):
                if(len(self.vars[i][j].domain)==0):
                    unsats.add(self.vars[i][j])
        return unsats     
    def force_consistency(self):
        for row in self.vars:
            for var in row:
                var.set_val(var.val)
        isConst = False
        while not isConst:
              isConst = self.apply_Consistency_iter()
        if self.notifyUI:
            self.notifyUI(self.get_unsatisfiable_vars())
        return True
    def apply_Consistency_iter(self):
        isConst = True
        for row in self.vars:
              for var in row:
                incons = self.get_incons(var)
                for key in incons:
                   var.update_domain(key)
                   isConst = False
        return isConst                
    def get_incons(self,var):
        incons = dict()
        if(var.readOnly):
            return incons
        arcs = self.arcs[var]
        for arc in arcs:
            if len(arc.domain)>1:
                continue
            for val in var.domain:
                if(val in arc.domain):
                    incon = incons.get(val,set())
                    incon.add(arc)
                    incons[val] = incon
                    break
        return incons
    def __getitem__(self,items):
         if(type(items) == tuple):
              return self.vars[items[0]][items[1]]
         if(type(items) == int):
              return self.vars[items]
         return
    def clear(self):
        for i in range(9):
            for j in range(9):
                self.reset_var(i,j)
    def copy(self):
        board = Board(None)
        for row in self.vars:
            for var in row:
                board[var.i][var.j].set_val(var.val)
                board[var.i][var.j].update_lock(var.readOnly)
        board.force_consistency()
        board.notifyUI = self.notifyUI
        return board
    def find_empty_cell(self):
        vars = [x for row in self.vars for x in row if len(x.domain)>1]
        if len(vars)>0:
            empty =  min(vars,key=lambda x:len(x.domain))
            if empty.val == None:
                return empty
        #for row in self.vars:
        #    for var in row:
        #        if var.val == None:
        #            return var
        return None
    def assign_inevitables(self):
        assigned = False
        for row in self.vars:
            for var in row:
                if var.val:
                    continue
                if len(var.domain)==1:
                    for e in var.domain:
                        var.set_val(e)
                        assigned = True
                        break
        return assigned
    def __solve_sudoku__helper(self,board,verbose,history=[]):
        """
        Solves the Sudoku puzzle using backtracking.
        """
        empty_cell = board.find_empty_cell()
        if not empty_cell:
            return True  # All cells are filled, puzzle solved!
        for num in empty_cell.domain:
            empty_cell.set_val(num)
            board.force_consistency()
            if verbose:
                history.append(board.copy()) 
            if len(board.get_unsatisfiable_vars())>0:
                board.reset_var(empty_cell.i,empty_cell.j)
                if verbose:
                    history.append(board.copy())
                continue
            assigned = board.assign_inevitables()
            if verbose and assigned:
                history.append(board.copy())
            if self.__solve_sudoku__helper(board,verbose,history):
                return True
            board.reset_var(empty_cell.i,empty_cell.j)  # Undo the choice if it leads to an invalid solution
            if verbose:
                history.append(board.copy())
        return False
    @time_usage
    def solve(self, verbose=False):
        board = self.copy()
        board.notifyUI = None
        history = list()
        if verbose:
                history.append(board.copy())
        if self.__solve_sudoku__helper(board,verbose,history):
            board.notifyUI = self.notifyUI
            if verbose:
                return board,history
            else:
                return board,None
        else:
            return None,None
    def generate_sudoku(self,level):
        """
        Generates a random valid Sudoku puzzle
        """
        board = Board(None)
        first_row = random.sample(range(1, 10), 9)
        for i,val in enumerate(first_row):
            board[0][i].set_val(val)
        board.force_consistency()

        # Solve the entire puzzle to ensure a valid solution exists
        hints = 41 - (3**level)
        solved,_ = board.solve(False)
        if solved:
            solved.notifyUI = self.notifyUI
            resets = random.sample(range(81),81-hints)
            for k in resets:
                j = (k//9)%9
                i = (k-j*9)%9
                solved.reset_var(i,j)
            for row in solved.vars:
               for var in row:
                    var.update_lock(True)
            ensure_solve,hist = solved.solve()
            if ensure_solve:
                return solved
            else:
                return self.generate_sudoku(level) 
        else:
            return self.generate_sudoku(level) 