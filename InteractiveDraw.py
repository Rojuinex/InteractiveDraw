import bpy, math

from bpy.types import Panel, Operator
from mathutils import Vector
from enum import Enum
from bpy_extras import view3d_utils

bl_info = \
    {
        "name" : "Interactive Draw Tools",
        "author" : "Rojuinex <rojuinex@gmail.com>",
        "version" : (0, 0, 4),
        "blender" : (2, 7, 5),
        "location" : "View 3D > Edit Mode > Tool Shelf",
        "description" : "Allows for the creation of objects interactively.",
        "warning" : "In development (Alpha)",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Object",
    }

#        # Use plane of second point
#        if self._click_number == 2:
#            region = context.region
#            rv3d   = context.region_data
#            coord  = event.mouse_region_x, event.mouse_region_y
#        
#            N = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
#            N.z = 0
#            o = self._last_point    

def rayPlaneIntersection(P0, V, o, N):
    if V.dot(N) == 0:
        return None
    
    d = (o - P0).dot(N) / (V.dot(N))
    return d * V + P0

class IDT_draw_prototype:
    """Prototype for all interactive draw functions"""
    _click_number = 0
    
    def mousePlaneIntersection(self, context, event, o, N):
        scene  = context.scene
        region = context.region
        rv3d   = context.region_data
        coord  = event.mouse_region_x, event.mouse_region_y
        
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin  = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        if rv3d.view_perspective != 'ORTHO':
            return rayPlaneIntersection(ray_origin, view_vector, o, N), view_vector

        if abs(view_vector.y) == 1:
            ray_origin.y = 0
        elif abs(view_vector.x) == 1:
            ray_origin.x = 0
        elif abs(view_vector.z) == 1:
            ray_origin.z = 0
                    
        return ray_origin, view_vector

class IDT_draw_line(IDT_draw_prototype, Operator):
    """interactively draw a line"""
    bl_idname = "curve.idt_draw_line"
    bl_label = "Draw Line"
    
    _first_point = None
    _last_point  = None
    _curve       = None
    _curve_data  = None
    _curve_path  = None
    
    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navagation
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.leftmouse(context, event)
        elif event.type == 'MOUSEMOVE':
            self.mousemove(context, event)
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cleanup(context)
            return {'CANCELLED'}
        
        if self._click_number == 2:
            return {"FINISHED"}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            
            if context.mode == 'EDIT_CURVE':
                self._curve = context.object
                self._curve_data = self._curve.data
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(1)
                self._curve_path.use_cyclic_u = True
                self._curve_data.splines.active = self._curve_path
            else:
                self._curve_data = bpy.data.curves.new(name='Triangle', type='CURVE')
                self._curve_data.dimensions = '3D'
                
                self._curve = bpy.data.objects.new('Triangle', self._curve_data)
                self._curve.location = (0,0,0)
                bpy.context.scene.objects.link(self._curve)
                bpy.ops.object.select_all(action="DESELECT")
                self._curve.select = True
                context.scene.objects.active = self._curve
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(1)
                self._curve_path.use_cyclic_u = True

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
        
    def cleanup(self, context):
        if self._curve is not None:
            if context.mode == 'EDIT_CURVE':
                self._curve_data.splines.remove(self._curve_path)
            else:
                bpy.context.scene.objects.unlink(self._curve)
                bpy.data.objects.remove(self._curve)
                bpy.data.curves.remove(self._curve_data)
        
    def leftmouse(self, context, event):
        if self._last_point is not None:
            self._click_number += 1
            
        if self._click_number == 1:
            self._first_point = self._last_point

    def mousemove(self, context, event):
        o = Vector((0,0,0))
        N = Vector((0,0,1))
        self._last_point, view_normal = self.mousePlaneIntersection(context, event, o, N)
        
        if self._first_point is not None:
            fp = self._first_point
            lp = self._last_point

            self._curve_path.points[0].co = (fp.x, fp.y, fp.z, 1)
            self._curve_path.points[1].co = (lp.x, lp.y, lp.z, 1)

