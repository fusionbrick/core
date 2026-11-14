use <../../impl/openscad/pin.scad>
dl = 40 * sqrt(2);
echo(str("len = ", dl));
for (py = [-2.5, 62.5])
    translate([62.5, py, 42.5]) rotate([0,225,0]) rotate([90,0,0])
        pin(top="none", bottom="none", sides="none", ends="pin", len=dl);
