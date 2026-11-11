from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT_ROOT / "results"
RESULTS.mkdir(exist_ok=True)

MASS = 1.0
DAMPING = 10.0
SPRING = 20.0
SETPOINT = 1.0


@dataclass
class PIDController:
    """PID controller with derivative filtering and conditional anti-windup."""

    kp: float
    ki: float
    kd: float
    dt: float
    output_limit: float | None = None
    integral_limit: float | None = None
    derivative_filter_tau: float = 0.0
    derivative_on_measurement: bool = True
    anti_windup: bool = True

    def __post_init__(self) -> None:
        if self.dt <= 0.0:
            raise ValueError("Controller time step must be positive.")
        if self.derivative_filter_tau < 0.0:
            raise ValueError("Derivative filter time constant cannot be negative.")
        self.integral = 0.0
        self.previous_error: float | None = None
        self.previous_measurement: float | None = None
        self.filtered_derivative = 0.0

    def update(self, setpoint: float, measurement: float) -> float:
        error = setpoint - measurement
        if self.previous_error is None:
            error_rate = 0.0
            measurement_rate = 0.0
        else:
            error_rate = (error - self.previous_error) / self.dt
            measurement_rate = (measurement - self.previous_measurement) / self.dt

        raw_derivative = -measurement_rate if self.derivative_on_measurement else error_rate
        if self.derivative_filter_tau > 0.0:
            alpha = self.dt / (self.derivative_filter_tau + self.dt)
            self.filtered_derivative += alpha * (raw_derivative - self.filtered_derivative)
        else:
            self.filtered_derivative = raw_derivative

        candidate_integral = self.integral + error * self.dt
        if self.integral_limit is not None:
            candidate_integral = float(
                np.clip(candidate_integral, -self.integral_limit, self.integral_limit)
            )

        def output(integral: float) -> float:
            return (
                self.kp * error
                + self.ki * integral
                + self.kd * self.filtered_derivative
            )

        raw_output = output(candidate_integral)
        if self.output_limit is not None:
            clipped_output = float(
                np.clip(raw_output, -self.output_limit, self.output_limit)
            )
            pushes_further_into_saturation = (
                raw_output > self.output_limit and error > 0.0
            ) or (raw_output < -self.output_limit and error < 0.0)
            if not (self.anti_windup and pushes_further_into_saturation):
                self.integral = candidate_integral
            command = clipped_output
        else:
            self.integral = candidate_integral
            command = raw_output

        self.previous_error = error
        self.previous_measurement = measurement
        return command


