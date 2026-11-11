# PID Control Glossary

This glossary keeps the language consistent with the assignment and the project code. The point is to define the terms tightly so the explanation stays accurate and easy to follow.

## Terms

**Setpoint**:
The target value the controller is trying to reach, such as 1 meter or 60 RPM.

**Error**:
The difference between the target and the actual value: error = setpoint - measurement.

**Plant**:
The system being controlled, such as a motor, mass-spring-damper, or robot arm.

**Proportional gain (Kp)**:
The strength of the corrective action proportional to the current error. Larger Kp reacts more aggressively.

**Integral gain (Ki)**:
The strength of accumulated past error. It removes long-lasting offset but can cause overshoot if left unchecked.

**Derivative gain (Kd)**:
The strength of the reaction to how quickly the error is changing. It damps oscillations and improves stability.

**Step response**:
The output of a system when the setpoint suddenly changes, for example from 0 m to 1 m.

**Overshoot**:
The amount the system moves past the target before settling.

**Rise time**:
How long it takes the response to move from a low fraction to a high fraction of the final target.

**Settling time**:
How long it takes the response to stay inside a small band around the target.

**Steady-state error**:
The remaining difference between the target and final value after the system settles.

**Windup**:
A condition where the integral term keeps growing when the actuator is saturated, causing a large overshoot when the system finally responds.

**Sensor noise**:
Unwanted variation in the measured value, which can make the derivative term jumpy.
