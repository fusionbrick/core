import math,sys
th=120; h=math.radians(th/2); s,c=math.sin(h),math.cos(h)
alen=4*math.tan(h)
sgn=int(sys.argv[1]); hz=float(sys.argv[2])
dA=(-s, c,0); dB=(-s,-c,0)
nA=( s,-c,0); nB=( s, c,0)
uA=( c, s,0); uB=( c,-s,0)
pA=[alen*k for k in dA]; pB=[alen*k for k in dB]
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def emit(name,u,nv,port):
    z=[sgn*k for k in nv]
    y=cross(z,u); M=[[u[i],y[i],z[i]] for i in range(3)]
    hole=(4,12,hz)
    img=[sum(M[r][k]*hole[k] for k in range(3)) for r in range(3)]
    T=[port[k]-img[k] for k in range(3)]
    rows=[f"[{M[r][0]:.6f},{M[r][1]:.6f},{M[r][2]:.6f},{T[r]:.6f}]" for r in range(3)]
    return f'module {name}() {{ multmatrix([{",".join(rows)},[0,0,0,1]]) import("plate-3x3-h4.stl"); }}'
print('module nd() { import("node-120.stl"); }')
print(emit("plA",uA,nA,pA)); print(emit("plB",uB,nB,pB))
print('mode=0;')
print('if(mode==0){color("silver")plA();color("silver")plB();color("green")nd();}')
print('if(mode==1)intersection(){nd();plA();}')
