# PID Control Assignment

This repository contains a reproducible PID-control study for the supplied internship assignment. It includes a direct Python implementation, the required plant simulations and plots, a technical report, and the original assignment brief.

## Repository layout

```text
src/                         PID controller and simulations
tests/                       Focused unit tests
scripts/build_report.py      Build the submission PDF from Markdown
results/                     Generated figures and metric data
docs/assignment/             Original assignment PDF
docs/design/                 Working design notes
docs/final/                  Submission report (Markdown and PDF)
```

## Set up and run

From the repository root:

```bash
python -m pip install -e .
python src/pid_assignment.py
```

Running `src/pid_assignment.py` recreates all required simulation data and figures in `results/`:
- `p_only_strengths.png` (Section 5: P-only offset comparison)
- `all_together.png` (Section 6: P, PI, PD, and full PID comparison)
- `real_world_issues.png` (Section 7: Windup, sensor noise, derivative kick, loop latency)
- `ziegler_nichols.png` (Section 8: Ultimate gain oscillation & tuned response for plant G(s) = 1/(s + 1)^3)
- `controller_metrics.csv` (Rise time, overshoot, settling time, steady-state error)

Random sensor noise uses a fixed seed, ensuring completely reproducible results.

## Build the PDF report

After generating the figures, compile the final submission PDF from its Markdown source:

```bash
python scripts/build_report.py
```

### Deliverables & Artifacts

- **Primary Submission Document**: [`docs/final/PID_Control_Final.pdf`](docs/final/PID_Control_Final.pdf) (8 pages — strictly complies with the ≤ 15 pages limit).
- **Report Source**: [`docs/final/PID_Control_Final.md`](docs/final/PID_Control_Final.md) (structured into the 10 required sections).
- **Interview Walkthrough Script**: [`docs/final/PID_Control_Demo_Script.md`](docs/final/PID_Control_Demo_Script.md) (quick reference and talking points for the live 30-minute technical interview).

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Model and implementation notes

- The main plant is the assignment's mass–spring–damper system: `m = 1 kg`, `c = 10 N·s/m`, and `k = 20 N/m`.
- The controller is implemented in this repository; no ready-made control library is used.
- The controller supports actuator limits, conditional anti-windup, derivative-on-measurement, and an optional first-order derivative filter.
- The Ziegler–Nichols section simulates the separate unity-feedback plant `G(s) = 1/(s + 1)^3`.