def simulate_mass_spring(
    kp: float,
    ki: float,
    kd: float,
    *,
    dt: float = 0.01,
    total_time: float = 12.0,
    setpoint: float = SETPOINT,
    actuator_limit: float | None = None,
    sensor_noise_mm: float = 0.0,
    random_seed: int = 0,
    derivative_filter_tau: float = 0.0,
    derivative_on_measurement: bool = True,
    anti_windup: bool = True,
    control_period: float | None = None,
    integral_limit: float | None = None,
    step_time: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if dt <= 0.0 or total_time <= 0.0:
        raise ValueError("Simulation time step and duration must be positive.")
    if control_period is not None and control_period < dt:
        raise ValueError("Controller update period must be at least the plant time step.")
    time = np.arange(0.0, total_time + dt / 2.0, dt)
    position = np.zeros_like(time)
    velocity = np.zeros_like(time)
    force = np.zeros_like(time)
    rng = np.random.default_rng(random_seed)
    noise_amplitude = sensor_noise_mm / 1000.0
    sample_period = control_period or dt
    controller = PIDController(
        kp=kp,
        ki=ki,
        kd=kd,
        dt=sample_period,
        output_limit=actuator_limit,
        integral_limit=integral_limit,
        derivative_filter_tau=derivative_filter_tau,
        derivative_on_measurement=derivative_on_measurement,
        anti_windup=anti_windup,
    )
    command = 0.0
    next_update = 0.0

    for i in range(1, len(time)):
        current_time = time[i - 1]
        if current_time + 1e-12 >= next_update:
            target = setpoint if current_time >= step_time else 0.0
            measured_position = position[i - 1] + rng.uniform(
                -noise_amplitude, noise_amplitude
            )
            command = controller.update(target, measured_position)
            next_update += sample_period
        force[i] = command
        acceleration = (
            command - DAMPING * velocity[i - 1] - SPRING * position[i - 1]
        ) / MASS
        velocity[i] = velocity[i - 1] + acceleration * dt
        position[i] = position[i - 1] + velocity[i] * dt

    return time, position, force


def step_metrics(
    time: np.ndarray,
    response: np.ndarray,
    setpoint: float = SETPOINT,
    settling_band: float = 0.02,
) -> dict[str, float]:
    if setpoint == 0.0:
        raise ValueError("Step metrics require a non-zero setpoint.")

    initial_value = float(response[0])
    final_value = float(response[-1])
    response_range = final_value - initial_value
    rise_time = float("nan")
    if abs(response_range) > 1e-12:
        progress = (response - initial_value) / response_range
        crossed_10 = np.flatnonzero(progress >= 0.1)
        crossed_90 = np.flatnonzero(progress >= 0.9)
        if crossed_10.size and crossed_90.size:
            rise_time = float(time[crossed_90[0]] - time[crossed_10[0]])

    band = settling_band * max(abs(final_value), 1e-12)
    outside = np.flatnonzero(np.abs(response - final_value) > band)
    settling_time = float(time[outside[-1] + 1]) if outside.size and outside[-1] + 1 < len(time) else (
        float(time[0]) if not outside.size else float("nan")
    )
    overshoot = max(0.0, float(np.max(response) - setpoint)) / abs(setpoint) * 100.0
    steady_state_error = float(setpoint - response[-1])
    return {
        "rise_time_s": rise_time,
        "overshoot_percent": overshoot,
        "settling_time_s": settling_time,
        "steady_state_error_m": steady_state_error,
    }


def style_axes(ax: plt.Axes, title: str) -> None:
    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Position (m)")
    ax.grid(alpha=0.25)
    ax.legend()


def plot_response_metrics() -> dict[str, float]:
    time, position, _ = simulate_mass_spring(20.0, 30.0, 5.0, total_time=8.0)
    metrics = step_metrics(time, position)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(time, position, label="Mass position", linewidth=2)
    ax.axhline(SETPOINT, color="black", linestyle="--", label="Setpoint (1.00 m)")
    ax.axhspan(0.98, 1.02, color="green", alpha=0.08, label="±2% settling band")
    ax.axvline(metrics["settling_time_s"], color="green", linestyle=":", label="Settling time")
    peak_index = int(np.argmax(position))
    ax.scatter(time[peak_index], position[peak_index], color="crimson", zorder=3, label="Peak")
    target_10 = 0.1 * SETPOINT
    target_90 = 0.9 * SETPOINT
    t10 = time[np.flatnonzero(position >= target_10)[0]]
    t90 = time[np.flatnonzero(position >= target_90)[0]]
    ax.axvline(t10, color="purple", linestyle=":", alpha=0.7)
    ax.axvline(t90, color="purple", linestyle=":", alpha=0.7)
    ax.annotate(
        f'Rise time: {metrics["rise_time_s"]:.2f} s',
        xy=((t10 + t90) / 2.0, 0.2),
        xytext=(0, 0),
        textcoords="offset points",
        ha="center",
        color="purple",
    )
    displayed_error = metrics["steady_state_error_m"]
    if abs(displayed_error) < 0.0005:
        displayed_error = 0.0
    ax.text(
        0.98,
        0.78,
        f'Overshoot: {metrics["overshoot_percent"]:.2f}%\n'
        f'Final error: {displayed_error:.3f} m',
        transform=ax.transAxes,
        ha="right",
        va="top",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "alpha": 0.85},
    )
    style_axes(ax, "Mass-spring-damper step response (PID: Kp=20, Ki=30, Kd=5)")
    fig.tight_layout()
    fig.savefig(RESULTS / "tuned_response.png", dpi=180)
    plt.close(fig)
    return metrics


