# -*- coding: utf-8 -*-
"""Nós ComfyUI: projeção de texturas por múltiplas vistas (clean-room, MIT).

Três nós:

* ``LiaRenderProjectionViews`` — renderiza o mesh em N vistas ortográficas
  (normal-map em espaço de câmera, máscara, profundidade). São as "condições"
  que o gerador de imagem (Flux.2 Klein) usa para pintar cada vista de forma
  coerente com a geometria. Também devolve a lista de ângulos e o enquadramento
  para o nó de bake usar exatamente a mesma câmera.
* ``LiaProjectTexture`` — recebe as imagens pintadas (mesma ordem/ângulos) e
  projeta no atlas UV do mesh, com visibilidade por z-buffer e peso cos^k.
  Sai a textura ``base_color`` [1,S,S,3] para ligar em ``ApplyTextureToMesh``.
* ``LiaProjectionAngles`` — só monta a lista de ângulos (presets 4/6 vistas).

Só depende de torch e da API pública do core (``comfy_api.latest``).
"""
from __future__ import annotations

import json

import torch
from typing_extensions import override

import comfy.model_management
from comfy_api.latest import ComfyExtension, IO

from . import projection as P

PRESETS = {
    "4 vistas (0/90/180/270)": ([0, 90, 180, 270], [0, 0, 0, 0]),
    "6 vistas (+ 30/330 elev. 20)": ([0, 90, 180, 270, 330, 30], [0, 0, 0, 0, 20, 20]),
    "6 vistas (4 lados + cima/baixo)": ([0, 90, 180, 270, 0, 0], [0, 0, 0, 0, 89, -89]),
    "8 vistas (a cada 45)": ([0, 45, 90, 135, 180, 225, 270, 315], [0] * 8),
}


def _first_item(mesh):
    """(verts [N,3], faces [M,3], uvs [N,2] | None) do primeiro item do batch, no device de cálculo."""
    dev = comfy.model_management.get_torch_device()
    v = mesh.vertices[0]
    f = mesh.faces[0]
    if getattr(mesh, "vertex_counts", None) is not None:
        v = v[: int(mesh.vertex_counts[0])]
        f = f[: int(mesh.face_counts[0])]
    uv = None
    if mesh.uvs is not None:
        uv = mesh.uvs[0][: v.shape[0]].to(dev).float()
    return v.to(dev).float(), f.to(dev).long(), uv


def _angles_json(az, el, frame_scale):
    return json.dumps({"azimuths": [float(a) for a in az], "elevations": [float(e) for e in el],
                       "frame_scale": float(frame_scale)})


def _parse_angles(s):
    d = json.loads(s)
    return d["azimuths"], d["elevations"], float(d.get("frame_scale", 1.1))


class LiaProjectionAngles(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="LiaProjectionAngles",
            display_name="Projection Angles (Lia)",
            category="3d/texturing/projection",
            description="Lista de ângulos de câmera para os nós de projeção. Use um preset ou escreva "
                        "azimutes/elevações separados por vírgula (mesma quantidade).",
            inputs=[
                IO.Combo.Input("preset", options=list(PRESETS.keys()) + ["custom"]),
                IO.String.Input("azimuths", default="0, 90, 180, 270",
                                tooltip="0 = frente, 90 = lado esquerdo do personagem, 180 = costas, 270 = direito."),
                IO.String.Input("elevations", default="0, 0, 0, 0", tooltip="Graus; positivo = câmera acima."),
                IO.Float.Input("frame_scale", default=1.1, min=1.0, max=2.0, step=0.01,
                               tooltip="Quadro = maior lado do bounding box × este fator. Mesmo valor no render e no bake."),
            ],
            outputs=[IO.String.Output(display_name="angles")],
        )

    @classmethod
    def execute(cls, preset, azimuths, elevations, frame_scale):
        if preset != "custom":
            az, el = PRESETS[preset]
        else:
            az = [float(x) for x in azimuths.replace(";", ",").split(",") if x.strip()]
            el = [float(x) for x in elevations.replace(";", ",").split(",") if x.strip()]
            if len(el) == 1 and len(az) > 1:
                el = el * len(az)
            if len(az) != len(el):
                raise ValueError(f"azimuths ({len(az)}) e elevations ({len(el)}) precisam ter a mesma quantidade")
        return IO.NodeOutput(_angles_json(az, el, frame_scale))


