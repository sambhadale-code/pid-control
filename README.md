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

```powershell
python -m pip install -e .
python src\pid_assignment.py
```

The simulation writes the report figures and `controller_metrics.csv` into `results/`. Random sensor noise uses a fixed seed, so the noise comparison is reproducible.

## Build the PDF report

After regenerating the figures, build the PDF from its Markdown source:

```powershell
python scripts\build_report.py
```

The final deliverables are:

- `docs/final/PID_Control_Final.pdf`
- `docs/final/PID_Control_Final.md`
- `docs/final/PID_Control_Demo_Script.md`

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## Model and implementation notes

- The main plant is the assignment's mass–spring–damper system: `m = 1 kg`, `c = 10 N·s/m`, and `k = 20 N/m`.
- The controller is implemented in this repository; no ready-made control library is used.
- The controller supports actuator limits, conditional anti-windup, derivative-on-measurement, and an optional first-order derivative filter.
- The Ziegler–Nichols section simulates the separate unity-feedback plant `G(s) = 1/(s + 1)^3`.
