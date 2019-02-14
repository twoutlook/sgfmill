from . import sgfmill_test_support

from sgfmill import ascii_boards
from sgfmill import boards
from sgfmill import sgf
from sgfmill import sgf_moves

def make_tests(suite):
    suite.addTests(sgfmill_test_support.make_simple_tests(globals()))


SAMPLE_SGF = """\
(;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]PB[Black engine]
PL[B]PW[White engine]RE[W+R]SZ[9]AB[ai][bh][ee]AW[fc][gc];B[dg];W[ef]C[comment
on two lines];B[];W[tt]C[Final comment])
"""

DIAGRAM1 = """\
9  .  .  .  .  .  .  .  .  .
8  .  .  .  .  .  .  .  .  .
7  .  .  .  .  .  o  o  .  .
6  .  .  .  .  .  .  .  .  .
5  .  .  .  .  #  .  .  .  .
4  .  .  .  .  .  .  .  .  .
3  .  .  .  .  .  .  .  .  .
2  .  #  .  .  .  .  .  .  .
1  #  .  .  .  .  .  .  .  .
   A  B  C  D  E  F  G  H  J
"""

DIAGRAM2 = """\
9  .  .  .  .  .  .  .  .  .
8  .  .  .  .  .  .  .  .  .
7  .  .  .  .  .  .  .  .  .
6  .  .  .  .  .  .  .  .  .
5  .  .  .  .  .  .  .  .  .
4  .  .  .  .  #  .  .  .  .
3  .  .  .  .  .  .  .  .  .
2  .  .  #  .  .  .  .  .  .
1  .  .  .  .  .  .  .  .  .
   A  B  C  D  E  F  G  H  J
"""


def test_get_setup_and_moves(tc):
    g1 = sgf.Sgf_game.from_string(SAMPLE_SGF)
    board1, plays1 = sgf_moves.get_setup_and_moves(g1)
    tc.assertBoardEqual(board1, DIAGRAM1)
    tc.assertEqual(plays1,
                   [('b', (2, 3)), ('w', (3, 4)), ('b', None), ('w', None)])

    g2 = sgf.Sgf_game(size=9)
    root = g2.get_root()
    root.set("AB", [(1, 2), (3, 4)])
    node = g2.extend_main_sequence()
    node.set("B", (5, 6))
    node = g2.extend_main_sequence()
    node.set("W", (5, 7))
    board2, plays2 = sgf_moves.get_setup_and_moves(g2)
    tc.assertBoardEqual(board2, DIAGRAM2)
    tc.assertEqual(plays2,
                   [('b', (5, 6)), ('w', (5, 7))])

    g3 = sgf.Sgf_game.from_string("(;AB[ab][ba]AW[aa])")
    tc.assertRaisesRegex(ValueError, "setup position not legal",
                         sgf_moves.get_setup_and_moves, g3)

    g4 = sgf.Sgf_game.from_string("(;SZ[9];B[ab];AW[bc])")
    tc.assertRaisesRegex(ValueError, "setup properties after the root node",
                         sgf_moves.get_setup_and_moves, g4)

    g5 = sgf.Sgf_game.from_string("(;SZ[26];B[ab];W[bc])")
    board5, plays5 = sgf_moves.get_setup_and_moves(g5)
    tc.assertEqual(plays5,
                   [('b', (24, 0)), ('w', (23, 1))])


def test_get_setup_and_moves_move_in_root(tc):
    # A move in the root node is allowed (though deprecated) if there are no
    # setup stones.
    g1 = sgf.Sgf_game(size=9)
    root = g1.get_root()
    root.set("B", (1, 2))
    node = g1.extend_main_sequence()
    node.set("W", (3, 4))
    board1, plays1 = sgf_moves.get_setup_and_moves(g1)
    tc.assertTrue(board1.is_empty())
    tc.assertEqual(plays1,
                   [('b', (1, 2)), ('w', (3, 4))])

    g2 = sgf.Sgf_game(size=9)
    root = g2.get_root()
    root.set("B", (1, 2))
    root.set("AW", [(3, 3)])
    node = g2.extend_main_sequence()
    node.set("W", (3, 4))
    tc.assertRaisesRegex(ValueError, "mixed setup and moves in root node",
                         sgf_moves.get_setup_and_moves, g2)

