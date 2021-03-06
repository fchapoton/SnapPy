import tkinter, math, sys
from tkinter import ttk
from snappy.gui import WindowOrFrame
from .gui_utilities import UniformDictController, FpsLabelUpdater
from .raytracing_view import *
from .hyperboloid_utilities import unit_3_vector_and_distance_to_O13_hyperbolic_translation
from .zoom_slider import ZoomSlider

###############################################################################
# Main widget

class RaytracingWidget(WindowOrFrame):
    def __init__(self, manifold, parent = None, root = None,
                 title = '', window_type = 'untyped',
                 fillings_changed_callback = None):

        if not title:
            title = "Inside view of %s" % manifold.name()

        WindowOrFrame.__init__(self,
                               parent = parent,
                               title = title,
                               window_type = window_type)

        self.fillings_changed_callback = fillings_changed_callback

        main_frame = self.create_frame_with_main_widget(
            self.container, manifold)

        self.filling_dict = { 'fillings' : self._fillings_from_manifold() }

        row = 0
        self.notebook = ttk.Notebook(self.container)
        self.notebook.grid(row = row, column = 0, sticky = tkinter.NSEW,
                           padx = 0, pady = 0, ipady = 0)

        self.notebook.add(self.create_cusp_areas_frame(self.container),
                          text = 'Cusp areas')
        
        self.notebook.add(self.create_fillings_frame(self.container),
                          text = 'Fillings')

        self.notebook.add(self.create_skeleton_frame(self.container),
                          text = 'Skeleton')

        self.notebook.add(self.create_quality_frame(self.container),
                          text = 'Quality')

        self.notebook.add(self.create_light_frame(self.container),
                          text = 'Light')

        self.notebook.add(self.create_navigation_frame(self.container),
                          text = 'Navigation')

        row += 1
        main_frame.grid(row = row, column = 0, sticky = tkinter.NSEW)
        self.container.columnconfigure(0, weight = 1)
        self.container.rowconfigure(row, weight = 1)

        row += 1
        status_frame = self.create_status_frame(self.container)
        status_frame.grid(row = row, column = 0, sticky = tkinter.NSEW)

        UniformDictController(
            self.main_widget.ui_uniform_dict, 'fov',
            update_function = self.main_widget.redraw_if_initialized,
            scale = self.fov_scale,
            label = self.fov_label,
            format_string = '%.1f')

        self.main_widget.report_time_callback = FpsLabelUpdater(
            self.fps_label)

        self.update_volume_label()

    def create_cusp_areas_frame(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight = 0)
        frame.columnconfigure(1, weight = 1)
        frame.columnconfigure(2, weight = 0)

        row = 0

        cusp_area_maximum = 1.05 * _maximal_cusp_area(self.main_widget.manifold)

        for i in range(self.main_widget.manifold.num_cusps()):
            UniformDictController.create_horizontal_scale(
                frame,
                uniform_dict = self.main_widget.ui_parameter_dict,
                key = 'cuspAreas',
                title = 'Cusp %d' % i,
                from_ = 0.0,
                to = cusp_area_maximum,
                row = row,
                update_function = self.main_widget.recompute_raytracing_data_and_redraw,
                index = i)
            row += 1
            
        frame.rowconfigure(row, weight = 1)

        UniformDictController.create_checkbox(
            frame,
            self.main_widget.ui_uniform_dict,
            'perspectiveType',
            update_function = self.main_widget.redraw_if_initialized,
            text = "Ideal view",
            row = row, column = 1)

        return frame

    def create_fillings_frame(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight = 0)
        frame.columnconfigure(1, weight = 1)
        frame.columnconfigure(2, weight = 0)
        frame.columnconfigure(3, weight = 1)
        frame.columnconfigure(4, weight = 0)

        row = 0

        self.filling_controllers = []
        
        for i in range(self.main_widget.manifold.num_cusps()):
            self.filling_controllers.append(
                UniformDictController.create_horizontal_scale(
                    frame,
                    self.filling_dict,
                    key = 'fillings',
                    column = 0,
                    index = i,
                    component_index = 0,
                    title = 'Cusp %d' % i,
                    row = row,
                    from_ = -15,
                    to = 15,
                    update_function = self.push_fillings_to_manifold,
                    scale_class = ZoomSlider))

            self.filling_controllers.append(
                UniformDictController.create_horizontal_scale(
                    frame,
                    self.filling_dict,
                    key = 'fillings',
                    column = 3,
                    index = i,
                    component_index = 1,
                    title = None,
                    row = row,
                    from_ = -15,
                    to = 15,
                    update_function = self.push_fillings_to_manifold,
                    scale_class = ZoomSlider))

            row += 1

        frame.rowconfigure(row, weight = 1)

        subframe = ttk.Frame(frame)
        subframe.grid(row = row, column = 0, columnspan = 5)
        subframe.columnconfigure(0, weight = 1)
        subframe.columnconfigure(1, weight = 0)
        subframe.columnconfigure(2, weight = 0)
        subframe.columnconfigure(3, weight = 1)
        
        recompute_button = ttk.Button(
            subframe, text = "Recompute hyp. structure",
            command = self.recompute_hyperbolic_structure)
        recompute_button.grid(row = 0, column = 1)

        snap_button = ttk.Button(
            subframe, text = "Round to integers",
            command = self.round_fillings)
        snap_button.grid(row = 0, column = 2)

        return frame

    def create_skeleton_frame(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight = 0)
        frame.columnconfigure(1, weight = 1)
        frame.columnconfigure(2, weight = 0)

        row = 0
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_uniform_dict,
            key = 'edgeThickness',
            title = 'Face boundary thickness',
            row = row,
            from_ = 0.0,
            to = 0.35,
            update_function = self.main_widget.redraw_if_initialized,
            format_string = '%.3f')

        row += 1
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_parameter_dict,
            key = 'insphere_scale',
            title = 'Insphere scale',
            row = row,
            from_ = 0.0,
            to = 1.25,
            update_function = self.main_widget.recompute_raytracing_data_and_redraw,
            format_string = '%.2f')

        row += 1
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_parameter_dict,
            key = 'edgeTubeRadius',
            title = 'Edge thickness',
            row = row,
            from_ = 0.0,
            to = 0.5,
            update_function = self.main_widget.redraw_if_initialized)

        return frame

    def create_quality_frame(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight = 0)
        frame.columnconfigure(1, weight = 1)
        frame.columnconfigure(2, weight = 0)

        row = 0
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_uniform_dict,
            key = 'maxSteps',
            title = 'Max Steps',
            row = row,
            from_ = 1,
            to = 100,
            update_function = self.main_widget.redraw_if_initialized)

        row += 1
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_uniform_dict,
            key = 'maxDist',
            title = 'Max Distance',
            row = row,
            from_ = 1.0,
            to = 28.0,
            update_function = self.main_widget.redraw_if_initialized)

        row += 1
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_uniform_dict,
            key = 'subpixelCount',
            title = 'Subpixel count',
            row = row,
            from_ = 1.0,
            to = 4.25,
            update_function = self.main_widget.redraw_if_initialized)

        return frame

    def create_light_frame(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight = 0)
        frame.columnconfigure(1, weight = 1)
        frame.columnconfigure(2, weight = 0)

        row = 0
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_uniform_dict,
            key = 'lightBias',
            title = 'Light bias',
            row = row,
            from_ = 0.3,
            to = 4.0,
            update_function = self.main_widget.redraw_if_initialized)

        row += 1
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_uniform_dict,
            key = 'lightFalloff',
            title = 'Light falloff',
            row = row,
            from_ = 0.1,
            to = 2.0,
            update_function = self.main_widget.redraw_if_initialized)

        row += 1
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.ui_uniform_dict,
            key = 'brightness',
            title = 'Brightness',
            row = row,
            from_ = 0.3,
            to = 3.0,
            update_function = self.main_widget.redraw_if_initialized)

        return frame

    def create_navigation_frame(self, parent):
        frame = ttk.Frame(parent)

        frame.columnconfigure(0, weight = 0)
        frame.columnconfigure(1, weight = 1)
        frame.columnconfigure(2, weight = 0)
        frame.columnconfigure(3, weight = 0)

        row = 0
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.navigation_dict,
            key = 'translationVelocity',
            title = 'Translation Speed',
            row = row,
            from_ = 0.1,
            to = 1.0)

        label = ttk.Label(frame, text = "Keys: wasdec")
        label.grid(row = row, column = 3, sticky = tkinter.NSEW)

        row += 1
        UniformDictController.create_horizontal_scale(
            frame,
            self.main_widget.navigation_dict,
            key = 'rotationVelocity',
            title = 'Rotation Speed',
            row = row,
            from_ = 0.1,
            to = 1.0)

        label = ttk.Label(frame, text = u"Keys: \u2190\u2191\u2192\u2193xz")
        label.grid(row = row, column = 3, sticky = tkinter.NSEW)

        row +=1
        label = ttk.Label(frame, text = _mouse_gestures_text())
        label.grid(row = row, column = 0, columnspan = 4)

        return frame

    def create_frame_with_main_widget(self, parent, manifold):
        frame = ttk.Frame(parent)

        column = 0

        self.main_widget = RaytracingView(
            manifold, frame,
            width = 600, height = 500, double = 1, depth = 1)
        self.main_widget.grid(row = 0, column = column, sticky = tkinter.NSEW)
        self.main_widget.make_current()
        frame.columnconfigure(column, weight = 1)
        frame.rowconfigure(0, weight = 1)

        column += 1
        self.fov_scale = ttk.Scale(frame, from_ = 20, to = 120,
                                   orient = tkinter.VERTICAL)
        self.fov_scale.grid(row = 0, column = column, sticky = tkinter.NSEW)

        return frame

    def create_status_frame(self, parent):
        frame = ttk.Frame(parent)

        column = 0
        label = ttk.Label(frame, text = "FOV:")
        label.grid(row = 0, column = column)

        column += 1
        self.fov_label = ttk.Label(frame)
        self.fov_label.grid(row = 0, column = column)

        column += 1
        self.vol_label = ttk.Label(frame)
        self.vol_label.grid(row = 0, column = column)

        column += 1
        self.fps_label = ttk.Label(frame)
        self.fps_label.grid(row = 0, column = column)

        return frame

    def update_volume_label(self):
        try:
            vol_text = '%.3f' % self.main_widget.manifold.volume()
        except ValueError:
            vol_text = '-'
        sol_type = self.main_widget.manifold.solution_type(enum = True)
        sol_text = _solution_type_text[sol_type]
        try:
            self.vol_label.configure(text = 'Vol: %s (%s)' % (vol_text, sol_text))
        except AttributeError:
            pass

    def update_filling_sliders(self):
        for filling_controller in self.filling_controllers:
            filling_controller.update()

    def _fillings_from_manifold(self):
        return [ 'vec2[]',
                 [ [ d['filling'][0], d['filling'][1] ]
                   for d 
                   in self.main_widget.manifold.cusp_info() ] ]
    
    def pull_fillings_from_manifold(self):
        self.filling_dict['fillings'] = self._fillings_from_manifold()
        self.update_filling_sliders()
        self.main_widget.recompute_raytracing_data_and_redraw()
        self.update_volume_label()

    def push_fillings_to_manifold(self):
        self.main_widget.manifold.dehn_fill(
            self.filling_dict['fillings'][1])

        self.main_widget.recompute_raytracing_data_and_redraw()
        self.update_volume_label()
        
        if self.fillings_changed_callback:
            self.fillings_changed_callback()

    def recompute_hyperbolic_structure(self):
        self.main_widget.manifold.init_hyperbolic_structure(
            force_recompute = True)
        self.main_widget.recompute_raytracing_data_and_redraw()
        
        # Should we reset the view state since it might
        # be corrupted?
        # O13_orthonormalize seems stable enough now that
        # we always recover.
        # self.main_widget.reset_view_state()

        self.update_volume_label()

        if self.fillings_changed_callback:
            self.fillings_changed_callback()

    def round_fillings(self):
        for f in self.filling_dict['fillings'][1]:
            for i in [0, 1]:
                f[i] = float(round(f[i]))
        self.update_filling_sliders()
        self.push_fillings_to_manifold()

