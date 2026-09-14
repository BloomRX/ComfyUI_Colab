# -*- coding: utf-8 -*-
"""Núcleo matemático da projeção de texturas — torch puro, sem dependências de
renderizadores externos.

Escrito do zero (clean-room) para o projeto ComfyUI_Colab. Não deriva de
nvdiffrast, Hunyuan3D, LumiTex nem de nenhum pacote de terceiros; usa só
torch e numpy. Licença: MIT (ver LICENSE na raiz do pacote).

Convenções
----------
* Mesh no espaço do próprio GLB (Y para cima, como o three.js / SaveGLB do core).
* Câmeras **ortográficas** numa órbita ao redor do centro do bounding box:
  ``azimuth`` 0 = frente (câmera em +Z olhando para -Z), 90 = lado esquerdo do
  personagem (câmera em +X), 180 = costas, 270 = lado direito. ``elevation`` em
  graus, positivo = câmera acima.
* Imagens no formato ComfyUI: ``[B, H, W, C]`` float 0..1.
* UV: origem no canto inferior esquerdo (glTF/ OpenGL). O ``UnwrapMesh`` do
  core grava UV nessa convenção; a textura de saída aqui segue o mesmo
  padrão que o ``BakeTextureFromVoxel`` produz (linha 0 = v=0), para que
  ``ApplyTextureToMesh`` + ``SaveGLB`` funcionem sem flip.

Pipeline
--------
1. ``rasterize_uv``: para cada texel do atlas, qual triângulo e coordenadas
   baricêntricas → posição 3D e normal do texel (``texel_geometry``).
2. ``orbit_camera``: base ortonormal (forward/right/up) e escala da vista.
3. ``render_view``: z-buffer ortográfico por rasterização de triângulos em
   torch (tiles); dá profundidade, máscara e normais/posições por pixel.
   É o que gera as "condições" para o gerador de imagem.
4. ``project_texture``: para cada vista, projeta cada texel na imagem, testa
   visibilidade contra o z-buffer daquela vista, pesa por cos^k(normal·câmera),
   acumula média ponderada; ao fim dilata as bordas.
"""
from __future__ import annotations

import math
from typing import Sequence

import torch
import torch.nn.functional as F


# --------------------------------------------------------------------------- #
# Geometria básica
# --------------------------------------------------------------------------- #
def face_normals(verts: torch.Tensor, faces: torch.Tensor) -> torch.Tensor:
    tri = verts[faces]                                    # [F,3,3]
    n = torch.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0], dim=-1)
    return F.normalize(n, dim=-1, eps=1e-12)


def vertex_normals(verts: torch.Tensor, faces: torch.Tensor) -> torch.Tensor:
    """Normais por vértice ponderadas por área (soma das normais de face não normalizadas)."""
    tri = verts[faces]
    fn = torch.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0], dim=-1)  # área*2 embutida
    vn = torch.zeros_like(verts)
    for k in range(3):
        vn.index_add_(0, faces[:, k], fn)
    return F.normalize(vn, dim=-1, eps=1e-12)


def bbox_center_extent(verts: torch.Tensor):
    lo, hi = verts.amin(0), verts.amax(0)
    return (lo + hi) * 0.5, (hi - lo)


