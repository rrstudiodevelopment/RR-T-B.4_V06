
import bpy
import webbrowser
from bpy.props import FloatVectorProperty

#============================================ Anti-Lag ===================================================================
def update_simplify_subdivision(self, context):
    context.scene.render.simplify_subdivision = context.scene.simplify_subdivision

def pre_save_handler(dummy):
    scene = bpy.context.scene
    
    # Periksa apakah checkbox "Save Aman" aktif
    if not scene.get("save_aman", False):
        return  # Jika tidak aktif, tidak menjalankan script
    
    # Cek apakah use_simplify aktif
    if scene.render.use_simplify:
        scene.render.use_simplify = False
        print("Simplify dinonaktifkan sebelum menyimpan.")  
    
    # Ubah viewport shading ke wireframe
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'WIREFRAME'
                    print("Mode viewport diubah ke wireframe sebelum menyimpan.")
                    break

# ======================================= override_and_make_local  LINK  =================================================

def override_and_make_local(self, context):
    selected_objects = context.selected_objects
    
    if not selected_objects:
        self.report({'WARNING'}, "No objects selected")
        return {'CANCELLED'}
    
    for obj in selected_objects:
        bpy.context.view_layer.objects.active = obj  # Set active object
        bpy.ops.object.make_override_library()  # Override Library
        bpy.ops.object.make_local(type='SELECT_OBJECT')  # Make Local
    
    self.report({'INFO'}, "Overrides and Locals Applied")
    return {'FINISHED'}

class OBJECT_OT_OnlyOverride(bpy.types.Operator):
    """Hanya Make Override Library (tanpa Make Local)"""
    bl_idname = "object.only_override"
    bl_label = "Make Override Only"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        for obj in selected_objects:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.make_override_library()

        self.report({'INFO'}, "Only Override Applied")
        return {'FINISHED'}


#operator tombol untuk override
class OBJECT_OT_OverrideLocal(bpy.types.Operator):
    """Convert selected objects to override and make them local"""
    bl_idname = "object.override_local"
    bl_label = "Override & Make Local"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        return override_and_make_local(self, context)  
     
# Tambahkan properti checkbox dan slider di Scene
bpy.types.Scene.save_aman = bpy.props.BoolProperty(
    name="Save Aman",
    description="Aktifkan untuk menjalankan script sebelum menyimpan",
    default=False
)

bpy.types.Scene.simplify_subdivision = bpy.props.IntProperty(
    name="Simplify Subdivision",
    description="Atur nilai simplify subdivision",
    default=2,
    min=0,
    max=10,
    update=update_simplify_subdivision
)

# Mendaftarkan fungsi pre_save_handler ke event penyimpanan
bpy.app.handlers.save_pre.append(pre_save_handler)    
#=======================================================================================================================
 # CURSOR SELECTED 

class OBJECT_OT_CursorToSelected(bpy.types.Operator):
    """Move Cursor to Selected Bone (Shift+S, then 2 on numpad)"""
    bl_idname = "object.cursor_to_selected"
    bl_label = "Cursor to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object and context.active_object.type == 'ARMATURE':
            bpy.ops.view3d.snap_cursor_to_selected()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Please select bones in Pose Mode!")
            return {'CANCELLED'}

class OBJECT_OT_SelectToCursor(bpy.types.Operator):
    """Move Selected Bone to Cursor (Shift+S, then 8 on numpad)"""
    bl_idname = "object.select_to_cursor"
    bl_label = "Select to Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object and context.active_object.type == 'ARMATURE':
            bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Please select bones in Pose Mode!")
            return {'CANCELLED'}
# ======================================================================================================================
#                                  ALLIGN TOOLS

