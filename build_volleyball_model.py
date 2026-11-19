"""
VolleyLab - 排球素模 3D 生成器
Blender 5.3 Python 脚本
----------------------------------
程序化创建：男性素模人体 + 骨骼绑定 + 排球网场地 + 4 套排球动作动画
导出 4 个 GLB（带骨骼动画 clip）

运行：
  D:\\blender.exe --background --python build_volleyball_model.py

输出目录：c:\\Users\\33685\\Desktop\\val\\volleylab_app\\assets\\www\\models\\
  skill-spike.glb   扣球
  skill-set.glb     二传
  skill-pass.glb    垫球
  skill-block.glb   拦网
"""

import bpy
import bmesh
import math
import mathutils
import os
import sys

# ========== 配置 ==========
OUTPUT_DIR = r"c:\Users\33685\Desktop\val\volleylab_app\assets\www\models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCALE = 0.01  # Blender 默认单位 → 米，100 = 1m

# ========== 工具函数 ==========
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    # 清除残留数据
    for block in bpy.data.meshes:
        if block.users == 0: bpy.data.meshes.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0: bpy.data.armatures.remove(block)
    for block in bpy.data.materials:
        if block.users == 0 and block.name != "Material": bpy.data.materials.remove(block)

def set_mesh_material(obj, color=(0.5, 0.55, 0.65, 1.0), name="BodyMat"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    # 用 type 找节点（Blender 5.3 中文版名"原理化 BSDF"，英文版"Principled BSDF"）
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out: mat.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.7
    bsdf.inputs["Metallic"].default_value = 0.0
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

# ========== 1. 创建场地 + 灯光 ==========
def create_arena():
    # 地面（球场）
    bpy.ops.mesh.primitive_plane_add(size=1)
    floor = bpy.context.active_object
    floor.scale = (12, 6, 1)
    floor.location = (0, 0, 0)
    floor.name = "Court"
    set_mesh_material(floor, (0.08, 0.10, 0.13, 1.0), "CourtMat")
    
    # 中线
    bpy.ops.mesh.primitive_cube_add(size=1)
    mid = bpy.context.active_object
    mid.scale = (12, 0.005, 0.01)
    mid.location = (0, 0, 0.005)
    mid.name = "MidLine"
    set_mesh_material(mid, (0.9, 0.95, 1.0, 1.0), "WhiteLine")
    
    # 球网两侧柱子
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=2.4, location=(0, -5.9, 1.2))
    pole1 = bpy.context.active_object
    pole1.name = "NetPole1"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=2.4, location=(0, 5.9, 1.2))
    pole2 = bpy.context.active_object
    pole2.name = "NetPole2"
    set_mesh_material(pole1, (0.25, 0.27, 0.32, 1.0), "PoleMat")
    set_mesh_material(pole2, (0.25, 0.27, 0.32, 1.0), "PoleMat")
    
    # 球网（平面 + 细线）
    bpy.ops.mesh.primitive_plane_add(size=1)
    net = bpy.context.active_object
    net.scale = (0.03, 5.8, 1.0)  # 竖平面
    net.rotation_euler.x = math.radians(90)
    net.location = (0, 0, 1.22)
    net.name = "Net"
    set_mesh_material(net, (0.75, 0.78, 0.82, 0.35), "NetMat")
    net.modifiers.new("Wireframe", "WIREFRAME")
    net.modifiers["Wireframe"].thickness = 0.002
    
    # 灯光
    bpy.ops.object.light_add(type="SUN", location=(5, 3, 8))
    sun = bpy.context.active_object
    sun.data.energy = 2.5
    sun.data.color = (1.0, 0.95, 0.88)
    
    bpy.ops.object.light_add(type="AREA", location=(-3, -3, 5))
    fill = bpy.context.active_object
    fill.data.energy = 80
    # Blender 5.3: AREA 灯光用 size 而不是 size，但 data 属性名变了
    try:
        fill.data.size = 6
    except AttributeError:
        try:
            fill.data.shape = "RECTANGLE"
            fill.data.size_x = 6
            fill.data.size_y = 6
        except AttributeError:
            pass

