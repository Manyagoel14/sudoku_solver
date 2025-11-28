from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from random import randint, shuffle
import copy

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return render_template("index.html")


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
# MRV HELPERS
# ----------------------------------------------------------

def get_domain(board, pos):
    """Return the list of valid numbers for position pos (r,c)."""
    r, c = pos
    domain = []
    for num in range(1, 10):
        if valid(board, (r, c), num):
            domain.append(num)
    return domain


def find_empty_mrv(board):
    """
    Find the empty cell with Minimum Remaining Values (smallest domain).
    Returns (r, c, domain) if there is an empty cell, or None if board is full.
    If any empty cell has an empty domain, returns that cell with domain=[] (causes immediate backtrack).
    """
    best_pos = None
    best_domain = None
    min_size = 10  # larger than any possible domain

    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                domain = get_domain(board, (r, c))
                size = len(domain)

                # If any variable has zero possibilities, immediate fail (prune)
                if size == 0:
                    return r, c, domain

                if size < min_size:
                    min_size = size
                    best_pos = (r, c)
                    best_domain = domain

                    # If we find a singleton domain, that's optimal (can't get smaller)
                    if min_size == 1:
                        return best_pos[0], best_pos[1], best_domain

    if best_pos is None:
        return None
    return best_pos[0], best_pos[1], best_domain


# ----------------------------------------------------------
# SOLVER WITH MRV + VISUALIZATION STEPS
# ----------------------------------------------------------

def solve_with_steps(board, steps):
    """
    Backtracking solver that uses MRV to pick the next cell.
    Records each placement (and each backtrack) into steps for visualization.
    """
    empty_info = find_empty_mrv(board)
    if not empty_info:
        return True  # solved

    r, c, domain = empty_info

    # If domain is empty, this branch fails immediately
    if not domain:
        return False

    # Optionally apply a heuristic like LCV by sorting domain by
    # how many options they leave for neighbors. (Not implemented here.)
    for num in domain:
        board[r][c] = num
        steps.append({"row": r, "col": c, "value": num})

        if solve_with_steps(board, steps):
            return True

        # backtrack
        board[r][c] = 0
        steps.append({"row": r, "col": c, "value": 0})

    return False


def solve(board):
    """Normal MRV-based solver, no visualization."""
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


# ----------------------------------------------------------
# GENERATE FULL SOLVED GRID
# ----------------------------------------------------------

def generate_full_board():
    board = [[0] * 9 for _ in range(9)]

    # Fill diagonal boxes first (fast seeding)
    for box in range(0, 9, 3):
        nums = list(range(1, 10))
        shuffle(nums)
        for r in range(3):
            for c in range(3):
                board[box + r][box + c] = nums.pop()

    # Use MRV solver to fill the rest (works fine)
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

        # Check uniqueness (simple check: solvable at least once)
        test = copy.deepcopy(board)
        if not solve(test):
            board[r][c] = backup
        else:
            attempts -= 1

    return board


# ----------------------------------------------------------
# API ENDPOINTS
# ----------------------------------------------------------

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

    # Return solution as well for GAME MODE
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
