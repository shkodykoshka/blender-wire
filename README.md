## blender-wire

Blender plugin to draw wires between 'pole' objects or between two selected vertices. Plugin written and tested with Blender 3.3.1.

### Requirements

Requires `math`, `mathutils`, `os`, and `json` modules. All included with Blender 3.3 by default.

### Draw wires between poles
- Select two or more 'pole' objects that are defined in poles.json in object mode.
- Make any changes in Wire Configuration panel and press **Draw Wire** button to draw wires.

Wires are drawn from selected pole output to next selected pole input. Last wires are drawn between the two most recently selected pole input and output.

### Draw wires between vertices

Select two vertices in edit mode and press **Draw Wire** button to draw wires. More than two vertices can be selected but two vertices works best.

### To add new 'pole'

New 'pole' objects can be added to `poles.json` by selecting input/output vertices and using corresponding buttons in **Pole Options** menu.
- Pole Input: vertices where wire will end.
- Pole Output: vertices where wire will start.

The **Print Poles** button can be used to print all saved poles in `poles.json`.  
The **Delete Pole** button can be used to delete currently selected object form `poles.json`.

## Configuration options

- Update Mode: Sets update mode.
    - Manual Update only updates when **Update Wire** button used.
    - Auto Update will update when pole is moved or configuration option changed.
- Droop: Maximum droop of wire at midpoint, in meters. If set to 0, segments and droop are disabled and straight wire is drawn.
- Wire Segments: Segments to make wire out of. If set to 0, segments and droop are disabled and straight wire is drawn.

### Other Wire Options

- Catenary: Toggles catenary equation usage. When disabled, parabolic equation used. Catenary can  provide more natural looking wire in some cases. Wire balls will not use catenary equation.
- Shade Smooth: Toggles shade mesh wire smooth. When disabled, mesh wires are not shaded smooth.
- Mesh Wire: Toggles mesh wire. When mesh wire enabled, instead of edge object a mesh is drawn. Can be slow when using large segment or wire side values.
- Wire Sides: How many sides (segments) make up mesh wire. Large values can be slow.
- Delete Wire Props: Deletes wire objects connected to current object and clears them from current objects saved properties.

### Wire Balls

- Enable Wire Balls: Toggle wire balls. When enabled, balls will be drawn on the wire following the same parabolic equation that is used by default.
- Wire Ball Radius: Radius of wire balls in meters.
- Wire Ball Sides: How many sides (segments) make up wire balls. Large values can be slow.
- Wire Ball Amount: How many balls to draw on single wire. Large values can be slow.

### Pole Options
- Create Pole Input: Saves selected vertices of active object to its input vertices.
- Create Pole Output: Saves selected vertices of active object to its output vertices.
- Delete Pole: Deletes current active object from `poles.json`.
- Print Poles: Prints all saved poles in `poles.json`.

## Possible Improvements

This plugin now does everything I wanted when I started, but some things can still be improved such as:

- Remember all wires drawn by `Wire Between Vertices` unless deleted by `Delete Wire Props`.
    - Currently if wire(s) are drawn, other vertices are selected and `Wire Between Vertices` is used again, only most recently drawn wire(s) will be remembered and updated.
- Remember vertex and not its coordinates when using `Wire Between Vertices`.
    - Currently if vertex moves in edit mode but object does not, wire will be drawn in old location.
- Make drawing wire balls faster (potentially use C++ for getting points and faces).
- More wire types
