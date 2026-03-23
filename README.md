# DTAT

![Project logo](https://github.com/NASA-JPL-Teamtools-Studio/teamtools_documentation/blob/main/docs/images/tts_image_artifacts/dtat.png)

## About Teamtools Studio

Teamtools Studio Utilities is part of JPL's Teamtools Studio (TTS).

TTS is an effort originated in JPL's Planning and Execution section to centralize shared repositories across missions. This benefits JPL by reducing cost through reducing duplicated code, collaborating across missions, and unifying standards for development and design across JPL.

Although Planning and Execution is primarily concerned with flight operations, the TTS suite has been generalized and atomized to the point where many of these tools are applicable during other mission phases and even in non-spaceflight contexts. Through our work flying space missions, we hope to provide tools to the open source community that have utility in data analysis or planning for any complex system where failure is not an option.

For more infomation on how to contribute, and how these libraries form a complete ecosystem for high reliability data analysis, see the [Full TTS Documentation](https://nasa-jpl-teamtools-studio.github.io/teamtools-documentation/).

## What is DTAT?

### Overview

DTAT is the TTS solution to complex plotting. It is largely an extension of Plotly. Although we love Plotly and use it often,
one of the problems with such libraries is that they are so open ended that they take significant expertise in order to
create maintainable, reusable code.

DTAT wraps Plotly to handle common plotting issues with a more user friendly interface. It is not as flexible as raw Plotly,
but it is significantly easier to grab out of the box and use.

Furthermore, there are some known challenges with Plotly that every user hits and average developers struggle to overcome. DTAT
is a place where we can encode lessons learned about these limitations so not every user who wants to make a plot needs to
overcome them.

### Projects Currently Supported

* Europa Clipper
* Mars Sample Return
* Orbiting Carbon Observatory 2
* Mars 2020

## Architecture

### TTS dependencies

* TTS Utilities
