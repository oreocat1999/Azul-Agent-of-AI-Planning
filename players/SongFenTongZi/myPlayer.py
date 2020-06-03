from advance_model import AdvancePlayer
from copy import deepcopy, copy
import random
from utils import Tile
from operator import itemgetter
import math

epsilon = 0.5
MAX_INDEX = 5
MAX_TURN = 3
FUTURE = 0.4

class myPlayer(AdvancePlayer):
	def __init__(self, _id):
		super().__init__(_id)

	def SelectMove(self, moves, game_state):
		return monte_carlo_tree_search(Azul, State(game_state), 300, self.id)

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

def state_eval(graph, state, player):
	round_number = max([sum(state.game_state.players[player].grid_state[r][c] for c in range(5)) for r in range(5)]) + 1
	score_1 = _get_player_score(state.game_state.players[player], round_number)
	score_2 = _get_player_score(state.game_state.players[abs(1 - player)], round_number)
	return score_1 - score_2

def _get_player_score(player, round_number):
	score_inc = 0
	future_score = 0
	grid_size = player.GRID_SIZE
	number_of = copy(player.number_of)
	grid_state = deepcopy(player.grid_state)
	for row in range(grid_size):
		tc = player.lines_tile[row]
		col = int(player.grid_scheme[row][tc])
		if player.lines_number[row] == row + 1:
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

			if round_number < 5:
				if above + below == 3: future_score += player.COL_BONUS
				if left + right == 3: future_score += player.ROW_BONUS
				if number_of[tc] == grid_size - 2: future_score += player.SET_BONUS

				if (row != 0) and (not (col != 0 and grid_state[row - 1][col - 1] == 1) or (
						col != grid_size - 1 and grid_state[row - 1][col + 1] == 1)):
					future_score += abs(1 - grid_state[row - 1][col]) / 2
				if (row != grid_size - 1) and (not (col != 0 and grid_state[row + 1][col - 1] == 1) or (
						col != grid_size - 1 and grid_state[row + 1][col + 1] == 1)):
					future_score += abs(1 - grid_state[row + 1][col]) / 2
				if (col != 0) and (not (row != 0 and grid_state[row - 1][col - 1] == 1) or (
						row != grid_size - 1 and grid_state[row + 1][col - 1] == 1)):
					future_score += abs(1 - grid_state[row][col - 1]) / 2
				if (col != grid_size - 1) and (not (row != 0 and grid_state[row - 1][col + 1] == 1) or (
						row != grid_size - 1 and grid_state[row + 1][col + 1] == 1)):
					future_score += abs(1 - grid_state[row][col + 1]) / 2

				if row > above: future_score += below + 1
				if row + below < grid_size - 1: future_score += above + 1
				if col > left: future_score += right + 1
				if col + right < grid_size - 1: future_score += left + 1

				for r in range(grid_size):
					for c in range(grid_size):
						if grid_state[r][c] == 1:
							future_score += 1 / ((abs(row - r) + 1) * (abs(col - c) + 1))
		elif player.lines_number[row] > 0:
			if round_number < 5:
				future_score += sum(grid_state[r][col] for r in range(grid_size)) + sum(grid_state[row][c] for c in range(grid_size))

	penalties = 0
	for i in range(len(player.floor)):
		penalties += player.floor[i] * player.FLOOR_SCORES[i]

	score_change = score_inc + penalties
	if player.score < -score_change:
		score_change = -player.score

	if (round_number == 4): score_change += future_score * FUTURE / 2
	else: score_change += future_score * FUTURE

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
	grid_size = player.GRID_SIZE
	round_number = max([sum(player.grid_state[r][c] for c in range(grid_size)) for r in range(grid_size)]) + 1
	number_of = copy(player.number_of)
	for r in range(grid_size):
		if player.lines_number[r] == r + 1:
			number_of[player.lines_tile[r]] += 1
	score_dest = [0.03, 0.04, 0.02, 0.01, 0]
	addition_floor_penalty = [-1.5, -2, -2, -2.5, -3, -3, 0]
	move_list = []
	length = len(moves)
	for i in range(len(player.floor)):
		if player.floor[i] == 0:
			penalty_index = i
			break
	else: penalty_index = len(player.floor)
	for move in moves:
		score = 0
		future_score = 0
		row = move[2].pattern_line_dest
		num_to_pattern_line = move[2].num_to_pattern_line
		for i in range(move[2].num_to_floor_line):
			if i + penalty_index < len(player.floor):
				score += player.FLOOR_SCORES[i + penalty_index]
		if round_number < 5:
			future_score += addition_floor_penalty[min(len(player.floor) - 1, penalty_index + move[2].num_to_floor_line)]
		if row != -1:
			tc = move[2].tile_type
			col = int(player.grid_scheme[row][tc])
			if num_to_pattern_line + player.lines_number[row] == row + 1:
				grid_state = deepcopy(player.grid_state)
				for r in range(row + 1):
					if player.lines_number[r] == r + 1:
						grid_state[r][int(player.grid_scheme[r][player.lines_tile[r]])] = 1

				above = 0
				for r in range(row - 1, -1, -1):
					if grid_state[r][col] == 0: break
					else: above += 1
				below = 0
				for r in range(row + 1, grid_size, 1):
					if grid_state[r][col] == 0: break
					else: below += 1
				left = 0
				for c in range(col - 1, -1, -1):
					if grid_state[row][c] == 0: break
					else: left += 1
				right = 0
				for c in range(col + 1, grid_size, 1):
					if grid_state[row][c] == 0: break
					else: right += 1

				if round_number < 5:
					if above + below == 3: future_score += player.COL_BONUS
					if left + right == 3: future_score += player.ROW_BONUS
					if number_of[tc] == grid_size - 2: future_score += player.SET_BONUS

					if (row != 0) and (not (col != 0 and grid_state[row - 1][col - 1] == 1) or (col != grid_size - 1 and grid_state[row - 1][col + 1] == 1)):
						future_score += abs(1 - grid_state[row - 1][col]) / 2
					if (row != grid_size - 1) and (not (col != 0 and grid_state[row + 1][col - 1] == 1) or (col != grid_size - 1 and grid_state[row + 1][col + 1] == 1)):
						future_score += abs(1 - grid_state[row + 1][col]) / 2
					if (col != 0) and (not (row != 0 and grid_state[row - 1][col - 1] == 1) or (row != grid_size - 1 and grid_state[row + 1][col - 1] == 1)):
						future_score += abs(1 - grid_state[row][col - 1]) / 2
					if (col != grid_size - 1) and (not (row != 0 and grid_state[row - 1][col + 1] == 1) or (row != grid_size - 1 and grid_state[row + 1][col + 1] == 1)):
						future_score += abs(1 - grid_state[row][col + 1]) / 2

					if row > above: future_score += below + 1
					if row + below < grid_size - 1: future_score += above + 1
					if col > left: future_score += right + 1
					if col + right < grid_size - 1: future_score += left + 1

					for r in range(grid_size):
						for c in range(grid_size):
							if grid_state[r][c] == 1:
								future_score += 1 / ((abs(row - r) + 1) * (abs(col - c) + 1))

				score += 1 + above + below + left + right + future_score * FUTURE
				if (above != 0 or below != 0) and (left != 0 and right != 0):
					score += 1

				for c in range(grid_size):
					if c != col and grid_state[row][c] == 0: break
				else: score += player.ROW_BONUS

				for r in range(grid_size):
					if r != row and grid_state[r][col] == 0: break
				else: score += player.COL_BONUS

				if number_of[tc] == grid_size - 1: score += player.SET_BONUS

			else:
				grid_state = deepcopy(player.grid_state)
				for r in range(grid_size):
					if player.lines_number[r] == r + 1:
						grid_state[r][int(player.grid_scheme[r][player.lines_tile[r]])] = 1
				future_score += sum(grid_state[r][col] for r in range(grid_size)) + sum(grid_state[row][c] for c in range(grid_size))
				score += (4 - row + num_to_pattern_line + player.lines_number[row]) / 5 + future_score * FUTURE
			score += score_dest[row]
		move_list.append((score, move))
	move_list.sort(key = itemgetter(0), reverse = True)
	moves = []
	for i in range(length):
		score, move = move_list[i]
		moves.append(move)
		if len(moves) == MAX_INDEX: break
	return moves

