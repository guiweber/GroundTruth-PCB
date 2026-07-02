# GroundTruth - PCB Analysis
Ground Truth is a PCB analysis tool for inspecting, analyzing and annotating PCB images (front and back) side by side in synchronized views.

Note that the app is in early development and thus not feature complete but rich in bugs. At this point, savefile compatibility is not guaranteed when upgrading.

Contributions and pull requests are welcome! If you have a larger feature in mind please open an issue so we can discuss the implementation before you start.

## Running the app
- Clone the repo
- Create a python 3.14 virtual environment
- Install the dependencies from requirements.txt
- Run main.py

## Tips

- Align your images in GIMP using the perspective transform before loading them in GroundTruth. Make sure the sides of the PCB are well aligned with the borders of the image.
- Read the help file (displayed when the first files are loaded) to learn about how to use the app.

## Roadmap / Todo

- Add warning about savefile trust/safety
- Improve line selection
  - Show where the segment joints can be selected
  - Adjust the selection radius based on zoom level/pixel density?
- Add box annotation tool
- Make keybindings user-editable via a config file
- Make annotation transparency uniform within a layer instead of additive
- Add back arrow annotation subtype
- Fix rotate functionality
- Add tests
- investigate the possibility of adding automatic netlist/schematic extraction and export to kicad format