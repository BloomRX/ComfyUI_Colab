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

Fluxo sequencial (v2, "projeta-e-completa" — o mesmo princípio do Modddif/TEXTure):

* ``LiaRenderTextured`` — renderiza a vista com a textura parcial já acumulada;
  devolve a imagem (buracos em cinza), a máscara de inpaint (o que falta) e o
  normal map. O gerador só pinta o que falta, vendo o que já existe → vistas
  coerentes entre si.
* ``LiaProjectTextureAccumulate`` — soma UMA vista ao estado da textura
  (``LIA_TEXSTATE``), com correção de ganho de cor contra o que já foi pintado.
* ``LiaTextureFinalize`` — dilata bordas, preenche o que nenhuma vista viu e
  devolve ``base_color`` + máscara UV do não-visto.
* ``LiaPickReference`` — escolhe a imagem de referência da vista (costas/lados
  opcionais, cai na frontal se faltar).

Só depende de torch e da API pública do core (``comfy_api.latest``).
"""
from __future__ import annotations

import json

import torch
from typing_extensions import override

import comfy.model_management
from comfy_api.latest import ComfyExtension, IO, UI

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


# --------------------------------------------------------------------------- #
# v2 — fluxo sequencial
# --------------------------------------------------------------------------- #
TexState = IO.Custom("LIA_TEXSTATE")

_VIEW_TIPS = {
    "front": "frente (0)", "back": "costas (180)", "left": "esquerda (90)", "right": "direita (270)",
}


def _state_get(state):
    if state is None:
        return None, None
    return state.get("texture"), state.get("wsum")


class LiaRenderTextured(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="LiaRenderTextured",
            display_name="Render Textured View (Lia)",
            category="3d/texturing/projection",
            description="Renderiza o mesh numa vista ortográfica com a textura parcial já acumulada. "
                        "Pixels do mesh ainda sem textura saem em cinza e viram a máscara de inpaint. "
                        "Sem 'state' ligado, tudo é 'faltando' (primeira vista = geração completa).",
            inputs=[
                IO.Mesh.Input("mesh", tooltip="Mesh COM UV (o mesmo em todos os nós Lia do fluxo)."),
                IO.Float.Input("azimuth", default=0.0, min=-360.0, max=360.0, step=1.0,
                               tooltip="0 = frente, 90 = lado esquerdo do personagem, 180 = costas, 270 = direito."),
                IO.Float.Input("elevation", default=0.0, min=-89.0, max=89.0, step=1.0, tooltip="Positivo = câmera acima."),
                IO.Int.Input("resolution", default=1024, min=256, max=2048, step=64),
                IO.Float.Input("frame_scale", default=1.1, min=1.0, max=2.0, step=0.01,
                               tooltip="Enquadramento; use o MESMO valor no Accumulate."),
                IO.Int.Input("grow_mask_px", default=12, min=0, max=128,
                             tooltip="Expande a máscara de inpaint para o gerador fundir a borda com o que já existe."),
                IO.Combo.Input("missing_color", options=["grey", "white", "black", "magenta"], default="grey",
                               tooltip="Cor dos pixels ainda sem textura (cite-a no prompt)."),
                TexState.Input("state", optional=True, tooltip="Saída do Accumulate da vista anterior. Vazio na 1ª vista."),
            ],
            outputs=[
                IO.Image.Output(display_name="image"),
                IO.Mask.Output(display_name="inpaint_mask"),
                IO.Mask.Output(display_name="silhouette"),
                IO.Image.Output(display_name="normals"),
                IO.Float.Output(display_name="missing_fraction"),
            ],
        )

    @classmethod
    def execute(cls, mesh, azimuth, elevation, resolution, frame_scale, grow_mask_px, missing_color, state=None):
        v, f, uv = _first_item(mesh)
        if uv is None:
            raise ValueError("O mesh não tem UV. Ligue um UnwrapMesh antes deste nó.")
        tex, w = _state_get(state)
        mc = {"grey": (0.5, 0.5, 0.5), "white": (1, 1, 1), "black": (0, 0, 0), "magenta": (1, 0, 1)}[missing_color]
        img, missing, sil, ncam = P.render_textured(v, f, uv, tex, w, float(azimuth), float(elevation),
                                                    int(resolution), float(frame_scale), missing_color=mc)
        m = missing.float()
        if grow_mask_px > 0:
            k = int(grow_mask_px) * 2 + 1
            m = torch.nn.functional.max_pool2d(m[None, None], k, 1, k // 2)[0, 0]
            m = m * sil.float()   # nunca pinta fora da silhueta
        n = torch.where(sil[..., None], ncam * 0.5 + 0.5, torch.tensor([0.5, 0.5, 1.0], device=v.device))
        frac = float(missing.sum()) / max(1.0, float(sil.sum()))
        idev = comfy.model_management.intermediate_device()
        return IO.NodeOutput(img[None].to(idev), m[None].to(idev), sil.float()[None].to(idev),
                             n[None].to(idev), frac,
                             ui=UI.PreviewText(f"az {azimuth:g} el {elevation:g}: {frac*100:.1f}% da vista ainda sem textura"))


class LiaProjectTextureAccumulate(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="LiaProjectTextureAccumulate",
            display_name="Accumulate View Into Texture (Lia)",
            category="3d/texturing/projection",
            description="Projeta UMA imagem pintada no atlas UV e soma ao estado da textura. Encadeie um por "
                        "vista (frente → costas → lados → cima/baixo). 'color_match' corrige o tom da vista "
                        "nova pelo que já está pintado, para as costas não saírem com outra paleta.",
            inputs=[
                IO.Mesh.Input("mesh"),
                IO.Image.Input("image", tooltip="A vista pintada (mesma câmera do Render Textured View)."),
                IO.Float.Input("azimuth", default=0.0, min=-360.0, max=360.0, step=1.0),
                IO.Float.Input("elevation", default=0.0, min=-89.0, max=89.0, step=1.0),
                IO.Float.Input("frame_scale", default=1.1, min=1.0, max=2.0, step=0.01),
                IO.Int.Input("texture_size", default=2048, min=256, max=4096, step=256,
                             tooltip="Usado só na 1ª vista (sem state)."),
                IO.Float.Input("view_weight", default=1.0, min=0.05, max=4.0, step=0.05,
                               tooltip="Peso desta vista na média (frente 1.0; vistas de cima/baixo 0.5)."),
                IO.Float.Input("cos_power", default=4.0, min=0.5, max=16.0, step=0.5),
                IO.Float.Input("min_cos", default=0.15, min=0.0, max=0.9, step=0.01),
                IO.Float.Input("depth_tolerance", default=0.01, min=0.001, max=0.1, step=0.001),
                IO.Boolean.Input("color_match", default=True),
                IO.Boolean.Input("fill_only", default=False,
                                 tooltip="Só pinta texels ainda vazios (não mistura com o que já existe). Bom para vistas de retoque."),
                TexState.Input("state", optional=True),
                IO.Mask.Input("mask", optional=True, tooltip="1 = usar este pixel. Ligue a inpaint_mask (só o novo) ou a silhouette (tudo)."),
            ],
            outputs=[
                TexState.Output(display_name="state"),
                IO.Image.Output(display_name="base_color"),
                IO.Image.Output(display_name="coverage"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, mesh, image, azimuth, elevation, frame_scale, texture_size, view_weight, cos_power,
                min_cos, depth_tolerance, color_match, fill_only, state=None, mask=None):
        v, f, uv = _first_item(mesh)
        if uv is None:
            raise ValueError("O mesh não tem UV. Ligue um UnwrapMesh antes deste nó.")
        tex, w = _state_get(state)
        img = image[0, ..., :3].to(v.device).float()
        m = None
        if mask is not None:
            m = mask[0].to(v.device).float() if mask.ndim == 3 else mask.to(v.device).float()
            if m.shape != img.shape[:2]:
                m = torch.nn.functional.interpolate(m[None, None], size=img.shape[:2], mode="bilinear",
                                                    align_corners=False)[0, 0]
        tex, w, cover, st = P.accumulate_view(v, f, uv, tex, w, img, m, float(azimuth), float(elevation),
                                              frame_scale=float(frame_scale), cos_power=float(cos_power),
                                              depth_tolerance=float(depth_tolerance), min_cos=float(min_cos),
                                              view_weight=float(view_weight), color_match=bool(color_match),
                                              fill_only=bool(fill_only), texture_size=int(texture_size))
        cov = torch.zeros_like(tex)
        cov[..., 1] = (w > 1e-8).float()
        cov[..., 0] = (cover & (w <= 1e-8)).float()
        info = (f"az {azimuth:g} el {elevation:g}: +{st['new_texels']} texels novos, sobreposição {st['overlap']}, "
                f"ganho RGB {st['gain']}, cobertura {st['covered_frac']*100:.1f}%")
        idev = comfy.model_management.intermediate_device()
        new_state = {"texture": tex.to(idev), "wsum": w.to(idev), "size": int(tex.shape[0])}
        return IO.NodeOutput(new_state, tex.clamp(0, 1)[None].to(idev), cov[None].to(idev), info,
                             ui=UI.PreviewText(info))


class LiaTextureFinalize(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="LiaTextureFinalize",
            display_name="Finalize Texture (Lia)",
            category="3d/texturing/projection",
            description="Fecha a textura acumulada: dilata bordas das ilhas UV, preenche o que nenhuma vista viu "
                        "e devolve base_color para ApplyTextureToMesh + máscara UV do não-visto.",
            inputs=[
                IO.Mesh.Input("mesh"),
                TexState.Input("state"),
                IO.Int.Input("dilate_px", default=8, min=0, max=64),
                IO.Boolean.Input("fill_unseen", default=True),
                IO.Int.Input("fill_reach_px", default=48, min=4, max=256,
                             tooltip="Até onde a cor vizinha é 'esticada' para dentro do não-visto antes de cair na cor média."),
            ],
            outputs=[
                IO.Image.Output(display_name="base_color"),
                IO.Image.Output(display_name="coverage"),
                IO.Mask.Output(display_name="unseen_mask"),
                TexState.Output(display_name="state", tooltip="Textura final como estado (para Render Textured View de conferência ou mais vistas de retoque)."),
            ],
        )

    @classmethod
    def execute(cls, mesh, state, dilate_px, fill_unseen, fill_reach_px):
        v, f, uv = _first_item(mesh)
        tex, w = _state_get(state)
        if tex is None:
            raise ValueError("state vazio")
        tex = tex.to(v.device).float(); w = w.to(v.device).float()
        _, _, cover, _ = P.cached_texel_geometry(v, f, uv, tex.shape[0])
        unseen = cover & (w <= 1e-8)
        if dilate_px > 0:
            tex = P.dilate(tex, w > 1e-8, int(dilate_px))
        if fill_unseen:
            tex = P.fill_uncovered(tex, w, cover, reach_px=int(fill_reach_px))
        cov = torch.zeros_like(tex)
        cov[..., 1] = (w > 1e-8).float()
        cov[..., 0] = unseen.float()
        idev = comfy.model_management.intermediate_device()
        # estado final: válido = mesh + a margem dilatada (a textura já foi empurrada para lá)
        k = 2 * int(max(dilate_px, 1)) + 1
        valid_final = torch.nn.functional.max_pool2d(cover.float()[None, None], k, 1, k // 2)[0, 0]
        final_state = {"texture": tex.clamp(0, 1).to(idev), "wsum": valid_final.to(idev), "size": int(tex.shape[0])}
        return IO.NodeOutput(tex.clamp(0, 1)[None].to(idev), cov[None].to(idev), unseen.float()[None].to(idev), final_state)


class LiaPickReference(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="LiaPickReference",
            display_name="Pick Reference Image (Lia)",
            category="3d/texturing/projection",
            description="Escolhe a imagem de referência para a vista. Costas/lados são opcionais: se não "
                        "estiverem ligados (ou o LoadImage estiver em bypass), usa a frontal.",
            inputs=[
                IO.Combo.Input("view", options=list(_VIEW_TIPS.keys()), default="front"),
                IO.Image.Input("front"),
                IO.Image.Input("back", optional=True),
                IO.Image.Input("left", optional=True),
                IO.Image.Input("right", optional=True),
            ],
            outputs=[IO.Image.Output(display_name="image"), IO.String.Output(display_name="used")],
        )

    @classmethod
    def execute(cls, view, front, back=None, left=None, right=None):
        pick = {"front": front, "back": back, "left": left, "right": right}[view]
        if pick is None:
            return IO.NodeOutput(front, f"{view}: sem imagem própria → usando a frontal")
        return IO.NodeOutput(pick, f"{view}: imagem própria")


class LiaTextureProjectionExtension(ComfyExtension):
    @override
    async def get_node_list(self):
        return [LiaProjectionAngles, LiaRenderProjectionViews, LiaProjectTexture,
                LiaRenderTextured, LiaProjectTextureAccumulate, LiaTextureFinalize, LiaPickReference]


async def comfy_entrypoint():
    return LiaTextureProjectionExtension()
