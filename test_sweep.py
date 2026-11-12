from buckdesign.sweep import SweepPoint, smallest_passing


def test_picks_smallest_capacitance_that_meets_target():
    points = [SweepPoint(1.0, 3e-6, 0.85, []), SweepPoint(1.3, 3.9e-6, 1.0, []),
              SweepPoint(1.2, 3.6e-6, 0.99, [])]
    best = smallest_passing(points, target=0.99)
    assert best is not None
    assert best.scale == 1.2


def test_returns_none_when_nothing_reaches_target():
    assert smallest_passing([SweepPoint(1.0, 3e-6, 0.85, [])], target=0.99) is None