import torch, math, time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import projection as P
from test_projection import uv_sphere, gt_color

v, f, uv = uv_sphere()
center, extent = P.bbox_center_extent(v); half = float(extent.max()) * 0.5 * 1.1
pos, nrm, cv = P.texel_geometry(v, f, uv, 512); gt = gt_color(pos)
tex = None; w = None
az = [0, 180, 90, 270, 0, 0]; el = [0, 0, 0, 0, 60, -60]
t = time.time()
for a, e in zip(az, el):
    img, missing, m, nrm_img = P.render_textured(v, f, uv, tex, w, a, e, 256)
    rv = P.render_view(v, f, center, half, a, e, 256)
    paint = gt_color(rv['position']); paint[~rv['mask']] = 1
    comp = torch.where(missing[..., None], paint, img)          # "inpaint" só do que falta
    tex, w, cover, st = P.accumulate_view(v, f, uv, tex, w, comp, rv['mask'].float(), a, e, texture_size=512)
    print(a, e, 'missing px', int(missing.sum()), st)
    if a == 180 and e == 0:
        assert st['overlap'] < 5000, 'costas nao deveriam sobrepor muito a frente'
err = (tex - gt)[w > 0].abs().mean().item(); print('seq err', err, time.time() - t); assert err < 0.03
img, missing, m, _ = P.render_textured(v, f, uv, tex, w, 30, 10, 256)
print('final missing', int(missing.sum()), 'of', int(m.sum())); assert missing.sum() < 0.02 * m.sum()
# color_match: vista com ganho errado é corrigida
bad = (paint * 0.7).clamp(0, 1)
tex2, w2, _, st2 = P.accumulate_view(v, f, uv, tex, w, bad, m.float(), 30, 10, texture_size=512)
print('gain', st2['gain']); assert all(1.15 <= g <= 1.2 for g in st2['gain'])  # clamp 1.2
err2 = (tex2 - gt)[w2 > 0].abs().mean().item(); print('err after bad view w/ color_match', err2); assert err2 < 0.08
print('ALL OK')
# v82: zoom/offset (vista do rosto) e replace (passe de correção)
img_z, miss_z, m_z, _ = P.render_textured(v, f, uv, tex, w, 0, 0, 256, zoom=3.0, offset_y=0.3)
assert m_z.float().mean() > 0.5, 'com zoom 3 a esfera deve encher o quadro'
rvz = P.render_view(v, f, *(lambda c, h, e: (c, h))(*P.view_frame(v, 1.1, 3.0, 0.3)), 0, 0, 256)
paint_z = gt_color(rvz['position']); paint_z[~rvz['mask']] = 1
tz, wz, _, stz = P.accumulate_view(v, f, uv, tex, w, paint_z, m_z.float(), 0, 0, texture_size=512, zoom=3.0, offset_y=0.3)
errz = (tz - gt)[wz > 0].abs().mean().item(); print('zoom err', errz, stz['overlap']); assert errz < 0.03 and stz['overlap'] > 0
bad2 = torch.zeros_like(paint)  # vista toda preta
t_avg, _, _, _ = P.accumulate_view(v, f, uv, tex, w, bad2, m.float(), 30, 10, texture_size=512, color_match=False)
t_rep, w_rep, _, st_rep = P.accumulate_view(v, f, uv, tex, w, bad2, m.float(), 30, 10, texture_size=512, color_match=False, replace=True)
seen = st_rep['overlap'] > 0
d_avg = (t_avg - gt).abs().mean().item(); d_rep = (t_rep - gt).abs().mean().item()
print('replace: avg diff', d_avg, 'replace diff', d_rep); assert d_rep > d_avg * 1.5, 'replace deve sobrescrever mais que a média'
print('ZOOM/REPLACE OK')