# --------------------------------------------------------------------------- #
# 1. Rasterização do atlas UV
# --------------------------------------------------------------------------- #
@torch.no_grad()
def rasterize_uv(uvs: torch.Tensor, faces: torch.Tensor, size: int, tile: int = 128):
    """Rasteriza os triângulos no espaço UV.

    Retorna ``face_idx [S,S] long``, ``bary [S,S,3]``, ``cover [S,S] bool``.
    Linha 0 da imagem corresponde a v = 0 (origem embaixo), coluna 0 a u = 0.
    Texel é coberto se o seu centro cai dentro do triângulo (com epsilon para
    não deixar buracos nas arestas compartilhadas).
    """
    dev = uvs.device
    S = int(size)
    face_idx = torch.zeros((S, S), dtype=torch.long, device=dev)
    bary = torch.zeros((S, S, 3), dtype=torch.float32, device=dev)
    cover = torch.zeros((S, S), dtype=torch.bool, device=dev)
    if faces.numel() == 0:
        return face_idx, bary, cover

    p = (uvs.float() * S)[faces]                           # [F,3,2] em pixels
    x0, y0 = p[:, 0, 0], p[:, 0, 1]
    x1, y1 = p[:, 1, 0], p[:, 1, 1]
    x2, y2 = p[:, 2, 0], p[:, 2, 1]
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    ok = den.abs() > 1e-12
    xmin = torch.minimum(torch.minimum(x0, x1), x2).floor().clamp(0, S - 1)
    xmax = torch.maximum(torch.maximum(x0, x1), x2).ceil().clamp(0, S - 1)
    ymin = torch.minimum(torch.minimum(y0, y1), y2).floor().clamp(0, S - 1)
    ymax = torch.maximum(torch.maximum(y0, y1), y2).ceil().clamp(0, S - 1)
    eps = 2e-3  # em baricêntricas; cobre arestas compartilhadas

    for ty in range(0, S, tile):
        ty1 = min(ty + tile, S)
        for tx in range(0, S, tile):
            tx1 = min(tx + tile, S)
            sel = ok & (xmin < tx1) & (xmax >= tx) & (ymin < ty1) & (ymax >= ty)
            if not bool(sel.any()):
                continue
            idx = sel.nonzero(as_tuple=True)[0]
            ys = torch.arange(ty, ty1, device=dev, dtype=torch.float32) + 0.5
            xs = torch.arange(tx, tx1, device=dev, dtype=torch.float32) + 0.5
            yy, xx = torch.meshgrid(ys, xs, indexing="ij")
            X0, Y0 = x0[idx][:, None, None], y0[idx][:, None, None]
            X1, Y1 = x1[idx][:, None, None], y1[idx][:, None, None]
            X2, Y2 = x2[idx][:, None, None], y2[idx][:, None, None]
            D = den[idx][:, None, None]
            b0 = ((Y1 - Y2) * (xx - X2) + (X2 - X1) * (yy - Y2)) / D
            b1 = ((Y2 - Y0) * (xx - X2) + (X0 - X2) * (yy - Y2)) / D
            b2 = 1.0 - b0 - b1
            inside = (b0 >= -eps) & (b1 >= -eps) & (b2 >= -eps)        # [K,th,tw]
            if not bool(inside.any()):
                continue
            hit = inside.any(0)
            first = inside.float().argmax(0)                             # [th,tw]
            g = lambda b: b.gather(0, first[None]).squeeze(0)
            bsel = torch.stack([g(b0), g(b1), g(b2)], -1)
            face_idx[ty:ty1, tx:tx1][hit] = idx[first][hit]
            bary[ty:ty1, tx:tx1][hit] = bsel[hit]
            cover[ty:ty1, tx:tx1] |= hit
    return face_idx, bary, cover


@torch.no_grad()
def texel_geometry(verts, faces, uvs, size, vnormals=None):
    """Posição 3D e normal de cada texel coberto do atlas.

    Retorna ``pos [S,S,3]``, ``nrm [S,S,3]``, ``cover [S,S] bool``.
    """
    face_idx, bary, cover = rasterize_uv(uvs, faces, size)
    if vnormals is None:
        vnormals = vertex_normals(verts, faces)
    tri_p = verts[faces[face_idx]]                         # [S,S,3,3]
    tri_n = vnormals[faces[face_idx]]
    pos = (bary[..., None] * tri_p).sum(-2)
    nrm = F.normalize((bary[..., None] * tri_n).sum(-2), dim=-1, eps=1e-12)
    pos[~cover] = 0
    nrm[~cover] = 0
    return pos, nrm, cover


# --------------------------------------------------------------------------- #
# 2. Câmera ortográfica em órbita
# --------------------------------------------------------------------------- #
def orbit_camera(azimuth_deg: float, elevation_deg: float, device):
    """Base da câmera. Retorna (forward, right, up), cada um [3].

    azimuth 0 → câmera em +Z olhando -Z (frente do personagem, que olha para +Z).
    azimuth 90 → câmera em +X (vê o lado esquerdo do personagem).
    """
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    # posição unitária da câmera na esfera
    eye = torch.tensor([math.sin(az) * math.cos(el),
                        math.sin(el),
                        math.cos(az) * math.cos(el)], device=device, dtype=torch.float32)
    fwd = -eye
    world_up = torch.tensor([0.0, 1.0, 0.0], device=device)
    if abs(float((fwd * world_up).sum())) > 0.999:
        world_up = torch.tensor([0.0, 0.0, -1.0], device=device)
    right = F.normalize(torch.cross(fwd, world_up, dim=-1), dim=-1)
    up = torch.cross(right, fwd, dim=-1)
    return fwd, right, up