###############################################################################
# Helpers

_solution_type_text = [
    'degenerate',
    'geometric',
    'non-geometric',
    'flat',
    'degenerate',
    'degenerate',
    'degenerate']    

def _maximal_cusp_area(mfd):
    # Hack to prevent doctest failure M.browse() where
    # M is a SnapPy.Manifold instead of a snappy.Manifold.
    if not hasattr(mfd, 'cusp_area_matrix'):
        return 5.0

    try:
        mfd = mfd.copy()
        mfd.dehn_fill(mfd.num_cusps() * [(0,0)])
        mfd.init_hyperbolic_structure(force_recompute = True)

        # Using sqrt of maximum of diagonal of cusp area matrix.
        #
        # We use method = 'trigDependent' here for the following reasons:
        # - Faster than 'maximal'
        # - If a cusp neighborhood is not in standard form anymore, its
        #   boundary has holes in the raytraced view and looks broken.
        #   Thus, if a slider has less of a range because we use the diagonal
        #   entries from the 'trigDependent' matrix instead of the 'maximal'
        #   one, the values outside the slider's range correspond to broken
        #   images anyway.
        # - 'trigDependentCanonize' gives less biased diagonal entries but
        #   their maximum might be smaller. E.g., for t12828, the diagonal
        #   entries are [22.25, 22.25, 22.25] with canonizizng and
        #   [104.55, 6.38, 6.38] without canonizing. The latter gives a
        #   maximum of 104.55. The diagonal entries for the 'maximal'
        #   are actually [104.55, 104.55, 104.55], so 'trigDependentCanonize'
        #   gives actually the best possible result.
        m = mfd.cusp_area_matrix(method='trigDependent')

        return math.sqrt(max([m[i,i] for i in range(mfd.num_cusps())]))
    except Exception as e:
        print("Exception while trying to compute maximal cusp area:", e)
        return 5.0

