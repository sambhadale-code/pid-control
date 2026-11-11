# PID Control Demo Script

**Audience:** interviewer or technical reviewer  
**Planned duration:** 5–7 minutes  
**Goal:** explain the feedback loop, run the reproducible simulation, and show that you can predict and explain changes.

## Before the demo

From the repository root, confirm the dependencies are installed and generate the figures:

```powershell
python -m pip install -e .
python src\pid_assignment.py
```

The script writes figures and `controller_metrics.csv` to `results/`. Have these ready to open:

- `results\p_only_strengths.png`
- `results\all_together.png`
- `results\real_world_issues.png`
- `results\ziegler_nichols.png`

The report is `docs\final\PID_Control_Final.pdf`. If time is short, show the figures first and open the source only when asked.

## Spoken demo

### 1. Open with the problem — about 30 seconds

> “I built this project to demonstrate how PID control can move a physical system toward a target and how the response changes when the gains or implementation details change. I use the assignment’s 1 kg mass, spring constant of 20 newtons per metre, and damping coefficient of 10 newton-seconds per metre. The target position is 1 metre.”

### 2. Explain the loop and the plant — about 45 seconds

> “The setpoint is the desired position, and the sensor gives the current position. Their difference is the error. The controller converts that error into force, the mass-spring-damper responds, and the sensor feeds the new position back.”
>
> “The plant follows \(m\ddot{x}+c\dot{x}+kx=F\). At the target, the spring pulls back with \(kx=20\times1=20\) newtons, so the controller has to provide a steady 20-newton force just to hold the mass there.”

### 3. Explain P, I, and D — about 60 seconds

> “P reacts to the error right now. I accumulates error over time, which lets it supply the extra steady force needed to remove the offset. D reacts to how quickly the measurement changes and can damp the response.”
>
> “For a P-only controller, equilibrium gives \(K_p(r-x)=kx\), so \(x=K_pr/(K_p+k)\). With \(K_p=20\), \(k=20\), and \(r=1\), the final position is 0.5 metres. That is why P-only stops short.”

Open `p_only_strengths.png`.

> “The curves show the same result for four proportional gains: stronger P moves the final position closer to the target, but any finite gain leaves a nonzero offset.”

### 4. Compare the controllers — about 60 seconds

Open `all_together.png`, then `controller_metrics.csv` if the reviewer wants exact values.

> “To compare the terms fairly, I kept \(K_p=20\) for P, PI, PD, and PID. P and PD finish about 0.5 metres short because neither has integral action. PI and PID remove that steady-state error. In this example, PID settles in about 2.35 seconds, compared with about 3.33 seconds for PI, with negligible overshoot.”
>
> “These are results for this simulated plant and these gains, not universal PID settings.”

### 5. Show the practical issues — about 75 seconds

Open `real_world_issues.png`.

> “This figure shows four implementation details. First, with a 30-newton force limit, conditional anti-windup reduces the peak from about 1.117 metres to 1.000 metre. Second, filtering the derivative reduces force jitter caused by sensor noise bounded by plus or minus 1 millimetre.”
>
> “Third, a sudden setpoint step creates a large derivative kick if D is calculated from error. Calculating D from the measurement avoids differentiating the setpoint; here the peak force drops from about 54 newtons to about 4 newtons.”
>
> “Finally, with the same P-only gains, changing the update interval from 10 milliseconds to 300 milliseconds increases overshoot and makes the response settle more slowly. The plant keeps moving between controller updates.”

### 6. Explain Ziegler–Nichols and wrap up — about 60 seconds

Open `ziegler_nichols.png`.

> “The assignment also asks for the separate plant \(G(s)=1/(s+1)^3\). With unity feedback and P-only control, the stability boundary gives \(K_u=8\), and the oscillation period is about 3.63 seconds. Applying the classic Ziegler–Nichols PID recipe gives a useful starting point, but it overshoots by about 33 percent in this model.”
>
> “I then manually refined the gains. The plotted refinement reduces overshoot to about 1.31 percent and settling time from about 7.70 seconds to about 3.23 seconds, at the cost of a slower rise. That demonstrates why a tuning rule is a starting point rather than a guaranteed final answer.”
>
> “The main lesson is that P, I, and D address different parts of the error, and tuning is a trade-off among speed, overshoot, stability, noise, and steady-state accuracy.”

## Short version — about 2 minutes

If time is limited, use this:

> “This project implements PID control for the assignment’s 1 kg mass-spring-damper system. The model is \(m\ddot{x}+c\dot{x}+kx=F\), and the target is 1 metre. The spring needs 20 newtons of steady force at that position.”
>
> “P reacts to current error, I accumulates persistent error, and D damps rapid changes. The P-only equilibrium is \(x=K_pr/(K_p+k)\), so for \(K_p=k=20\) the mass stops at 0.5 metres. The comparison plot shows that I removes this offset and D improves damping.”
>
> “The practical-cases plot demonstrates anti-windup, derivative filtering, avoiding setpoint kick by differentiating the measurement, and the effect of slower updates. The separate \(1/(s+1)^3\) example shows Ziegler–Nichols tuning and then a refinement that reduces overshoot from about 33 percent to about 1.3 percent.”
>
> “All plots and metrics can be regenerated with `python src\pid_assignment.py`.”

## Likely follow-up questions

**Why does P-only stop short?**  
At steady state the spring needs a holding force \(kx\). With P-only, the force is \(K_p(r-x)\). Equating the two gives \(x=K_pr/(K_p+k)\), which is less than the target for finite positive gains.

**Why does integral action remove the offset?**  
When error persists, the integral grows and contributes a steady actuator force. It can therefore supply the spring’s holding force even after the position error approaches zero. If the actuator saturates, the integral needs anti-windup protection.

**Why calculate D from the measurement?**  
The setpoint can jump instantly, creating an artificial derivative spike if D uses the error derivative. Measurement derivative avoids differentiating the setpoint. For a fixed setpoint, the derivative contribution is \(-K_d\Delta y/\Delta t\).

**Why filter D?**  
Differentiation magnifies rapid measurement changes, including noise. A low-pass filter reduces high-frequency jitter, but adds lag.

**Why does the Ziegler–Nichols result overshoot?**  
The ultimate-gain recipe is an empirical starting rule that often produces an aggressive response. It does not optimize every objective or account for every practical limitation.

**What would change if the mass increased?**  
For the same gains and force, the acceleration \(a=(F-c\dot{x}-kx)/m\) would be smaller. I would expect a slower response; the gains may need retuning.

**What would change if the actuator limit were lowered?**  
The system would have less available force, so it would generally respond more slowly. Integral windup would become more important unless anti-windup is used.

**How do I reproduce the demo?**  
Run `python src\pid_assignment.py` from the repository root. The script regenerates the PNG figures and `results\controller_metrics.csv`.

## Presenter notes

- Say “in this simulation” when reporting numeric results; do not imply they are universal hardware measurements.
- If asked to predict a change, state the physical reason first, then predict the direction of change, then run or edit the simulation.
- The report PDF is limited to 15 pages; this demo script is a separate presenter aid and is not part of the submitted report.