class IDT_draw_triangle(IDT_draw_prototype, Operator):
    """interactively draw a triangle"""
    bl_idname = "curve.idt_draw_triangle"
    bl_label = "Draw Triangle"
    
    _first_point  = None
    _second_point = None
    _last_point   = None
    _curve        = None
    _curve_data   = None
    _curve_path   = None
    
    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navagation
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.leftmouse(context, event)
        elif event.type == 'MOUSEMOVE':
            self.mousemove(context, event)
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cleanup(context)
            return {'CANCELLED'}
        
        if self._click_number == 3:
            return {"FINISHED"}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            
            if context.mode == 'EDIT_CURVE':
                self._curve = context.object
                self._curve_data = self._curve.data
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(2)
                self._curve_path.use_cyclic_u = True
                self._curve_data.splines.active = self._curve_path
            else:
                self._curve_data = bpy.data.curves.new(name='Triangle', type='CURVE')
                self._curve_data.dimensions = '3D'
                
                self._curve = bpy.data.objects.new('Triangle', self._curve_data)
                self._curve.location = (0,0,0)
                bpy.context.scene.objects.link(self._curve)
                bpy.ops.object.select_all(action="DESELECT")
                self._curve.select = True
                context.scene.objects.active = self._curve
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(2)
                self._curve_path.use_cyclic_u = True
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
        
    def cleanup(self, context):
        if self._curve is not None:
            if context.mode == 'EDIT_CURVE':
                self._curve_data.splines.remove(self._curve_path)
            else:
                bpy.context.scene.objects.unlink(self._curve)
                bpy.data.objects.remove(self._curve)
                bpy.data.curves.remove(self._curve_data)
        
    def leftmouse(self, context, event):
        if self._last_point is not None:
            self._click_number += 1
            
        if self._click_number == 1:
            self._first_point = self._last_point
        
        if self._click_number == 2:
            self._second_point = self._last_point

    def mousemove(self, context, event):
        o = Vector((0,0,0))
        N = Vector((0,0,1))
        self._last_point, view_normal = self.mousePlaneIntersection(context, event, o, N)
        
        if self._first_point is not None:
            fp = self._first_point
            lp = self._last_point

            self._curve_path.points[0].co = (fp.x, fp.y, fp.z, 1)

            if self._second_point is None:
                self._curve_path.points[1].co = (lp.x, lp.y, lp.z, 1) 
                self._curve_path.points[2].co = (lp.x, lp.y, lp.z, 1)
            else:
                sp = self._second_point
            
                self._curve_path.points[1].co = (sp.x, sp.y, sp.z, 1)
                self._curve_path.points[2].co = (lp.x, lp.y, lp.z, 1)

class IDT_draw_rectangle(IDT_draw_prototype, Operator):
    """interactively draw a rectangle"""
    bl_idname = "curve.idt_draw_rectangle"
    bl_label = "Draw Rectangle"
    
    _first_point    = None
    _last_point     = None
    _curve      = None
    _curve_data = None
    _curve_path = None
    
    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navagation
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.leftmouse(context, event)
        elif event.type == 'MOUSEMOVE':
            self.mousemove(context, event)
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cleanup(context)
            return {'CANCELLED'}
        
        if self._click_number == 2:
            return {"FINISHED"}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            
            if context.mode == 'EDIT_CURVE':
                self._curve = context.object
                self._curve_data = self._curve.data
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(3)
                self._curve_path.use_cyclic_u = True
                self._curve_data.splines.active = self._curve_path
            else:                    
                self._curve_data = bpy.data.curves.new(name='Rectangle', type='CURVE')
                self._curve_data.dimensions = '3D'
                
                self._curve = bpy.data.objects.new('Rectangle', self._curve_data)
                self._curve.location = (0,0,0)
                bpy.context.scene.objects.link(self._curve)
                bpy.ops.object.select_all(action="DESELECT")
                self._curve.select = True
                context.scene.objects.active = self._curve
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(3)
                self._curve_path.use_cyclic_u = True
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
        
    def cleanup(self, context):
        if self._curve is not None:
            if context.mode == 'EDIT_CURVE':
                self._curve_data.splines.remove(self._curve_path)
            else:
                bpy.context.scene.objects.unlink(self._curve)
                bpy.data.objects.remove(self._curve)
                bpy.data.curves.remove(self._curve_data)
        
    def leftmouse(self, context, event):
        if self._last_point is not None:
            self._click_number += 1
            
        if self._click_number == 1:
            self._first_point = self._last_point

    def mousemove(self, context, event):
        o = Vector((0,0,0))
        N = Vector((0,0,1))
        self._last_point, view_normal = self.mousePlaneIntersection(context, event, o, N)
        
        if self._first_point is not None:
            
            fp = self._first_point
            lp = self._last_point

            self._curve_path.points[0].co = (fp.x, fp.y, fp.z, 1)
            
            if abs(view_normal.y) == 1:
                self._curve_path.points[1].co = (lp.x, lp.y, fp.z, 1)
                self._curve_path.points[2].co = (lp.x, lp.y, lp.z, 1)
                self._curve_path.points[3].co = (fp.x, lp.y, lp.z, 1)
            elif abs(view_normal.x) == 1:
                self._curve_path.points[1].co = (lp.x, lp.y, fp.z, 1)
                self._curve_path.points[2].co = (lp.x, lp.y, lp.z, 1)
                self._curve_path.points[3].co = (lp.x, fp.y, lp.z, 1)
            else:
                self._curve_path.points[1].co = (lp.x, fp.y, lp.z, 1)
                self._curve_path.points[2].co = (lp.x, lp.y, lp.z, 1)
                self._curve_path.points[3].co = (fp.x, lp.y, lp.z, 1)

