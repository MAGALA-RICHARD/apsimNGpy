import numpy as np
import pandas as pd


class MorrisAnalyzer:
    """
    APSIM-oriented Morris sensitivity workflow.

    Handles:
    - APSIM yearly outputs
    - simulation aggregation
    - trajectory reconstruction
    - elementary effects
    - Morris statistics

    """

    def __init__(
            self,
            parameter_cols,
            output_col,
            simulation_col="SimulationID",
            aggregation="mean",
            epsilon=1e-12
    ):

        self.parameter_cols = parameter_cols
        self.output_col = output_col
        self.simulation_col = simulation_col
        self.aggregation = aggregation
        self.epsilon = epsilon

    # ---------------------------------------------------------
    # STEP 1: Collapse APSIM yearly outputs
    # ---------------------------------------------------------

    def collapse_outputs(self, df):

        agg_df = (
            df.groupby(self.simulation_col)
            .agg({
                **{
                    p: "first"
                    for p in self.parameter_cols
                },
                self.output_col: self.aggregation
            })
            .reset_index()
        )

        return agg_df

    # ---------------------------------------------------------
    # STEP 2: Validate Morris trajectories
    # ---------------------------------------------------------

    def validate_trajectories(self, X):

        n = len(X)

        d = len(self.parameter_cols)

        if n % (d + 1) != 0:
            raise ValueError(
                f"Expected rows divisible by {d + 1} "
                f"for Morris trajectories."
            )

        n_trajectories = n // (d + 1)

        for t in range(n_trajectories):

            start = t * (d + 1)
            end = start + (d + 1)

            traj = X[start:end]

            for i in range(d):

                dx = traj[i + 1] - traj[i]

                changed = np.where(
                    np.abs(dx) > self.epsilon
                )[0]

                if len(changed) != 1:

                    raise ValueError(
                        f"Invalid Morris trajectory:\n"
                        f"Trajectory={t}, Step={i}\n"
                        f"Expected exactly one parameter change.\n"
                        f"Changed={changed}"
                    )

    # ---------------------------------------------------------
    # STEP 3: Compute elementary effects
    # ---------------------------------------------------------

    def elementary_effects(self, X, Y):

        d = len(self.parameter_cols)

        step = d + 1

        n_trajectories = len(X) // step

        effects = {
            p: []
            for p in self.parameter_cols
        }

        for t in range(n_trajectories):

            start = t * step
            end = start + step

            X_traj = X[start:end]
            Y_traj = Y[start:end]

            for i in range(d):

                dx = X_traj[i + 1] - X_traj[i]

                changed = np.where(
                    np.abs(dx) > self.epsilon
                )[0]

                j = changed[0]

                delta_x = dx[j]

                ee = (
                    (Y_traj[i + 1] - Y_traj[i])
                    / delta_x
                )

                effects[self.parameter_cols[j]].append(ee)

        return effects

    # ---------------------------------------------------------
    # STEP 4: Morris statistics
    # ---------------------------------------------------------

    def summarize_effects(self, effects):

        rows = []

        for param, ee in effects.items():

            ee = np.asarray(ee, dtype=float)

            mu = np.mean(ee)

            mu_star = np.mean(np.abs(ee))

            sigma = (
                np.std(ee, ddof=1)
                if len(ee) > 1 else 0
            )

            conf = (
                1.96 * sigma / np.sqrt(len(ee))
                if len(ee) > 0 else np.nan
            )

            rows.append({
                "parameter": param,
                "mu": mu,
                "mu_star": mu_star,
                "sigma": sigma,
                "mu_star_conf": conf,
                "n_effects": len(ee)
            })

        return (
            pd.DataFrame(rows)
            .sort_values("mu_star", ascending=False)
            .reset_index(drop=True)
        )

    # ---------------------------------------------------------
    # COMPLETE PIPELINE
    # ---------------------------------------------------------

    def analyze(self, df):

        # STEP 1
        collapsed = self.collapse_outputs(df)

        # STEP 2
        X = (
            collapsed[self.parameter_cols]
            .apply(pd.to_numeric, errors="coerce")
            .to_numpy(dtype=float)
        )

        Y = pd.to_numeric(
            collapsed[self.output_col],
            errors="coerce"
        ).to_numpy(dtype=float)

        # STEP 3
        self.validate_trajectories(X)

        # STEP 4
        effects = self.elementary_effects(X, Y)

        # STEP 5
        results = self.summarize_effects(effects)

        return results


