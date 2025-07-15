import bpy
import os

# ====== Cek safe_area.png di dua folder ======
ADDONS_PATH = bpy.utils.user_resource('SCRIPTS', path="addons")
RAHA_TOOLS_PATH = os.path.join(ADDONS_PATH, "Raha_Tools", "safe_area.png")
RAHA_LAUNCHER_PATH = os.path.join(ADDONS_PATH, "Raha_Tools_LAUNCHER", "safe_area.png")

if os.path.exists(RAHA_TOOLS_PATH):
    DEFAULT_SAFE_AREA_IMAGE_PATH = RAHA_TOOLS_PATH
elif os.path.exists(RAHA_LAUNCHER_PATH):
    DEFAULT_SAFE_AREA_IMAGE_PATH = RAHA_LAUNCHER_PATH
else:
    DEFAULT_SAFE_AREA_IMAGE_PATH = ""

# ========== OPERATOR AKTIFKAN HUD ==========
class RAHA_OT_ActivateHUD(bpy.types.Operator):
    """Aktifkan HUD dengan background image dan render stamp"""
    bl_idname = "raha.activate_hud"
    bl_label = "Activate HUD"

    def execute(self, context):
        scene = context.scene
        obj = bpy.context.object

        if obj and obj.type == 'CAMERA':
            if not obj.data.show_background_images:
                obj.data.show_background_images = True
                self.report({'INFO'}, "Background image enabled on active camera.")

        if not scene.raha_hud_use:
            cam = scene.camera
            if cam and cam.data.background_images:
                for bg in cam.data.background_images:
                    bg.show_background_image = False
            scene.render.use_stamp = False
            self.report({'INFO'}, "HUD disabled")
            return {'FINISHED'}

        cams = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        if cams:
            bpy.context.view_layer.objects.active = cams[0]
            cams[0].select_set(True)

        scene.render.use_stamp = True
        scene.render.use_stamp_note = True
        scene.render.use_stamp_camera = False
        scene.render.use_stamp_render_time = False
        scene.render.use_stamp_time = False
        scene.render.use_stamp_filename = False
        scene.render.use_stamp_lens = True
        scene.render.stamp_font_size = 32

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_bones = False
                        space.overlay.show_cursor = False
                        space.overlay.show_extras = False
                        space.overlay.show_motion_paths = False
                        space.overlay.show_relationship_lines = False

        cam = scene.camera
        if not cam:
            self.report({'ERROR'}, "No active camera found")
            return {'CANCELLED'}

        if not cam.data.background_images:
            bg_image = cam.data.background_images.new()
        else:
            bg_image = cam.data.background_images[0]

        if scene.raha_hud_use_custom_path:
            custom_path = scene.raha_hud_custom_path
            if os.path.exists(custom_path):
                bg_image.image = bpy.data.images.load(custom_path)
            else:
                self.report({'ERROR'}, "Custom image not found")
                return {'CANCELLED'}
        else:
            if DEFAULT_SAFE_AREA_IMAGE_PATH:
                bg_image.image = bpy.data.images.load(DEFAULT_SAFE_AREA_IMAGE_PATH)
            else:
                self.report({'ERROR'}, "Default safe area image not found")
                return {'CANCELLED'}

        bg_image.show_background_image = True
        bg_image.display_depth = 'FRONT'
        bg_image.frame_method = 'FIT'  # Tambahan: pastikan FIT ke kamera
        cam.data.show_background_images = True

        self.report({'INFO'}, "HUD activated")
        return {'FINISHED'}

# ========== TOGGLE SAFE AREA ==========
class VIEW3D_OT_ToggleSafeArea(bpy.types.Operator):
    """Toggle safe area"""
    bl_idname = "view3d.toggle_safe_area"
    bl_label = "Toggle Safe Area"

    def execute(self, context):
        cam = context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}

        if cam.data.background_images:
            bg = cam.data.background_images[0]
            bg.show_background_image = not bg.show_background_image
            context.scene.render.use_stamp = bg.show_background_image
            status = "ON" if bg.show_background_image else "OFF"
            self.report({'INFO'}, f"Safe area {status}")
        else:
            self.report({'ERROR'}, "No background image found")
            return {'CANCELLED'}

        return {'FINISHED'}

# ========== DELETE SAFE AREA IMAGE ==========
class VIEW3D_OT_DeleteSafeAreaImage(bpy.types.Operator):
    """Delete safe area image"""
    bl_idname = "view3d.delete_safe_area_image"
    bl_label = "Delete Safe Area"

    def execute(self, context):
        cam = context.scene.camera
        if cam and cam.data.background_images:
            cam.data.background_images.clear()
            cam.data.show_background_images = False
            context.scene.render.use_stamp = False
            self.report({'INFO'}, "Safe area image deleted")
        else:
            self.report({'ERROR'}, "No image to delete")
        return {'FINISHED'}

# ========== PANEL ==========
class VIEW3D_PT_HUDPanel(bpy.types.Panel):
    """Panel HUD"""
    bl_label = "HUD Tools"
    bl_idname = "RAHA_PT_HUD"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="HUD Settings ")
        layout.prop(scene, "name", text="Scene Name")
        layout.prop(scene.render, "stamp_note_text", text="Animator Name")
        layout.prop(scene, "raha_hud_use_custom_path", text="Use Custom Safe Area Path")

        if scene.raha_hud_use_custom_path:
            layout.prop(scene, "raha_hud_custom_path", text="Safe Area Image")

        cam = scene.camera
        highlight = False
        if cam and cam.data.background_images:
            if cam.data.background_images[0].show_background_image:
                highlight = True

        row = layout.row()  # Semua tombol dalam satu baris
        row.operator("raha.activate_hud", text="Activate HUD")
        row.operator("view3d.delete_safe_area_image", text="", icon='X')

        op_toggle = row.operator("view3d.toggle_safe_area", text="", icon='HIDE_OFF')



# ========== REGISTER ==========
def register():
    bpy.utils.register_class(RAHA_OT_ActivateHUD)
    bpy.utils.register_class(VIEW3D_OT_ToggleSafeArea)
    bpy.utils.register_class(VIEW3D_OT_DeleteSafeAreaImage)
    bpy.utils.register_class(VIEW3D_PT_HUDPanel)

    bpy.types.Scene.raha_hud_use = bpy.props.BoolProperty(name="Use HUD", default=False)
    bpy.types.Scene.raha_hud_use_custom_path = bpy.props.BoolProperty(name="Use Custom Safe Area Path", default=False)
    bpy.types.Scene.raha_hud_custom_path = bpy.props.StringProperty(name="Custom Image Path", subtype='FILE_PATH')

def unregister():
    bpy.utils.unregister_class(RAHA_OT_ActivateHUD)
    bpy.utils.unregister_class(VIEW3D_OT_ToggleSafeArea)
    bpy.utils.unregister_class(VIEW3D_OT_DeleteSafeAreaImage)
    bpy.utils.unregister_class(VIEW3D_PT_HUDPanel)

    del bpy.types.Scene.raha_hud_use
    del bpy.types.Scene.raha_hud_use_custom_path
    del bpy.types.Scene.raha_hud_custom_path

if __name__ == "__main__":
    register()