class OBJECT_OT_AlignTool(bpy.types.Operator):
    """Apply Copy Rotation and Location Constraints"""
    bl_idname = "pose.align_tool"
    bl_label = "Align Tool"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'WARNING'}, "Please switch to Pose Mode!")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        active_bone = context.active_pose_bone

        if len(selected_bones) < 2 or active_bone is None:
            self.report({'WARNING'}, "Please select at least 2 bones and ensure one is active!")
            return {'CANCELLED'}

        target_bone = active_bone
        source_bone = next((bone for bone in selected_bones if bone != target_bone), None)

        if not source_bone:
            self.report({'ERROR'}, "Unable to determine the source bone!")
            return {'CANCELLED'}

        # Add Copy Rotation and Copy Location Constraints
        copy_rot_constraint = source_bone.constraints.new(type='COPY_ROTATION')
        copy_rot_constraint.name = "CopasRot"
        copy_rot_constraint.target = context.object
        copy_rot_constraint.subtarget = target_bone.name

        copy_loc_constraint = source_bone.constraints.new(type='COPY_LOCATION')
        copy_loc_constraint.name = "CopasPos"
        copy_loc_constraint.target = context.object
        copy_loc_constraint.subtarget = target_bone.name

        # Apply constraints
        bpy.context.view_layer.update()
        bpy.ops.pose.visual_transform_apply()

        # Remove constraints
        source_bone.constraints.remove(copy_rot_constraint)
        source_bone.constraints.remove(copy_loc_constraint)

        self.report({'INFO'}, f"Applied Align Tool: {target_bone.name} to {source_bone.name}")
        return {'FINISHED'}
 #====================================================================================================================
 
 #                                      COPY ROTATE    
 
 # Operator untuk Auto Copy Rotation Constraint
class OBJECT_OT_CopyRotation(bpy.types.Operator):
    """Copy Rotation from Selected Bone to Active"""
    bl_idname = "pose.auto_copy_rotation_constraint"
    bl_label = "Auto Copy Rotation Constraint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Ensure the operator is run in Pose Mode with at least two bones selected
        if not context.mode == 'POSE':
            self.report({'WARNING'}, "Please switch to Pose Mode!")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        active_bone = context.active_pose_bone

        if len(selected_bones) < 2 or active_bone is None:
            self.report({'WARNING'}, "Please select at least 2 bones and ensure one is active!")
            return {'CANCELLED'}

        # Active bone as target (second selected bone)
        target_bone = active_bone

        # Determine the source bone (the other bone in the selection)
        source_bone = next((bone for bone in selected_bones if bone != target_bone), None)

        if not source_bone:
            self.report({'ERROR'}, "Unable to determine the source bone!")
            return {'CANCELLED'}

        # Add a Copy Rotation Constraint to the source bone
        constraint = source_bone.constraints.new(type='COPY_ROTATION')
        constraint.name = "CopasRot"
        constraint.target = context.object  # Armature object
        constraint.subtarget = target_bone.name  # Set target to the active bone

        # Update the scene to ensure constraints are applied correctly
        bpy.context.view_layer.update()

        # Apply the constraint (Ctrl + A equivalent in Blender for pose transforms)
        bpy.ops.pose.visual_transform_apply()

        # Remove the constraint after applying (to bake the transformation)
        source_bone.constraints.remove(constraint)

        self.report({'INFO'}, f"Copy Rotation Constraint applied from {target_bone.name} to {source_bone.name}.")
        return {'FINISHED'}
    
#======================================= Copy Miror ============================================================= 
class OBJECT_OT_CopyMirrorPose(bpy.types.Operator):
    """Copy Pose and Mirror it to the other side"""
    bl_idname = "pose.copy_mirror_pose"
    bl_label = "Copy Mirror Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'WARNING'}, "Switch to Pose Mode to use this.")
            return {'CANCELLED'}

        bpy.ops.pose.copy()
        bpy.ops.pose.paste(flipped=True)
        self.report({'INFO'}, "Pose copied and mirrored.")
        return {'FINISHED'}
    
    
       

#=========================================================================================================================
class FLOATING_OT_Decimate_Temporary(bpy.types.Operator):
    bl_idname = "floating.open_decimate_temporary"
    bl_label = "open_decimate_temporary"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="VIEW3D_PT_decimate_panel", keep_open=True)  
        return {'FINISHED'}  



