import sys, wave, json, numpy as np
from pathlib import Path
sys.path.insert(0,"engine")
from audio import SR, riser, boom, kick, snare, normalize
P=Path("projects/nihilism")
tim=json.loads((P/"timing.json").read_text(encoding="utf-8"))
DROP=tim["lines"][14]["start"]; DROP2=tim["lines"][15]["start"]; THESIS=tim["lines"][17]["start"]
def read(p):
    with wave.open(str(p),"rb") as f:
        a=np.frombuffer(f.readframes(f.getnframes()),dtype="<i2").astype(np.float32)/32768
        return a.reshape(-1,f.getnchannels()).T
def write(p,x):
    with wave.open(str(p),"wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(x.T,-1,1)*32767).astype("<i2").tobytes())
def add(buf,sig,t,g=1):
    i=int(t*SR); n=min(len(sig),buf.shape[1]-i)
    if n>0: buf[:,i:i+n]+=sig[:n]*g
v=read(P/"voice.wav"); b=read(P/"bgm_ref.wav")
n=v.shape[1]; b=b[:,:n]
if b.shape[1]<n: b=np.pad(b,((0,0),(0,n-b.shape[1])))
# BGM: gradual duck, tiny breath, restore on drop
gain=np.ones(n,float)
def ramp(a,bb,ga,gb):
    i0,i1=int(a*SR),int(bb*SR)
    if i1>i0: gain[i0:i1]=np.linspace(ga,gb,i1-i0)
ramp(53.8,55.2,1.0,0.72); ramp(55.2,57.40,0.72,0.38); ramp(57.40,57.58,0.38,0.03)
gain[int((DROP-0.04)*SR):int((DROP+1.0)*SR)]=1.0
# lift accents only, no vacuum at thesis
gain[int((THESIS-0.02)*SR):int((THESIS+0.6)*SR)]=1.0
# groove into the drop: 8th-note kick + snare roll
sfx=np.zeros((2,n))
for tt in np.arange(53.8, DROP-0.05, 60/112/2):
    add(sfx,kick(.22,115,52),tt,.16)
for tt in np.arange(DROP-1.5, DROP-0.04, .06):
    g=.06+.28*(tt-(DROP-1.5))/1.5
    add(sfx,snare(.1,220),tt,g)
add(sfx,riser(1.6),DROP-1.6,.30)
add(sfx,boom(1.2,46),DROP-0.04,.62)
add(sfx,boom(.7,55),DROP2,.34)
add(sfx,boom(.7,52),THESIS,.30)
# micro breath: only 0.17s, then hit
vac=np.ones(n); i0,i1=int(57.42*SR),int(57.60*SR); vac[i0:i1]=.02
b=b*vac[None,:]; sfx=sfx*vac[None,:]
mix=v*1.12 + b*.62*gain + sfx*.85
mix=np.tanh(mix*1.05)/np.tanh(1.05); mix=normalize(mix,.92)
write(P/"mix_v3_voice.wav",mix)
mix2=b*.75*gain + sfx*.95
mix2=np.tanh(mix2*1.05)/np.tanh(1.05); mix2=normalize(mix2,.92)
write(P/"mix_v3_novoice.wav",mix2)
print("DROP",DROP,"DROP2",DROP2,"THESIS",THESIS,"dur",n/SR)
