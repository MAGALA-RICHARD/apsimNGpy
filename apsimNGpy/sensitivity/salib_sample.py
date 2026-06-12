def generate_samples(configured_prob, N, method, **kwargs):
    method = method.lower()

    if method == "sobol":
        from SALib.sample import sobol

        X = sobol.sample(
            configured_prob.problem,
            N=N,
            calc_second_order=kwargs.get("calc_second_order", True)
        )

    elif method == "saltelli":
        from SALib.sample import saltelli

        X = saltelli.sample(
            configured_prob.problem,
            N=N,
            calc_second_order=kwargs.get("calc_second_order", True)
        )

    elif method == "morris":
        from SALib.sample import morris

        X = morris.sample(
            configured_prob.problem,
            N=N,
            num_levels=kwargs.get("num_levels", 4),
            optimal_trajectories=kwargs.get("optimal_trajectories"),
            local_optimization=kwargs.get("local_optimization", True),
        )

    elif method == "fast":
        from SALib.sample import fast_sampler

        X = fast_sampler.sample(
            configured_prob.problem,
            N=N,
            M=kwargs.get("M", 4)
        )

    elif method == "latin":
        from SALib.sample import latin

        X = latin.sample(
            configured_prob.problem,
            N=N
        )

    elif method == "finite_diff":
        from SALib.sample import finite_diff

        X = finite_diff.sample(
            configured_prob.problem,
            N=N,
            delta=kwargs.get("delta", 0.01)
        )

    elif method == "ff":
        from SALib.sample import ff

        X = ff.sample(configured_prob.problem)

    else:
        raise ValueError(
            f"Unknown sampling method '{method}'. "
            "Choose from: sobol, saltelli, morris, fast, latin, finite_diff, ff"
        )

    return X