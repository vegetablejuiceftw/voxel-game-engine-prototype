# WIP: voxel game prototype
<img src="images/edit.gif" width="292" />
<img src="images/smart_path.gif" width="292" />
<img src="images/population.gif" width="292" />

# Main controls:

    Mouse to look, wasd to fly and shift to fly faster.

    Right click to add and left click to remove voxels.
    Scroll to change affected area size.

    To spawn a herd sheep: 1
    To spawn wolf: 2
    To spawn human: 3

    Scroll click to set the target for human.

    Toggle pause npc:  - or F11 key
    Change debug mode: + or F12 key

    To enable mouse: M

    In game press tab for controls reminder.

# Disclaimer:
This is my hobby project that got made into my bachelor thesis.

It has the _distinct smell_ of a student cutting close to the deadline.
I will also include some more broad explanations for said thesis here also.

The main features are:
* voxel rendering through optimized greedy meshing
* examination of different npc ai implementations
* voxel aware destructive path-finding

# Meshing

<img src="http://i.imgur.com/doc0IMR.jpg" width="600" />

The main challenge in using polygons is figuring out how to convert the voxels into
**minimum amount of polygons efficiently**.

In a typical voxel game the voxels do not get modified that often compared to how frequently they are drawn.
Which is why the main heavy lifting happens at rendering the voxels.
As a result, it is quite sensible to optimize the mesh upfront.

<img src="http://i.imgur.com/nMY4iAk.png" width="300" />

No culling method has a voxel to face ratio of 6.

Clearly, in order to improve on the naive method is to simply not to draw the faces that
are obscured by checking each cubes neighbours before creating a face.

<img src="http://i.imgur.com/T28c2DL.png" width="300" />

For a Perlin noise map this amounts to somewhere from 1 to 2 faces per voxel.

Improvement can be brought by merging adjacent quads together into larger regions.
While not optimal greedy implementations perform quite well.

<img src="http://i.imgur.com/DuWI8GD.png" width="300" />

Example of greedy meshing on a solid chunk of voxels

The idea was inspired by Karnaugh map method which is used to simplify boolean
algebra exressions.

Meshing can be improved by allowing faces to overlap and extend over undefined (culled) space as shown in next the image.

<img src="http://i.imgur.com/jYJ1E5f.jpg" width="500" />

Given that the material (visual) is the same, there is no z-fighting or other artifact for this approach.
There is no rule that faces can not intersect.

![](http://i.imgur.com/NwhhMDY.png)

# Pathfinding in voxel games is different

There is inherent expectation of the world's capability to perform alteration.
Likewise to the user who is able to manipulate the state of the world also the inhabiting actors must meet the same expectations.
This means that the pathfinding not only has to traverse nodes but also should be able to alter the state of the world.
By bringing this new dimension of complexity to the pathfinding problem the prospect of finding the optimal path becomes seemingly unreachable.

This algorithm follows the A* path-finding pattern. The main change to the algorithm is
the added functionality for passing through solid voxels where the travel cost is
calculated with the necessary changes in mind.

<img src="http://i.imgur.com/EwdjEm6.jpg" width="400" />
<img src="http://i.imgur.com/NTXZWAe.jpg" width="400" />

# Extra
Pseudo-random pathfinding.

Simplest would be the Brownian motion inspired pathfinding.
If one can offset the probability of the vectors appearing by some dynamic function the resulting biased motion or drift
will try to reach the direction.
If the motion to the direction of the target is more probable, it may get there eventually.

<img src="http://i.imgur.com/QlyZY81.jpg" width="400" />
<img src="http://i.imgur.com/Kd5MF0j.jpg" width="400" />

Dispersion of sheep from danger and competition

This is great for simulating large set of npc to convey a sense of activity in the world.

Wolves

<img src="http://i.imgur.com/DocAdX0.png" width="400" />
<img src="http://i.imgur.com/fgtKyDi.jpg" width="400" />
<img src="http://i.imgur.com/Yj2vJN4.jpg" width="400" />
<img src="http://i.imgur.com/JHBiQft.jpg" width="400" />


# Soon

Every chunk with n**3 voxels has 3(n+1) planes where faces are drawn as seen on 8x8x8 chunk above.
While sharing polygons is a proven viable idea,
all voxel faces on a plane can be drawn with a single polygon where the texture's pixels represent the voxel faces.
Having one polygon for all voxel faces in a plane would improve the rendering overhead significantly.

<img src="http://i.imgur.com/ShpJfuN.jpg" width="600" />
![](http://i.imgur.com/3UIIvrn.png)
![](http://i.imgur.com/wfDlpZR.png)