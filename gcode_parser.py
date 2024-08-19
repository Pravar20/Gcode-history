# TODO: Make the cascading end active.
import copy
import re
import os
import numpy as np
import sys


class GcodeWriter:
    def __init__(self, read_file=None, write_file=None):
        self.m_x_amt = 3
        self.m_y_amt = 20
        self.m_z_amt = 45
        self.m_f_amt = 2000

        self.m_soder_amt = 62
        self.m_retract_soder_amt = 54

        self.m_slow_f_amt = 75
        self.m_color_thickness = 4
        self.m_x_advance_amt = 0

        self.m_rest_xy = 250
        self.m_end_z_pos = 45

        # self.m_split_groups = 30
        self.m_split_groups = 0
        self.m_soder_step = 1

        self.m_dft_glass_size = 304

        self.m_tip_diff = 10
        self.m_is_edge = True

        self.m_file_name = "C:\\Users\\Admin\\Desktop\\PreTin Code\\code.txt" if read_file is None else read_file
        self.m_write_file = "C:\\Users\\Admin\\Desktop\\PreTin Code\\test.nc" if write_file is None else write_file

        self.base_steps = {
            'start': lambda: f'G21     ; Millimiter Units\nG91     ; Relative mode\n' + self.base_steps['spin'](),
            'spin': lambda: f'M3 S9000\n',
            'stop_spin': lambda: f'M5\n',
            'move_x': lambda x, f: f'G1 X{x} F{f}\n',
            'move_y': lambda y, f: f'G1 Y{y} F{f}\n',
            'move_z': lambda z, f: f'G1 Z{z} F{f}\n',
            'feed': lambda a, f: f'G1 A{a} F{f}\n',
            'feed_z': lambda z, a, f: f'G1 Z{z} A{a} F{f}\n',
            'move_xy': lambda x, y, f: f'G1 X{x} Y{y} F{f}\n',
            'move_xyz': lambda x, y, z, f: f'G1 Z{z} X{x} Y{y} F{f}\n',
            'feed_move_xy': lambda x, y, a, f: f'G1 X{x} Y{y} A{a} F{f}\n',
            'end': lambda: self.base_steps['move_z'](self.m_end_z_pos, self.m_f_amt) + self.base_steps['stop_spin']()
        }

    # ________________________________Update methods_______________________________________
    def update_m_x_amt(self, amt):
        self.m_x_amt = amt

    def update_m_y_amt(self, amt):
        self.m_y_amt = amt

    def update_m_z_amt(self, amt):
        self.m_z_amt = amt

    def update_m_f_amt(self, amt):
        self.m_f_amt = amt

    def update_m_soder_amt(self, amt):
        self.m_soder_amt = amt

    def update_m_retract_soder_amt(self, amt):
        self.m_retract_soder_amt = amt

    def update_m_slow_f_amt(self, amt):
        self.m_slow_f_amt = amt

    def update_m_color_thickness(self, amt):
        self.m_color_thickness = amt

    def update_m_x_advance_amt(self, amt):
        self.m_x_advance_amt = amt

    def update_m_rest_xy(self, amt):
        self.m_rest_xy = amt

    def update_m_end_z_pos(self, amt):
        self.m_end_z_pos = amt

    def update_m_split_groups(self, amt):
        self.m_split_groups = amt

    def update_m_soder_step(self, amt):
        self.m_soder_step = amt

    def update_m_dft_glass_size(self, amt):
        self.m_dft_glass_size = amt

    def update_m_tip_diff(self, amt):
        self.m_tip_diff = amt

    def update_m_is_edge(self, amt):
        self.m_is_edge = amt

    def update_m_file_name(self, amt):
        self.m_file_name = amt

    def update_m_write_file(self, amt):
        self.m_write_file = amt

    def run_func(self, fn_str):
        return exec(fn_str)

    def change_class_variables(self):
        print("Enter log value to replace the class variables by (Ctrl+D (UNIX) or Ctrl+Z + Enter (Win) to end input):")
        log_values = sys.stdin.readlines()
        values = []
        for value in log_values:
            name, val = value.split(': ')
            name, val = name.strip(), val.strip()
            # If not a file name then eval, else leave as is
            if 'file' not in name:
                val = eval(val.strip())
            else:
                val = f'\'{val}\''
                val = val.replace('\\', '\\\\')
            values.append(('update_' + name, val))

        for pair in values:
            self.run_func(f'self.{pair[0]}({pair[1]})')

    # _____________________________________________________________________________________

    def param_dft(self, lst):
        # List pad with None.
        if len(lst) != 6:
            lst += [None] * (6 - len(lst))
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
                case 'color_up':
                    file_write += self.__color_up(cmd[1])
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

        paint_step = self.m_y_amt
        y_lst = [paint_step for _ in range(0, (self.m_dft_glass_size - self.m_tip_diff), paint_step)][:-1]
        y_lst = y_lst + [(self.m_dft_glass_size - self.m_tip_diff) % paint_step]

        # # TODO: TEST CODE
        # print(y_lst, len(y_lst), sum(y_lst))
        # a = copy.deepcopy(y_lst)
        # for y, idx in zip(a[:], range(len(a[:]))):
        #     a[idx] = y + paint_step*idx
        # print(a, len(a))
        # exit(0)

        # Calc the max amount of y, y movement.
        y_max = sum(y_lst)

        cd = ''
        for y_cnt, y in enumerate(y_lst):
            # First one; add more soder.
            if y_cnt == 0:
                cd += f'feed_soder(,{y},,,{self.m_soder_amt + 4},)\n'
            elif y_cnt % self.m_soder_step == 0:
                cd += f'feed_soder(,,{self.m_z_amt},{self.m_f_amt},{self.m_soder_amt},)\n'

            cd += f'color_up({self.m_x_amt},{y},{self.m_z_amt},{self.m_slow_f_amt},{self.m_soder_amt},)\n'

        # # Change axis for double side
        # cd += f'change_axis({self.m_dft_glass_size - self.m_tip_diff},{-y_max},,,,)\n'
        #
        # for y_cnt, y in enumerate(y_lst):
        #     # First one; add more soder.
        #     if y_cnt == 0:
        #         cd += f'feed_soder(,{y},,,{self.m_soder_amt + 4},)\n'
        #     elif y_cnt % self.m_soder_step == 0:
        #         cd += f'feed_soder(,,{self.m_z_amt},{self.m_f_amt},{self.m_soder_amt},)\n'
        #
        #     cd += f'color_up({-self.m_x_amt},{y},{self.m_z_amt},{self.m_slow_f_amt},{self.m_soder_amt},)\n'

        # cd += f'change_axis({-(self.m_dft_glass_size - self.m_tip_diff)},{-y_max},,,,)\n'
        cd += f'change_axis({0},{-y_max},,,,)\n'
        cd += f'end()\n'

        code_write = open(self.m_file_name, 'w')
        code_write.write(cd)
        code_write.close()

    def __color_right(self, param_lst):
        x, y, _, f, _, is_edge = self.param_dft(param_lst)

        code = f'; Color a strip of length {x}, width {y * self.m_color_thickness}.\n'
        if is_edge:
            code += f'; Edge strip, extra step.\n'
        # Paint 'color_thickness' times.
        for _ in range(self.m_color_thickness):
            # if edge do it twice.
            if is_edge:
                code += self.base_steps['move_x'](x, f)
                code += self.base_steps['move_x'](-x, f)

            # Go right by given.
            code += self.base_steps['move_x'](x, f)
            # While back up by 1
            code += self.base_steps['move_xy'](-x, y, f)

            # TODO: Temp test to see if still good.
            # Do it again
            # code += self.base_steps['move_x'](x, f)
            # code += self.base_steps['move_x'](-x, f)

            # code += self.base_steps['move_x'](x, f)

        # Prime next step with y reset.
        code += self.base_steps['move_xy'](self.m_x_advance_amt, -y * self.m_color_thickness, f)
        return code + '\n'

    # def __color_up(self, param_lst):
    #     x, y, z, f, s, _ = self.param_dft(param_lst)
    #     code = f'; Color a strip of length {y}, width {x}.\n'
    #     # Spread color on half strip segment.
    #     code += f'; Spread solder on half the segment.\n'
    #     for _ in range(self.m_color_thickness // 2):
    #         code += self.base_steps['move_y'](y, self.m_f_amt)
    #         code += self.base_steps['move_x'](x, self.m_f_amt)
    #         code += self.base_steps['move_y'](-y, self.m_f_amt)
    #     code += self.base_steps['move_x'](-(x * (self.m_color_thickness // 2)), self.m_f_amt)
    #
    #     code += f'; Massage the solder onto the segment.\n'
    #     # Extensively go over the segment slowly massaging the solder in.
    #     # for _ in range(self.m_color_thickness):
    #     code += self.base_steps['move_y'](y, f)
    #     code += self.base_steps['move_xyz'](x * self.m_color_thickness // 2, -y, 5, self.m_f_amt)
    #     code += self.base_steps['move_z'](-5, self.m_f_amt)
    #
    #     code += self.base_steps['move_y'](y, f)
    #     code += self.base_steps['move_xyz'](0, -y, 5, self.m_f_amt)
    #     code += self.base_steps['move_z'](-5, self.m_f_amt)
    #
    #     # Refill on solder
    #     code += '\n' + self.__feed_soder([x, y, z, self.m_f_amt, s])
    #
    #     # Spread color on other half strip segment.
    #     code += f'; Spread solder on other half the segment.\n'
    #     for _ in range(self.m_color_thickness // 2):
    #         code += self.base_steps['move_y'](y, self.m_f_amt)
    #         code += self.base_steps['move_x'](x, self.m_f_amt)
    #         code += self.base_steps['move_y'](-y, self.m_f_amt)
    #     code += self.base_steps['move_y'](y, f)
    #     code += self.base_steps['move_x'](-(x * self.m_color_thickness), self.m_f_amt)
    #
    #     # code += f'; Massage the solder onto the segment.\n'
    #     # # Extensively go over the segment slowly massaging the solder in.
    #     # for _ in range(self.m_color_thickness):
    #     #     code += self.base_steps['move_y'](y, f)
    #     #     code += self.base_steps['move_xyz'](x, -y, 5, self.m_f_amt)
    #     #     code += self.base_steps['move_z'](-5, self.m_f_amt)
    #     # code += self.base_steps['move_xyz'](-(x * self.m_color_thickness), y, 5, self.m_f_amt)
    #     # code += self.base_steps['move_z'](-5, self.m_f_amt)
    #
    #     return code + '\n'

    """
    Attempt at solder feeder with less frequent feeding.
    """
    def __color_up(self, param_lst):
        x, y, z, f, s, _ = self.param_dft(param_lst)
        code = f'; Color a strip of length {y}, width {x}.\n'
        # Spread color on half strip segment.
        code += f'; Spread solder on the segment.\n'
        for _ in range(self.m_color_thickness):
            code += self.base_steps['move_y'](y, self.m_f_amt)
            code += self.base_steps['move_x'](x, self.m_f_amt)
            code += self.base_steps['move_y'](-y, self.m_f_amt)
        code += self.base_steps['move_x'](-(x * self.m_color_thickness), self.m_f_amt)

        # Extensively go over the segment slowly massaging the solder in.
        code += f'; Massage the solder onto the segment.\n'
        for _ in range(self.m_color_thickness):
            code += self.base_steps['move_y'](y, f)
            code += self.base_steps['move_xyz'](x, -y, 5, self.m_f_amt)
            code += self.base_steps['move_z'](-5, self.m_f_amt)
        code += self.base_steps['move_xyz'](-(x * self.m_color_thickness), y, 5, self.m_f_amt)
        code += self.base_steps['move_z'](-5, self.m_f_amt)

        return code + '\n'

    def __feed_soder(self, param_lst):
        _, _, z, f, s, *_ = self.param_dft(param_lst)
        # Feed soder.
        code = f'; Feed {s} amount of soder.\n'
        code += self.base_steps['move_z'](z, f)
        code += self.base_steps['feed'](-s, f)
        code += f'; Retract {self.m_retract_soder_amt} soder\n'
        code += self.base_steps['feed'](self.m_retract_soder_amt, f)
        code += self.base_steps['move_z'](-z, f)
        return code + '\n'

    def __change_axis(self, param_lst):
        x, y, z, f, *_ = self.param_dft(param_lst)
        code = f'; Change axis to (x, y, z): ({x}, {y}, {z}).\n'
        code += self.base_steps['move_z'](z, f)
        code += self.base_steps['move_xy'](x, y, f)
        code += self.base_steps['move_z'](-z, f)
        return code + '\n'

    def run(self):
        self.prompt()
        self.compile_code()

    def compile_code(self):
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
    if len(sys.argv) == 3 and sys.argv[2] == 'custom':
        print('change')
        G.change_class_variables()
    if len(sys.argv) == 2 and sys.argv[1] == 'code':
        print('compile')
        G.compile_code()
    else:
        print('run')
        G.run()