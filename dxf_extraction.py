# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 10:50:49 2025

@author: Esneyder Montoya, PhD, PE
"""

import pandas as pd
import ezdxf as ed
from collections import Counter
import math
from fractions import Fraction
from ezdxf import colors


def process_dxf(dxf_file_path, selected_layer, z_offset, output_dxf_name):

    
    
    # Open a DXF file
    doc = ed.readfile(dxf_file_path)
    
    # Now you can work with the DXF document
    # For example, to access the modelspace:
    msp = doc.modelspace()
    
    # To iterate through all entities in modelspace:
    #for entity in msp:
    #    print(f"Entity: {entity.dxftype()}")
    
    # To get specific layers:
    # layers = doc.layers
    # for layer in layers:
    #     print(f"Layer: {layer.dxf.name}")
    #    for entity in layer:
    #        print(f"Entity: {entity.dxftype()}")
    
    
    # Specify the layer name you want to analyze
    layer_name = selected_layer  # Replace with your actual layer name
    
    # Filter entities by layer and collect their types
    entity_types = []
    for entity in msp.query(f'*[layer=="{layer_name}"]'):
        entity_types.append(entity.dxftype())
    
    # Count and print the unique entity types in the layer
    type_counter = Counter(entity_types)
    print(f"Entity types in layer '{layer_name}':")
    for entity_type, count in type_counter.items():
        print(f"  - {entity_type}: {count} entities")
    
    # If you want to print all entities in the layer with their types
    print(f"\nDetailed list of entities in layer '{layer_name}':")
    for i, entity in enumerate(msp.query(f'*[layer=="{layer_name}"]')):
        print(f"  {i+1}. Type: {entity.dxftype()}, Handle: {entity.dxf.handle}")
    
    # Helper function to convert AutoCAD color index to RGB
    def acad_color_to_rgb(doc, color_index):
        """Convert AutoCAD color index to RGB tuple"""
        if color_index == 0:  # ByBlock
            return "ByBlock"
        elif color_index == 256:  # ByLayer
            return "ByLayer"
        elif color_index == 257:  # ByEntity
            return "ByEntity"
        
        try:
            # Try to get RGB from the document's color table
            rgb = doc.tables.colors.get(color_index)
            if rgb:
                return rgb
        except:
            pass
        
        # Fallback to standard AutoCAD color table
        # This is a simplified version - a complete implementation would have all 255 colors
        standard_colors = {
            1: (255, 0, 0),      # Red
            2: (255, 255, 0),    # Yellow
            3: (0, 255, 0),      # Green
            4: (0, 255, 255),    # Cyan
            5: (0, 0, 255),      # Blue
            6: (255, 0, 255),    # Magenta
            7: (255, 255, 255),  # White/Black
            8: (128, 128, 128),  # Gray
            9: (192, 192, 192),  # Light Gray
        }
        
        return standard_colors.get(color_index, (0, 0, 0))  # Default to black if not found
    
    # Filter MTEXT entities by layer and collect their data
    mtext_data = []
    for entity in msp.query(f'MTEXT[layer=="{layer_name}"]'):
        # Get the insertion point (x, y coordinates)
        x, y, z = entity.dxf.insert
        
        # Get the text content
        text_content = entity.text
        
        # Get the color index
        color_index = entity.dxf.color
        
        # Convert color index to RGB
        #rgb = acad_color_to_rgb(doc, color_index)
        
        # Format RGB as a string for display
        if isinstance(color_index, tuple):
            rgb_str = f"RGB({color_index[0]}, {color_index[1]}, {color_index[2]})"
        else:
            rgb_str = color_index
        
        # Add data to our list
        mtext_data.append({
            'full_text': text_content,
            'x': x,
            'y': y,
            'z': z,
            'color_index': color_index,
    #       'rgb': rgb_str,
            'handle': entity.dxf.handle
        })
    
    # Create a DataFrame from the collected data
    mtext_df = pd.DataFrame(mtext_data)
    
    # Print summary information
    print(f"Found {len(mtext_df)} MTEXT entities in layer '{layer_name}'")
    print("\nDataFrame Preview:")
    print(mtext_df.head())
    
    # Optional: Save to CSV
    # mtext_df.to_csv(f"mtext_entities_{layer_name}.csv", index=False)
    
    # Print entity type counts for reference
    entity_types = []
    for entity in msp.query(f'*[layer=="{layer_name}"]'):
        entity_types.append(entity.dxftype())
    
    type_counter = Counter(entity_types)
    print(f"\nAll entity types in layer '{layer_name}':")
    for entity_type, count in type_counter.items():
        print(f"  - {entity_type}: {count} entities")
    
    # Drop rows where full_text contains "Elong"
    mtext_df=mtext_df[~mtext_df.full_text.str.contains("Elong")].reset_index(drop=True)
    # mtext_df.drop('handle', axis=1, inplace=True)
    
    text = mtext_df.full_text.str.split(';')
    text = text.str[-1]
    mtext_df['text'] =  text
    
    mtext_df.drop('full_text', axis=1, inplace=True)
    
    r = mtext_df.text.astype(float)
    h_CG_max= max(r)
    h_CG_min= min(r)
    
    h_CG_max , h_CG_min
    
    r1 = max(mtext_df.z)
    r2 = min(mtext_df.z)
    h_cable = (r1-r2)*1000 / 25  #max cable height from top to bot in inches
    
    r1, r2, h_cable
    
    # Define a function to get chair height in inches
    # Ask the user if the chair heights given in the dxf already have the z-offset !!!
    #z_offset = input("Check if offset given in dxf, What is the offset b/w the cable CGS and the chair height (inches)? ")
    
    # z_offset = 0.75
    
    def chair(h_CG):
        x = float(h_CG)
        if x >= 25:
            hc = round(float(Fraction(round((x / 25 - float(z_offset))*4,0)/4)),2)   # ok.
        elif x >= 10:
            hc = 0.75
        #else: hc = (round(x,1))
        else: hc = 0
        return hc
    
    # Apply the function to the 'Age' column
    mtext_df['Chairs'] = mtext_df['text'].apply(chair)
    
    
    def convert_to_mixed_number(x):

        #decimal_value = 5.25
        fraction_object = Fraction(x)
        
        whole_number = fraction_object.numerator // fraction_object.denominator
        remainder_numerator = fraction_object.numerator % fraction_object.denominator
        denominator = fraction_object.denominator
        
        if remainder_numerator == 0:

            if whole_number == 0:
                return " "
            else: return (f"{whole_number}")
                
            print (f"{remainder_numerator}/{denominator}")
            
        else:

            if whole_number == 0:
                return (f"{remainder_numerator}/{denominator}")
            else: return  (f"{whole_number} {remainder_numerator}/{denominator}")

    
    
    
    def assign_chair_colors(chair_height):
        if not isinstance(chair_height, (int, float)) or chair_height == " ":
            return (125, 125, 125)  # Default gray for missing/invalid values
        
        # Convert to float to ensure proper comparison
        height = float(chair_height)
        
        # Define colors for different height ranges
        # Starting from 1.00 with increments of 0.25
        if height == 1.00:
            return (0, 0, 255)  # Blue
        elif height == 1.25:
            return (0, 125, 255)
        elif height == 1.50:
            return (0, 255, 255)  # Cyan
        elif height == 1.75:
            return (0, 255, 125)
        elif height == 2.00:
            return (0, 255, 125)  # Green
        elif height == 2.25:
            return (125, 255, 0)
        elif height == 2.50:
            return (255, 255, 0)  # Yellow
        elif height == 2.75:
            return (255, 191, 0)
        elif height == 3.00:
            return (255, 125, 0)  # Orange
        elif height == 3.25:
            return (255, 64, 0)
        elif height == 3.50:
            return (255, 0, 0)  # Red
        elif height == 3.75:
            return (255, 0, 64)
        elif height == 4.00:
            return (255, 0, 125)  # Pink
        elif height == 4.25:
            return (255, 0, 191)
        elif height == 4.50:
            return (255, 0, 255)  # Magenta
        elif height == 4.75:
            return (191, 0, 255)
        elif height == 5.00:
            return (125, 0, 255)  # Purple
        elif height == 5.25:
            return (64, 0, 255)
        elif height == 5.50:
            return (0, 0, 191)  # Dark blue
        elif height == 5.75:
            return (0, 0, 125)
        elif height >= 6.00:
            return (0, 0, 64)  # Very dark blue
        else:
            # For values that fall between defined increments, find the closest lower increment
            # and return its color directly instead of recursively calling the function
            base_height = int(height * 4) / 4  # Round down to nearest 0.25
            
            # Use a direct mapping instead of recursion
            color_map = {
                1.00: (0, 0, 255),
                1.25: (0, 125, 255),
                1.50: (0, 255, 255),
                1.75: (0, 255, 125),
                2.00: (0, 255, 125),
                2.25: (125, 255, 0),
                2.50: (255, 255, 0),
                2.75: (255, 191, 0),
                3.00: (255, 125, 0),
                3.25: (255, 64, 0),
                3.50: (255, 0, 0),
                3.75: (255, 0, 64),
                4.00: (255, 0, 125),
                4.25: (255, 0, 191),
                4.50: (255, 0, 255),
                4.75: (191, 0, 255),
                5.00: (125, 0, 255),
                5.25: (64, 0, 255),
                5.50: (0, 0, 191),
                5.75: (0, 0, 125),
                6.00: (0,0,64)
            }
            
            # Return the color for the base_height if it exists in the map
            if base_height in color_map:
                return color_map[base_height]
            # If base_height is less than 1.00, return a default color
            elif base_height < 1.00:
                return (125, 125, 125)  # Default gray
            # If base_height is greater than 5.75 but less than 6.00
            else:
                return (0, 0, 64)  # Very dark blue
    
            if type(chair_height) == str : return " "
    
    # Apply the function to create a new 'Color' column in the dataframe
    mtext_df['chairColor'] = mtext_df['Chairs'].apply(assign_chair_colors)
    
    def assign_chair_hex_colors(chair_height):
        if not isinstance(chair_height, (int, float)) or chair_height == " ":
            return "#808080"  # Default gray for missing/invalid values
        
        # Convert to float to ensure proper comparison
        height = float(chair_height)
        
        # Define colors for different height ranges using hex notation
        # Starting from 1.00 with increments of 0.25
        if height == 1.00:
            return "#0000FF"  # Blue
        elif height == 1.25:
            return "#0080FF"
        elif height == 1.50:
            return "#00FFFF"  # Cyan
        elif height == 1.75:
            return "#00FF80"
        elif height == 2.00:
            return "#00FF00"  # Green
        elif height == 2.25:
            return "#80FF00"
        elif height == 2.50:
            return "#FFFF00"  # Yellow
        elif height == 2.75:
            return "#FFBF00"
        elif height == 3.00:
            return "#FF8000"  # Orange
        elif height == 3.25:
            return "#FF4000"
        elif height == 3.50:
            return "#FF0000"  # Red
        elif height == 3.75:
            return "#FF0040"
        elif height == 4.00:
            return "#FF0080"  # Pink
        elif height == 4.25:
            return "#FF00BF"
        elif height == 4.50:
            return "#FF00FF"  # Magenta
        elif height == 4.75:
            return "#BF00FF"
        elif height == 5.00:
            return "#8000FF"  # Purple
        elif height == 5.25:
            return "#4000FF"
        elif height == 5.50:
            return "#0000BF"  # Dark blue
        elif height == 5.75:
            return "#000080"
        elif height >= 6.00:
            return "#000040"  # Very dark blue
        else:
            # For values that fall between defined increments, find the closest lower increment
            # and return its color directly instead of recursively calling the function
            base_height = int(height * 4) / 4  # Round down to nearest 0.25
            
            # Use a direct mapping instead of recursion
            color_map = {
                1.00: "#0000FF",
                1.25: "#0080FF",
                1.50: "#00FFFF",
                1.75: "#00FF80",
                2.00: "#00FF00",
                2.25: "#80FF00",
                2.50: "#FFFF00",
                2.75: "#FFBF00",
                3.00: "#FF8000",
                3.25: "#FF4000",
                3.50: "#FF0000",
                3.75: "#FF0040",
                4.00: "#FF0080",
                4.25: "#FF00BF",
                4.50: "#FF00FF",
                4.75: "#BF00FF",
                5.00: "#8000FF",
                5.25: "#4000FF",
                5.50: "#0000BF",
                5.75: "#000080"
            }
            
            # Return the color for the base_height if it exists in the map
            if base_height in color_map:
                return color_map[base_height]
            # If base_height is less than 1.00, return a default color
            elif base_height < 1.00:
                return "#808080"  # Default gray
            # If base_height is greater than 5.75 but less than 6.00
            else:
                return "#000040"  # Very dark blue
    
            if type(chair_height) == str : return " "
    
    # Apply the function to create a new 'Color' column in the dataframe
    mtext_df['chairHexColor'] = mtext_df['Chairs'].apply(assign_chair_hex_colors)
    
    mtext_df['trueColor'] = mtext_df.chairColor.apply(ed.colors.rgb2int)
    
    
    
    
    mtext_df['Chairs_Fraction'] =mtext_df['Chairs'].apply(convert_to_mixed_number)
    
    
    
    
    # To delete entities from a layer
    
    # Specify the layer name from which to delete MTEXT entities
    layer_name = selected_layer
    
    # Find all MTEXT entities on the specified layer
    mtext_entities = msp.query('MTEXT[layer=="{}"]'.format(layer_name))
    
    # Count how many will be deleted
    count = len(mtext_entities)
    print(f"Found {count} MTEXT entities on layer '{layer_name}'")
    
    # Delete each entity
    for entity in mtext_entities:
        msp.delete_entity(entity)
    
    
    # Create a new layer if it doesn't exist
    new_layer_name = selected_layer + "_chairs"
    if new_layer_name not in doc.layers:
        doc.layers.new(name=new_layer_name)
    
    # Assuming mtext_df has columns: 'text', 'x', 'y'
    # Loop through each row in the DataFrame and add text
    for index, row in mtext_df.iterrows():
        # Extract text and coordinates
        text_content = str(row['Chairs_Fraction'])
        colorRGB = row['chairColor']
        colorHex = row['chairHexColor']
    #    true_Color = row['trueColor']
        x_coord = row['x']
        y_coord = row['y']
        z_coord = row['z']
    
        # Add text entity to the new layer with position directly specified
        # Note: Fixed the syntax error by properly organizing arguments
        msp.add_text(
            text_content,  # Positional argument first
            # text.dxf.true_color removed or should be part of dxfattribs
            # If you need to set color, include it in dxfattribs
            dxfattribs={
                'layer': new_layer_name,
                'height': 0.100,  # Text height - adjust as needed
                'style': 'STANDARD',  # Text style - adjust as needed
                'insert': (x_coord, y_coord, z_coord),  # Specify position directly here
    #            'set_elevation' : 'MIDDLE',
    #            'halign' : 4,
                 'rgb': ed.colors.RGB(colorRGB[0], colorRGB[1], colorRGB[2]) # Uncomment if you want to use the color from DataFrame
                # Or use: 'true_color': text.dxf.true_color  # If this is what you intended
            }, 
        )     # .set_align_enum(align=text_content.Alignment.LEFT)
        
    
    # Save the modified DXF file
    doc.saveas(output_dxf_name)
    print(f"Added {len(mtext_df)} text entities to layer '{new_layer_name}'")
    
    chair_counts = mtext_df['Chairs'].value_counts()
   
    
    chairs_df = chair_counts.to_frame()
    chairs_df = chairs_df.sort_values(by='Chairs', ascending=True)
    chairs_df = chairs_df.drop(0)
    chairs_df.index.name = 'h_chair [in]'
    print("\nCounts for 'chairs':\n", chair_counts)
    chairs_df = chairs_df.reset_index()
    
    chairs_df.rename(columns={'index': 'h_chair [in]'}, inplace=True)
    
    chairs_df['h_chairs_inches'] =chairs_df['h_chair [in]'].apply(convert_to_mixed_number)
    
    # chairs_df.drop(['h_chair [in]'], axis = 1, inplace = True)
    
    # chairs_df.rename(columns={'h_chairs_inches': 'h_chair [in]'}, inplace=True)
    
    # Save the chairs and count in an excel file
    
    Excel_file = dxf_file_path.split(".")[0] + ".xlsx"
    
    chairs_df.to_excel(Excel_file, sheet_name='Counts')
    

    return mtext_df , chairs_df

