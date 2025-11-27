from flask import Flask, request, jsonify
from flask_cors import CORS
from random import randint, shuffle
import copy

app = Flask(__name__)
CORS(app)


# ----------------------------------------------------------
# BASIC UTILITIES
# ----------------------------------------------------------

def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def valid(board, pos, num):
    r, c = pos

    # Row
    if num in board[r]:
        return False

    # Column
    for i in range(9):
        if board[i][c] == num:
            return False

    # Box
    br = r - r % 3
    bc = c - c % 3
    for i in range(3):
        for j in range(3):
            if board[br + i][bc + j] == num:
                return False

    return True


# ----------------------------------------------------------
# SOLVER WITH VISUALIZATION STEPS
# ----------------------------------------------------------

def solve_with_steps(board, steps):
    empty = find_empty(board)
    if not empty:
        return True

    r, c = empty

    for num in range(1, 10):
        if valid(board, (r, c), num):

            board[r][c] = num
            steps.append({"row": r, "col": c, "value": num})

            if solve_with_steps(board, steps):
                return True

            board[r][c] = 0
            steps.append({"row": r, "col": c, "value": 0})

    return False


def solve(board):
    """Normal solver, no visualization."""
    empty = find_empty(board)
    if not empty:
        return True

    r, c = empty
    for num in range(1, 10):
        if valid(board, (r, c), num):
            board[r][c] = num
            if solve(board):
                return True
            board[r][c] = 0

    return False


# ----------------------------------------------------------
# GENERATE FULL SOLVED GRID
# ----------------------------------------------------------

def generate_full_board():
    board = [[0] * 9 for _ in range(9)]

    # Fill diagonal boxes first
    for box in range(0, 9, 3):
        nums = list(range(1, 10))
        shuffle(nums)
        for r in range(3):
            for c in range(3):
                board[box + r][box + c] = nums.pop()

    solve(board)
    return board


# ----------------------------------------------------------
# GENERATE PUZZLE
# ----------------------------------------------------------

def generate_puzzle(remove_min, remove_max):
    board = generate_full_board()

    attempts = randint(remove_min, remove_max)

    while attempts > 0:
        r, c = randint(0, 8), randint(0, 8)

        if board[r][c] == 0:
            continue

        backup = board[r][c]
        board[r][c] = 0

        # Check uniqueness
        test = copy.deepcopy(board)
        if not solve(test):
            board[r][c] = backup
        else:
            attempts -= 1

    return board


# ----------------------------------------------------------
# API ENDPOINTS
# ----------------------------------------------------------

@app.get("/generate")
def generate_api():
    difficulty = request.args.get("difficulty", "easy").lower()

    if difficulty == "easy":
        remove_min, remove_max = 38, 45
    elif difficulty == "medium":
        remove_min, remove_max = 46, 54
    elif difficulty == "hard":
        remove_min, remove_max = 56, 64
    else:
        remove_min, remove_max = 40, 45

    puzzle = generate_puzzle(remove_min, remove_max)

    # Return solution as well for GAME MODE
    solution = copy.deepcopy(puzzle)
    solve(solution)

    return jsonify({
        "puzzle": puzzle,
        "solution": solution
    })


@app.post("/solve")
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