beta = 1

class Node:
	def __init__(self, state, score, visit, parent, visit_child, wait_child, move, round_end):
		self.state = state
		self.score = score
		self.visit = visit
		self.parent = parent
		self.visit_child = visit_child
		self.wait_child = wait_child
		self.move = move
		self.round_end = round_end

def _tree_policy(Graph, node, root_player, player):
	while not node.round_end:
		player = abs(1 - player)
		if node.wait_child:
			expand_node = node.wait_child.pop(0)
			node.visit_child.append(expand_node)
			_expand(Graph, expand_node, player)
			return expand_node, player
		else:
			if player != root_player: node.visit_child.sort(key = _MCTS_sort, reverse = True)
			else: node.visit_child.sort(key = _MCTS_sort, reverse = False)
			node = node.visit_child[0]
	return node, player

def _expand(Graph, node, player):
	if node.state == None:
		node.state, node.round_end = node.parent.state.next_state(abs(1 - player), node.move)
	moves = Graph.successors(node.state, player)
	moves = sort_move(moves, node.state.game_state.players[player])
	for move in moves:
		node.wait_child.append(Node(None, 0, 0, node, [], [], move, None))

def _child_score(node, c):
	if node.visit == 0:
		return None
	else:
		return node.score / node.visit + c * math.sqrt(2 * math.log(node.parent.visit) / node.visit)

def _MCTS_sort(node):
	return _child_score(node, beta)

def _MCTS_answer_sort(node):
	return _child_score(node, 0)

def _default_policy(Graph, node, root_player, player):
	state = node.state
	round_end = False
	turn = 0
	while not round_end:
		moves = Graph.successors(state, player)
		moves = sort_move(moves, state.game_state.players[player])
		if moves == None or len(moves) == 0:
			break
		state, round_end = state.next_state(player, random.choice(moves))
		player = abs(1 - player)
		turn += 1
		if turn == MAX_TURN: break
	value = state_eval(Graph, state, root_player)
	return value

def _backup(node, reward):
	while node is not None:
		node.score += reward
		node.visit += 1
		node = node.parent

def monte_carlo_tree_search(Graph, state, budget, player):
	root_node = Node(state, 0, 0, None, [], [], None, False)
	root_player = player
	_expand(Graph, root_node, player)
	while budget > 0:
		expand_node, expand_player = _tree_policy(Graph, root_node, root_player, player)
		reward = _default_policy(Graph, expand_node, root_player, expand_player)
		_backup(expand_node, reward)
		budget -= 1
	root_node.visit_child.sort(key = _MCTS_answer_sort, reverse = True)
	return root_node.visit_child[0].move
