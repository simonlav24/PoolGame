'''
pysimplegui like gui manager for pygame
by Simon Labusnky
'''

from enum import Enum
from typing import List, Any, Tuple, Dict
import pygame

__version__ = '1.0.5'

GUI_DEBUG_MODE = False

check_box_image = pygame.image.load(r'./Assets/checkbox.png')
check_box_size = (13, 13)
check_box_areas = [((check_box_size[0] * i, 0), check_box_size) for i in range(4)]

def point_in_rect(pos, rect):
    rect_pos = rect[0]
    rect_size = rect[1]
    return pos[0] > rect_pos[0] and pos[0] < rect_pos[0] + rect_size[0] and\
            pos[1] > rect_pos[1] and pos[1] < rect_pos[1] + rect_size[1]


class VerticalAlignment(Enum):
    TOP = 0
    CENTER = 1
    BOTTOM = 2

class HorizontalAlignment(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2

class MouseButton(Enum):
    LEFT = 1
    RIGHT = 2
    MIDDLE = 3
    SCROLL_UP = 4
    SCROLL_DOWN = 5

class ColorPallete:
    def __init__(self):
        self.text_color = (213,213,213)
        self.button_back_color = (93,93,93)
        self.button_focus_back_color = (106,106,106)
        self.button_toggle_back_color = (60,60,70)
        self.button_slider_color = (0,117,255)
        self.button_slider_color2 = (75,160,255)

pygame_to_gui_mouse = [None, MouseButton.LEFT, MouseButton.MIDDLE, MouseButton.RIGHT, MouseButton.SCROLL_UP, MouseButton.SCROLL_DOWN]

class Gui:
    ''' main gui manager
        args:
            - win: pygame window surface 
            - layout: list of rows of elements
    '''
    def __init__(self, win: pygame.Surface, layout, **kwargs):
        self.name = 'Gui'
        name = kwargs.get('name', None)
        if name:
            self.name = name
        self.win : pygame.Surface = win
        self.layout : List[List[Element]]= layout
        self.default_font = pygame.font.SysFont('Calibri', 14)
        font = kwargs.get('font', None)
        if font:
            self.default_font = font
        self.color_pallete = ColorPallete()
        
        self.focused_element : Element = None
        self.event : str = None
        
        self.min_element_height = kwargs.get('min_element_height', 16)
        self.margin = kwargs.get('margin', 3)
        self.inner_element_margin = kwargs.get('inner_element_margin', 6)
        
        self.elements : List[Element] = []
        self.dict : Dict[str : Element] = {}
        self.pos = kwargs.get('pos', (0,0))
        self.size = (0,0)
        
        self.calculate()
        
        self.mouse_hold = False

        self.context_menu: Gui = None

    def __str__(self):
        return f'<Gui: {self.name}>'
    
    def __repr__(self):
        return str(self)

    def set_pos(self, pos):
        self.pos = pos
        self.calculate()
    
    def calculate(self):
        ''' process layout, each element receives gui, position and initializes.
            also calculates self size '''
        pos_y_acc = self.pos[1]
        size_x = 0
        size_y = 0
        
        # rows for cell size calculation
        row_cells = []

        for row in self.layout:
            pos_x_acc = self.pos[0]
            row_y_max = 0

            size_row_x = 0
            for element in row:
                self.elements.append(element)
                element.set_gui(self)
                if element.key:
                    self.dict[element.key] = element
                element.parent = self
                element.pos = (pos_x_acc, pos_y_acc)
                element.initialize()

                size_row_x += element.size[0] + self.margin

                pos_x_acc += element.size[0] + self.margin
                row_y_max = max(row_y_max, element.size[1])

            size_x = max(size_x, size_row_x)
            
            row_cells.append(row_y_max)

            pos_y_acc += row_y_max + self.margin
            size_y += row_y_max + self.margin

        self.size = (size_x - self.margin, size_y - self.margin)

        # update cell size
        for i, row in enumerate(self.layout):
            cell_y = row_cells[i]
            for element in row:
                element.cell_size = (element.size[0], cell_y)
                element.cell_offset = {
                    VerticalAlignment.TOP: (0, 0),
                    VerticalAlignment.CENTER: (0, element.cell_size[1] / 2 - element.size[1] / 2),
                    VerticalAlignment.BOTTOM: (0, element.cell_size[1] - element.size[1]),
                }.get(element.vertical_alignment)

    def handle_event(self, event):
        if self.context_menu:
            self.context_menu.handle_event(event)
            return
        if event.type == pygame.MOUSEBUTTONUP:
            if pygame_to_gui_mouse[event.button] == MouseButton.LEFT:
                self.mouse_hold = False
            if self.focused_element:
                self.focused_element.on_click_up(pygame_to_gui_mouse[event.button])
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if pygame_to_gui_mouse[event.button] == MouseButton.LEFT:
                if not point_in_rect(pygame.mouse.get_pos(), (self.pos, self.size)):
                    self.click_outside(pygame_to_gui_mouse[event.button])
                self.mouse_hold = True
            if self.focused_element:
                self.focused_element.on_click_down(pygame_to_gui_mouse[event.button])
        
        if self.focused_element:
            # send event of mouse held
            if self.mouse_hold:
                self.focused_element.on_hold()
    
    def step(self):
        if self.context_menu:
            self.context_menu.step()
        if not self.mouse_hold:
            self.focused_element = None
        for element in self.elements:
            element.step()
        
    def draw(self):
        for element in self.elements:
            element.draw()

        if GUI_DEBUG_MODE:
            pygame.draw.rect(self.win, (255,0,0), (self.pos, self.size), 1)

        if self.context_menu:
            self.context_menu.draw()
    
    def read(self):
        if not self.event:
            return None, None
        
        event = self.event
        self.event = None
        values = {'gui': self}
        for element in self.elements:
            returned_values = element.get_values()
            if returned_values:
                for value in returned_values:
                    values[value[0]] = value[1]
        return event, values
    
    def notify_event(self, event):
        ''' elements can notify internal events '''
        self.event = event

    def __getitem__(self, key : str) -> 'Element':
        return self.dict[key]
    
    def set_context_menu(self, context_menu: 'Gui'):
        self.context_menu = context_menu
    
    def click_outside(self, mouse_button: MouseButton=None):
        pass


class Element:
    ''' element base abstract class '''
    def __init__(self, **kwargs):
        self.pos = kwargs.get('pos', (0,0))
        self.margin = kwargs.get('margin', None)
        self.size = (0,0)
        self.gui : Gui = None
        self.parent : Element | Gui = None
        self.key = None

        self.initial_width = kwargs.get('width', 0)

        self.vertical_alignment = kwargs.get('vertical_alignment', VerticalAlignment.TOP)
        self.horizontal_alignment = kwargs.get('horizontal_alignment', HorizontalAlignment.CENTER)
        self.text_horizontal_alignment = kwargs.get('text_horizontal_alignment', HorizontalAlignment.CENTER)

        # size inside cell of layout
        self.cell_size = (0,0)
        # offset in cell
        self.cell_offset = (0,0)
        # offset in bounding box
        self.box_offset = (0,0)
    
    def initialize(self):
        ''' initial position is given, calculate self size and other attributes '''
        self.margin = self.margin if self.margin is not None else self.gui.inner_element_margin
    
    def set_pos(self, pos):
        vector = (pos[0] - self.pos[0], pos[1] - self.pos[1])
        self.pos = (self.pos[0] + vector[0], self.pos[1] + vector[1])

    def set_gui(self, gui):
        self.gui = gui
        
    def step(self):
        pass
        
    def draw(self):
        if GUI_DEBUG_MODE:
            pygame.draw.rect(self.gui.win, (255,255,0), ((self.pos[0] + self.cell_offset[0], self.pos[1] + self.cell_offset[1]), self.size), 1)
            pygame.draw.rect(self.gui.win, (255,0,255), (self.pos, self.cell_size), 1)
        
    def get_values(self) -> Tuple[Any, Any]:
        ''' return key value '''
        return None
        
    def on_click_up(self, mouse_button: MouseButton=None):
        pass

    def on_click_down(self, mouse_button: MouseButton=None):
        pass
        
    def on_release(self):
        pass
    
    def on_hold(self):
        pass


class Text(Element):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def initialize(self):
        super().initialize()
        bg_color = None
        if GUI_DEBUG_MODE:
            bg_color = (10,10,10)
        self.text_surf = self.gui.default_font.render(self.text, True, self.gui.color_pallete.text_color, bg_color)
        self.size = (max(self.text_surf.get_width() + self.margin * 2, self.initial_width), max(self.text_surf.get_height() + self.margin * 2, self.gui.min_element_height))
        self.box_offset = {
            HorizontalAlignment.LEFT: (0, self.size[1] / 2 - self.text_surf.get_height() / 2),
            HorizontalAlignment.CENTER: (self.size[0] / 2 - self.text_surf.get_width() / 2, self.size[1] / 2 - self.text_surf.get_height() / 2),
            HorizontalAlignment.RIGHT: (self.size[0] - self.text_surf.get_width(), self.size[1] / 2 - self.text_surf.get_height() / 2)
        }.get(self.text_horizontal_alignment)

    def draw(self):
        super().draw()
        self.gui.win.blit(self.text_surf, (self.pos[0] + self.box_offset[0] + self.cell_offset[0], self.pos[1] + self.box_offset[1] + self.cell_offset[1]))


class Surf(Element):
    def __init__(self, surf: pygame.Surface, scale: float=1.0, fixed_size=None, smooth=False, **kwargs):
        super().__init__(**kwargs)
        self.smooth = smooth
        self.scale = scale
        self.fixed_size = fixed_size
        self.update_surf(surf)

    def update_surf(self, surf: pygame.Surface):
        if self.smooth:
            self.surf = pygame.transform.smoothscale_by(surf, self.scale)
        else:
            self.surf = pygame.transform.scale_by(surf, self.scale)

        if self.fixed_size:
            if self.smooth:
                self.surf = pygame.transform.smoothscale(surf, self.fixed_size)
            else:
                self.surf = pygame.transform.scale(surf, self.fixed_size)

    def initialize(self):
        super().initialize()
        self.size = self.surf.get_size()
    
    def draw(self):
        super().draw()
        self.gui.win.blit(self.surf, self.pos)


class Button(Element):
    def __init__(self, text, key, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.text = text
        self.mouse_button = kwargs.get('mouse_button', MouseButton.LEFT)
        
    def initialize(self):
        super().initialize()
        self.text_surf = self.gui.default_font.render(self.text, True, self.gui.color_pallete.text_color)
        self.size = (max(self.text_surf.get_width() + self.margin * 2, self.initial_width), max(self.text_surf.get_height() + self.margin * 2, self.gui.min_element_height))
        self.box_offset = {
            HorizontalAlignment.LEFT: (self.gui.inner_element_margin, self.size[1] / 2 - self.text_surf.get_height() / 2),
            HorizontalAlignment.CENTER: (self.size[0] / 2 - self.text_surf.get_width() / 2, self.size[1] / 2 - self.text_surf.get_height() / 2),
            HorizontalAlignment.RIGHT: (self.size[0] - self.text_surf.get_width() - self.gui.inner_element_margin, self.size[1] / 2 - self.text_surf.get_height() / 2)
        }.get(self.text_horizontal_alignment)

    def on_click_up(self, mouse_button: MouseButton):
        super().on_click_up(mouse_button)
        if mouse_button == self.mouse_button:
            self.parent.notify_event(self.key)

    def step(self):
        super().step()
        mouse_pos = pygame.mouse.get_pos()

        if point_in_rect(mouse_pos, (self.pos, self.size)):
            self.gui.focused_element = self

    def draw(self):
        super().draw()
        if self is self.gui.focused_element:
            color = self.gui.color_pallete.button_focus_back_color
        else:
            color = self.gui.color_pallete.button_back_color
        
        pygame.draw.rect(self.gui.win, color, (self.pos, self.size))
        self.gui.win.blit(self.text_surf, (self.pos[0] + self.box_offset[0], self.pos[1] + self.box_offset[1]))


class CheckBox(Button):
    def __init__(self, text, key, **kwargs):
        super().__init__(text, key, **kwargs)
        self.selected = False
    
    def initialize(self):
        super().initialize()
        self.text_surf = self.gui.default_font.render(self.text, True, self.gui.color_pallete.text_color)
        self.size = (self.text_surf.get_width() + self.margin * 3 + check_box_size[0], max(self.text_surf.get_height() + self.margin * 2, self.gui.min_element_height, check_box_size[1]))

    def get_values(self) -> Tuple[Any, Any]:
        return [(self.key, self.selected)]
        
    def on_click_up(self, mouse_button: MouseButton=None):
        if mouse_button == self.mouse_button:
            self.selected = not self.selected
        super().on_click_up(mouse_button)
    
    def draw(self):
        Element.draw(self)
        pos = self.pos
        focus = self is self.gui.focused_element
        selected = self.selected

        if not selected and not focus:
            area = check_box_areas[0]
        if not selected and focus:
            area = check_box_areas[1]
        if selected and not focus:
            area = check_box_areas[2]
        if selected and focus:
            area = check_box_areas[3]

        self.gui.win.blit(check_box_image, (self.pos[0], self.pos[1] + self.size[1] / 2 - check_box_size[1] / 2), area)
        self.gui.win.blit(self.text_surf, (self.pos[0] + check_box_size[0] + self.margin , self.pos[1] + self.size[1] / 2 - self.text_surf.get_height() / 2))


class Slider(Element):
    def __init__(self, key, min_value, max_value, initial_value, width=100, enable_events=False, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.width = width
        self.key = key
        
        self.margin = 3
        self.enable_events = enable_events
        
    def initialize(self):
        super().initialize()
        self.size = (self.width, self.gui.min_element_height)
        
    def get_values(self) -> Tuple[Any, Any]:
        return [(self.key, self.value)]
        
    def step(self):
        super().step()
        if self.gui.mouse_hold and self is not self.gui.focused_element:
            return 
        mouse_pos = pygame.mouse.get_pos()
        if point_in_rect(mouse_pos, (self.pos, self.size)):
            self.gui.focused_element = self

    def on_hold(self):
        if self is not self.gui.focused_element:
            return 
        
        x = self.pos[0] + self.margin
        width = self.size[0] - 2 * self.margin
        mouse_pos = pygame.mouse.get_pos()
        
        value = (mouse_pos[0] - x) / width
        
        # clamp
        if value > 1.0:
            value = 1.0
        elif value < 0.0:
            value = 0.0
        
        self.value = (self.max_value - self.min_value) * value
        if self.enable_events:
            self.parent.notify_event(self.key)
        
    def draw(self):
        super().draw()
        if self is self.gui.focused_element:
            color = self.gui.color_pallete.button_focus_back_color
        else:
            color = self.gui.color_pallete.button_back_color
        pygame.draw.rect(self.gui.win, color, (self.pos, self.size))
        value = (self.value - self.min_value) / (self.max_value - self.min_value)
        
        x = self.pos[0] + self.margin
        y = self.pos[1] + self.margin
        width = (self.size[0] - 2 * self.margin) * value
        height = self.size[1] - 2 * self.margin
        pygame.draw.rect(self.gui.win, self.gui.color_pallete.button_slider_color, ((x, y), (width, height)))
        pygame.draw.line(self.gui.win, self.gui.color_pallete.button_slider_color2, (x + width, y), (x + width, y + height - 1), 2)


class ElementComposition(Element):
    def __init__(self, layout, **kwargs):
        super().__init__(**kwargs)
        self.layout : List[List[Element]] = layout
        self.elements : List[Element]= []

    def initialize(self):
        super().initialize()
        self.calculate()

    def set_pos(self, pos):
        vector = (pos[0] - self.pos[0], pos[1] - self.pos[1])
        self.pos = (self.pos[0] + vector[0], self.pos[1] + vector[1])
        for element in self.elements:
            element.set_pos((element.pos[0] + vector[0], element.pos[1] + vector[1]))

    def calculate(self):
        size_x = 0
        size_y = 0
        pos_y_acc = self.pos[1]
        
        for row in self.layout:
            pos_x_acc = self.pos[0]
            row_y_max = 0
            size_row_x = 0
            for element in row:

                self.elements.append(element)
                element.set_gui(self.gui)
                element.parent = self
                element.pos = (pos_x_acc, pos_y_acc)
                element.initialize()

                size_row_x += element.size[0] + self.gui.margin 

                pos_x_acc += element.size[0] + self.gui.margin
                row_y_max = max(row_y_max, element.size[1])
            size_x = max(size_x, size_row_x)
            
            pos_y_acc += row_y_max + self.gui.margin
            size_y += row_y_max + self.gui.margin
        
        self.size = (size_x - self.gui.margin, size_y - self.gui.margin)
    
    def step(self):
        super().step()
        for element in self.elements:
            element.step()
    
    def draw(self):
        super().draw()
        for element in self.elements:
            element.draw()

    def get_values(self) -> Tuple[Any, Any]:
        values = []
        for element in self.elements:
            returned_values = element.get_values()
            if returned_values:
                values += returned_values
        return values


    def notify_event(self, event : str):
        ''' internal elements can notify the parent of events '''
        self.parent.notify_event(event)


class RadioButtonContainer(ElementComposition):
    ''' can hold stateful elements and allows only one to be selected '''
    def notify_event(self, event: str):
        for element in self.elements:
            try:
                if element.selected and element.key != event:
                    element.selected = False
            except Exception as e:
                print(f'element {element} is not a toggle button but is inside RadioButtonContainer')
                quit(1)
        self.parent.notify_event(event)


class ButtonContainer(ElementComposition):
    ''' button container of elements '''
    def __init__(self, key, layout, **kwargs):
        super().__init__(layout, **kwargs)
        self.key = key
        self.mouse_button = kwargs.get('mouse_button', MouseButton.LEFT)

    def step(self):
        super().step()
        if self.gui.mouse_hold:
            return
        mouse_pos = pygame.mouse.get_pos()

        if point_in_rect(mouse_pos, (self.pos, self.size)):
            self.gui.focused_element = self
        for element in self.elements:
            element.step()

    def on_click_up(self, mouse_button: MouseButton = None):
        super().on_click_up(mouse_button)
        if mouse_button == self.mouse_button:
            self.parent.notify_event(self.key)

    def draw(self):
        super().draw()
        if self is self.gui.focused_element:
            color = self.gui.color_pallete.button_focus_back_color
        else:
            color = self.gui.color_pallete.button_back_color
        pygame.draw.rect(self.gui.win, color, (self.pos, self.size))
        for element in self.elements:
            element.draw()


class ButtonToggleContainer(ElementComposition):
    ''' toggle button container of elements '''
    def __init__(self, key, layout, **kwargs):
        super().__init__(layout, **kwargs)
        self.key = key
        self.selected = kwargs.get('selected', False)
        self.mouse_button = kwargs.get('mouse_button', MouseButton.LEFT)

    def step(self):
        super().step()
        if self.gui.mouse_hold:
            return
        mouse_pos = pygame.mouse.get_pos()

        if point_in_rect(mouse_pos, (self.pos, self.size)):
            self.gui.focused_element = self
        for element in self.elements:
            element.step()

    def on_click_up(self, mouse_button: MouseButton=None):
        super().on_click_up(mouse_button)
        if self.mouse_button == mouse_button:
            self.selected = not self.selected
            self.parent.notify_event(self.key)

    def draw(self):
        super().draw()
        if self is self.gui.focused_element or self.selected:
            color = self.gui.color_pallete.button_focus_back_color
        else:
            color = self.gui.color_pallete.button_back_color
        pygame.draw.rect(self.gui.win, color, (self.pos, self.size))
        if self.selected:
            pygame.draw.rect(self.gui.win, self.gui.color_pallete.button_slider_color, (self.pos, (2, self.size[1])))
        for element in self.elements:
            element.draw()


class Canvas(ElementComposition):
    def calculate(self):
        ''' elements are positioned relative to self pos '''
        size_x = 0
        size_y = 0
        for row in self.layout:
            for element in row:
                self.elements.append(element)
                element.set_gui(self.gui)
                element.parent = self
                element.pos = (self.pos[0] + element.pos[0], self.pos[1] + element.pos[1])
                element.initialize()

                size_x = max(size_x, element.pos[0] - self.pos[0] + element.size[0] + self.margin)
                size_y = max(size_y, element.pos[1] - self.pos[1] + element.size[1] + self.margin)
        self.size = (size_x, size_y)


class DragContainer(ElementComposition):
    def __init__(self, layout, **kwargs):
        super().__init__(layout, **kwargs)
        self.dragging = False
        self.offset = (0,0)

    def on_click_down(self, mouse_button: MouseButton=None):
        mouse_pos = pygame.mouse.get_pos()
        self.offset = (self.pos[0] - mouse_pos[0], self.pos[1] - mouse_pos[1])
        self.dragging = True
    
    def on_click_up(self, mouse_button: MouseButton=None):
        self.dragging = False

    def step(self):
        mouse_pos = pygame.mouse.get_pos()

        if point_in_rect(mouse_pos, (self.pos, self.size)):
            self.gui.focused_element = self

        if self.dragging:
            mouse_pos = pygame.mouse.get_pos()
            self.set_pos((mouse_pos[0] + self.offset[0], mouse_pos[1] + self.offset[1]))
        
        super().step()


class ContextMenu(Gui):
    def __init__(self, win: pygame.Surface, layout, parent: Gui, **kwargs):
        super().__init__(win, layout, **kwargs)
        self.parent = parent

    def click_outside(self, mouse_button: MouseButton=None):
        super().click_outside(mouse_button)
        self.parent.set_context_menu(None)

    def draw(self):
        rect = (self.pos, self.size)
        pygame.draw.rect(self.win, self.parent.color_pallete.button_back_color, rect)
        super().draw()
    
    def notify_event(self, event):
        self.parent.notify_event(event)
        self.parent.set_context_menu(None)
    
    def calculate(self):
        super().calculate()
        for element in self.elements:
            element.size = (max(self.size[0], element.size[0]), element.size[1])


class ContextMenuButton(Button):
    def __init__(self, text, context_menu_layout, **kwargs):
        super().__init__(text, None, **kwargs)
        self.layout = context_menu_layout
    
    def on_click_up(self, mouse_button: MouseButton=None):
        super().on_click_up(mouse_button)
        if mouse_button == self.mouse_button:
            pos = (self.pos[0], self.pos[1] + self.size[1] + self.gui.margin)
            context_menu = ContextMenu(self.gui.win, self.layout, self.gui, pos=pos, name=self.gui.name + '_context_menu')
            self.gui.set_context_menu(context_menu)


class ContextMenuButtonContainer(ElementComposition):
    def __init__(self, layout, context_menu_layout, **kwargs):
        super().__init__(layout, **kwargs)
        self.context_menu_layout = context_menu_layout
        self.mouse_button = kwargs.get('mouse_button', MouseButton.LEFT)

    def open_context_menu(self):
        pos = pygame.mouse.get_pos()
        context_menu = ContextMenu(self.gui.win, self.context_menu_layout, self.gui, pos=pos, name=self.gui.name + '_context_menu')
        self.gui.set_context_menu(context_menu)

    def step(self):
        super().step()
        mouse_pos = pygame.mouse.get_pos()

        if point_in_rect(mouse_pos, (self.pos, self.size)):
            self.gui.focused_element = self

    def on_click_up(self, mouse_button: MouseButton=None):
        super().on_click_up(mouse_button)
        if mouse_button == self.mouse_button:
            self.open_context_menu()


if __name__ == '__main__':
    print(f'gui for pygame version {__version__}')

    # example:
    pygame.init()
    win = pygame.display.set_mode((1280, 800))
    clock = pygame.time.Clock()
 
    font1 = pygame.font.SysFont('Arial', 16)

    radio_buttons = [
        [CheckBox('left', '-left-'), CheckBox('middle', '-middle-'), CheckBox('right', '-right-')]
    ]

    context_menu = [
        [Button('save', '-save-')],
        [Button('save as', '-save as-')],
        [Button('open', '-open-')],
    ]

    layout = [
        [Text('heres button:') ,Button('button', '-button-')],
        [CheckBox('Check one', '-one-'), CheckBox('Check two', '-two-')],
        [Text('Slider:'), Slider('-slider-', 0, 100, 50)],
        [Text('Radio buttons:'), RadioButtonContainer(radio_buttons)],
        [ContextMenuButton('Context Menu', context_menu)]
    ]

    gui = Gui(win, layout, pos=(100,100))

    done = False
    while not done:
        for event in pygame.event.get():
            gui.handle_event(event)
            if event.type == pygame.QUIT:
                done = True
        
        gui.step()

        event, values = gui.read()
        if event:
            print(event, values)

        win.fill((0,0,0))
        gui.draw()

        pygame.display.update()
        clock.tick(30)
    
    pygame.quit()