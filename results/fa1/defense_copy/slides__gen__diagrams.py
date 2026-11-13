import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, FancyArrowPatch, Circle
from matplotlib import font_manager as fm
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
plt.rcParams.update({'font.family':'Inter','font.size':15})
OUT='/tmp/claude-0/-home-claude/3a874df3-3a87-50a5-adf3-824bd0eda443/scratchpad/assets/'
P='#3D2A4D'; PA='#8C5AA6'; T='#146F70'; O='#C8693A'; G='#8A7F96'; L='#F3EFF6'; LG='#CFC3DA'
rng=np.random.default_rng(7)

# A: neuron raster normal vs synchronous
fig,axs=plt.subplots(2,2,figsize=(12,5.2),gridspec_kw={'height_ratios':[3,1]},dpi=200)
t=np.linspace(0,2,2000)
for col,(title,sync) in enumerate([('Normal: neurons fire independently',False),('Seizure: excessive, synchronous firing',True)]):
    ax=axs[0,col]; tot=np.zeros_like(t)
    for i in range(12):
        if sync:
            sp=np.concatenate([np.arange(0.05,2,0.125)+rng.normal(0,0.008,16)])
            c=O
        else:
            sp=np.sort(rng.uniform(0,2,rng.integers(5,10))); c=P
        ax.vlines(sp,i+0.15,i+0.85,color=c,lw=2.2)
        for s in sp: tot+=np.exp(-((t-s)/0.012)**2)
    ax.set_xlim(0,2); ax.set_ylim(0,12); ax.axis('off'); ax.set_title(title,fontsize=19,color=(O if sync else P),loc='left',fontweight='bold')
    ax2=axs[1,col]; ax2.plot(t,tot,color=(O if sync else P),lw=1.6); ax2.set_ylim(0,13); ax2.axis('off')
    ax2.text(0,11.5,'summed activity (what the scalp sees)',fontsize=14,color=G)
fig.text(0.995,0.01,'schematic',ha='right',fontsize=12,color=G)
plt.tight_layout(); plt.savefig(OUT+'d_raster.png',transparent=False,facecolor='white'); plt.close()

# B: long recording strip
fig,ax=plt.subplots(figsize=(16,2.2),dpi=200)
n=6000; x=np.arange(n)
for k in range(3):
    y=np.cumsum(rng.normal(0,1,n)); y=y-np.convolve(y,np.ones(200)/200,'same'); y=y/np.std(y)*0.28+k
    ax.plot(x,y,color=LG,lw=0.7)
for s,w in [(1450,25),(4120,18)]:
    ax.axvspan(s,s+w,color=O,alpha=0.95)
for d,xx in enumerate([0,2000,4000]):
    ax.axvline(xx,color=G,lw=1,ls=':'); ax.text(xx+30,2.55,f'Day {d+1}',fontsize=16,color=G)
ax.set_xlim(0,n); ax.set_ylim(-0.6,2.9); ax.axis('off')
plt.tight_layout(pad=0.2); plt.savefig(OUT+'d_strip.png',facecolor='white'); plt.close()

# C: GAE architecture
fig,ax=plt.subplots(figsize=(16,6.6),dpi=200); ax.set_xlim(0,160); ax.set_ylim(0,66); ax.axis('off')
# input graph
cx,cy,r=17,36,13; ang=np.linspace(0,2*np.pi,18,endpoint=False)
pts=np.c_[cx+r*np.cos(ang),cy+r*np.sin(ang)]
pairs=set()
while len(pairs)<30:
    a,b=sorted(rng.choice(18,2,replace=False)); pairs.add((a,b))
