"""V5 hero shot 3D-A: a volumetric (Hirst-type) pollen trap whose sticky tape
unrolls into the flat strip the rest of the film uses. Procedural geometry only,
matte clay on a paper ground, no labels on the geometry.

Run:
  blender -b -P video/v5/blender/trap_scene.py -- --out <dir> [--still 205] [--samples 96]
          [--res 1920x1080] [--device OPTIX|CUDA|METAL|CPU] [--save scene.blend]
Animation: 300 frames at 30 fps, timed to the scene-2 voice (see the key() calls).
  0-80    dolly in from a 3/4 wide to the cutaway window (drum and tape visible)
  80-150  the tape peels off the drum and unrolls to the right, flat on the paper plane
  150-210 macro push along the tape, grains in focus; last 12 frames locked
"""
import argparse
import math
import random
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--still", type=int, default=None)
ap.add_argument("--samples", type=int, default=96)
ap.add_argument("--res", default="1920x1080")
ap.add_argument("--frames", default="1-300")
ap.add_argument("--device", default="OPTIX")
ap.add_argument("--save", default=None)
a = ap.parse_args(argv)
random.seed(7)


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


PAPER, INK, CLAY, CLAY2 = srgb("#F6F4EE"), srgb("#15201B"), srgb("#E4DFD3"), srgb("#C9C2B2")
TAPE, GRAIN = srgb("#D8D3C6"), srgb("#B9A97A")

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
sc.cycles.max_bounces = 6
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "Standard"   # keeps paper exact
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = a.out.rstrip("/") + "/trap_"
prefs = bpy.context.preferences.addons["cycles"].preferences
if a.device != "CPU":
    try:
        prefs.compute_device_type = a.device
        prefs.refresh_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU not available, CPU render:", e)
bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"

world = bpy.data.worlds.new("paper")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = PAPER
world.node_tree.nodes["Background"].inputs[1].default_value = 0.78


def mat(name, color, rough=0.75, sss=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = color
    p.inputs["Roughness"].default_value = rough
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.4, 0.3, 0.15)
        p.inputs["Subsurface Scale"].default_value = 0.002
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
    return m


M_CLAY, M_CLAY2, M_INK = mat("clay", CLAY), mat("clay2", CLAY2), mat("ink", INK, 0.6)
M_TAPE = mat("tape", TAPE, 0.35)
M_GRAIN = mat("grain", GRAIN, 0.5, sss=0.3)
M_PAPER = mat("paperfloor", PAPER, 0.95)


def put(o, m):
    o.data.materials.append(m)
    return o


