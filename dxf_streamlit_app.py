import streamlit as st
import pandas as pd
import subprocess
import sys
import os
from pathlib import Path
import tempfile
import dxf_extraction
from dxf_extraction import process_dxf

# Try to import ezdxf for layer extraction
try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    st.error("ezdxf library not found. Please install it with: pip install ezdxf")

def get_dxf_layers(dxf_file_path):
    """Extract layer names from DXF file"""
    if not EZDXF_AVAILABLE:
        return []
    
    try:
        doc = ezdxf.readfile(dxf_file_path)
        layers = [layer.dxf.name for layer in doc.layers]
        return layers
    except Exception as e:
        st.error(f"Error reading DXF file: {str(e)}")
        return []

def run_dxf_extraction(dxf_file_path, selected_layer, z_offset, output_dxf_name):
    """Execute the dxf_extraction.py script and return the dataframes"""
    try:
        # Check if dxf_extraction.py exists
        if not os.path.exists("C:/Users/User/cad/dxf_extraction.py"):
            st.error("dxf_extraction.py file not found in the current directory")
            return None, None, None
        
        # Import the extraction module
        sys.path.append(os.getcwd())
        
        # Try to import and run the extraction
        try:
            import dxf_extraction
            # Assuming the extraction module has a main function that accepts parameters
            # You may need to modify this based on your actual dxf_extraction.py structure
            if hasattr(dxf_extraction, 'process_dxf'):
                mtext_df, chairs_df = dxf_extraction.process_dxf(dxf_file_path, selected_layer, z_offset, output_dxf_name)
            else:
                # Alternative: run as subprocess if no direct function available
                result = subprocess.run([
                    sys.executable, "dxf_extraction.py", 
                    dxf_file_path, selected_layer, str(z_offset), output_dxf_name
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    st.error(f"Error running extraction: {result.stderr}")
                    return None, None, None
                
                # This would require the script to save results to files
                # and then load them back - adjust based on your implementation
                mtext_df = pd.DataFrame()  # Load from saved file
                chairs_df = pd.DataFrame()  # Load from saved file
                
        except Exception as e:
            st.error(f"Error importing or running dxf_extraction: {str(e)}")
            return None, None, None
            
        # Check if the output DXF file was created
        output_dxf_path = output_dxf_name if os.path.exists(output_dxf_name) else None
        
        return mtext_df, chairs_df, output_dxf_path
        
    except Exception as e:
        st.error(f"Error in extraction process: {str(e)}")
        return None, None, None

# Streamlit App Layout
st.set_page_config(page_title="DXF File Analyzer", layout="wide")

st.title("DXF File Analyzer")

# Create the layout columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Controls")
    
    # File upload section
    st.subheader("Load File")
    uploaded_file = st.file_uploader("Choose a DXF file", type=['dxf'])
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Layer selection section
        st.subheader("Select Layer from File")
        layers = get_dxf_layers(tmp_file_path)
        
        if layers:
            selected_layer = st.selectbox("Available Layers:", layers)
            
            # Z-offset input
            st.subheader("Z Offset (Distance between CG of tendon and chair height in inches)")
            z_offset = st.number_input("Enter Z offset value:", value=0.0, step=0.25)
            
            # Modified DXF filename input
            st.subheader("Output DXF Filename")
            output_dxf_name = st.text_input("Enter name for modified DXF file:", 
                                           value="modified_output.dxf",
                                           help="This will be the name of the processed DXF file")
            
            # Execute button
            if st.button("Execute Chair Heights and Count Extraction", type="primary"):
                with st.spinner("Processing DXF file..."):
                    mtext_df, chairs_df, output_dxf_path = run_dxf_extraction(tmp_file_path, selected_layer, z_offset, output_dxf_name)
                    
                    if mtext_df is not None and chairs_df is not None:
                        # Store results in session state
                        st.session_state['mtext_df'] = mtext_df
                        st.session_state['chairs_df'] = chairs_df
                        st.session_state['output_dxf_path'] = output_dxf_path
                        st.session_state['output_dxf_name'] = output_dxf_name
                        st.success("Extraction completed successfully!")
                    else:
                        st.error("Extraction failed. Please check the error messages above.")
        else:
            st.warning("No layers found in the DXF file or file could not be read.")

with col2:
    st.header("Results")
    
    # Upper right: Show mtext_df
    st.subheader("MText Data")
    if 'mtext_df' in st.session_state and not st.session_state['mtext_df'].empty:
        st.dataframe(st.session_state['mtext_df'], use_container_width=False, height=300)
    else:
        st.info("MText data will appear here after extraction")
    
    # Lower right: Show chairs_df
    st.subheader("Chairs Data")
    if 'chairs_df' in st.session_state and not st.session_state['chairs_df'].empty:
        st.dataframe(st.session_state['chairs_df'], use_container_width=False, height=300)
    else:
        st.info("Chairs data will appear here after extraction")
    
    # Modified DXF file section
    st.subheader("Modified DXF File")
    if 'output_dxf_path' in st.session_state and st.session_state['output_dxf_path']:
        st.success(f"✅ Modified DXF file created: {st.session_state['output_dxf_name']}")
        
        # Download button for the modified DXF file
        if os.path.exists(st.session_state['output_dxf_path']):
            with open(st.session_state['output_dxf_path'], 'rb') as file:
                st.download_button(
                    label="📥 Download Modified DXF",
                    data=file.read(),
                    file_name=st.session_state['output_dxf_name'],
                    mime="application/octet-stream"
                )
        
        # Display file info
        if os.path.exists(st.session_state['output_dxf_path']):
            file_size = os.path.getsize(st.session_state['output_dxf_path'])
            st.text(f"File size: {file_size:,} bytes")
            st.text(f"Path: {st.session_state['output_dxf_path']}")
    else:
        st.info("Modified DXF file will appear here after extraction")

# Sidebar with additional information
st.sidebar.header("Instructions")
st.sidebar.markdown("""
1. **Upload** a DXF file using the file uploader
2. **Select** a layer from the dropdown list
3. **Set** the Z-offset value if needed
4. **Click** Execute Extraction to process the file
5. **View** results in the right panel:
   - MText data in the upper window
   - Chairs data in the lower window
""")

st.sidebar.header("Requirements")
st.sidebar.markdown("""
- `dxf_extraction.py` file in the same directory
- `ezdxf` library installed
- DXF file with valid layers
""")


# Footer
st.markdown("---")
st.markdown("DXF PT Chair Extraction - R&DC USA Copyright 2025")
