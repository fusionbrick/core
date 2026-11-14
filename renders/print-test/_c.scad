module nd() { import("node-120.stl"); }
module plA() { multmatrix([[0.500000,0.000000,-0.866025,-4.535898],[0.866025,0.000000,0.500000,-2.000000],[0.000000,-1.000000,0.000000,12.000000],[0,0,0,1]]) import("plate-3x3-h4.stl"); }
module plB() { multmatrix([[0.500000,0.000000,-0.866025,-4.535898],[-0.866025,0.000000,-0.500000,2.000000],[0.000000,1.000000,0.000000,-12.000000],[0,0,0,1]]) import("plate-3x3-h4.stl"); }
mode=0;
if(mode==0){color("silver")plA();color("silver")plB();color("green")nd();}
if(mode==1)intersection(){nd();plA();}
