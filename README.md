
<h1 align="center"><b>PyTissueOptics</b></h1>

<p align="center"><i>Monte Carlo simulations of light transport made easy.</i></p>
<p align="center">
<img src="./docs/README.assets/pytissue-demo-banenr.jpg">
</p>

This python package is an object-oriented implementation of Monte Carlo modeling for light tranport in diffuse media.
The package is **extremely easy to use**, and **polyvalent** as it allows simulations in arbitrary complex scenes,
but as it is in python, it is **very slow** compared to C++ alternatives. However, we are working on a **very fast** OpenCL
implementation, which will be released soon.

However, as discussed in the [why use this package](#why-use-this-package) section, code efficiency isn't the only
variable at play. it is **easy to understand**, **easily scalable** and **very simple to modify** for your need.
It was designed with **research and education** in mind.

## Getting started

Install with `pip` or get the [code](https://github.com/DCC-Lab/PyTissueOptics) from GitHub. If you're having trouble installing,
please [read the documentation](https://pytissueoptics.readthedocs.io/en/latest/).

```shell
pip install pytissueoptics
```
To launch a simple simulation, follow these steps.
1. Import the `pytissueoptics` module
2. Define the following objects:
    - `scene`: a `RayScatteringScene` object, which defines the scene and the optical properties of the media. This objects takes in a list of `Solid` as its argument. These `Solid` will have a `ScatteringMaterial` and a position. This is clear in the example code below.
    - `source`: a `Source` object, which defines the source of photons
    - `logger`: a `Logger` object, which logs the simulation progress
    - `stats`: a `Stats` object, which computes the statistics of the simulation and displays the results
3. propagate the photons in your `scene` with `source.propagate`.
4. display the results by calling the appropriate method from your `stats` object.

Here's what it might look like:
```python
from pytissueoptics import *

 
 myMaterial1 = ScatteringMaterial(mu_s=3.0, mu_a=1.0, g=0.8, n=1.5)

 cuboid = Cuboid(a=1, b=3, c=1, position=Vector(2, 0, 0), material=myMaterial1)
 myCustomScene = RayScatteringScene([cuboid])

 logger = Logger()
 source = PencilSource(position=Vector(-3, 0, 0), direction=Vector(1, 0, 0), N=1000)
 source.propagate(myCustomScene, logger)

 stats = Stats(logger, source, myCustomScene)
 stats.showEnergy3D()
```
For more details on how to use this package for your own research, please refer to the [documentation](https://pytissueoptics.readthedocs.io/en/latest/).

Also, you can check out the `pytissueoptics/example` folder for more examples on how to use the package.


## Why use this package
It may be slow, but speed is more than code performance: anyone with little to no experience can simulate
something instantly instead of having to understand C, C++ or, GPU code. With this package,
you can quickly build your simulation in minutes and get your results in a few hours, instead of learning C
(a few weeks?), learn to work with compiled code (a few days? libraries anyone?) and finally modify the C code written
by someone else (days? weeks?). Considering this, the overall speed to be concerned about is "the time it takes to get
an answer", not necessarily "the time it takes to run 100,000 photons". It is fairly reasonable to imagine you could
start a calculation in Python, run it overnight and get an answer the next day after a few hours of calculations. This
is the solution that the CPU-based portion of this package offers you.

Therefore, the whole point is the following: this code is perfect for quickly prototyping a small calculation,
and then determine if you need performance or not. For many things, you actually don't.

### Advantages
However, there are advantages:

1. It is extremely simple to understand and to use.
2. It can be used for teaching tissue optics.
3. It can be used for teaching object-oriented programming for those not familiar with it.
5. It is fairly easy to modify for your own purpose. Many modifications do not even require to subclass.

### Known Limitations
There are some limitations as of now.

1. It uses Henyey-Greenstein approximation for scattering direction because it is sufficient most of the time.
2. Reflections are specular, which does not accounts for the roughness of materials. It is planned to implement Bling-Phong reflection model in a future release.
2. It is approximately 50x slower than the well-known code [MCML](https://omlc.org/software/mc/mcml/) on the same machine. However, this will be accounted for when photons intersections will be coded in OpenCL in a future release.

## Acknowledgment
This package was first inspired by the standard, tested, and loved [MCML from Wang, Jacques and Zheng](https://omlc.org/software/mc/mcpubs/1995LWCMPBMcml.pdf) , itself based on [Prahl](https://omlc.org/~prahl/pubs/abs/prahl89.html) and completely documented, explained, dissected by [Jacques](https://omlc.org/software/mc/) and [Prahl](https://omlc.org/~prahl/pubs/abs/prahl89.html). This would not be possible without the work of these pionneers.
