from optimization.maxcut_problem import exact_maxcut, cut_value

def test_triangle_maxcut():
    optimum, solutions = exact_maxcut(3, [(0,1), (1,2), (0,2)])
    assert optimum == 2
    assert solutions

def test_cut_value():
    assert cut_value("010", [(0,1), (1,2), (0,2)]) == 2
