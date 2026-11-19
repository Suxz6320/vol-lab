import bpy
bpy.ops.mesh.primitive_plane_add(size=1)
obj = bpy.context.active_object
mat = bpy.data.materials.new("Test")
mat.use_nodes = True
obj.data.materials.append(mat)
tree = mat.node_tree
for n in tree.nodes:
    print(f"Node: name='{n.name}', type='{n.type}', bl_idname='{n.bl_idname}'")
