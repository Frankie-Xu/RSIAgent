from rsiaagent_healthcare_fixture import assert_case_disjoint, build_cases, build_tasks, run_benchmark


def test_benchmark_has_case_disjoint_and_temporal_slices():
    cases = build_cases()
    tasks = build_tasks(cases)
    assert {case.split for case in cases} == {"public", "hidden", "temporal_holdout", "drift"}
    assert_case_disjoint(tasks)
    assert all(task.case_id == task.task_id.removeprefix("TASK-") for task in tasks)
    temporal = [task for task in tasks if task.split == "temporal_holdout"]
    assert all(task.as_of == next(event for event in next(case for case in cases if case.case_id == task.case_id).events if event.code == "8480-6").observed_at for task in temporal)


def test_benchmark_reports_quality_cost_and_negative_transfer():
    report = run_benchmark(build_cases(), build_tasks(build_cases()), seed=20260919)
    assert report.seed == 20260919
    assert set(report.aggregates) == {"breadth", "depth", "frozen_memory"}
    assert report.split_summary["case_disjoint"] is True
    assert report.split_summary["case_splits"] == {
        "drift": 2, "hidden": 4, "public": 4, "temporal_holdout": 2,
    }
    assert report.split_summary["evaluation_splits"] == ["hidden", "temporal_holdout", "drift"]
    for metrics in report.aggregates.values():
        assert set(metrics) >= {
            "quality", "evidence_coverage", "interaction_units", "review_seconds", "compute_units",
            "matched_budget_units", "unused_budget_units", "exploration_compute_units",
            "total_compute_units", "human_cost", "total_human_cost", "negative_transfer",
        }
        assert metrics["compute_units"] > 0
        assert metrics["interaction_units"] > 0
        assert metrics["human_cost"] > 0
        assert metrics["matched_budget_units"] == 16.0
        assert metrics["exploration_compute_units"] == 20.0
        assert metrics["total_compute_units"] == metrics["compute_units"] + 20.0 + metrics["verification_compute_units"]
        assert metrics["total_human_cost"] == metrics["human_cost"]
    assert report.aggregates["depth"]["quality"] > report.aggregates["breadth"]["quality"]
    assert report.aggregates["frozen_memory"]["negative_transfer"] >= 1
    assert report.frozen_memory_hash_before == report.frozen_memory_hash_after


def test_each_strategy_receives_the_same_per_attempt_budget():
    report = run_benchmark(build_cases(), build_tasks(build_cases()), seed=20260919)
    for attempt in report.attempts:
        assert attempt.matched_budget_units == 2
        assert attempt.compute_units <= attempt.matched_budget_units
        assert attempt.unused_budget_units == attempt.matched_budget_units - attempt.compute_units


def test_frozen_memory_is_not_mutated_by_evaluation():
    cases = build_cases(7)
    tasks = build_tasks(cases)
    first = run_benchmark(cases, tasks, seed=7)
    second = run_benchmark(cases, tasks, seed=7)
    assert first == second