def plot_p_only_sweep() -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for kp in (2.0, 5.0, 10.0, 20.0):
        time, position, _ = simulate_mass_spring(kp, 0.0, 0.0)
        theoretical_position = kp / (kp + SPRING)
        ax.plot(time, position, label=f"Kp={kp:g}; final={theoretical_position:.2f} m")
    ax.axhline(SETPOINT, color="black", linestyle="--", label="Setpoint (1.00 m)")
    style_axes(ax, "P-only control: stronger proportional action reduces offset")
    fig.tight_layout()
    fig.savefig(RESULTS / "p_only_strengths.png", dpi=180)
    plt.close(fig)


def plot_controller_comparison() -> list[tuple[str, tuple[float, float, float], dict[str, float]]]:
    gains = {
        "P": (20.0, 0.0, 0.0),
        "PI": (20.0, 30.0, 0.0),
        "PD": (20.0, 0.0, 5.0),
        "PID": (20.0, 30.0, 5.0),
    }
    results = []
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for name, (kp, ki, kd) in gains.items():
        time, position, _ = simulate_mass_spring(kp, ki, kd, total_time=15.0)
        ax.plot(time, position, label=name)
        results.append((name, (kp, ki, kd), step_metrics(time, position)))
    ax.axhline(SETPOINT, color="black", linestyle="--", label="Setpoint (1.00 m)")
    style_axes(ax, "P, PI, PD, and PID comparison")
    fig.tight_layout()
    fig.savefig(RESULTS / "all_together.png", dpi=180)
    plt.close(fig)

    with (RESULTS / "controller_metrics.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["controller", "Kp", "Ki", "Kd", "rise_time_s", "overshoot_percent",
             "settling_time_s", "steady_state_error_m"]
        )
        for name, (kp, ki, kd), metrics in results:
            writer.writerow(
                [name, kp, ki, kd, *[metrics[key] for key in metrics]]
            )
    return results


def plot_practical_issues() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Compare ordinary integration with conditional integration at a 30 N force limit.
    for anti_windup, label in ((False, "No anti-windup"), (True, "Conditional anti-windup")):
        time, position, _ = simulate_mass_spring(
            80.0, 100.0, 0.0, actuator_limit=30.0, total_time=12.0,
            anti_windup=anti_windup,
        )
        axes[0, 0].plot(time, position, label=label)
    axes[0, 0].axhline(SETPOINT, color="black", linestyle="--", label="Setpoint")
    axes[0, 0].set_title("(a) Integral windup: anti-windup limits overshoot")
    axes[0, 0].set_xlabel("Time (s)")
    axes[0, 0].set_ylabel("Position (m)")

    # Raw derivative versus filtered derivative with the same seeded sensor noise.
    for tau, label in ((0.0, "Unfiltered derivative"), (0.05, "Filtered derivative (τ=0.05 s)")):
        time, position, force = simulate_mass_spring(
            20.0, 30.0, 5.0, sensor_noise_mm=1.0, random_seed=21,
            derivative_filter_tau=tau, total_time=20.0,
        )
        axes[0, 1].plot(time, force, label=label)
    axes[0, 1].set_title("(b) 1 mm sensor noise appears in derivative force")
    axes[0, 1].set_xlabel("Time (s)")
    axes[0, 1].set_ylabel("Control force (N)")
    axes[0, 1].set_xlim(19.0, 20.0)

    # Error derivative spikes at a setpoint step; measurement derivative does not.
    for on_measurement, label in ((False, "Derivative on error"), (True, "Derivative on measurement")):
        time, position, force = simulate_mass_spring(
            4.0, 2.0, 0.5, derivative_on_measurement=on_measurement,
            step_time=2.0, total_time=6.0,
        )
        axes[1, 0].plot(time, force, label=label)
    axes[1, 0].set_title("(c) Derivative on measurement avoids setpoint kick")
    axes[1, 0].set_xlabel("Time (s)")
    axes[1, 0].set_ylabel("Control force (N)")

    for sample_period, label in ((0.01, "10 ms update"), (0.30, "300 ms update")):
        time, position, _ = simulate_mass_spring(
            80.0, 0.0, 0.0, control_period=sample_period, total_time=6.0,
        )
        axes[1, 1].plot(time, position, label=label)
    axes[1, 1].axhline(SETPOINT, color="black", linestyle="--", label="Setpoint")
    axes[1, 1].set_title("(d) Slower updates increase lag and degrade response")
    axes[1, 1].set_xlabel("Time (s)")
    axes[1, 1].set_ylabel("Position (m)")

    for ax in axes.flat:
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / "real_world_issues.png", dpi=180)
    plt.close(fig)