# ==================== Properties ====================
class PoseCopyPasteProps(bpy.types.PropertyGroup):
    flipped: bpy.props.BoolProperty(
        name="Flipped Paste",
        description="Paste pose as mirror",
        default=False
    )

# ==================== Operators ====================
class POSE_OT_CopyPose(bpy.types.Operator):
    bl_idname = "pose_tools.copy_pose"
    bl_label = "Copy Pose"
    bl_description = "Copy current pose"

    def execute(self, context):
        bpy.ops.pose.copy()
        self.report({'INFO'}, "Pose copied")
        return {'FINISHED'}


class POSE_OT_PastePose(bpy.types.Operator):
    bl_idname = "pose_tools.paste_pose"
    bl_label = "Paste Pose"
    bl_description = "Paste pose normally (not flipped)"

    def execute(self, context):
        bpy.ops.pose.paste(flipped=False)
        self.report({'INFO'}, "Pose pasted")
        return {'FINISHED'}


class POSE_OT_PastePoseFlipped(bpy.types.Operator):
    bl_idname = "pose_tools.paste_pose_flipped"
    bl_label = "Paste Mirror"
    bl_description = "Paste pose as mirror (flipped)"

    def execute(self, context):
        bpy.ops.pose.paste(flipped=True)
        self.report({'INFO'}, "Pose pasted (flipped)")
        return {'FINISHED'}
    
        
#=========================================================================================================================
#                       ADD CONTROLER 

# Script 1: Operator untuk menjalankan Raha Tools
class OBJECT_OT_add_controler(bpy.types.Operator):
    bl_idname = "object.add_controler"
    bl_label = "add controler"
    
    def execute(self, context):
        # Pindah ke Object Mode
        bpy.ops.object.posemode_toggle()

        # Tambahkan curve
        bpy.ops.curve.primitive_bezier_circle_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.object.name = "For_add_CTRL_BezierCircle"

        # Tambahkan armature dengan satu bone, pastikan location dan rotation di (0,0,0)
        bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))
        armature = bpy.context.object
        armature.location = (0, 0, 0)
        armature.rotation_euler = (0, 0, 0)

        # Pindah ke Edit Mode untuk mengedit bone
        bpy.ops.object.editmode_toggle()

        # Pilih bone pertama dan ubah namanya menjadi 'induk'
        armature_data = bpy.context.object.data
        first_bone = armature_data.edit_bones[0]  # Bone pertama yang ditambahkan
        first_bone.select = True
        first_bone.name = "induk"
        first_bone.head = (0, 0, 0)
        first_bone.tail = (0, 0, 1)

        # Deselect bone yang baru diberi nama
        first_bone.select = False

        # Tambahkan bone kedua (child)
        bpy.ops.armature.bone_primitive_add()

        # Pilih bone kedua dan ubah namanya menjadi 'child'
        second_bone = armature_data.edit_bones[-1]  # Bone terakhir yang ditambahkan
        second_bone.name = "child"
        second_bone.head = (0, 0, 0)
        second_bone.tail = (0, 0, 1)

        #selected child - induk lalu parent keep offset
        bpy.context.object.data.edit_bones["child"].select = True
        bpy.context.object.data.edit_bones["induk"].select = True
        bpy.ops.armature.parent_set(type='OFFSET')
        bpy.context.object.data.edit_bones["child"].select = False
        bpy.context.object.data.edit_bones["induk"].select = False

        # Pindah ke Pose Mode
        bpy.ops.object.posemode_toggle()

        #selected child
        bpy.context.object.pose.bones["child"].bone.select = True
        #ubah ke euler
        bpy.context.object.pose.bones["child"].rotation_mode = 'XYZ'
        #masukan custom display beziercircle
        bpy.context.object.pose.bones["child"].custom_shape = bpy.data.objects["For_add_CTRL_BezierCircle"]
        #rotate x nya 90 derajat
        bpy.context.object.pose.bones["child"].custom_shape_rotation_euler[0] = 1.5708
        #unselect child
        bpy.context.object.pose.bones["child"].bone.select = False

        # Selected induk
        bpy.context.object.pose.bones["induk"].bone.select = True
        #ubah ke euler
        bpy.context.object.pose.bones["induk"].rotation_mode = 'XYZ'
        #masukan custom display beziercircle
        bpy.context.object.pose.bones["induk"].custom_shape = bpy.data.objects["For_add_CTRL_BezierCircle"]
        #rotate x nya 90 derajat
        bpy.context.object.pose.bones["induk"].custom_shape_rotation_euler[0] = 1.5708
        #scale custom shape
        bpy.context.object.pose.bones["induk"].custom_shape_scale_xyz = (1.3, 1.3, 1.3)

        #balik ke object mode
        bpy.ops.object.posemode_toggle()

        #ubah nama add controler
        bpy.context.object.name = "add_ctrl_armature"

        # Nama koleksi tujuan
        collection_name = "ETC"

        # Periksa apakah koleksi sudah ada, jika tidak buat koleksi baru
        if collection_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)
            print(f"Koleksi '{collection_name}' berhasil dibuat.")
        else:
            new_collection = bpy.data.collections[collection_name]
            print(f"Koleksi '{collection_name}' sudah ada.")

        # Pastikan ada objek aktif yang bisa dipindahkan
        active_object = bpy.context.active_object
        if active_object:
            # Hapus objek dari koleksi saat ini
            for collection in active_object.users_collection:
                collection.objects.unlink(active_object)

            # Pindahkan objek ke koleksi "ETC"
            new_collection.objects.link(active_object)
            print(f"Objek '{active_object.name}' telah dipindahkan ke koleksi '{collection_name}'.")
        else:
            print("Tidak ada objek aktif untuk dipindahkan.")

        #deselect all
        bpy.ops.object.select_all(action='DESELECT')

        # Pastikan berada di Object Mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect semua objek terlebih dahulu
        bpy.ops.object.select_all(action='DESELECT')

        # Loop untuk memilih objek yang namanya diawali dengan "For_add_CTRL_BezierCircle"
        for obj in bpy.data.objects:
            if obj.name.startswith("For_add_CTRL_BezierCircle") and obj.visible_get():
                obj.select_set(True)

        print("Object dengan nama awal 'For_add_CTRL_BezierCircle' berhasil dipilih.")

        #hapus curve        
        bpy.ops.object.delete()

        return {'FINISHED'}