# ========== 2. 创建排球 ==========
def create_ball():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, segments=32, ring_count=16)
    ball = bpy.context.active_object
    ball.name = "Volleyball"
    set_mesh_material(ball, (0.95, 0.58, 0.24, 1.0), "BallMat")
    return ball

# ========== 3. 创建骨骼 Armature ==========
def create_armature():
    bpy.ops.object.armature_add(location=(0, 0, 0), radius=0.3)
    arm = bpy.context.active_object
    arm.name = "Skeleton"
    arm.data.display_type = "OCTAHEDRAL"
    arm.data.show_axes = True
    
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    
    # --- 重建骨骼结构 ---
    edit_bones = arm.data.edit_bones
    
    # 骨盆（根）—— 重命名默认骨骼
    pelvis = edit_bones[0]  # 取第一个默认骨骼（Blender 5.3 叫"骨骼"或"Bone"）
    pelvis.name = "Pelvis"
    pelvis.head = (0, 0, 0.95)
    pelvis.tail = (0, 0, 1.05)
    
    # 脊柱
    spine = edit_bones.new("Spine")
    spine.head = pelvis.head
    spine.tail = (0, 0, 1.25)
    spine.parent = pelvis
    
    chest = edit_bones.new("Chest")
    chest.head = spine.tail
    chest.tail = (0, 0, 1.48)
    chest.parent = spine
    
    # 头
    neck = edit_bones.new("Neck")
    neck.head = chest.tail
    neck.tail = (0, 0, 1.56)
    neck.parent = chest
    
    head = edit_bones.new("Head")
    head.head = neck.tail
    head.tail = (0, 0, 1.72)
    head.parent = neck
    
    # 左臂
    l_shoulder = edit_bones.new("L_Shoulder")
    l_shoulder.head = chest.head
    l_shoulder.tail = (-0.22, 0.05, 1.45)
    l_shoulder.parent = chest
    
    l_upper_arm = edit_bones.new("L_UpperArm")
    l_upper_arm.head = l_shoulder.tail
    l_upper_arm.tail = (-0.32, 0.05, 1.12)
    l_upper_arm.parent = l_shoulder
    
    l_elbow = edit_bones.new("L_Elbow")
    l_elbow.head = l_upper_arm.tail
    l_elbow.tail = (-0.38, 0.05, 0.82)
    l_elbow.parent = l_upper_arm
    
    l_hand = edit_bones.new("L_Hand")
    l_hand.head = l_elbow.tail
    l_hand.tail = (-0.40, 0.05, 0.58)
    l_hand.parent = l_elbow
    
    # 右臂（镜像）
    r_shoulder = edit_bones.new("R_Shoulder")
    r_shoulder.head = chest.head
    r_shoulder.tail = (0.22, 0.05, 1.45)
    r_shoulder.parent = chest
    
    r_upper_arm = edit_bones.new("R_UpperArm")
    r_upper_arm.head = r_shoulder.tail
    r_upper_arm.tail = (0.32, 0.05, 1.12)
    r_upper_arm.parent = r_shoulder
    
    r_elbow = edit_bones.new("R_Elbow")
    r_elbow.head = r_upper_arm.tail
    r_elbow.tail = (0.38, 0.05, 0.82)
    r_elbow.parent = r_upper_arm
    
    r_hand = edit_bones.new("R_Hand")
    r_hand.head = r_elbow.tail
    r_hand.tail = (0.40, 0.05, 0.58)
    r_hand.parent = r_elbow
    
    # 左腿
    l_hip = edit_bones.new("L_Hip")
    l_hip.head = pelvis.head
    l_hip.tail = (-0.12, 0, 0.58)
    l_hip.parent = pelvis
    
    l_knee = edit_bones.new("L_Knee")
    l_knee.head = l_hip.tail
    l_knee.tail = (-0.12, 0, 0.28)
    l_knee.parent = l_hip
    
    l_ankle = edit_bones.new("L_Ankle")
    l_ankle.head = l_knee.tail
    l_ankle.tail = (-0.12, 0.06, 0.03)
    l_ankle.parent = l_knee
    
    # 右腿
    r_hip = edit_bones.new("R_Hip")
    r_hip.head = pelvis.head
    r_hip.tail = (0.12, 0, 0.58)
    r_hip.parent = pelvis
    
    r_knee = edit_bones.new("R_Knee")
    r_knee.head = r_hip.tail
    r_knee.tail = (0.12, 0, 0.28)
    r_knee.parent = r_hip
    
    r_ankle = edit_bones.new("R_Ankle")
    r_ankle.head = r_knee.tail
    r_ankle.tail = (0.12, 0.06, 0.03)
    r_ankle.parent = r_knee
    
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm

