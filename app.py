from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from random import randint, shuffle
import copy

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return render_template("index.html")

#all it does is checks whether all the tiles on the grid are empty i.e. 0
def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None

#this is one of the main functions for our algo
#for a num to be placed at a particular tile, three rules need to be true
def valid(board, pos, num):
    r, c = pos
    #rule 1- should not be in row
    if num in board[r]:
        return False

    #rule 2- should not be in column
    for i in range(9):
        if board[i][c] == num:
            return False

    #rule 3- should not be in that box
    br = r - r % 3
    bc = c - c % 3
    for i in range(3):
        for j in range(3):
            if board[br + i][bc + j] == num:
                return False
    return True

#this is another imp function
#MRV algo
#checks how many numbers betwween 1-9 are valid for a particular tile
#this becomes the domain of that tile
def get_domain(board, pos):
    r, c = pos
    domain = []
    for num in range(1, 10):
        if valid(board, (r, c), num):
            domain.append(num)
    return domain

#this finds empty cells for mrv
def find_empty_mrv(board):
    best_pos = None
    best_domain = None
    min_size = 10

    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                domain = get_domain(board, (r, c))
                size = len(domain)
                
                if size == 0:
                    return r, c, domain

                if size < min_size:
                    min_size = size
                    best_pos = (r, c)
                    best_domain = domain

                    if min_size == 1: #if domain len=1 then use it since this is the minimum
                        return best_pos[0], best_pos[1], best_domain

    if best_pos is None:
        return None
    return best_pos[0], best_pos[1], best_domain

#the code to visualise our algo
def solve_with_steps(board, steps):
    empty_info = find_empty_mrv(board)
    if not empty_info:
        return True

    r, c, domain = empty_info
    if not domain:
        return False

    for num in domain:
        board[r][c] = num
        steps.append({"row": r, "col": c, "value": num})

        if solve_with_steps(board, steps):
            return True

        board[r][c] = 0
        steps.append({"row": r, "col": c, "value": 0})

    return False

#this directly solves our sudoku
def solve(board):
    empty_info = find_empty_mrv(board)
    if not empty_info:
        return True

    r, c, domain = empty_info

    if not domain:
        return False

    for num in domain:
        board[r][c] = num
        if solve(board):
            return True
        board[r][c] = 0
    return False

#generate a grid
#step 1 fill diagonal 3 boxes in a random order
#step 2 solve the board
#step 3 now remove random numbers from it based on the difficultly level
def generate_full_board():
    board = [[0] * 9 for _ in range(9)]
    for box in range(0, 9, 3):
        nums = list(range(1, 10))
        shuffle(nums)
        for r in range(3):
            for c in range(3):
                board[box + r][box + c] = nums.pop()
    solve(board)
    return board

def generate_puzzle(remove_min, remove_max):
    board = generate_full_board()
    attempts = randint(remove_min, remove_max)
    while attempts > 0:
        r, c = randint(0, 8), randint(0, 8)

        if board[r][c] == 0:
            continue

        backup = board[r][c]
        board[r][c] = 0

        #simple check: solvable at least once
        test = copy.deepcopy(board)
        if not solve(test):
            board[r][c] = backup
        else:
            attempts -= 1

    return board


#flask part
@app.route("/generate", methods=["GET"])
def generate_api():
    difficulty = request.args.get("difficulty", "easy").lower()

    if difficulty == "easy":
        remove_min, remove_max = 38, 45
    elif difficulty == "medium":
        remove_min, remove_max = 46, 54
    elif difficulty == "hard":
        remove_min, remove_max = 55, 64
    else:
        remove_min, remove_max = 40, 45

    puzzle = generate_puzzle(remove_min, remove_max)

    solution = copy.deepcopy(puzzle)
    solve(solution)

    return jsonify({
        "puzzle": puzzle,
        "solution": solution
    })


@app.route("/solve", methods=["POST"])
def solve_api():
    data = request.json
    board = data.get("grid")

    if not board:
        return jsonify({"error": "Missing grid"}), 400

    steps = []
    board_copy = copy.deepcopy(board)

    if solve_with_steps(board_copy, steps):
        return jsonify({
            "solution": board_copy,
            "steps": steps
        })

    return jsonify({"error": "Unsolvable"}), 400


if __name__ == "__main__":
    app.run(port=5000, debug=True)