def cyl(r, depth, loc, m, verts=96, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    o.modifiers.new("bevel", "BEVEL").width = min(r, depth) * 0.08
    return put(o, m)


def box(size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    bev = o.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.006, 3
    return put(o, m)


# ---------- ground ----------
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
put(bpy.context.active_object, M_PAPER)

# ---------- trap (body axis vertical; front faces -Y) ----------
BODY_Z, BODY_R, BODY_H = 1.05, 0.20, 0.34
cyl(0.035, BODY_Z - BODY_H / 2, (0, 0, (BODY_Z - BODY_H / 2) / 2), M_CLAY2, 48)          # mast
cyl(0.16, 0.03, (0, 0, 0.015), M_CLAY2, 64)                                                 # foot
body = cyl(BODY_R, BODY_H, (0, 0, BODY_Z), M_CLAY)
cap = cyl(BODY_R * 1.32, 0.03, (0, 0, BODY_Z + BODY_H / 2 + 0.03), M_CLAY2)                 # rain cap
cyl(BODY_R * 0.9, 0.06, (0, 0, BODY_Z + BODY_H / 2 + 0.075), M_CLAY2)
# cutaway window: remove a wedge facing the camera side (-Y, +X)
bpy.ops.mesh.primitive_cube_add(size=1, location=(BODY_R * 0.55, -BODY_R * 0.55, BODY_Z))
cutter = bpy.context.active_object
cutter.scale = (BODY_R * 1.1, BODY_R * 1.1, BODY_H * 0.62)
cutter.rotation_euler = (0, 0, math.radians(45))
boo = body.modifiers.new("cut", "BOOLEAN")
boo.object, boo.operation = cutter, "DIFFERENCE"
cutter.hide_render = cutter.hide_viewport = True
# intake orifice on the front (-Y), slightly left of the window
box((0.07, 0.07, 0.11), (-0.11, -BODY_R - 0.02, BODY_Z + 0.02), M_CLAY2)
box((0.012, 0.01, 0.07), (-0.11, -BODY_R - 0.056, BODY_Z + 0.02), M_INK)                   # slit
# wind vane on the back (+Y)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, BODY_R + 0.32, BODY_Z + 0.02), rotation=(0, math.radians(90), 0))
vane = put(bpy.context.active_object, M_CLAY2)
vane.scale = (0.26, 0.5, 1)
vane.modifiers.new("thick", "SOLIDIFY").thickness = 0.012
cyl(0.012, 0.36, (0, BODY_R + 0.09, BODY_Z + 0.02), M_CLAY2, 24, rot=(math.radians(90), 0, 0))

# drum + tape inside the body
DRUM_R, DRUM_H = 0.12, 0.10
drum = cyl(DRUM_R, DRUM_H, (0, 0, BODY_Z - 0.01), M_CLAY2)
bpy.ops.mesh.primitive_cylinder_add(vertices=192, radius=DRUM_R + 0.003, depth=DRUM_H * 0.78,
                                    location=(0, 0, BODY_Z - 0.01), end_fill_type="NOTHING")
tape_ring = put(bpy.context.active_object, M_TAPE)
bpy.ops.object.shade_smooth()
tape_ring.modifiers.new("thick", "SOLIDIFY").thickness = 0.002
# day ticks on the ring: 7 thin ink lines
for i in range(7):
    ang = 2 * math.pi * i / 7
    box((0.0016, 0.0016, DRUM_H * 0.78), ((DRUM_R + 0.0055) * math.cos(ang), (DRUM_R + 0.0055) * math.sin(ang), BODY_Z - 0.01), M_INK)

# ---------- unrolled tape: a flat strip on the paper running to +X ----------
TAPE_W, TAPE_L = DRUM_H * 0.78, 3.2
X0 = 0.35
bpy.ops.mesh.primitive_plane_add(size=1, location=(X0 + TAPE_L / 2, -0.25, 0.0015))
strip = put(bpy.context.active_object, M_TAPE)
strip.scale = (TAPE_L, TAPE_W * 3.0, 1)
strip.modifiers.new("thick", "SOLIDIFY").thickness = 0.0012
# day ticks on the flat strip
ticks = []
for i in range(1, 14):
    ticks.append(box((0.002, TAPE_W * 3.0, 0.0008), (X0 + i * TAPE_L / 14, -0.25, 0.003), M_INK))

# grains: a deposit band along the strip (denser toward the centre line, like an impaction trace)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1)
proto = bpy.context.active_object
proto.name = "grain_proto"
put(proto, M_GRAIN)
bpy.ops.object.shade_smooth()
d = proto.modifiers.new("rough", "DISPLACE")
d.texture = bpy.data.textures.new("g", "VORONOI")
d.texture.noise_scale = 0.25
d.strength = 0.05
proto.hide_render = proto.hide_viewport = True
coll = bpy.data.collections.new("grains")
sc.collection.children.link(coll)
for i in range(5200):
    x = X0 + random.random() * TAPE_L
    y = -0.25 + random.gauss(0, TAPE_W * 0.45)
    if abs(y + 0.25) > TAPE_W * 1.4:
        continue
    r = 0.0021 * (1 + random.uniform(-0.15, 0.15))
    g = proto.copy()
    g.hide_render = g.hide_viewport = False
    g.location = (x, y, 0.003 + r * 0.8)
    g.scale = (r, r, r * 0.9)
    g.rotation_euler = (random.random() * 6.28, random.random() * 6.28, random.random() * 6.28)
    coll.objects.link(g)

# ---------- light ----------
def area(name, loc, size, energy, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    L = bpy.context.active_object
    L.data.size, L.data.energy, L.data.color = size, energy, color
    L.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return L

area("Key", (-2.5, -3.0, 4.5), 4.0, 170, (1.0, 0.96, 0.90))
area("Fill", (4.0, -2.5, 1.5), 4.0, 45, (0.92, 0.96, 1.0))

# ---------- ink outlines (Freestyle) so the 3D reads as the same drawing as the flat scenes ----------
sc.render.use_freestyle = True
sc.render.line_thickness_mode = "ABSOLUTE"
sc.render.line_thickness = 1.3 * (w / 1920)
ls = sc.view_layers[0].freestyle_settings.linesets.new("ink")
ls.select_by_visibility = True
ls.select_silhouette = ls.select_crease = True
ls.select_border = False
ls.select_by_collection = True
ls.collection = coll
ls.collection_negation = "EXCLUSIVE"
ls.linestyle.color = INK[:3]
ls.linestyle.alpha = 0.85

# ---------- camera ----------
bpy.ops.object.camera_add()
cam = bpy.context.active_object
sc.camera = cam
cam.data.lens = 50
cam.data.dof.use_dof = True
tgt = bpy.data.objects.new("CamTarget", None)
sc.collection.objects.link(tgt)
cam.data.dof.focus_object = tgt
tc = cam.constraints.new("TRACK_TO")
tc.target, tc.track_axis, tc.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"


def key(frame, cam_loc, tgt_loc, fstop, lens):
    cam.location, tgt.location = cam_loc, tgt_loc
    cam.data.dof.aperture_fstop, cam.data.lens = fstop, lens
    cam.keyframe_insert("location", frame=frame)
    tgt.keyframe_insert("location", frame=frame)
    cam.data.keyframe_insert("dof.aperture_fstop", frame=frame)
    cam.data.keyframe_insert("lens", frame=frame)


# timed to the s2 voice (30 fps): "pollen trap" ~f175, "read yesterday" ~f200,
# "tested it the hard way" ~f242-280, cut to the lock timeline at f300 ("We wrote the test down")
key(1, (1.25, -2.05, 1.55), (0.02, 0.0, 1.0), 5.6, 50)            # wide 3/4 on the trap
key(165, (0.85, -1.45, 1.30), (0.03, 0.0, 1.02), 5.0, 50)         # slow dolly in
key(205, (0.42, -0.78, 1.12), (0.04, -0.02, 1.03), 3.2, 55)       # the cutaway: drum + tape
key(226, (0.40, -0.80, 1.10), (0.04, -0.02, 1.03), 3.2, 55)
key(252, (0.90, -1.50, 0.90), (0.70, -0.25, 0.0), 4.5, 50)        # swing down to the tape coming out on the paper
key(286, (1.55, -1.30, 0.85), (1.55, -0.25, 0.0), 5.6, 50)        # straight on: the tape is the strip
key(300, (1.55, -1.30, 0.85), (1.55, -0.25, 0.0), 5.6, 50)        # locked for the match cut

U0, U1 = 230, 282   # the unrolling: strip grows from the trap to full length (scale X from 0)
strip.scale = (0.001, TAPE_W * 3.0, 1)
strip.location.x = X0
strip.keyframe_insert("scale", frame=U0)
strip.keyframe_insert("location", frame=U0)
strip.scale = (TAPE_L, TAPE_W * 3.0, 1)
strip.location.x = X0 + TAPE_L / 2
strip.keyframe_insert("scale", frame=U1)
strip.keyframe_insert("location", frame=U1)
# grains and day ticks appear behind the unrolling front
for g in list(coll.objects) + ticks:
    t = U0 + int((U1 - U0) * (g.location.x - X0) / TAPE_L)
    g.hide_render = True
    g.keyframe_insert("hide_render", frame=max(1, t - 1))
    g.hide_render = False
    g.keyframe_insert("hide_render", frame=t)

if a.save:
    bpy.ops.wm.save_as_mainfile(filepath=a.save)
if a.still is not None:
    sc.frame_set(a.still)
    sc.render.filepath = a.out.rstrip("/") + f"/trap_still_{a.still:04d}.png"
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