class LiaRenderProjectionViews(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="LiaRenderProjectionViews",
            display_name="Render Projection Views (Lia)",
            category="3d/texturing/projection",
            description="Renderiza o mesh em N vistas ortográficas: normal map (espaço de câmera, estilo "
                        "OpenGL: R=direita, G=cima, B=para a câmera), máscara e profundidade. As imagens "
                        "saem em batch na ordem dos ângulos; ligue-as como referência/condição do gerador.",
            inputs=[
                IO.Mesh.Input("mesh"),
                IO.String.Input("angles", tooltip="Saída do nó Projection Angles."),
                IO.Int.Input("resolution", default=1024, min=256, max=2048, step=64),
                IO.Combo.Input("background", options=["grey", "black", "white"], default="grey",
                               tooltip="Fundo do normal map. Cinza (128,128,255 ≈ normal neutra) é o padrão de ControlNet."),
            ],
            outputs=[
                IO.Image.Output(display_name="normals"),
                IO.Mask.Output(display_name="masks"),
                IO.Image.Output(display_name="depth"),
                IO.Image.Output(display_name="mesh_preview"),
                IO.String.Output(display_name="angles"),
            ],
        )

    @classmethod
    def execute(cls, mesh, angles, resolution, background):
        az, el, fs = _parse_angles(angles)
        v, f, _ = _first_item(mesh)
        center, extent = P.bbox_center_extent(v)
        half = float(extent.max()) * 0.5 * fs
        vn = P.vertex_normals(v, f)
        normals, masks, depths, previews = [], [], [], []
        bg = {"grey": (0.5, 0.5, 1.0), "black": (0.0, 0.0, 0.0), "white": (1.0, 1.0, 1.0)}[background]
        bg_t = torch.tensor(bg, device=v.device)
        light = torch.nn.functional.normalize(torch.tensor([0.3, 0.6, 1.0], device=v.device), dim=0)
        for a, e in zip(az, el):
            rv = P.render_view(v, f, center, half, a, e, resolution, vn)
            m = rv["mask"]
            n = rv["normal"] * 0.5 + 0.5
            n = torch.where(m[..., None], n, bg_t)
            d = rv["depth"].clone()
            if bool(m.any()):
                dm = d[m]
                lo, hi = float(dm.min()), float(dm.max())
                d = ((hi - d) / max(hi - lo, 1e-6)).clamp(0, 1)
            d = torch.where(m, d, torch.zeros_like(d))
            shade = (rv["normal"] * light).sum(-1).clamp(0, 1) * 0.8 + 0.2
            pv = torch.where(m[..., None], shade[..., None].expand(-1, -1, 3), torch.zeros_like(n))
            normals.append(n); masks.append(m.float()); depths.append(d[..., None].expand(-1, -1, 3)); previews.append(pv)
        idev = comfy.model_management.intermediate_device()
        return IO.NodeOutput(torch.stack(normals).to(idev), torch.stack(masks).to(idev),
                             torch.stack(depths).to(idev), torch.stack(previews).to(idev),
                             _angles_json(az, el, fs))