# ========== 4. 创建素模人体（体块组合） ==========
def _set_mat_color(mat, color, roughness=0.85):
    mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out: mat.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness

def create_body(arm):
    # 材质
    skin_mat = bpy.data.materials.new("SkinMat")
    _set_mat_color(skin_mat, (0.45, 0.48, 0.52, 1.0), 0.85)
    
    dark_mat = bpy.data.materials.new("DarkMat")
    _set_mat_color(dark_mat, (0.18, 0.20, 0.24, 1.0), 0.9)
    
    def make_part(name, mesh_type, args, loc, mat, parent=None):
        if mesh_type == "cube":
            bpy.ops.mesh.primitive_cube_add(**args)
        elif mesh_type == "cyl":
            bpy.ops.mesh.primitive_cylinder_add(**args)
        elif mesh_type == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(**args)
        elif mesh_type == "capsule" or mesh_type == "cap":
            # Blender 5.3 移除了 capsule，用 cylinder + 两端 sphere 合并代替
            bpy.ops.mesh.primitive_cylinder_add(**args)
            bpy.context.active_object.name = name + "_shaft"
            # 上半球
            bpy.ops.mesh.primitive_uv_sphere_add(radius=args.get("radius", 0.05), location=(0, 0, args.get("depth", 0.3)/2))
            bpy.context.active_object.name = name + "_cap_top"
            # 下半球
            bpy.ops.mesh.primitive_uv_sphere_add(radius=args.get("radius", 0.05), location=(0, 0, -args.get("depth", 0.3)/2))
            bpy.context.active_object.name = name + "_cap_bot"
            # 合并
            bpy.ops.object.select_all(action="DESELECT")
            for suffix in ["_shaft", "_cap_top", "_cap_bot"]:
                obj = bpy.data.objects.get(name + suffix)
                if obj: obj.select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects.get(name + "_shaft")
            bpy.ops.object.join()
            obj = bpy.context.active_object
            obj.name = name
            obj.location = loc
            obj.data.materials.append(mat)
            return obj
        obj = bpy.context.active_object
        obj.name = name
        obj.location = loc
        obj.data.materials.append(mat)
        return obj
    
    # 骨盆
    pelvis = make_part("Body_Pelvis", "cube", {"size": 0.22}, (0, 0, 0.95), dark_mat)
    pelvis.scale = (1.0, 0.7, 0.5)
    
    # 躯干
    torso = make_part("Body_Torso", "cube", {"size": 0.3}, (0, 0, 1.32), dark_mat)
    torso.scale = (0.8, 0.45, 1.1)
    
    # 头
    head = make_part("Body_Head", "sphere", {"radius": 0.13}, (0, 0, 1.64), skin_mat)
    head.scale = (1, 0.95, 1.05)
    
    # 脖子
    neck = make_part("Body_Neck", "cyl", {"radius": 0.04, "depth": 0.08}, (0, 0, 1.55), skin_mat)
    
    # 肩膀 + 上臂（胶囊）
    l_upper = make_part("Body_L_Upper", "capsule", {"radius": 0.045, "depth": 0.35}, (-0.28, 0.05, 1.28), skin_mat)
    l_upper.scale = (1, 1, 1)
    l_upper.rotation_euler.z = math.radians(15)
    
    r_upper = make_part("Body_R_Upper", "capsule", {"radius": 0.045, "depth": 0.35}, (0.28, 0.05, 1.28), skin_mat)
    r_upper.rotation_euler.z = math.radians(-15)
    
    # 前臂
    l_fore = make_part("Body_L_Fore", "capsule", {"radius": 0.04, "depth": 0.3}, (-0.36, 0.05, 0.9), skin_mat)
    l_fore.rotation_euler.z = math.radians(60)
    
    r_fore = make_part("Body_R_Fore", "capsule", {"radius": 0.04, "depth": 0.3}, (0.36, 0.05, 0.9), skin_mat)
    r_fore.rotation_euler.z = math.radians(-60)
    
    # 手
    l_hand = make_part("Body_L_Hand", "sphere", {"radius": 0.045}, (-0.4, 0.05, 0.62), skin_mat)
    r_hand = make_part("Body_R_Hand", "sphere", {"radius": 0.045}, (0.4, 0.05, 0.62), skin_mat)
    
    # 大腿
    l_thigh = make_part("Body_L_Thigh", "capsule", {"radius": 0.06, "depth": 0.55}, (-0.12, 0, 0.58), skin_mat)
    r_thigh = make_part("Body_R_Thigh", "capsule", {"radius": 0.06, "depth": 0.55}, (0.12, 0, 0.58), skin_mat)
    
    # 小腿
    l_shin = make_part("Body_L_Shin", "capsule", {"radius": 0.045, "depth": 0.5}, (-0.12, 0, 0.28), skin_mat)
    r_shin = make_part("Body_R_Shin", "capsule", {"radius": 0.045, "depth": 0.5}, (0.12, 0, 0.28), skin_mat)
    
    # 脚（椭圆胶囊）
    l_foot = make_part("Body_L_Foot", "cube", {"size": 0.18}, (-0.12, 0.06, 0.03), dark_mat)
    l_foot.scale = (0.7, 1.3, 0.4)
    r_foot = make_part("Body_R_Foot", "cube", {"size": 0.18}, (0.12, 0.06, 0.03), dark_mat)
    r_foot.scale = (0.7, 1.3, 0.4)
    
    # 合并所有 body parts
    bpy.ops.object.select_all(action="DESELECT")
    body_objs = [obj for obj in bpy.data.objects if obj.name.startswith("Body_")]
    for obj in body_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body_objs[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = "PlayerMesh"
    
    # 绑定到 Armature（自动权重）
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE", xmirror=True)
    
    return body

# ========== 5. 创建排球动作动画（骨骼关键帧） ==========
def create_action(arm, name, keyframes):
    """
    keyframes: list of (frame, bone_name, location, rotation_euler)
    rotation_euler: tuple (rx, ry, rz) in radians, or None for static
    """
    arm.animation_data_create()
    action = bpy.data.actions.new(name=name)
    arm.animation_data.action = action
    arm.animation_data.action_slot = action.slots.new(arm, action.name)
    
    # 对骨骼设置关键帧
    for frame, bone_name, loc, rot in keyframes:
        # 进入 pose mode 设置 bone
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")
        
        bone = arm.pose.bones.get(bone_name)
        if bone:
            if loc is not None:
                bone.location = loc
                bone.keyframe_insert(data_path="location", frame=frame)
            if rot is not None:
                bone.rotation_mode = "XYZ"
                bone.rotation_euler = rot
                bone.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    bpy.ops.object.mode_set(mode="OBJECT")
    action.frame_range = (1, 60)  # 60帧 / 30fps = 2秒
    return action

def setup_clip_simple(arm, action_name, poses):
    """更可靠的简化版：直接在 Pose Mode 里逐帧设置骨骼姿态"""
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    
    # 重置所有 pose
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    
    # 为每个 pose 设置关键帧
    frame = 0
    arm.keyframe_insert(data_path="location", frame=0)
    arm.location = (0, 0, 0)
    arm.keyframe_insert(data_path="location", frame=0)
    
    for pose in poses:
        frame += pose.get("duration", 15)
        arm.location = pose.get("arm_location", (0, 0, 0))
        arm.keyframe_insert(data_path="location", frame=frame)
        
        for bone_name, rot in pose.get("rotations", {}).items():
            pb = arm.pose.bones.get(bone_name)
            if pb:
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = rot
                pb.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        for bone_name, loc in pose.get("locations", {}).items():
            pb = arm.pose.bones.get(bone_name)
            if pb:
                pb.location = loc
                pb.keyframe_insert(data_path="location", frame=frame)
    
    bpy.ops.object.mode_set(mode="OBJECT")
    
    # 重命名 action
    if arm.animation_data and arm.animation_data.action:
        action = arm.animation_data.action
        action.name = action_name
        action.frame_range = (0, frame)
    
    return frame

# ======== 4 套排球姿态 ========
def get_poses_spike():
    """扣球：准备姿势 → 助跑 → 起跳 → 挥臂 → 击球 → 落地"""
    d = math.radians
    return [
        {"duration": 10, "arm_location": (0, -1, 0),
         "rotations": {
             "Pelvis": (0, 0, 0), "Spine": (d(5), 0, 0), "Chest": (d(3), 0, 0),
             "L_Shoulder": (d(10), 0, d(15)), "L_UpperArm": (0, 0, d(35)), "L_Elbow": (0, 0, d(-20)),
             "R_Shoulder": (d(10), 0, d(-15)), "R_UpperArm": (0, 0, d(-35)), "R_Elbow": (0, 0, d(20)),
             "L_Hip": (0, 0, 0), "L_Knee": (0, 0, 0),
             "R_Hip": (0, 0, 0), "R_Knee": (0, 0, 0),
         }},
        {"duration": 10, "arm_location": (0.5, -0.5, 0),
         "rotations": {
             "Spine": (d(8), 0, d(15)), "Chest": (d(5), 0, d(10)),
             "L_UpperArm": (0, 0, d(45)), "R_UpperArm": (0, 0, d(-45)),
             "L_Knee": (0, 0, d(-25)), "R_Knee": (0, 0, d(-30)),
         }},
        {"duration": 8, "arm_location": (0.8, 0, 0.6),
         "rotations": {
             "Spine": (d(-5), 0, d(20)), "Chest": (d(-8), 0, d(15)),
             "L_Shoulder": (d(-20), 0, d(30)), "L_UpperArm": (d(-30), 0, d(60)), "L_Elbow": (d(-40), 0, d(10)),
             "R_Shoulder": (d(-25), 0, d(-60)), "R_UpperArm": (d(-50), 0, d(-100)), "R_Elbow": (0, 0, d(60)),
             "L_Knee": (0, 0, d(-45)), "R_Knee": (0, 0, d(-50)),
         }},
        {"duration": 6, "arm_location": (1.0, 0.5, 1.3),
         "rotations": {
             "Spine": (d(-15), 0, d(25)), "Chest": (d(-20), 0, d(20)),
             "R_Shoulder": (d(-80), 0, d(-140)), "R_UpperArm": (d(-60), d(-20), d(-170)), "R_Elbow": (d(-30), d(-10), d(-50)),
             "L_UpperArm": (d(-10), 0, d(40)),
             "L_Knee": (0, 0, d(-15)), "R_Knee": (0, 0, d(-10)),
         }},
        {"duration": 6, "arm_location": (1.0, 0.8, 1.4),
         "rotations": {
             "Spine": (d(-5), 0, d(20)), "Chest": (0, 0, d(15)),
             "R_Shoulder": (d(-50), 0, d(-90)), "R_UpperArm": (d(-30), 0, d(-60)), "R_Elbow": (0, 0, d(40)),
             "L_UpperArm": (0, 0, d(30)),
         }},
        {"duration": 10, "arm_location": (0.8, 0.6, 0),
         "rotations": {
             "Spine": (d(10), 0, d(15)), "Chest": (d(8), 0, d(10)),
             "R_UpperArm": (0, 0, d(-20)), "L_UpperArm": (0, 0, d(25)),
             "L_Knee": (0, 0, d(-30)), "R_Knee": (0, 0, d(-25)),
         }},
    ]

def get_poses_set():
    """二传：举球准备 → 传球手型 → 推送传球"""
    d = math.radians
    return [
        {"duration": 12, "arm_location": (0, -0.5, 0),
         "rotations": {
             "Spine": (d(8), 0, 0), "Chest": (d(5), 0, 0),
             "L_UpperArm": (d(20), 0, d(25)), "L_Elbow": (d(15), 0, d(-10)),
             "R_UpperArm": (d(20), 0, d(-25)), "R_Elbow": (d(15), 0, d(10)),
             "L_Knee": (0, 0, d(-20)), "R_Knee": (0, 0, d(-20)),
         }},
        {"duration": 8, "arm_location": (0, -0.3, 0),
         "rotations": {
             "Spine": (d(3), 0, 0), "Chest": (d(2), 0, 0),
             "L_Shoulder": (d(-5), 0, d(10)), "L_UpperArm": (d(-15), 0, d(15)), "L_Elbow": (d(25), 0, d(0)),
             "R_Shoulder": (d(-5), 0, d(-10)), "R_UpperArm": (d(-15), 0, d(-15)), "R_Elbow": (d(25), 0, d(0)),
             "L_Knee": (0, 0, d(-15)), "R_Knee": (0, 0, d(-15)),
         }},
        {"duration": 10, "arm_location": (0, -0.2, 0),
         "rotations": {
             "Spine": (d(-8), 0, 0), "Chest": (d(-10), 0, 0),
             "L_UpperArm": (d(-30), 0, d(5)), "L_Elbow": (d(35), 0, d(0)),
             "R_UpperArm": (d(-30), 0, d(-5)), "R_Elbow": (d(35), 0, d(0)),
             "L_Knee": (0, 0, d(-5)), "R_Knee": (0, 0, d(-5)),
         }},
        {"duration": 8, "arm_location": (0, 0.3, 0),
         "rotations": {
             "Spine": (d(-3), 0, d(10)), "Chest": (d(-5), 0, d(8)),
             "L_UpperArm": (d(-5), 0, d(-15)), "L_Elbow": (d(10), 0, d(5)),
             "R_UpperArm": (d(-5), 0, d(-35)), "R_Elbow": (d(10), 0, d(5)),
             "L_Knee": (0, 0, d(-10)), "R_Knee": (0, 0, d(-10)),
         }},
    ]

def get_poses_pass():
    """垫球：低姿准备 → 双臂并拢 → 垫球 → 跟随"""
    d = math.radians
    return [
        {"duration": 10, "arm_location": (0.3, -0.3, 0),
         "rotations": {
             "Spine": (d(25), 0, 0), "Chest": (d(15), 0, 0),
             "L_UpperArm": (d(30), 0, d(20)), "L_Elbow": (d(50), 0, d(-10)),
             "R_UpperArm": (d(30), 0, d(-20)), "R_Elbow": (d(50), 0, d(10)),
             "L_Knee": (0, 0, d(-55)), "R_Knee": (0, 0, d(-55)),
         }},
        {"duration": 6, "arm_location": (0.25, -0.25, 0),
         "rotations": {
             "Spine": (d(30), 0, 0),
             "L_UpperArm": (d(55), 0, d(0)), "L_Elbow": (d(25), 0, d(0)),
             "R_UpperArm": (d(55), 0, d(0)), "R_Elbow": (d(25), 0, d(0)),
             "L_Knee": (0, 0, d(-60)), "R_Knee": (0, 0, d(-60)),
         }},
        {"duration": 6, "arm_location": (0.2, -0.2, 0.05),
         "rotations": {
             "Spine": (d(35), 0, 0),
             "L_UpperArm": (d(65), 0, d(0)), "L_Elbow": (d(15), 0, d(0)),
             "R_UpperArm": (d(65), 0, d(0)), "R_Elbow": (d(15), 0, d(0)),
             "L_Knee": (0, 0, d(-65)), "R_Knee": (0, 0, d(-65)),
         }},
        {"duration": 6, "arm_location": (0.1, -0.1, 0.15),
         "rotations": {
             "Spine": (d(20), 0, 0),
             "L_UpperArm": (d(40), 0, d(5)), "L_Elbow": (d(30), 0, d(-5)),
             "R_UpperArm": (d(40), 0, d(-5)), "R_Elbow": (d(30), 0, d(5)),
             "L_Knee": (0, 0, d(-45)), "R_Knee": (0, 0, d(-45)),
         }},
    ]

def get_poses_block():
    """拦网：近网站位 → 微屈膝 → 起跳封网 → 落地"""
    d = math.radians
    return [
        {"duration": 10, "arm_location": (0, 0, 0),
         "rotations": {
             "Spine": (d(3), 0, 0),
             "L_UpperArm": (d(-5), 0, d(15)), "R_UpperArm": (d(-5), 0, d(-15)),
             "L_Knee": (0, 0, d(-10)), "R_Knee": (0, 0, d(-10)),
         }},
        {"duration": 8, "arm_location": (0, 0, 0),
         "rotations": {
             "L_UpperArm": (d(-15), 0, d(10)), "L_Elbow": (d(20), 0, d(-5)),
             "R_UpperArm": (d(-15), 0, d(-10)), "R_Elbow": (d(20), 0, d(5)),
             "L_Knee": (0, 0, d(-40)), "R_Knee": (0, 0, d(-40)),
         }},
        {"duration": 6, "arm_location": (0, 0, 0.8),
         "rotations": {
             "Spine": (d(-5), 0, 0),
             "L_Shoulder": (d(-40), 0, d(10)), "L_UpperArm": (d(-140), 0, d(25)), "L_Elbow": (d(-50), 0, d(10)),
             "R_Shoulder": (d(-40), 0, d(-10)), "R_UpperArm": (d(-140), 0, d(-25)), "R_Elbow": (d(-50), 0, d(-10)),
             "L_Knee": (0, 0, d(-15)), "R_Knee": (0, 0, d(-15)),
         }},
        {"duration": 8, "arm_location": (0, 0, 1.3),
         "rotations": {
             "Spine": (d(-8), 0, 0),
             "L_Shoulder": (d(-70), 0, d(5)), "L_UpperArm": (d(-160), 0, d(15)), "L_Elbow": (d(-5), 0, d(5)),
             "R_Shoulder": (d(-70), 0, d(-5)), "R_UpperArm": (d(-160), 0, d(-15)), "R_Elbow": (d(-5), 0, d(-5)),
             "L_Knee": (0, 0, d(-5)), "R_Knee": (0, 0, d(-5)),
         }},
        {"duration": 8, "arm_location": (0, 0, 0),
         "rotations": {
             "L_UpperArm": (d(-5), 0, d(15)), "L_Elbow": (d(30), 0, d(-10)),
             "R_UpperArm": (d(-5), 0, d(-15)), "R_Elbow": (d(30), 0, d(10)),
             "L_Knee": (0, 0, d(-50)), "R_Knee": (0, 0, d(-50)),
         }},
    ]

# ========== 6. 导出 GLB ==========
def export_glb(filepath, animate=True):
    # Blender 5.3 gltf 导出器参数重构，用最简参数
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        use_selection=False,
        export_animations=animate,
    )
    print(f"Exported: {filepath}")

