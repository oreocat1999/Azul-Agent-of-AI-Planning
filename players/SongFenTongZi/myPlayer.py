from advance_model import AdvancePlayer
from copy import deepcopy
import random
from utils import Tile
from operator import itemgetter
import sys

sys.path.append('players/SongFenTongZi/')

MAX_INDEX = 8

class myPlayer(AdvancePlayer):
	def __init__(self, _id):
		super().__init__(_id)

	def SelectMove(self, moves, game_state):
		return min_max_search(Azul, State(game_state), 4, self.id)

class State:
	def __init__(self, game_state):
		self.game_state = game_state

	def next_state(self, player_id, move):
		game_state = deepcopy(self.game_state)
		game_state.ExecuteMove(player_id = player_id, move = move)
		if not game_state.TilesRemaining():
			return State(game_state), True
		return State(game_state), False

	def clone(self):
		return State(self.game_state)

	def __eq__(self, other):
		if isinstance(other, State):
			return self.game_state == other.game_state
		elif other is None:
			return False
		return NotImplemented

	def __hash__(self):
		return hash(str(self.game_state))

class Azul:
	def __init__(self):
		pass

	@staticmethod
	def successors(state, player_id):
		return state.game_state.players[player_id].GetAvailableMoves(state.game_state)

	@staticmethod
	def isGoal(state):
		return state.game_state.players[0].GetCompletedRows() > 0 or state.game_state.players[1].GetCompletedRows() > 0

def state_eval(Graph, state, player):
	score_1 = _get_player_score(state.game_state.players[player])
	score_2 = _get_player_score(state.game_state.players[abs(1 - player)])
	if Graph.isGoal(state):
		return float("inf") if score_1 > score_2 else -float("inf")
	return score_1 - score_2

def _get_player_score(player):
	score_inc = 0
	grid_size = player.GRID_SIZE
	number_of = player.number_of
	grid_state = deepcopy(player.grid_state)
	for row in range(grid_size):
		if player.lines_number[row] == row + 1:
			tc = player.lines_tile[row]
			col = int(player.grid_scheme[row][tc])

			number_of[tc] += 1
			grid_state[row][col] = 1

			above = 0
			for c in range(col - 1, -1, -1):
				if grid_state[row][c] == 0: break
				else: above += 1
			below = 0
			for c in range(col + 1, grid_size, 1):
				if grid_state[row][c] == 0: break
				else: below += 1
			left = 0
			for r in range(row - 1, -1, -1):
				if grid_state[r][col] == 0: break
				else: left += 1
			right = 0
			for r in range(row + 1, grid_size, 1):
				if grid_state[r][col] == 0: break
				else: right += 1

			score_inc += 2 + left + right + above + below

			if (above == 0 and below == 0) or (left == 0 and right == 0):
				score_inc -= 1

	penalties = 0
	for i in range(len(player.floor)):
		penalties += player.floor[i] * player.FLOOR_SCORES[i]

	score_change = score_inc + penalties
	if player.score < -score_change:
		score_change = -player.score

	rows = 0
	for i in range(grid_size):
		for j in range(grid_size):
			if grid_state[i][j] == 0: break
		else: rows += 1

	cols = 0
	for i in range(grid_size):
		for j in range(grid_size):
			if grid_state[j][i] == 0: break
		else: cols += 1

	sets = 0
	for tile in Tile:
		if number_of[tile] == grid_size: sets += 1

	bonus = (rows * player.ROW_BONUS) + (cols * player.COL_BONUS) + (sets * player.SET_BONUS)

	return player.score + score_change + bonus