class LiaProjectTexture(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="LiaProjectTexture",
            display_name="Project Images To Texture (Lia)",
            category="3d/texturing/projection",
            description="Projeta um batch de imagens (uma por ângulo, mesma ordem do Render Projection Views) "
                        "no atlas UV do mesh. Visibilidade por z-buffer, peso cos^k(normal·câmera), média "
                        "ponderada, dilatação de bordas. Saída: base_color para ApplyTextureToMesh.",
            inputs=[
                IO.Mesh.Input("mesh", tooltip="Precisa ter UV (passe pelo UnwrapMesh antes)."),
                IO.Image.Input("images", tooltip="[V,H,W,3] — as vistas pintadas, na ordem dos ângulos."),
                IO.String.Input("angles"),
                IO.Int.Input("texture_size", default=2048, min=256, max=4096, step=256),
                IO.Float.Input("cos_power", default=4.0, min=0.5, max=16.0, step=0.5,
                               tooltip="Quanto maior, mais a vista frontal a cada ponto domina (menos fantasma, mais costura)."),
                IO.Float.Input("min_cos", default=0.15, min=0.0, max=0.9, step=0.01,
                               tooltip="Ângulo rasante abaixo do qual a vista é ignorada (0.15 ≈ 81°)."),
                IO.Float.Input("depth_tolerance", default=0.01, min=0.001, max=0.1, step=0.001,
                               tooltip="Tolerância de visibilidade, fração do tamanho do objeto."),
                IO.Int.Input("dilate_px", default=8, min=0, max=64),
                IO.Boolean.Input("fill_unseen", default=True,
                                 tooltip="Preenche texels que nenhuma vista viu com a cor vizinha/média."),
                IO.Mask.Input("masks", optional=True, tooltip="Máscara por vista (1 = usar). Se vazio, usa tudo."),
                IO.String.Input("view_weights", default="", optional=True,
                                tooltip="Pesos por vista separados por vírgula, ex.: 1,0.7,1,0.7 (frente/costas dominam)."),
            ],
            outputs=[
                IO.Image.Output(display_name="base_color"),
                IO.Image.Output(display_name="coverage"),
            ],
        )

    @classmethod
    def execute(cls, mesh, images, angles, texture_size, cos_power, min_cos, depth_tolerance,
                dilate_px, fill_unseen, masks=None, view_weights=""):
        az, el, fs = _parse_angles(angles)
        v, f, uv = _first_item(mesh)
        if uv is None:
            raise ValueError("O mesh não tem UV. Ligue um UnwrapMesh antes deste nó.")
        V = images.shape[0]
        if V != len(az):
            raise ValueError(f"{V} imagem(ns) para {len(az)} ângulo(s). A ordem e a quantidade têm de bater.")
        vw = None
        if view_weights and view_weights.strip():
            vw = [float(x) for x in view_weights.replace(";", ",").split(",") if x.strip()]
            if len(vw) != V:
                raise ValueError(f"view_weights tem {len(vw)} valores para {V} vistas")
        imgs = images[..., :3].to(v.device).float()
        ms = None
        if masks is not None:
            ms = masks.to(v.device).float()
            if ms.ndim == 2:
                ms = ms[None]
            if ms.shape[0] == 1 and V > 1:
                ms = ms.expand(V, -1, -1)
            if ms.shape[-2:] != imgs.shape[1:3]:
                ms = torch.nn.functional.interpolate(ms[:, None], size=imgs.shape[1:3], mode="bilinear",
                                                     align_corners=False)[:, 0]
        tex, w, cover = P.project_texture(v, f, uv, imgs, ms, az, el, int(texture_size), frame_scale=fs,
                                          cos_power=float(cos_power), depth_tolerance=float(depth_tolerance),
                                          min_cos=float(min_cos), view_weights=vw, dilate_px=int(dilate_px))
        if fill_unseen:
            tex = P.fill_uncovered(tex, w, cover)
        cov = torch.zeros_like(tex)
        cov[..., 1] = (w > 1e-8).float()            # verde = coberto
        cov[..., 0] = (cover & (w <= 1e-8)).float()  # vermelho = mesh mas não visto
        idev = comfy.model_management.intermediate_device()
        return IO.NodeOutput(tex.clamp(0, 1)[None].to(idev), cov[None].to(idev))


class LiaTextureProjectionExtension(ComfyExtension):
    @override
    async def get_node_list(self):
        return [LiaProjectionAngles, LiaRenderProjectionViews, LiaProjectTexture]


async def comfy_entrypoint():
    return LiaTextureProjectionExtension()