#==========================================================================================
   
 
#=====================================================================================================================  

#  ======================================================  TOMBOL ============================================== 
class VIEW3D_PT_MiniTools(bpy.types.Panel):
    bl_label = "Raha Mini Tools"
    bl_idname = "VIEW3D_PT_mini_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10
                
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        wm = context.window_manager
        
        # Main styling settings
        layout.use_property_split = True
        layout.use_property_decorate = False  # Smoother animation
        



        # ==================== SAFETY & SIMPLIFY ====================
        safety_box = layout.box()
        safety_box.label(text="Performance", icon='TIME')               
                
        safety_box.prop(scene, "save_aman", text="Safety Mode", icon='LOCKED' if scene.save_aman else 'UNLOCKED')
        safety_box.prop(scene.render, "use_simplify", text="Simplify Render")
        
        if scene.render.use_simplify:
            simplify_row = safety_box.row()
            simplify_row.prop(scene, "simplify_subdivision", text="Subdivision", slider=True)
        
        # ==================== LINK TOOLS ====================
        link_box = layout.box()
        link_box.label(text="Linking Tools", icon='LINKED')
        
        flow = link_box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        flow.operator("object.only_override", text="Make Override", icon="LINKED")
        flow.operator("object.override_local", text="Local Override", icon="FILE_TICK")
        
        # ==================== ALIGNMENT TOOLS ====================
        align_box = layout.box()
        align_box.label(text="Bone Alignment", icon='BONE_DATA')
        
        align_grid = align_box.grid_flow(row_major=True, columns=3, even_columns=True, align=True)
        align_grid.operator("object.cursor_to_selected", text="", icon="CURSOR")
        align_grid.operator("object.select_to_cursor", text="", icon="PIVOT_CURSOR")
        align_grid.operator("pose.align_tool", text="", icon="CON_TRANSFORM")
        
        # ==================== POSE TOOLS ====================
        pose_box = layout.box()
        pose_box.label(text="Pose Tools", icon='ARMATURE_DATA')
        
        pose_grid = pose_box.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        pose_grid.operator("pose.auto_copy_rotation_constraint", text="Copy Rotation", icon="AUTOMERGE_ON")
        pose_grid.operator("pose.copy_mirror_pose", text="Mirror Pose", icon="ARMATURE_DATA")  

        pose_grid = pose_box.grid_flow(row_major=True, columns=3, even_columns=True, align=True)
      
        pose_grid.operator("pose_tools.copy_pose", text="", icon='COPYDOWN')
        pose_grid.operator("pose_tools.paste_pose", text="", icon='PASTEDOWN')
        pose_grid.operator("pose_tools.paste_pose_flipped", text="", icon='MOD_MIRROR')        
          
        pose_box = layout.box()         
        pose_box.operator("object.add_controler", text="Add Controller", icon="BONE_DATA")
                            
          
