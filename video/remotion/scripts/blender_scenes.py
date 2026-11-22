"""Two short EEVEE clips for the PollenPlan film. Run: blender -b -P blender_scenes.py
Env: ONLY=hook|grid to render one; TEST=1 renders frame 1 of each only."""
import bpy, math, os, random, subprocess, sys, time, shutil
from mathutils import Vector

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", "media"))
W, H, FPS = 1280, 720, 30
TEST = os.environ.get("TEST") == "1"
ONLY = os.environ.get("ONLY")

def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), a)

def reset(bg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 4
    try: sc.eevee.use_shadows = False
    except Exception as e: print("use_shadows:", e)
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = hexc(bg)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.world = w
    return sc

def emit_mat(name, col, strength, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if alpha >= 1:
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value = hexc(col); e.inputs[1].default_value = strength
        nt.links.new(e.outputs[0], out.inputs[0])
    else:
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value = hexc(col); e.inputs[1].default_value = strength
        t = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs[0].default_value = alpha
        nt.links.new(t.outputs[0], mix.inputs[1]); nt.links.new(e.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
    if alpha < 1:
        try: m.surface_render_method = "BLENDED"
        except Exception as e: print("blend:", e)
    return m

def orb_mat(name, col, strength):
    """Emission brighter at the core, darker at the rim: reads as a soft 3D sphere."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.15; ramp.color_ramp.elements[0].color = hexc(col)
    ramp.color_ramp.elements[1].position = 0.9
    c = hexc(col); ramp.color_ramp.elements[1].color = (c[0]*0.12, c[1]*0.12, c[2]*0.12, 1)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[1].default_value = strength
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], e.inputs[0])
    nt.links.new(e.outputs[0], out.inputs[0])
    return m

def diffuse_mat(name, col, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hexc(col); b.inputs["Roughness"].default_value = rough
    return m

def camera(loc, target, lens=35):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = lens
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam

def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def render(sc, folder, frames, mp4):
    shutil.rmtree(folder, ignore_errors=True); os.makedirs(folder)
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.filepath = folder + "/"
    n = 1 if TEST else frames
    t = time.time()
    if TEST:
        sc.frame_set(1); sc.render.filepath = folder + "/0001.png"
        bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = folder + "/"
        sc.render.image_settings.file_format = "PNG"
        for f in range(1, frames + 1):
            sc.frame_set(f); sc.render.filepath = f"{folder}/{f:04d}.png"
            bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    print(f"RENDER {mp4}: {n} frames in {dt:.1f}s ({dt/n:.2f}s/frame)")
    if not TEST:
        os.makedirs(OUT_DIR, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", folder + "/%04d.png",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
                        os.path.join(OUT_DIR, mp4)], check=True)

# ---------- Clip A: pollen hook ----------
def clip_hook():
    sc = reset("#0D1117")
    random.seed(7)
    cam = camera((0, -9, 0), (0, 0, 0), lens=50); cam.location = (0, -10, 0.3); aim(cam, (0, 0, 0))
    mats = [orb_mat("amber", "#F5A524", 1.3), orb_mat("gold", "#FFD166", 1.1), orb_mat("teal", "#4ECCA3", 1.1),
            orb_mat("deep", "#0F766E", 1.2)]
    weights = [0.38, 0.27, 0.25, 0.10]
    for i in range(70):
        # near-field clusters in front of camera, wide spread in depth
        x, z = random.gauss(0, 3.4), random.gauss(0, 1.9)
        y = random.uniform(-5.5, 6)
        r = random.uniform(0.07, 0.34) * (1 + 0.15 * (y > 0))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(x, y, z))
        o = bpy.context.active_object
        # organic: random displacement of verts
        for v in o.data.vertices:
            v.co *= random.uniform(0.82, 1.18)
        o.rotation_euler = [random.uniform(0, 6.28) for _ in range(3)]
        o.data.materials.append(random.choices(mats, weights)[0])
        # depth drift (loops cleanly) + sway
        dy = random.uniform(0.8, 1.8); ph = random.uniform(0, 6.28); sw = random.uniform(0.15, 0.5)
        for f in (1, 61, 121):
            t = (f - 1) / 120 * 2 * math.pi
            o.location = (x + sw * math.sin(t + ph), y + dy * math.sin(t + ph * 0.5), z + sw * math.cos(t + ph))
            o.keyframe_insert("location", frame=f)
        o.rotation_euler = o.rotation_euler
    # slow camera push-in
    cam.location = (0, -10, 0.3); cam.keyframe_insert("location", frame=1)
    cam.location = (0.4, -8.6, 0.1); cam.keyframe_insert("location", frame=120)
    for fc in cam.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if hasattr(cam.animation_data.action, "layers") else []:
        for kp in fc.keyframe_points: kp.interpolation = "BEZIER"
    render(sc, "/tmp/bl_hook", 120, "flow_pollen_hook.mp4")

# ---------- Clip B: grid vs traps ----------
def clip_grid():
    sc = reset("#0D1117")
    # ground
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    g = bpy.context.active_object; g.data.materials.append(emit_mat("ground", "#161B22", 1.0))
    # ground grid lines (thin emissive 11 km cell edges)
    lm = emit_mat("gline", "#0F766E", 0.7)
    for i in range(-4, 5):
        for ax in (0, 1):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 2 if ax == 0 else 0, i * 2 if ax == 1 else 0, 0.01))
            o = bpy.context.active_object
            o.scale = (0.012, 16, 0.004) if ax == 0 else (16, 0.012, 0.004)
            o.data.materials.append(lm)
    # translucent voxel cube (one CAMS ~11 km cell) as wireframe edges + faint faces
    S, Zc = 4.0, 3.2
    bpy.ops.mesh.primitive_cube_add(size=S, location=(0, 0, Zc))
    c = bpy.context.active_object
    c.data.materials.append(emit_mat("glass", "#0F766E", 1.0, alpha=0.16))
    bpy.ops.object.modifier_add(type="SUBSURF") if False else None
    # voxel subdivision lines: 3x3x3 wireframe
    bpy.ops.mesh.primitive_cube_add(size=S, location=(0, 0, Zc))
    wf = bpy.context.active_object
    sub = wf.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = "SIMPLE"; sub.levels = 1; sub.render_levels = 1
    w = wf.modifiers.new("wire", "WIREFRAME"); w.thickness = 0.02; w.use_replace = True
    wf.data.materials.append(emit_mat("wire", "#0F766E", 2.0))
    # beacons: Madrid, Basel, Zurich rooftops
    bm = emit_mat("beacon", "#4ECCA3", 1.3)
    cap = emit_mat("cap", "#BFF7E4", 1.4)
    spots = [(-1.6, -0.9), (0.2, 1.4), (1.7, -0.4)]
    for (x, y) in spots:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=3.0, location=(x, y, 1.5))
        p = bpy.context.active_object; p.data.materials.append(bm)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.2, location=(x, y, 3.05))
        s = bpy.context.active_object; s.data.materials.append(cap)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.015, location=(x, y, 0.03))
        t = bpy.context.active_object; t.data.materials.append(bm)
        for f, sc_ in ((1, 1.0), (75, 1.6), (150, 1.0)):
            t.scale = (sc_, sc_, 1); t.keyframe_insert("scale", frame=f)
    # camera orbit
    cam = camera((0, 0, 0), (0, 0, 2.2), lens=32)
    R, Zcam = 11.5, 5.2
    for f in range(1, 151, 5):
        a = math.radians(-35 + 70 * (f - 1) / 149)
        cam.location = (R * math.sin(a), -R * math.cos(a), Zcam)
        aim(cam, (0, 0, 2.2))
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    render(sc, "/tmp/bl_grid", 150, "blender_pollen_grid.mp4")

if ONLY != "grid": clip_hook()
if ONLY != "hook": clip_grid()