class IDT_draw_quad(IDT_draw_prototype, Operator):
    """interactively draw a quad"""
    bl_idname = "curve.idt_draw_quad"
    bl_label = "Draw Quad"
    
    _first_point  = None
    _second_point = None
    _third_point  = None
    _last_point   = None
    _curve        = None
    _curve_data   = None
    _curve_path   = None
    
    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navagation
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.leftmouse(context, event)
        elif event.type == 'MOUSEMOVE':
            self.mousemove(context, event)
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cleanup(context)
            return {'CANCELLED'}
        
        if self._click_number == 4:
            return {"FINISHED"}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            
            if context.mode == 'EDIT_CURVE':
                self._curve = context.object
                self._curve_data = self._curve.data
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(3)
                self._curve_path.use_cyclic_u = True
                self._curve_data.splines.active = self._curve_path
            else:                   
                self._curve_data = bpy.data.curves.new(name='Rectangle', type='CURVE')
                self._curve_data.dimensions = '3D'
                
                self._curve = bpy.data.objects.new('Rectangle', self._curve_data)
                self._curve.location = (0,0,0)
                bpy.context.scene.objects.link(self._curve)
                bpy.ops.object.select_all(action="DESELECT")
                self._curve.select = True
                context.scene.objects.active = self._curve
                
                self._curve_path = self._curve_data.splines.new('POLY')
                self._curve_path.points.add(3)
                self._curve_path.use_cyclic_u = True
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
        
    def cleanup(self, context):
        if self._curve is not None:
            if context.mode == 'EDIT_CURVE':
                self._curve_data.splines.remove(self._curve_path)
            else:
                bpy.context.scene.objects.unlink(self._curve)
                bpy.data.objects.remove(self._curve)
                bpy.data.curves.remove(self._curve_data)
        
    def leftmouse(self, context, event):
        if self._last_point is not None:
            self._click_number += 1
            
        if self._click_number == 1:
            self._first_point = self._last_point
        
        if self._click_number == 2:
            self._second_point = self._last_point

        if self._click_number == 3:
            self._third_point = self._last_point


    def mousemove(self, context, event):
        o = Vector((0,0,0))
        N = Vector((0,0,1))
        self._last_point, view_normal = self.mousePlaneIntersection(context, event, o, N)
        
        if self._first_point is not None: 
            fp = self._first_point
            lp = self._last_point

            self._curve_path.points[0].co = (fp.x, fp.y, fp.z, 1)

            if self._second_point is None:
                self._curve_path.points[1].co = (lp.x, lp.y, lp.z, 1) 
                self._curve_path.points[2].co = (lp.x, lp.y, lp.z, 1)
                self._curve_path.points[3].co = (lp.x, lp.y, lp.z, 1)
            else:
                sp = self._second_point
            
                if self._third_point is None:
                    self._curve_path.points[1].co = (sp.x, sp.y, sp.z, 1)
                    self._curve_path.points[2].co = (lp.x, lp.y, lp.z, 1)
                    self._curve_path.points[3].co = (lp.x, lp.y, lp.z, 1)
                else:
                    tp = self._third_point
                    self._curve_path.points[1].co = (sp.x, sp.y, sp.z, 1)
                    self._curve_path.points[2].co = (tp.x, tp.y, tp.z, 1)
                    self._curve_path.points[3].co = (lp.x, lp.y, lp.z, 1)


