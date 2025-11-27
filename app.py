from flask import Flask, request, jsonify
from flask_cors import CORS
from random import randint, shuffle

app = Flask(__name__)
CORS(app)


def find_empty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None


def valid(board, pos, num):
    # Check row
    for j in range(9):
        if board[pos[0]][j] == num and j != pos[1]:
            return False

    # Check column
    for i in range(9):
        if board[i][pos[1]] == num and i != pos[0]:
            return False

    # Check 3×3 box
    box_row = pos[0] - pos[0] % 3
    box_col = pos[1] - pos[1] % 3

    for i in range(3):
        for j in range(3):
            if board[box_row + i][box_col + j] == num:
                return False
    return True


def solve(board, steps):
    """
    Backtracking solver that also records each step.

    steps: list of dicts with:
      { "row": int, "col": int, "value": int, "action": "place" | "remove" }
    """
    empty = find_empty(board)
    if not empty:
        return True

    row, col = empty

    for num in range(1, 10):
        if valid(board, (row, col), num):
            # Try placing num
            board[row][col] = num
            steps.append({
                "row": row,
                "col": col,
                "value": num,
                "action": "place"
            })

            if solve(board, steps):
                return True

            # Backtrack
            board[row][col] = 0
            steps.append({
                "row": row,
                "col": col,
                "value": 0,
                "action": "remove"
            })

    return False


def generate_board():
    board = [[0 for _ in range(9)] for _ in range(9)]

    # Fill diagonal boxes
    for i in range(0, 9, 3):
        nums = list(range(1, 10))
        shuffle(nums)
        for r in range(3):
            for c in range(3):
                board[i + r][i + c] = nums.pop()

    # Fill remaining
    def fill(board, row, col):
        if row == 9:
            return True
        if col == 9:
            return fill(board, row + 1, 0)
        if board[row][col] != 0:
            return fill(board, row, col + 1)

        for num in range(1, 10):
            if valid(board, (row, col), num):
                board[row][col] = num
                if fill(board, row, col + 1):
                    return True
        board[row][col] = 0
        return False

    fill(board, 0, 0)

    # Remove random 45–55 cells
    for _ in range(randint(45, 55)):
        r, c = randint(0, 8), randint(0, 8)
        board[r][c] = 0

    return board


# ---------------------------
#     API ENDPOINTS
# ---------------------------

@app.post("/solve")
def solve_api():
    data = request.json
    board = data.get("grid")

    if not board:
        return jsonify({"error": "No grid provided"}), 400

    board_copy = [row[:] for row in board]
    steps = []

    if solve(board_copy, steps):
        return jsonify({
            "solution": board_copy,
            "steps": steps
        })
    else:
        return jsonify({"error": "No solution found"}), 400


@app.get("/generate")
def generate_api():
    puzzle = generate_board()
    return jsonify({"puzzle": puzzle})


# ---------------------------
#     RUN SERVER
# ---------------------------

if __name__ == "__main__":
    app.run(port=5000, debug=True)
