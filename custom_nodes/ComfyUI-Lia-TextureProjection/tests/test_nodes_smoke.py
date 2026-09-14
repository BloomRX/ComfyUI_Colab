"""Smoke test dos nós com um mock mínimo da API do core (sem ComfyUI instalado)."""
import sys, types, os, torch
HERE = os.path.dirname(os.path.abspath(__file__))
class _In:
    def __init__(self, *a, **k): pass
class _T:
    Input = _In; Output = _In
io = types.SimpleNamespace(ComfyNode=object, Schema=lambda **k: k, NodeOutput=lambda *a, **k: a,
                           Combo=_T, String=_T, Float=_T, Int=_T, Boolean=_T, Image=_T, Mask=_T, Mesh=_T, Custom=lambda s: _T)
class _PT:
    def __init__(self, v, **k): self.value = v
m = types.ModuleType('comfy_api.latest'); m.IO = io; m.ComfyExtension = object; m.UI = types.SimpleNamespace(PreviewText=_PT)
sys.modules['comfy_api'] = types.ModuleType('comfy_api'); sys.modules['comfy_api.latest'] = m
comfy = types.ModuleType('comfy'); mm = types.ModuleType('comfy.model_management')
mm.get_torch_device = lambda: torch.device('cpu'); mm.intermediate_device = lambda: torch.device('cpu')
comfy.model_management = mm; sys.modules['comfy'] = comfy; sys.modules['comfy.model_management'] = mm
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import importlib
pkg = importlib.import_module(os.path.basename(os.path.dirname(HERE)) + '.nodes') if False else None
import importlib.util
spec = importlib.util.spec_from_file_location("lia_nodes_pkg", os.path.join(os.path.dirname(HERE), "__init__.py"),
                                              submodule_search_locations=[os.path.dirname(HERE)])
pkg = importlib.util.module_from_spec(spec); sys.modules["lia_nodes_pkg"] = pkg
nodes = importlib.import_module("lia_nodes_pkg.nodes")
from test_projection import uv_sphere
v, f, uv = uv_sphere()
class Mesh: pass
mesh = Mesh(); mesh.vertices = v[None]; mesh.faces = f[None]; mesh.uvs = uv[None]; mesh.vertex_counts = None
R = nodes.LiaRenderTextured; A = nodes.LiaProjectTextureAccumulate; F = nodes.LiaTextureFinalize; PK = nodes.LiaPickReference
state = None
for az, el in [(0, 0), (180, 0), (0, 60)]:
    img, mask, sil, nrm, frac = R.execute(mesh, az, el, 256, 1.1, 12, "grey", state)
    print(az, el, 'missing frac', round(frac, 3), tuple(img.shape), tuple(mask.shape), tuple(nrm.shape))
    assert img.shape == (1, 256, 256, 3) and mask.shape == (1, 256, 256)
    paint = torch.where(mask[0][..., None] > 0, torch.rand(3), img[0])[None]
    state, bc, cov, info = A.execute(mesh, paint, az, el, 1.1, 512, 1.0, 4.0, 0.15, 0.01, True, False, state, mask)
    print(' ', info)
assert frac < 0.2
bc, cov, un, fst = F.execute(mesh, state, 8, True, 48)
assert 'texture' in fst; print('final', tuple(bc.shape), int(un.sum()))
assert bc.shape == (1, 512, 512, 3)
print(PK.execute("back", torch.zeros(1, 4, 4, 3))[1], '|', PK.execute("back", torch.zeros(1, 4, 4, 3), back=torch.ones(1, 4, 4, 3))[1])
print("SMOKE OK")