class InteractiveDrawPanel:
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
class VIEW3D_IDT_draw_shapes_panel(InteractiveDrawPanel, Panel):
    bl_category = 'Interactive'
    bl_context  = "objectmode"
    bl_label    = "Draw Shapes"    
    
    @staticmethod
    def draw_add_mesh(layout, label=False):
        if label:
            layout.label(text="Primitives:")
        layout.operator("mesh.primitive_plane_add", text="Plane", icon='MESH_PLANE')
        layout.operator("mesh.primitive_cube_add", text="Cube", icon='MESH_CUBE')
        layout.operator("mesh.primitive_circle_add", text="Circle", icon='MESH_CIRCLE')
        layout.operator("mesh.primitive_uv_sphere_add", text="UV Sphere", icon='MESH_UVSPHERE')
        layout.operator("mesh.primitive_ico_sphere_add", text="Ico Sphere", icon='MESH_ICOSPHERE')
        layout.operator("mesh.primitive_cylinder_add", text="Cylinder", icon='MESH_CYLINDER')
        layout.operator("mesh.primitive_cone_add", text="Cone", icon='MESH_CONE')
        layout.operator("mesh.primitive_torus_add", text="Torus", icon='MESH_TORUS')

        if label:
            layout.label(text="Special:")
        else:
            layout.separator()
        layout.operator("mesh.primitive_grid_add", text="Grid", icon='MESH_GRID')
        layout.operator("mesh.primitive_monkey_add", text="Monkey", icon='MESH_MONKEY')
        
    @staticmethod
    def draw_add_curve(layout, label=False):
        if label:
            layout.label(text="Poly:")
        layout.operator("curve.idt_draw_line", text="Line", icon='CURVE_PATH')
        layout.operator("curve.idt_draw_triangle", text="Triangle", icon='EDITMODE_VEC_DEHLT')
        layout.operator("curve.idt_draw_rectangle", text="Rectangle", icon='STICKY_UVS_VERT')
        layout.operator("curve.idt_draw_quad", text="Quad", icon='EDIT_VEC')
        

    def draw(self, context):
        layout = self.layout
        
        #col = layout.column(align=True)
        #col.label(text="Mesh:")
        #self.draw_add_mesh(col)
        
        col = layout.column(align=True)
        col.label(text="Curve:")
        self.draw_add_curve(col)
        
class VIEW3D_IDT_draw_shapes_panel_edit(InteractiveDrawPanel, Panel):
    bl_category = "Interactive"
    bl_context  = "curve_edit"
    bl_label    = "Draw Shapes"
    
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        VIEW3D_IDT_draw_shapes_panel.draw_add_curve(col, label=True)

def register():
    bpy.utils.register_class(IDT_draw_line)
    bpy.utils.register_class(IDT_draw_triangle)
    bpy.utils.register_class(IDT_draw_rectangle)
    bpy.utils.register_class(IDT_draw_quad)
    bpy.utils.register_class(VIEW3D_IDT_draw_shapes_panel)
    bpy.utils.register_class(VIEW3D_IDT_draw_shapes_panel_edit)
    
def unregister():
    bpy.utils.unregister_class(IDT_draw_line)
    bpy.utils.unregister_class(IDT_draw_triangle)
    bpy.utils.unregister_class(IDT_draw_rectangle)
    bpy.utils.unregister_class(IDT_draw_quad)
    bpy.utils.unregister_class(VIEW3D_IDT_draw_shapes_panel)
    bpy.utils.unregister_class(VIEW3D_IDT_draw_shapes_panel_edit)
    
if __name__ == "__main__":
    register()