# mv_professor

Abstract: The purpose of this Python project is to programmatically derive an electrical connectivity model
of a medium voltage (16kV) feeder circuit from GIS latitude/longitude data provided by Southern California
Edison's Distribution Resources Plan External Portal (DRPEP). In other words, this package seeks to transform
geographic topology into electrical topology.

===Why make an electrical connectivity model?=== 
The electrical topology is required to model the circuit's electrical behavior. Ultimately this electrical model
will be converted to EPRI's Common Information Model (CIM), for import into electrical solvers like OpenDSS.

===Why do this programmatically?===

For a single circuit, it would be easier to have a human "click and connect" the MV lines to their obvious neighbors.

1) Unfortunately, no such software is readily available. I could write a GUI to aid this task, but the time 
investment may be even greater than the rough programatic approach.

2) A semi-automated processing pipeline from GIS -> CIM means that whenever the network topology changes (in the real world,
or because data is updated), the CIM can be quickly regenerated.

3) Most importantly, this regeneration capability enables broader analysis. The electrical model is saved as a "Graph" 
(in the mathematical sense) using NetworkX, which has a powerful engine for reconfiguring networks. For instance, it should be
to model the effects of a constrained line or identify bottlenecks which degrade hosting capacity.

SoCalEdison's DRPEP: https://drpep.sce.com/drpep/
Common Information Model: https://site.ieee.org/pes-enews/2015/12/10/a-brief-history-the-common-information-model/
