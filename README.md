# Sunrun
A planter that that uses smart sensors to detect the trajectory of the sun, and then makes micro-adjustments to “chase” the sun.

# Basic Functionality, Pseudo-code, & Systems Diagram
Sunrun uses solar sensors to detect solar levels, and "chases" the sun when it detects the sun's movement. The diagram shows how two user action flow through the system: defining a plant profile and retrieving today's log. The diagram is split into User (user action), Evidence (what user interfaces with) and the Script and Services that remain behind the line of visibility.  The interaction script runs top-down. Please review the pseudo-code to understand the workflow in detail. 