def _mouse_gestures_text():
    if sys.platform == 'darwin':
        return u"Move: Click & Drag     Rotate: Shift-Click & Drag     Orbit: \u2318-Click & Drag"
    else:
        return "Move: Click & Drag     Rotate: Shift-Click & Drag     Orbit: Alt-Click & Drag"

###############################################################################
# Performance test

class PerfTest:
    def __init__(self, widget, num_iterations = 20):
        self.widget = widget
        self.m = unit_3_vector_and_distance_to_O13_hyperbolic_translation(
            [ 0.3 * math.sqrt(2.0), 0.4 * math.sqrt(2.0), 0.5 * math.sqrt(2.0) ],
            0.1 / num_iterations)
        self.num_iterations = num_iterations
        self.current_iteration = 0
        self.total_time = 0.0
        
        self.widget.report_time_callback = self.report_time

        self.widget.after(250, self.redraw)

        self.widget.focus_set()
        self.widget.mainloop()


    def report_time(self, t):
        self.total_time += t
        
    def redraw(self):
        self.current_iteration += 1
        if self.current_iteration == self.num_iterations:
            print("Total time: %.1fms" % (1000 * self.total_time))
            print("Time: %.1fms" % (1000 * self.total_time / self.num_iterations))
            sys.exit(0)

        self.widget.view_state = self.widget.raytracing_data.update_view_state(
            self.widget.view_state, self.m)
        
        self.widget.redraw_if_initialized()
        self.widget.after(250, self.redraw)
        
def run_perf_test(): 
    from snappy import Manifold

    gui = RaytracingWidget(Manifold("m004"))

    PerfTest(gui.main_widget)