for a,b in pairs: ax.plot(*zip(pts[a],pts[b]),color=LG,lw=1.6,zorder=1)
for i,p in enumerate(pts): ax.add_patch(Circle(p,1.5,color=(PA if i==4 else P),zorder=2))
ax.text(cx,17,'Graph of one 4 s window',ha='center',fontsize=17,fontweight='bold',color=P)
ax.text(cx,12.5,'18 channels · 30 strongest edges',ha='center',fontsize=14,color=G)
ax.text(cx,9,'30 features per channel',ha='center',fontsize=14,color=G)
def arrow(x0,y0,x1,y1,c=G): ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=22,color=c,lw=2.2))
arrow(33,36,40,36)
# encoder trapezoids
ax.add_patch(Polygon([[41,22],[41,50],[53,45],[53,27]],closed=True,color=PA,alpha=0.9))
ax.text(47,36,'Graph\nconv',ha='center',va='center',fontsize=15,color='white',fontweight='bold')
ax.text(47,18.5,'30 → 64',ha='center',fontsize=14,color=P)
ax.add_patch(Polygon([[55,27],[55,45],[66,40.5],[66,31.5]],closed=True,color=PA,alpha=0.75))
ax.text(60.5,36,'Graph\nconv',ha='center',va='center',fontsize=14,color='white',fontweight='bold')
ax.text(60.5,23.5,'64 → 16',ha='center',fontsize=14,color=P)
ax.text(53.5,55,'ENCODER',ha='center',fontsize=15,color=PA,fontweight='bold')
arrow(67,36,72,36)
# latent matrix
Z=rng.random((18,16))
for i in range(18):
    for j in range(16):
        ax.add_patch(plt.Rectangle((73+j*0.95,52-i*1.75),0.95,1.75,color=plt.cm.BuGn(0.25+0.6*Z[i,j]),lw=0))
ax.add_patch(plt.Rectangle((73,52-4*1.75),16*0.95,1.75,fill=False,ec=O,lw=2.6))
ax.text(80.6,57.5,'LATENT  Z',ha='center',fontsize=15,color=T,fontweight='bold')
ax.text(80.6,15.5,'one 16-number code\nper channel',ha='center',fontsize=14,color=T)
ax.text(90.5,45.6,'◀ channel code',fontsize=13,color=O,va='center')
# decoders
arrow(89.5,46,104,52); arrow(89.5,26,104,20)
ax.text(112.5,61,'DECODERS',ha='center',fontsize=15,color=G,fontweight='bold')
ax.add_patch(FancyBboxPatch((104,47),17,10,boxstyle='round,pad=0.4',fc=L,ec=LG,lw=1.5))
ax.text(112.5,52,'Inner product\n$ZZ^{\\top}$',ha='center',va='center',fontsize=14,color=P)
ax.add_patch(FancyBboxPatch((104,15),17,10,boxstyle='round,pad=0.4',fc=L,ec=LG,lw=1.5))
ax.text(112.5,20,'Small MLP\n16 → 32 → 12',ha='center',va='center',fontsize=14,color=P)
arrow(122,52,127,52); arrow(122,20,127,20)
A=rng.random((10,10)); A=(A+A.T)/2
ax.imshow(A,cmap='Purples',extent=(128,138,47,57),zorder=2)
ax.text(139.5,52,'rebuilt\ncoupling',va='center',fontsize=14,color=P)
for k,h in enumerate(rng.random(8)*7+2):
    ax.add_patch(plt.Rectangle((128+k*1.25,15),1.0,h,color=PA))
ax.text(139.5,20,'rebuilt\nfeatures',va='center',fontsize=14,color=P)
ax.add_patch(FancyBboxPatch((100,31),56,10,boxstyle='round,pad=0.4',fc='white',ec=T,lw=1.8))
ax.text(128,36,'Trained on seizure-free windows only:\nloss = coupling error + 0.1 × feature error',ha='center',va='center',fontsize=14,color=T)
ax.set_aspect('auto')
plt.savefig(OUT+'d_gae.png',facecolor='white',bbox_inches='tight',pad_inches=0.15); plt.close()

# D: latent reference schematic
fig,ax=plt.subplots(figsize=(10,7),dpi=200)
m1=rng.multivariate_normal([0,0],[[1,0.3],[0.3,0.6]],260)
m2=rng.multivariate_normal([3.3,2.0],[[0.25,0.05],[0.05,0.2]],60)
ax.scatter(m1[:,0],m1[:,1],s=16,color=P,alpha=0.55,lw=0)
ax.scatter(m2[:,0],m2[:,1],s=22,color=PA,alpha=0.85,lw=0)
ax.add_patch(Ellipse((-0.2,-0.1),5.4,3.6,angle=20,fill=False,ec=G,lw=2.2,ls='--'))
ax.add_patch(Ellipse((1.3,0.85),8.4,5.6,angle=22,fill=False,ec=T,lw=3))
ax.scatter([6.3],[-1.6],s=420,marker='*',color=O,zorder=5)
ax.add_patch(FancyArrowPatch((1.0,0.6),(6.1,-1.5),arrowstyle='-|>',mutation_scale=20,color=O,lw=2,ls='-'))
ax.text(3.6,-2.75,'distance from this\npatient’s normal',fontsize=15,color=O,ha='center')
ax.text(6.3,-1.0,'seizure',fontsize=16,color=O,ha='center',fontweight='bold')
ax.text(6.25,3.3,'high-amplitude\nbut normal state',fontsize=14,color=PA,ha='center')
ax.text(-3.85,-3.15,'normal learned from other patients',fontsize=13,color=G,va='bottom')
ax.text(-3.1,4.2,'reference = this patient’s\nwhole recording',fontsize=15,color=T,fontweight='bold')
ax.set_xlim(-4,7.6); ax.set_ylim(-3.3,5.2); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_color(LG)
ax.set_xlabel('channel code (16 numbers, shown in 2D)',color=G,fontsize=14)
ax.text(7.5,-3.2,'schematic',ha='right',va='bottom',fontsize=12,color=G)
plt.tight_layout(); plt.savefig(OUT+'d_reference.png',facecolor='white'); plt.close()