def sort_move(moves, player):
	score_dest = [0.03, 0.04, 0.02, 0.01, 0]
	length_bonus = [1, 2, 3, 4, 5]
	addition_floor_penalty = [-1.5, -2, -2, -2.5, -3, -3, 0]
	move_list = []
	length = len(moves)
	for i in range(len(player.floor)):
		if player.floor[i] == 0:
			penalty_index = i
			break
	else: penalty_index = len(player.floor) - 1
	for move in moves:
		score = 0
		grid_size = player.GRID_SIZE
		row = move[2].pattern_line_dest
		num_to_pattern_line = move[2].num_to_pattern_line
		for i in range(1, move[2].num_to_floor_line):
			if i + penalty_index < len(player.floor):
				score += player.FLOOR_SCORES[i + penalty_index]
		score += addition_floor_penalty[min(len(player.floor) - 1, penalty_index + move[2].num_to_floor_line)]
		if row != -1:
			if num_to_pattern_line + player.lines_number[row] == row + 1:
				tc = move[2].tile_type
				col = int(player.grid_scheme[row][tc])
				above = 0
				for c in range(col - 1, -1, -1):
					if player.grid_state[row][c] == 0: break
					else: above += 1
				below = 0
				for c in range(col + 1, grid_size, 1):
					if player.grid_state[row][c] == 0: break
					else: below += 1
				left = 0
				for r in range(row - 1, -1, -1):
					if player.grid_state[r][col] == 0: break
					else: left += 1
				right = 0
				for r in range(row + 1, grid_size, 1):
					if player.grid_state[r][col] == 0: break
					else: right += 1

				if (row != 0) and (not (col != 0 and player.grid_state[row - 1][col - 1] == 1) or (col != grid_size - 1 and player.grid_state[row - 1][col + 1] == 1)):
					score += abs(1 - player.grid_state[row - 1][col])
				if (row != grid_size - 1) and (not (col != 0 and player.grid_state[row + 1][col - 1] == 1) or (col != grid_size - 1 and player.grid_state[row + 1][col + 1] == 1)):
					score += abs(1 - player.grid_state[row + 1][col])
				if (col != 0) and (not (row != 0 and player.grid_state[row - 1][col - 1] == 1) or (row != grid_size - 1 and player.grid_state[row + 1][col - 1] == 1)):
					score += abs(1 - player.grid_state[row][col - 1])
				if (col != grid_size - 1) and (not (row != 0 and player.grid_state[row - 1][col + 1] == 1) or (row != grid_size - 1 and player.grid_state[row + 1][col + 1] == 1)):
					score += abs(1 - player.grid_state[row][col + 1])

				if (row > above): score += below + 1
				if (row + below < grid_size - 1): score += above + 1
				if (col > left): score += right + 1
				if (col + right < grid_size - 1): score += left + 1
				score += 1 + above + below + left + right + length_bonus[above + below] + length_bonus[left + right]

				if (above + below == 3): score += player.COL_BONUS
				if (left + right == 3): score += player.ROW_BONUS

				if (above != 0 or below != 0) and (left != 0 and right != 0):
					score += 1

				flag = True
				for c in range(grid_size):
					if c != col and player.grid_state[row][c] == 0: flag = False
				if flag: score += player.ROW_BONUS

				flag = True
				for r in range(grid_size):
					if r != row and player.grid_state[r][col] == 0: flag = False
				if flag: score += player.COL_BONUS

				if player.number_of[tc] == grid_size - 1: score += player.SET_BONUS

			else:
				score += (4 - row + num_to_pattern_line + player.lines_number[row]) / 5
			score += score_dest[row]
		move_list.append((score, move))
	move_list.sort(key = itemgetter(0), reverse = True)
	moves = []
	for i in range(min(MAX_INDEX, length)):
		score, move = move_list[i]
		moves.append(move)
	return moves

def min_max_search(Graph, state, depth_limit, player):
	alpha = -float("inf")
	beta = float("inf")
	return _max_node_value(Graph, state, 0, depth_limit, player, alpha, beta)[0]

def _max_node_value(Graph, state, depth, depth_limit, player, alpha, beta):
	depth += 1
	moves = Graph.successors(state, player)
	moves = sort_move(moves, state.game_state.players[player])
	best_move = random.choice(moves)
	max_alpha = -float("inf")
	for move in moves:
		next_state, round_end = state.next_state(player, move)
		if round_end or depth == depth_limit:
			state_alpha = state_eval(Graph, next_state, player)
		else:
			succ_state, state_alpha = _min_node_value(Graph, next_state, depth, depth_limit, abs(1 - player), alpha, beta)
		if max_alpha < state_alpha:
			max_alpha = state_alpha
			best_move = move
			alpha = max(alpha, state_alpha)
			if alpha >= beta:
				return best_move, alpha
	return best_move, alpha

def _min_node_value(Graph, state, depth, depth_limit, player, alpha, beta):
	depth += 1
	moves = Graph.successors(state, player)
	moves = sort_move(moves, state.game_state.players[player])
	best_move = random.choice(moves)
	min_beta = float("inf")
	for move in moves:
		next_state, round_end = state.next_state(player, move)
		if round_end or depth == depth_limit:
			state_beta = state_eval(Graph, next_state, abs(1 - player))
		else:
			succ_state, state_beta = _max_node_value(Graph, next_state, depth, depth_limit, abs(1 - player), alpha, beta)
		if min_beta > state_beta:
			min_beta = state_beta
			best_move = move
			beta = min(beta, min_beta)
			if beta <= alpha:
				return best_move, beta
	return best_move, beta
