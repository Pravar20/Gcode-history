# TODO: Make the cascading end active.
import copy
import re
import os
import numpy as np
import math


class GcodeWriter:
    def __init__(self, read_file=None, write_file=None):
        # Make m_y_amt * m_color_thickness  . (6mm proper bonded rest 2 as collateral)
        self.m_x_amt = 12
        self.m_y_amt = 1.5
        self.m_z_amt = 10
        self.m_f_amt = 4000

        self.m_soder_amt = 13
        self.m_retract_soder_amt = 10

        self.m_slow_f_amt = 3000
        self.m_color_thickness = 4
        self.m_x_advance_amt = 10

        self.m_rest_xy = 250
        self.m_end_z_pos = 30
        
        # self.m_split_groups = 30
        self.m_split_groups = 10
        self.m_soder_step = 2

        self.m_dft_glass_size = 304
        
        self.m_tip_diff = 12
        self.m_is_edge = True

        self.m_file_name = "C:\\Users\\Admin\\Desktop\\Practice\\code.txt" if read_file is None else read_file
        self.m_write_file = "C:\\Users\\Admin\\Desktop\\Practice\\test.nc" if write_file is None else write_file

        # {self.base_steps['move_z'](-self.m_end_z_pos, self.m_f_amt)}
        self.base_steps = {
            'start': lambda: f'G21     ; Millimiter Units\nG91     ; Relative mode\n',
            'move_x': lambda x, f: f'G1 X{x} F{f}\n',
            'move_y': lambda y, f: f'G1 Y{y} F{f}\n',
            'move_z': lambda z, f: f'G1 Z{z} F{f}\n',
            'feed': lambda a, f: f'G1 A{a} F{f}\n',
            'feed_z': lambda z, a, f: f'G1 Z{z} A{a} F{f}\n',
            'move_xy': lambda x, y, f: f'G1 X{x} Y{y} F{f}\n',
            'move_xyz': lambda x, y, z, f: f'G1 Z{z} X{x} Y{y} F{f}\n',
            'feed_move_xy': lambda x, y, a, f: f'G1 X{x} Y{y} A{a} F{f}\n',
            'end': lambda: self.base_steps['move_z'](self.m_end_z_pos, self.m_slow_f_amt)
        }
    
    # Update methods
    def update_x(self, amt): self.m_x_amt = amt
    def update_y(self, amt): self.m_y_amt = amt
    def update_z(self, amt): self.m_z_amt = amt
    def update_f(self, amt): self.m_f_amt = amt
    def update_z_f(self, amt): self.m_slow_f_amt = amt
    
    def param_dft(self, lst):
        # List pad with None.
        if len(lst) != 6:
            lst += [None] * (6-len(lst))
        
        # X dft.
        if lst[0] is None:
            lst[0] = self.m_x_amt
        # Y dft.
        if lst[1] is None:
            lst[1] = self.m_y_amt
        # Z dft.
        if lst[2] is None:
            lst[2] = self.m_z_amt
        # F dft.
        if lst[3] is None:
            lst[3] = self.m_f_amt
        # Soder dft amt.
        if lst[4] is None:
            lst[4] = self.m_soder_amt
        # Edge bool.
        if lst[5] is None:
            lst[5] = self.m_is_edge
        return lst

    # Parser function.
    def parser(self):
        # Open file and read all.
        code_f = open(self.m_file_name, 'r')
        code = [_.strip() for _ in code_f.readlines()]
        code_f.close()

        file_write = self.base_steps['start']()
        
        # Parse and execute code to convert into g-code.
        for cmd in code:
            cmd = [c for c in re.split(r'[()]', cmd)][:-1]
            cmd[1] = [eval(prm) if prm != '' else None for prm in cmd[1].split(',')]
            
            # Match commands.
            match cmd[0]:
                case 'color_right':
                    file_write += self.__color_right(cmd[1])
                case 'feed_soder':
                    file_write += self.__feed_soder(cmd[1])
                case 'paint_right':
                    file_write += self.__feed_soder(cmd[1])
                    file_write += self.__color_right(cmd[1])
                case 'change_axis':
                    file_write += self.__change_axis(cmd[1])
                case 'end':
                    file_write += self.base_steps['end']()
        
        g_code_write = open(self.m_write_file, 'w')
        g_code_write.write(file_write)
        g_code_write.close()

    def prompt(self):
        invalid_input = True

        mm_size = self.m_dft_glass_size
        while invalid_input:
            # mm_size = input(f"Insert glass size (press enter for default size of {self.m_dft_glass_size}mm):")
            # Default value.
            if mm_size == '':
                mm_size = self.m_dft_glass_size
                invalid_input = False
            
            if mm_size in ['q', 'quit']:
                exit(0)

            try:
                mm_size = int(mm_size)
                invalid_input = False
            except ValueError as e:
                print(mm_size, ' is not an int.\n', e)

        paint_step = mm_size // self.m_split_groups
        x_lst = [paint_step for _ in range(paint_step, mm_size - self.m_tip_diff, self.m_x_advance_amt)]
        if (mm_size - self.m_tip_diff) % paint_step != 0:
            paint_step = paint_step - self.m_x_advance_amt
            while paint_step > self.m_tip_diff * 20:
                x_lst += [paint_step]
                paint_step = paint_step - self.m_x_advance_amt

        # Calc the max amount of x, y movement.
        y_max = self.m_color_thickness * self.m_y_amt
        y_max = int(y_max) if y_max.is_integer() else y_max
        x_end = self.m_x_advance_amt * len(x_lst)
        x_end = int(x_end) if x_end.is_integer() else x_end

        cd = ''
        # Color whole strip
        x_idx_lst = list(range(len(x_lst)))
        x_center_lst = x_idx_lst[np.ceil(len(x_idx_lst) / self.m_split_groups).astype(int): np.floor((self.m_split_groups - 1) * len(x_idx_lst) / self.m_split_groups).astype(int)]
        x_center_lst = x_center_lst[:np.floor(len(x_center_lst) / 2).astype(int) - 1] + x_center_lst[np.ceil(len(x_center_lst) / 2).astype(int) + 1:]

        for x, x_cnt in zip(x_lst, x_idx_lst):
            if x_cnt % self.m_soder_step == 0:
                # Add more soder at start middle and end.
                if self.__isclose(x_cnt, [x_idx_lst[0], len(x_idx_lst) // 2, x_idx_lst[-1]]):
                    cd += f'feed_soder({x},{y_max},,,{self.m_soder_amt + 8},)\n'
                else:
                    cd += f'feed_soder({x},{y_max},,,,)\n'

            # If edge double stroke.
            if x_cnt in x_center_lst:
                cd += f'color_right({x},,,,,{not self.m_is_edge})\n'
            else:
                cd += f'color_right({x},,,,,{self.m_is_edge})\n'

        # Change axis
        cd += f'change_axis({-(mm_size - self.m_tip_diff - x_lst[-1] - 1)},{(mm_size - self.m_tip_diff)},,,)\n'

        # Color the other whole strip
        for x, x_cnt in zip(x_lst, range(len(x_lst))):
            # First one add more soder.
            if x_cnt == 0:
                cd += f'feed_soder({x},{y_max},,,{self.m_soder_amt + 10},)\n'
            elif x_cnt % self.m_soder_step == 0:
                cd += f'feed_soder({x},{y_max},,,,)\n'
            cd += f'color_right({x},,,,)\n'

        # Return
        cd += f'change_axis({-(mm_size - self.m_tip_diff - x_lst[-1] - 1)},{-(mm_size - self.m_tip_diff)},,,)\n'
        cd += f'end()\n'

        code_write = open(self.m_file_name, 'w')
        code_write.write(cd)
        code_write.close()

    def __color_right(self, param_lst):
        x, y, _, f, _, do_double = self.param_dft(param_lst)
        y = round(y, 2)

        code = f'; Color a strip of length {x}, width {y * self.m_color_thickness}.\n'
        if do_double:
            code += f'; Edge strip, extra step.\n'
        # Paint 'color_thickness' times.
        for _ in range(self.m_color_thickness):
            # if edge do it twice.
            if do_double:
                code += self.base_steps['move_x'](x, f)
                code += self.base_steps['move_x'](-x, f)

            # Go right by given.
            code += self.base_steps['move_x'](x, f)
            # While back up by 1
            code += self.base_steps['move_xy'](-x, y, f)

            # TODO: Temp test to see if still good.
            # # Do it again
            # code += self.base_steps['move_x'](-x, f)
            # code += self.base_steps['move_x'](x, f)
            # code += self.base_steps['move_x'](x, f)

        # Paint 'color_thickness' times while going down.
        for _ in range(self.m_color_thickness):
            # if edge do it twice.
            if do_double:
                code += self.base_steps['move_x'](x, f)
                code += self.base_steps['move_x'](-x, f)

            # Go right by given.
            # While back down by y
            code += self.base_steps['move_xy'](x, -y, f)
            code += self.base_steps['move_x'](-x, f)

            # TODO: Temp test to see if still good.
            # # Do it again
            # code += self.base_steps['move_x'](-x, f)
            # code += self.base_steps['move_x'](x, f)
            # code += self.base_steps['move_x'](x, f)

        # Prime next step with y reset.
        code += self.base_steps['move_xy'](self.m_x_advance_amt, 0, f)
        # code += self.base_steps['move_xy'](self.m_x_advance_amt, -y * self.m_color_thickness, f)
        return code + '\n'

    """
    def __colour_right(self, param_lst):
        x, y, z, f, s = self.param_dft(param_lst)

        code = ''
        pass
    """

    def __feed_soder(self, param_lst):
        x, y, z, f, s, *_ = self.param_dft(param_lst)
        y = round(y, 2)
        # Feed soder.
        code = f'; Feed {s} amount of soder.\n'
        code += self.base_steps['feed_z'](8, 0, f)
        code += self.base_steps['feed_z'](z - 8, -s, f)

        # code += self.base_steps['move_z'](-z, self.m_slow_f_amt)
        # code += self.base_steps['feed_move_xy'](x, y, self.m_retract_soder_amt, f)

        # Retract soder while spreading.
        code += f'; Retract {self.m_retract_soder_amt} and spread till ({x}, {y}).\n'
        code += self.base_steps['move_z'](-z, f)
        code += self.base_steps['feed_move_xy'](x, y, self.m_retract_soder_amt, f)
        code += self.base_steps['move_xy'](-x, 0, f)
        code += self.base_steps['move_y'](-y, f)

        # # Make the soder step a heating existing soder step
        # code = ''
        # code += self.base_steps['move_xyz'](x, y, z, f)
        # code += self.base_steps['move_z'](-z, f)
        # code += self.base_steps['move_xy'](-x, -y, self.m_slow_f_amt)
        return code + '\n'
    
    def __change_axis(self, param_lst):
        x, y, z, f, *_ = self.param_dft(param_lst)
        y = round(y, 2)

        code = f'; Change axis to (x, y, z): ({x}, {y}, {z}).\n'
        code += self.base_steps['move_z'](z, self.m_slow_f_amt)
        code += self.base_steps['move_xy'](x, y, f)
        code += self.base_steps['move_z'](-z, self.m_slow_f_amt)
        return code + '\n'

    def __isclose(self, num, lst):
        return any(np.isclose([num] * len(lst), lst, rtol=0, atol=self.m_soder_step))

    def run(self):
        self.prompt()
        self.parser()
        self.log_out()
        os.startfile(self.m_write_file)

    def log_out(self):
        print('\nDebug log for all class variables:-')
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], (int, str)):
                print(f'\t{key}: {self.__dict__[key]}')


if __name__ == '__main__':
    G = GcodeWriter()
    G.run()