# E: spatial scales
fig,ax=plt.subplots(figsize=(10,4.6),dpi=200)
v=np.sort(np.abs(rng.normal(0,1.2,18))+np.r_[np.linspace(5,1,9),np.zeros(9)])[::-1]
cols=[LG]*18
for k,c in [(5,O),(8,O),(11,O)]: cols[k]=c
ax.bar(range(1,19),v,color=cols,width=0.75)
for k,lab in [(6,'6th'),(9,'9th'),(12,'12th')]:
    ax.text(k,v[k-1]+0.25,lab,ha='center',fontsize=15,color=O,fontweight='bold',bbox=dict(fc='white',ec='none',pad=1))
ax.axhline(v.mean(),color=T,ls='--',lw=2); ax.text(18.4,v.mean()+0.2,'mean',color=T,fontsize=15,ha='right',fontweight='bold')
ax.set_xticks([1,6,9,12,18]); ax.set_xlabel('channels of one window, ranked by anomaly',fontsize=14,color=G)
ax.set_ylabel('channel anomaly',fontsize=14,color=G)
for s in ['top','right']: ax.spines[s].set_visible(False)
for s in ['left','bottom']: ax.spines[s].set_color(LG)
ax.tick_params(colors=G); ax.text(18.5,v.max(),'schematic',ha='right',va='top',fontsize=12,color=G)
plt.tight_layout(); plt.savefig(OUT+'d_scales.png',facecolor='white'); plt.close()

# F: idea minis
def mini(name,draw):
    fig,ax=plt.subplots(figsize=(3.2,2.2),dpi=200); ax.axis('off'); draw(ax); plt.tight_layout(pad=0.1); plt.savefig(OUT+name,facecolor='white'); plt.close()
def g(ax):
    ang=np.linspace(0,2*np.pi,8,endpoint=False); p=np.c_[np.cos(ang),np.sin(ang)]
    for a,b in [(0,3),(1,5),(2,6),(4,7),(0,5),(3,6),(1,2)]: ax.plot(*zip(p[a],p[b]),color=LG,lw=2)
    ax.scatter(p[:,0],p[:,1],s=160,color=P,zorder=3); ax.scatter([p[2,0]],[p[2,1]],s=160,color=O,zorder=4); ax.set_aspect('equal')
def ae(ax):
    ax.add_patch(Polygon([[0,0],[0,4],[2.2,2.8],[2.2,1.2]],color=PA)); ax.add_patch(Polygon([[2.8,1.2],[2.8,2.8],[5,4],[5,0]],color=LG))
    ax.add_patch(plt.Rectangle((2.25,1.2),0.5,1.6,color=T)); ax.set_xlim(-0.2,5.2); ax.set_ylim(-0.2,4.2)
def cl(ax):
    m=rng.multivariate_normal([0,0],[[1,0.3],[0.3,0.5]],120); ax.scatter(m[:,0],m[:,1],s=10,color=P,alpha=0.6)
    ax.add_patch(Ellipse((0,0),5,3,angle=18,fill=False,ec=T,lw=2.5)); ax.scatter([3.4],[-1.6],marker='*',s=300,color=O); ax.set_xlim(-3,4.2); ax.set_ylim(-2.4,2.4)
def cp(ax):
    t=np.arange(200); y=rng.normal(0,0.25,200); y[80:130]+=2.2; ax.plot(t,y,color=P,lw=1.6)
    for x in [80,130]: ax.axvline(x,color=O,lw=3)
    ax.axvspan(80,130,color=O,alpha=0.12)
for n,f in [('m_graph.png',g),('m_ae.png',ae),('m_ref.png',cl),('m_cpd.png',cp)]: mini(n,f)
print('ok')
