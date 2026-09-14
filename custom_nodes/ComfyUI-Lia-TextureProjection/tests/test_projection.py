import torch, math, time, sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import projection as P

# UV sphere with a spherical UV map
def uv_sphere(nu=64, nv=32, r=0.8):
    vs, uvs = [], []
    for j in range(nv+1):
        th = math.pi*j/nv
        for i in range(nu+1):
            ph = 2*math.pi*i/nu
            vs.append([r*math.sin(th)*math.sin(ph), r*math.cos(th), r*math.sin(th)*math.cos(ph)])
            uvs.append([i/nu, 1-j/nv])
    fs=[]
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i; b=a+1; c=a+nu+1; d=c+1
            fs.append([a,c,b]); fs.append([b,c,d])
    return torch.tensor(vs), torch.tensor(fs, dtype=torch.long), torch.tensor(uvs)

v,f,uv = uv_sphere()
# ground-truth colour = function of world position (so any view can be checked)
def gt_color(p):  # p [...,3]
    return torch.stack([(p[...,0]/0.8*0.5+0.5), (p[...,1]/0.8*0.5+0.5), (p[...,2]/0.8*0.5+0.5)],-1).clamp(0,1)

t=time.time()
az=[0,90,180,270]; el=[0,0,0,0]
center,extent=P.bbox_center_extent(v); half=float(extent.max())*0.5*1.1
imgs=[]; masks=[]
for a,e in zip(az,el):
    rv=P.render_view(v,f,center,half,a,e,256)
    img=gt_color(rv['position']); img[~rv['mask']]=0
    imgs.append(img); masks.append(rv['mask'].float())
    # check face-normal sanity: front view centre pixel normal should point to camera (z>0)
    c=rv['normal'][128,128]; assert c[2]>0.9, (a,c)
imgs=torch.stack(imgs); masks=torch.stack(masks)
print('render ok', time.time()-t)

t=time.time()
tex,w,cover=P.project_texture(v,f,uv,imgs,masks,az,el,512,cos_power=4.0)
print('project', time.time()-t, 'cover',cover.float().mean().item(), 'weighted',(w>0).float().mean().item())
pos,nrm,cv=P.texel_geometry(v,f,uv,512)
gt=gt_color(pos)
err=(tex-gt).abs()[w>0].mean().item()
print('mean abs err on covered texels', err)
assert err<0.03, err
# top/bottom poles unseen with elevation 0? they are grazing; check fill
tex2=P.fill_uncovered(tex,w,cover)
print('uncovered before',((cover)&(w<=0)).sum().item(),'after fill black texels',(cover & (tex2.sum(-1)==0)).sum().item())
print('ALL OK')