#=========================================================================================================================
#                                               REGISTER     
# Daftar operator dan panel untuk registrasi
def register():
    
    
    bpy.types.Scene.simplify_subdivision = bpy.props.IntProperty(
        name="Simplify Subdivision",
        description="Atur nilai simplify subdivision",
        default=5,
        min=0,
        max=10,
        update=update_simplify_subdivision
    )    
    
    bpy.utils.register_class(FLOATING_OT_Decimate_Temporary)     
    bpy.utils.register_class(OBJECT_OT_OverrideLocal)
    bpy.utils.register_class(OBJECT_OT_OnlyOverride)    
    
    bpy.utils.register_class(OBJECT_OT_CursorToSelected)
    bpy.utils.register_class(OBJECT_OT_SelectToCursor)
    bpy.utils.register_class(OBJECT_OT_AlignTool)
    bpy.utils.register_class(OBJECT_OT_CopyMirrorPose)     
    bpy.utils.register_class(OBJECT_OT_CopyRotation)  
         
              
    bpy.utils.register_class(VIEW3D_PT_MiniTools)    
    bpy.utils.register_class(OBJECT_OT_add_controler)      
    
    bpy.utils.register_class(PoseCopyPasteProps) 
    bpy.utils.register_class(POSE_OT_CopyPose)            
    bpy.utils.register_class(POSE_OT_PastePose) 
    bpy.utils.register_class(POSE_OT_PastePoseFlipped)      
    
   

        
# Fungsi untuk menghapus pendaftaran class dari Blender
def unregister():
    bpy.utils.unregister_class(FLOATING_OT_Decimate_Temporary)     
    bpy.utils.unregister_class(VIEW3D_PT_MiniTools)  
        
    bpy.utils.unregister_class(OBJECT_OT_OverrideLocal) 
    bpy.utils.unregister_class(OBJECT_OT_OnlyOverride)           
    
    bpy.utils.unregister_class(OBJECT_OT_add_controler)        
    bpy.utils.unregister_class(OBJECT_OT_CursorToSelected)
    bpy.utils.unregister_class(OBJECT_OT_SelectToCursor)
    bpy.utils.unregister_class(OBJECT_OT_CopyMirrorPose)     
    bpy.utils.unregister_class(OBJECT_OT_AlignTool)
    
    bpy.utils.unregister_class(PoseCopyPasteProps) 
    bpy.utils.unregister_class(POSE_OT_CopyPose)            
    bpy.utils.unregister_class(POSE_OT_PastePose) 
    bpy.utils.unregister_class(POSE_OT_PastePoseFlipped)      
        
    
  
    bpy.utils.unregister_class(OBJECT_OT_CopyRotation)  
    bpy.utils.unregister_class(SaveAmanPanel)
    del bpy.types.Scene.simplify_subdivision          
   
    del bpy.types.Scene.capsulman_tools_rotation

if __name__ == "__main__":
    register()
