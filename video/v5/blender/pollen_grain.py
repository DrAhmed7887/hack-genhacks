"""V5 hero shot: a procedural grass-pollen grain (Poaceae: near-spherical, one pore
with a raised annulus and a lid, finely granular surface). Procedural geometry only.

Run:  blender -b -P video/v5/blender/pollen_grain.py -- --out <dir> [--still 60] [--samples 64]
      [--res 1920x1080] [--frames 1-150] [--device METAL|OPTIX|CUDA|CPU]
Writes PNG frames <dir>/grain_####.png (transparent off; paper backdrop is in-scene).
"""
import bpy, sys, math, argparse

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--still", type=int, default=None)
ap.add_argument("--samples", type=int, default=96)
ap.add_argument("--res", default="1920x1080")
ap.add_argument("--frames", default="1-150")
ap.add_argument("--device", default="METAL")
ap.add_argument("--save", default=None, help="save .blend here")
a = ap.parse_args(argv)

PAPER = (0.921, 0.906, 0.871)   # #F6F4EE in linear-ish (slightly darker so the grain reads)
INK = (0.0075, 0.015, 0.011)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
w, h = map(int, a.res.split("x"))
sc.render.resolution_x, sc.render.resolution_y = w, h
sc.render.fps = 30
f0, f1 = map(int, a.frames.split("-"))
sc.frame_start, sc.frame_end = f0, f1
sc.cycles.samples = a.samples
sc.cycles.use_denoising = True
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_depth = "8"
sc.render.filepath = a.out.rstrip("/") + "/grain_"

prefs = bpy.context.preferences.addons["cycles"].preferences
if a.device != "CPU":
    try:
        prefs.compute_device_type = a.device
        prefs.refresh_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:  # fall back loudly
        print("GPU device not available:", e)
        sc.cycles.device = "CPU"

# ---------- world: warm paper studio ----------
world = bpy.data.worlds.new("paper")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (*PAPER, 1)
bg.inputs[1].default_value = 0.55

# ---------- grain body ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=192, ring_count=128, radius=1.0)
grain = bpy.context.active_object
grain.name = "Grain"
grain.scale = (1.0, 0.96, 0.92)       # slightly oblate, like a real grass grain
bpy.ops.object.shade_smooth()

# scabrate surface: fine granules + a soft large-scale wobble
tex_fine = bpy.data.textures.new("granules", "VORONOI")
tex_fine.noise_scale = 0.035
tex_fine.distance_metric = "DISTANCE"
m1 = grain.modifiers.new("granules", "DISPLACE")
m1.texture = tex_fine
m1.strength = 0.018
m1.mid_level = 0.6
tex_soft = bpy.data.textures.new("wobble", "CLOUDS")
tex_soft.noise_scale = 0.7
m2 = grain.modifiers.new("wobble", "DISPLACE")
m2.texture = tex_soft
m2.strength = 0.05

# ---------- the pore: annulus ring + lid (operculum) ----------
bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.055,
                                 major_segments=96, minor_segments=32,
                                 location=(0, 0, 0.905))
ring = bpy.context.active_object
ring.name = "Annulus"
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.115,
                                     location=(0, 0, 0.90))
lid = bpy.context.active_object
lid.name = "Operculum"
lid.scale = (1, 1, 0.45)
bpy.ops.object.shade_smooth()
for o in (ring, lid):
    o.parent = grain
    o.matrix_parent_inverse = grain.matrix_world.inverted()

# ---------- material: translucent golden exine ----------
mat = bpy.data.materials.new("exine")
mat.use_nodes = True
nt = mat.node_tree
p = nt.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value = (0.78, 0.52, 0.17, 1)
p.inputs["Roughness"].default_value = 0.42
p.inputs["Subsurface Weight"].default_value = 0.35
p.inputs["Subsurface Radius"].default_value = (0.5, 0.25, 0.08)
p.inputs["Subsurface Scale"].default_value = 0.15
p.inputs["Coat Weight"].default_value = 0.25
p.inputs["Coat Roughness"].default_value = 0.2
# cavity darkening via AO so the granules read
ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
ao.inputs["Distance"].default_value = 0.05
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
mix.inputs["A"].default_value = (0.36, 0.20, 0.05, 1)
mix.inputs["B"].default_value = (0.82, 0.57, 0.20, 1)
nt.links.new(ao.outputs["AO"], mix.inputs["Factor"])
nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
for o in (grain, ring, lid):
    o.data.materials.append(mat)

# ---------- soft floor that fades into paper ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -1.25))
floor = bpy.context.active_object
fm = bpy.data.materials.new("paperfloor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*PAPER, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
floor.data.materials.append(fm)

# ---------- lights: big soft key, warm rim, cool fill ----------
def area(name, loc, rot, size, energy, color):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.active_object
    L.name = name
    L.data.size = size
    L.data.energy = energy
    L.data.color = color
    return L

area("Key", (3.5, -3.0, 4.0), (math.radians(45), 0, math.radians(50)), 4.0, 900, (1.0, 0.97, 0.92))
area("Rim", (-3.0, 3.2, 2.0), (math.radians(-60), 0, math.radians(215)), 2.0, 700, (1.0, 0.80, 0.55))
area("Fill", (-4.0, -3.5, 0.5), (math.radians(85), 0, math.radians(-50)), 5.0, 160, (0.85, 0.92, 1.0))

# ---------- camera: slow push-in while the grain turns to show its pore ----------
bpy.ops.object.camera_add(location=(0, -6.2, 1.1))
cam = bpy.context.active_object
sc.camera = cam
cam.data.lens = 85
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 2.2
tgt = bpy.data.objects.new("CamTarget", None)
sc.collection.objects.link(tgt)
cam.data.dof.focus_object = tgt
trk = cam.constraints.new("TRACK_TO")
trk.target = tgt
trk.track_axis = "TRACK_NEGATIVE_Z"
trk.up_axis = "UP_Y"

bpy.context.preferences.edit.keyframe_new_interpolation_type = "SINE"
cam.location = (0.6, -7.4, 1.3)
cam.keyframe_insert("location", frame=f0)
cam.location = (0.15, -5.2, 0.7)
cam.keyframe_insert("location", frame=f1)

# grain composition: sits right of centre so a title can live on the left
grain.location = (0.85, 0, 0)
tgt.location = (0.35, 0, 0.1)
grain.rotation_euler = (math.radians(-70), math.radians(10), math.radians(-30))
grain.keyframe_insert("rotation_euler", frame=f0)
grain.rotation_euler = (math.radians(-62), math.radians(18), math.radians(25))
grain.keyframe_insert("rotation_euler", frame=f1)

if a.save:
    bpy.ops.wm.save_as_mainfile(filepath=a.save)

if a.still is not None:
    sc.frame_set(a.still)
    sc.render.filepath = a.out.rstrip("/") + f"/grain_still_{a.still:04d}.png"
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