def ortho_project(points: torch.Tensor, center: torch.Tensor, fwd, right, up, half_size: float):
    """Projeta pontos [...,3] em coordenadas normalizadas [-1,1] (x, y) e profundidade.

    ``half_size`` = metade da largura/altura do quadro no espaço do mesh.
    y cresce para cima (convertido para linha de imagem depois).
    """
    d = points - center
    x = (d * right).sum(-1) / half_size
    y = (d * up).sum(-1) / half_size
    z = (d * fwd).sum(-1)              # maior = mais longe da câmera
    return x, y, z


# --------------------------------------------------------------------------- #
# 3. Render ortográfico com z-buffer (para as condições e para visibilidade)
# --------------------------------------------------------------------------- #
@torch.no_grad()
def render_view(verts, faces, center, half_size, azimuth, elevation, res: int,
                vnormals=None, tile: int = 128):
    """Z-buffer ortográfico por rasterização em tiles.

    Retorna dict com ``depth [R,R]`` (inf onde vazio), ``mask [R,R] bool``,
    ``normal [R,R,3]`` (espaço da câmera, x=right, y=up, z=para a câmera),
    ``normal_world [R,R,3]``, ``position [R,R,3]``.
    Linha 0 da imagem = topo (convenção de imagem).
    """
    dev = verts.device
    R = int(res)
    fwd, right, up = orbit_camera(azimuth, elevation, dev)
    if vnormals is None:
        vnormals = vertex_normals(verts, faces)

    x, y, z = ortho_project(verts, center, fwd, right, up, half_size)
    px = (x * 0.5 + 0.5) * R
    py = (1.0 - (y * 0.5 + 0.5)) * R                      # topo = linha 0
    P = torch.stack([px, py], -1)[faces]                  # [F,3,2]
    Z = z[faces]                                          # [F,3]

    x0, y0 = P[:, 0, 0], P[:, 0, 1]
    x1, y1 = P[:, 1, 0], P[:, 1, 1]
    x2, y2 = P[:, 2, 0], P[:, 2, 1]
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    ok = den.abs() > 1e-12
    xmin = torch.minimum(torch.minimum(x0, x1), x2).floor().clamp(0, R - 1)
    xmax = torch.maximum(torch.maximum(x0, x1), x2).ceil().clamp(0, R - 1)
    ymin = torch.minimum(torch.minimum(y0, y1), y2).floor().clamp(0, R - 1)
    ymax = torch.maximum(torch.maximum(y0, y1), y2).ceil().clamp(0, R - 1)

    depth = torch.full((R, R), float("inf"), device=dev)
    fidx = torch.full((R, R), -1, dtype=torch.long, device=dev)
    bary = torch.zeros((R, R, 3), device=dev)
    eps = 1e-4

    for ty in range(0, R, tile):
        ty1 = min(ty + tile, R)
        for tx in range(0, R, tile):
            tx1 = min(tx + tile, R)
            sel = ok & (xmin < tx1) & (xmax >= tx) & (ymin < ty1) & (ymax >= ty)
            if not bool(sel.any()):
                continue
            idx = sel.nonzero(as_tuple=True)[0]
            # processa em blocos de triângulos para limitar memória [K,th,tw]
            th, tw = ty1 - ty, tx1 - tx
            max_k = max(1, int(4e7 // (th * tw)))
            ys = torch.arange(ty, ty1, device=dev, dtype=torch.float32) + 0.5
            xs = torch.arange(tx, tx1, device=dev, dtype=torch.float32) + 0.5
            yy, xx = torch.meshgrid(ys, xs, indexing="ij")
            for s in range(0, idx.numel(), max_k):
                k = idx[s:s + max_k]
                X0, Y0 = x0[k][:, None, None], y0[k][:, None, None]
                X1, Y1 = x1[k][:, None, None], y1[k][:, None, None]
                X2, Y2 = x2[k][:, None, None], y2[k][:, None, None]
                D = den[k][:, None, None]
                b0 = ((Y1 - Y2) * (xx - X2) + (X2 - X1) * (yy - Y2)) / D
                b1 = ((Y2 - Y0) * (xx - X2) + (X0 - X2) * (yy - Y2)) / D
                b2 = 1.0 - b0 - b1
                inside = (b0 >= -eps) & (b1 >= -eps) & (b2 >= -eps)
                if not bool(inside.any()):
                    continue
                zk = Z[k]                                                    # [K,3]
                zi = b0 * zk[:, 0, None, None] + b1 * zk[:, 1, None, None] + b2 * zk[:, 2, None, None]
                zi = torch.where(inside, zi, torch.full_like(zi, float("inf")))
                zmin, arg = zi.min(0)                                        # [th,tw]
                cur = depth[ty:ty1, tx:tx1]
                better = zmin < cur
                if not bool(better.any()):
                    continue
                g = lambda b: b.gather(0, arg[None]).squeeze(0)
                bsel = torch.stack([g(b0), g(b1), g(b2)], -1)
                depth[ty:ty1, tx:tx1][better] = zmin[better]
                fidx[ty:ty1, tx:tx1][better] = k[arg][better]
                bary[ty:ty1, tx:tx1][better] = bsel[better]

    mask = fidx >= 0
    safe = fidx.clamp_min(0)
    tri_n = vnormals[faces[safe]]                                            # [R,R,3,3]
    nw = F.normalize((bary[..., None] * tri_n).sum(-2), dim=-1, eps=1e-12)
    tri_p = verts[faces[safe]]
    pw = (bary[..., None] * tri_p).sum(-2)
    # normal no espaço da câmera: (right, up, -fwd) → z aponta para a câmera
    ncam = torch.stack([(nw * right).sum(-1), (nw * up).sum(-1), (nw * -fwd).sum(-1)], -1)
    nw[~mask] = 0
    ncam[~mask] = 0
    pw[~mask] = 0
    return {"depth": depth, "mask": mask, "normal": ncam, "normal_world": nw, "position": pw,
            "fwd": fwd, "right": right, "up": up}


# --------------------------------------------------------------------------- #
# 4. Projeção das imagens de volta no atlas
# --------------------------------------------------------------------------- #
@torch.no_grad()
def project_texture(verts, faces, uvs, images: torch.Tensor, masks: torch.Tensor | None,
                    azimuths: Sequence[float], elevations: Sequence[float],
                    texture_size: int, frame_scale: float = 1.1, cos_power: float = 4.0,
                    depth_tolerance: float = 0.01, min_cos: float = 0.1, view_weights=None,
                    dilate_px: int = 8, chunk: int = 1 << 20):
    """Projeta ``images [V,H,W,3]`` no atlas UV do mesh.

    * Todas as vistas usam o mesmo enquadramento (``frame_scale`` × maior
      dimensão do bounding box), idêntico ao usado em ``render_view`` — as
      imagens geradas a partir das condições encaixam pixel a pixel.
    * Visibilidade: o texel só recebe cor de uma vista se a sua profundidade
      nessa vista ≈ z-buffer (tolerância relativa ao tamanho do objeto).
    * Peso = max(0, cos)^cos_power × peso da vista × máscara.

    Retorna ``texture [S,S,3]``, ``weight [S,S]`` (soma dos pesos; 0 = não coberto
    por nenhuma vista) e ``cover [S,S] bool`` (texel pertence ao mesh).
    """
    dev = verts.device
    V, H, W, _ = images.shape
    center, extent = bbox_center_extent(verts)
    half = float(extent.max()) * 0.5 * frame_scale
    vn = vertex_normals(verts, faces)
    pos, nrm, cover = texel_geometry(verts, faces, uvs, texture_size, vn)
    S = int(texture_size)
    acc = torch.zeros((S, S, 3), device=dev)
    wsum = torch.zeros((S, S), device=dev)
    tol = depth_tolerance * float(extent.max())
    if view_weights is None:
        view_weights = [1.0] * V

    P = pos[cover]                                                   # [K,3]
    N = nrm[cover]
    for v in range(V):
        rv = render_view(verts, faces, center, half, azimuths[v], elevations[v], max(H, W), vn)
        fwd, right, up = rv["fwd"], rv["right"], rv["up"]
        img = images[v].to(dev).float()
        m = masks[v].to(dev).float() if masks is not None else None
        # z-buffer reamostrado para HxW caso H != W
        zbuf = rv["depth"]
        if zbuf.shape[0] != H or zbuf.shape[1] != W:
            zb = zbuf.clone(); zb[torch.isinf(zb)] = 1e9
            zbuf = F.interpolate(zb[None, None], size=(H, W), mode="nearest")[0, 0]
        out_w = torch.zeros((P.shape[0],), device=dev)
        out_c = torch.zeros((P.shape[0], 3), device=dev)
        for s in range(0, P.shape[0], chunk):
            p = P[s:s + chunk]; n = N[s:s + chunk]
            x, y, z = ortho_project(p, center, fwd, right, up, half)
            cosang = (n * -fwd).sum(-1)                              # normal virada para a câmera
            col = (x * 0.5 + 0.5) * W - 0.5
            row = (1.0 - (y * 0.5 + 0.5)) * H - 0.5
            inb = (x.abs() <= 1) & (y.abs() <= 1) & (cosang > min_cos)
            # visibilidade
            ci = col.round().long().clamp(0, W - 1)
            ri = row.round().long().clamp(0, H - 1)
            vis = (z - zbuf[ri, ci]).abs() <= tol
            wgt = torch.where(inb & vis, cosang.clamp_min(0) ** cos_power, torch.zeros_like(cosang))
            # amostragem bilinear
            grid = torch.stack([x, -y], -1)[None, None]              # grid_sample: y para baixo
            smp = F.grid_sample(img.permute(2, 0, 1)[None], grid, mode="bilinear",
                                padding_mode="border", align_corners=False)[0, :, 0].T
            if m is not None:
                ms = F.grid_sample(m[None, None], grid, mode="bilinear",
                                   padding_mode="zeros", align_corners=False)[0, 0, 0]
                wgt = wgt * ms
            out_w[s:s + chunk] = wgt * float(view_weights[v])
            out_c[s:s + chunk] = smp
        acc[cover] += out_c * out_w[:, None]
        wsum[cover] += out_w
    tex = torch.where(wsum[..., None] > 1e-8, acc / wsum[..., None].clamp_min(1e-8), torch.zeros_like(acc))
    if dilate_px > 0:
        tex = dilate(tex, (wsum > 1e-8), dilate_px)
    return tex, wsum, cover


@torch.no_grad()
def dilate(tex: torch.Tensor, valid: torch.Tensor, px: int) -> torch.Tensor:
    """Empurra a cor dos texels válidos para os vizinhos vazios (evita costuras
    pretas nas bordas das ilhas UV e nos buracos de cobertura)."""
    t = tex.permute(2, 0, 1)[None]                                  # [1,3,S,S]
    v = valid.float()[None, None]
    for _ in range(int(px)):
        tsum = F.avg_pool2d(t * v, 3, 1, 1, count_include_pad=True) * 9
        vsum = F.avg_pool2d(v, 3, 1, 1, count_include_pad=True) * 9
        fill = (v == 0) & (vsum > 0)
        t = torch.where(fill, tsum / vsum.clamp_min(1e-8), t)
        v = torch.where(fill, torch.ones_like(v), v)
    return t[0].permute(1, 2, 0)


@torch.no_grad()
def fill_uncovered(tex: torch.Tensor, wsum: torch.Tensor, cover: torch.Tensor,
                   fill_color: torch.Tensor | None = None, reach_px: int = 32) -> torch.Tensor:
    """Texels do mesh que nenhuma vista viu (axila, sola…) recebem a cor dos
    vizinhos (dilatação longa) ou, se nada chega até eles, ``fill_color``."""
    valid = wsum > 1e-8
    out = dilate(tex, valid, reach_px)
    reached = dilate(valid.float()[..., None].expand(-1, -1, 3).contiguous(), valid, reach_px)[..., 0] > 0
    if fill_color is None:
        fill_color = tex[valid].mean(0) if bool(valid.any()) else torch.zeros(3, device=tex.device)
    out[cover & ~valid & ~reached] = fill_color
    return out
