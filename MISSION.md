# Mission: PID control for an internship assignment

## Why
I need to produce a clear beginner-friendly explanation and working Python simulation of PID control for a robotics/control assignment. The goal is to understand the concept deeply enough to explain it, tune controllers, and defend my result in an interview with concrete graphs and code.

## Success looks like
- I can explain what setpoint, error, plant, Kp/Ki/Kd, overshoot, and step response mean in plain English.
- I can write and run a Python PID controller that simulates a 1 kg spring-damper system and recreate the required graphs.
- I can explain how P, I, D, anti-windup, sensor noise, and slow sampling change the response.

## Constraints
- The assignment is 7 days and the final deliverable is a PDF plus GitHub code.
- I want the explanation to be simple enough for a beginner but rigorous enough to satisfy a technical interviewer.
- I prefer starting from physical intuition, then formulas, then code and graphs.

## Out of scope
- Advanced nonlinear control design (e.g., Lyapunov analysis, sliding mode control, gain scheduling) — practical constraints like actuator saturation and anti-windup remain in scope
- Modern state-space and optimal control (e.g., LQR, MPC, Kalman filters / state observers)
- Industrial motor drive commissioning beyond the simulated transfer functions
- Physical hardware deployment and embedded C/C++/RTOS implementation
