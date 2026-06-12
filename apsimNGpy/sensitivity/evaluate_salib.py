def evaluate_sensitivity(configured_prob, Y, method="sobol", **kwargs):
    method = method.lower()

    if method == "sobol":
        from SALib.analyze import sobol

        Si = sobol.analyze(
            configured_prob.problem,
            Y,
            calc_second_order=kwargs.get("calc_second_order", True),
            conf_level=kwargs.get("conf_level", 0.95),
            num_resamples=kwargs.get("num_resamples", 100),
            print_to_console=kwargs.get("print_to_console", False),
        )

    elif method == "morris":
        from SALib.analyze import morris

        Si = morris.analyze(
            configured_prob.problem,
            X=kwargs["X"],
            Y=Y,
            conf_level=kwargs.get("conf_level", 0.95),
            num_resamples=kwargs.get("num_resamples", 100),
            print_to_console=kwargs.get("print_to_console", False),
        )

    elif method == "fast":
        from SALib.analyze import fast

        Si = fast.analyze(
            configured_prob.problem,
            Y,
            M=kwargs.get("M", 4),
            print_to_console=kwargs.get("print_to_console", False),
        )

    elif method == "rbd_fast":
        from SALib.analyze import rbd_fast

        Si = rbd_fast.analyze(
            configured_prob.problem,
            kwargs["X"],
            Y,
            print_to_console=kwargs.get("print_to_console", False),
        )

    elif method == "delta":
        from SALib.analyze import delta

        Si = delta.analyze(
            configured_prob.problem,
            kwargs["X"],
            Y,
            print_to_console=kwargs.get("print_to_console", False),
        )

    elif method == "dgsm":
        from SALib.analyze import dgsm

        Si = dgsm.analyze(
            configured_prob.problem,
            kwargs["X"],
            Y,
            print_to_console=kwargs.get("print_to_console", False),
        )

    elif method == "ff":
        from SALib.analyze import ff

        Si = ff.analyze(
            configured_prob.problem,
            kwargs["X"],
            Y,
            second_order=kwargs.get("second_order", False),
            print_to_console=kwargs.get("print_to_console", False),
        )

    else:
        raise ValueError(
            f"Unknown sensitivity method '{method}'. "
            "Choose from: sobol, morris, fast, rbd_fast, delta, dgsm, ff"
        )

    return Si