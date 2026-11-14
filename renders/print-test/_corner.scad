module wd(){ import("/Volumes/SSD/Projects/opensource/FusionBrick/renders/corner/corner-120.stl"); }
module plA(){ multmatrix([[0.500000,-0.000000,0.866025,-11.464102],[0.866025,0.000000,-0.500000,2.000000],[0.000000,1.000000,0.000000,-12.000000],[0,0,0,1]]) import("/Volumes/SSD/Projects/opensource/FusionBrick/renders/print-test/plate-3x3-h4.stl"); }
module plB(){ multmatrix([[0.500000,0.000000,0.866025,-11.464102],[-0.866025,0.000000,0.500000,-2.000000],[0.000000,-1.000000,0.000000,12.000000],[0,0,0,1]]) import("/Volumes/SSD/Projects/opensource/FusionBrick/renders/print-test/plate-3x3-h4.stl"); }
mode=0;
if(mode==0){color("silver")plA();color("silver")plB();color("green")wd();}
if(mode==1)intersection(){plA();plB();}
