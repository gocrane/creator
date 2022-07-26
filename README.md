# creator

Creator is the core brain of the crane project, including the implementation of the crane's core algorithm and the algorithm evaluation module. It helps you better achieve the purpose of increasing efficiency and reducing costs through the iteration of algorithm optimization.

## Motivation
Crane's algorithm module is deeply coupled with the crane code. The advantage of this is that the algorithm can be directly integrated into the entire crane system, and the algorithm will be updated after the crane is updated, but this also brings several disadvantages:
1. Unfriendly to algorithm developers: The current mainstream algorithm development process uses an interpreted language such as python as the default model development language, while the algorithm implementation language of crane is a compiled language such as golang, so algorithm engineers have a certain learning burden
2. The algorithm iteration of the crane system is prone to problems: the current algorithm verification is only a small-scale test case, without a large-scale offline algorithm evaluation, it is difficult to ensure that the algorithm can play a role in complex online applications
3. The algorithm iteration of crane is submerged in numerous commits, which is inconvenient for the maintenance and participation of community partners. Here, the crane version and the algorithm version are formed into a mapping relationship

In order to solve the above problems and allow more partners to participate in the crane resource optimization algorithm, we open source and maintain this repository, and work with the community to help the Finops best practice project - crane.