from auto_slicer.octopi_integration import upload_nested_dict_to_octopi
from auto_slicer.octopi_integration import add_set_to_continous_print, get_continuous_print_state
from auto_slicer.ui import clean_file_dict


path_to_gcode = './auto_slicer/examples/xyz-10mm-calibration-cube_0_6mmNoz_11m_0.20mm_205C_PLA_ENDER3BLTOUCH.gcode'

# Example usage:
location = 'local'  # Or 'sdcard'
f_dict = {'test': [path_to_gcode], 'delete': []}
f_dict = clean_file_dict(f_dict)
print(f'cleaned dict: {f_dict}')
response = upload_nested_dict_to_octopi(f_dict)
print("Upload response:", response)

"""
print("Sending example requests ")
# print("Stopping management")
# set_active(active=False)
print("Adding an example set/job")
add_set_to_continous_print("example.gcode")
print("Fetching queue state")
print(get_continuous_print_state())
"""