# ========== 主流程 ==========
def main():
    print("=== VolleyLab 3D Builder ===")
    print(f"Output: {OUTPUT_DIR}")
    
    # --- 扣球 ---
    print("\n[1/4] Building SPIKE ...")
    clear_scene()
    create_arena()
    ball = create_ball()
    arm = create_armature()
    body = create_body(arm)
    setup_clip_simple(arm, "spike", get_poses_spike())
    bpy.context.scene.frame_end = 60
    export_glb(os.path.join(OUTPUT_DIR, "skill-spike.glb"))
    
    # --- 二传 ---
    print("\n[2/4] Building SET ...")
    clear_scene()
    create_arena()
    ball = create_ball()
    arm = create_armature()
    body = create_body(arm)
    setup_clip_simple(arm, "set", get_poses_set())
    bpy.context.scene.frame_end = 40
    export_glb(os.path.join(OUTPUT_DIR, "skill-set.glb"))
    
    # --- 垫球 ---
    print("\n[3/4] Building PASS ...")
    clear_scene()
    create_arena()
    ball = create_ball()
    arm = create_armature()
    body = create_body(arm)
    setup_clip_simple(arm, "pass", get_poses_pass())
    bpy.context.scene.frame_end = 32
    export_glb(os.path.join(OUTPUT_DIR, "skill-pass.glb"))
    
    # --- 拦网 ---
    print("\n[4/4] Building BLOCK ...")
    clear_scene()
    create_arena()
    ball = create_ball()
    arm = create_armature()
    body = create_body(arm)
    setup_clip_simple(arm, "block", get_poses_block())
    bpy.context.scene.frame_end = 50
    export_glb(os.path.join(OUTPUT_DIR, "skill-block.glb"))
    
    print("\n=== ALL DONE ===")
    print(f"Check: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