def simulate_three_poles(
    kp: float,
    ki: float,
    kd: float,
    *,
    dt: float = 0.01,
    total_time: float = 20.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate unity feedback around G(s)=1/(s+1)^3 with RK4 integration."""
    time = np.arange(0.0, total_time + dt / 2.0, dt)
    output = np.zeros_like(time)
    states = np.zeros(3)
    controller = PIDController(kp, ki, kd, dt, derivative_on_measurement=True)

    def derivative(state: np.ndarray, command: float) -> np.ndarray:
        first, second, third = state
        return np.array((-first + command, -second + first, -third + second))

    for index in range(1, len(time)):
        command = controller.update(1.0, states[2])
        step1 = derivative(states, command)
        step2 = derivative(states + 0.5 * dt * step1, command)
        step3 = derivative(states + 0.5 * dt * step2, command)
        step4 = derivative(states + dt * step3, command)
        states += dt * (step1 + 2 * step2 + 2 * step3 + step4) / 6.0
        output[index] = states[2]
    return time, output


def plot_ziegler_nichols() -> dict[str, float]:
    # The marginal-stability condition gives Ku=8 and omega_u=sqrt(3) rad/s.
    ku = 8.0
    pu = 2.0 * np.pi / np.sqrt(3.0)
    kp, ki, kd = 0.6 * ku, 1.2 * (0.6 * ku) / pu, 0.075 * ku * pu
    time, critical_output = simulate_three_poles(ku, 0.0, 0.0, total_time=18.0)
    zn_time, zn_output = simulate_three_poles(kp, ki, kd)
    refined_gains = (2.4, 0.6, 1.8)
    refined_time, refined_output = simulate_three_poles(*refined_gains)
    metrics = step_metrics(zn_time, zn_output)
    refined_metrics = step_metrics(refined_time, refined_output)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].plot(time, critical_output, label=f"P-only at Ku={ku:g}")
    axes[0].axhline(1.0, color="black", linestyle="--", label="Setpoint")
    axes[0].set_title(f"Critical oscillation: Pu ≈ {pu:.2f} s")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Output")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(
        zn_time,
        zn_output,
        label=f"ZN PID ({kp:.1f}, {ki:.2f}, {kd:.2f})",
    )
    axes[1].plot(
        refined_time,
        refined_output,
        label=f"Refined PID {refined_gains}",
    )
    axes[1].axhline(1.0, color="black", linestyle="--", label="Setpoint")
    axes[1].set_title("Ziegler-Nichols starting point and manual refinement")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Output")
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / "ziegler_nichols.png", dpi=180)
    plt.close(fig)
    return {
        "Ku": ku,
        "Pu_s": float(pu),
        "Kp": kp,
        "Ki": ki,
        "Kd": kd,
        **metrics,
        "refined_kp": refined_gains[0],
        "refined_ki": refined_gains[1],
        "refined_kd": refined_gains[2],
        "refined_overshoot_percent": refined_metrics["overshoot_percent"],
        "refined_settling_time_s": refined_metrics["settling_time_s"],
    }


def main() -> None:
    plot_p_only_sweep()
    comparison = plot_controller_comparison()
    plot_practical_issues()
    zn_metrics = plot_ziegler_nichols()
    tuned_metrics = plot_response_metrics()

    print(f"Generated figures and metrics in {RESULTS}")
    print("\nController comparison")
    print("Name  Kp    Ki    Kd    Rise(s)  Overshoot(%)  Settle(s)  Final error(m)")
    for name, gains, metrics in comparison:
        print(
            f"{name:<5} {gains[0]:<5.1f} {gains[1]:<5.1f} {gains[2]:<5.1f} "
            f"{metrics['rise_time_s']:<8.3f} {metrics['overshoot_percent']:<13.2f} "
            f"{metrics['settling_time_s']:<10.3f} {metrics['steady_state_error_m']:.4f}"
        )
    print("\nTuned mass-spring-damper response:", tuned_metrics)
    print("Ziegler-Nichols three-pole system:", zn_metrics)


if __name__ == "__main__":
    main()
