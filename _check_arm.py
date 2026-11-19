import bpy
bpy.ops.object.armature_add(location=(0,0,0), radius=0.3)
arm = bpy.context.active_object
bpy.ops.object.mode_set(mode="EDIT")
for eb in arm.data.edit_bones:
    print(f"EditBone: name='{eb.name}'")
bpy.ops.object.mode_set(mode="OBJECT")