def test_get_setup_and_moves_board_provided(tc):
    b = boards.Board(9)
    g1 = sgf.Sgf_game.from_string(SAMPLE_SGF)
    board1, plays1 = sgf_moves.get_setup_and_moves(g1, b)
    tc.assertIs(board1, b)
    tc.assertBoardEqual(board1, DIAGRAM1)
    tc.assertEqual(plays1,
                   [('b', (2, 3)), ('w', (3, 4)), ('b', None), ('w', None)])
    tc.assertRaisesRegex(ValueError, "board not empty",
                         sgf_moves.get_setup_and_moves, g1, b)
    b2 = boards.Board(19)
    tc.assertRaisesRegex(ValueError, "wrong board size, must be 9$",
                         sgf_moves.get_setup_and_moves, g1, b2)


def test_set_initial_position(tc):
    board = ascii_boards.interpret_diagram(DIAGRAM1, 9)
    sgf_game = sgf.Sgf_game(9)
    sgf_moves.set_initial_position(sgf_game, board)
    root = sgf_game.get_root()
    tc.assertEqual(root.get("AB"), {(0, 0), (1, 1), (4, 4)})
    tc.assertEqual(root.get("AW"), {(6, 5), (6, 6)})
    tc.assertRaises(KeyError, root.get, 'AE')

def test_indicate_first_player(tc):
    # Normal game
    g1 = sgf.Sgf_game.from_bytes(b"(;FF[4]GM[1]SZ[9];B[aa];W[ab])")
    sgf_moves.indicate_first_player(g1)
    tc.assertEqual(g1.serialise(),
                   b"(;FF[4]GM[1]SZ[9];B[aa];W[ab])\n")
    # White plays first
    g2 = sgf.Sgf_game.from_bytes(b"(;FF[4]GM[1]SZ[9];W[aa];B[ab])")
    sgf_moves.indicate_first_player(g2)
    tc.assertEqual(g2.serialise(),
                   b"(;FF[4]GM[1]PL[W]SZ[9];W[aa];B[ab])\n")
    # No moves
    g3 = sgf.Sgf_game.from_bytes(b"(;FF[4]GM[1]SZ[9];C[no game])")
    sgf_moves.indicate_first_player(g3)
    tc.assertEqual(g3.serialise(),
                   b"(;FF[4]GM[1]SZ[9];C[no game])\n")
    # Normal handicap game
    g4 = sgf.Sgf_game.from_bytes(b"(;FF[4]GM[1]HA[5]SZ[9];W[aa];B[ab])")
    sgf_moves.indicate_first_player(g4)
    tc.assertEqual(g4.serialise(),
                   b"(;FF[4]GM[1]HA[5]SZ[9];W[aa];B[ab])\n")
    # Handicap game, black plays first
    g5 = sgf.Sgf_game.from_bytes(b"(;FF[4]GM[1]HA[5]SZ[9];B[aa];W[ab])")
    sgf_moves.indicate_first_player(g5)
    tc.assertEqual(g5.serialise(),
                   b"(;FF[4]GM[1]HA[5]PL[B]SZ[9];B[aa];W[ab])\n")
    # White setup stones
    g6 = sgf.Sgf_game.from_bytes(b"(;AW[bc]FF[4]GM[1]SZ[9];B[aa];W[ab])")
    sgf_moves.indicate_first_player(g6)
    tc.assertEqual(g6.serialise(),
                   b"(;FF[4]AW[bc]GM[1]PL[B]SZ[9];B[aa];W[ab])\n")
    # Black setup stones
    g7 = sgf.Sgf_game.from_bytes(b"(;AB[bc]FF[4]GM[1]SZ[9];B[aa];W[ab])")
    sgf_moves.indicate_first_player(g7)
    tc.assertEqual(g7.serialise(),
                   b"(;FF[4]AB[bc]GM[1]PL[B]SZ[9];B[aa];W[ab])\n")
    # Black setup stones, handicap, white plays first
    g8 = sgf.Sgf_game.from_bytes(
        b"(;FF[4]AB[bc][cd]GM[1]HA[2]SZ[9];W[aa];B[ab])")
    sgf_moves.indicate_first_player(g8)
    tc.assertEqual(g8.serialise(),
                   b"(;FF[4]AB[bc][cd]GM[1]HA[2]SZ[9];W[aa];B[ab])\n")
