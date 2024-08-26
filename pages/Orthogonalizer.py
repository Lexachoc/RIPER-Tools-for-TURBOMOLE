import streamlit as st
import numpy as np
from io import StringIO
from ase import Atoms
from ase.build import make_supercell
from ase.io import read, write
from abtem.structures import orthogonalize_cell, is_cell_orthogonal
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.io.cif import CifWriter
import py3Dmol
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title='Surface Cell Orthogonalization Tool', layout='wide', page_icon="⚛️")

# Sidebar stuff
st.sidebar.write('# About')
st.sidebar.write('Made By [Manas Sharma](https://manas.bragitoff.com)')
st.sidebar.write('In the group of [Prof. Dr. Marek Sierka](https://cmsg.uni-jena.de)')
st.sidebar.write('### *Powered by*')
st.sidebar.write('* [Py3Dmol](https://3dmol.csb.pitt.edu/) for Chemical System Visualizations')
st.sidebar.write('* [Streamlit](https://streamlit.io/) for making of the Web App')
st.sidebar.write('* [PyMatgen](https://pymatgen.org/) for Periodic Structure Representations')
st.sidebar.write('* [PubChempy](https://pypi.org/project/PubChemPy/1.0/) for Accessing the PubChem Database')
st.sidebar.write('* [MP-API](https://pypi.org/project/mp-api/) for Accessing the Materials Project Database')
st.sidebar.write('* [ASE](https://wiki.fysik.dtu.dk/ase/) for File Format Conversions')
st.sidebar.write('### *Contributors*')
st.sidebar.write('[Ya-Fan Chen ](https://github.com/Lexachoc)')
st.sidebar.write('### *Source Code*')
st.sidebar.write('[GitHub Repository](https://github.com/manassharma07/RIPER-Tools-for-TURBOMOLE)')

def visualize_structure(structure, html_file_name='viz.html'):
    spin = st.checkbox('Spin', value=False, key='key' + html_file_name)
    view = py3Dmol.view(width=500, height=400)
    cif_for_visualization = structure.to(fmt="cif")
    view.addModel(cif_for_visualization, 'cif')
    view.setStyle({'sphere': {'colorscheme': 'Jmol', 'scale': 0.3},
                   'stick': {'colorscheme': 'Jmol', 'radius': 0.2}})
    view.addUnitCell()
    view.zoomTo()
    view.spin(spin)
    view.setClickable({'clickable': 'true'})
    view.enableContextMenu({'contextMenuEnabled': 'true'})
    view.show()
    view.render()
    t = view.js()
    f = open(html_file_name, 'w')
    f.write(t.startjs)
    f.write(t.endjs)
    f.close()

    HtmlFile = open(html_file_name, 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height=400, width=500)
    HtmlFile.close()

# Function to display structure information
def display_structure_info(structure, key='1'):
    st.subheader("Structure Information")
    st.write("Formula: ", structure.composition.reduced_formula)

    #Display lattice parameters
    a, b, c = structure.lattice.abc
    alpha, beta, gamma = structure.lattice.angles

    # Create a DataFrame for the lattice parameters and angles
    data = {
        "Lattice Parameters": [a, b, c, alpha, beta, gamma]
    }
    df_latt_params = pd.DataFrame(data, index=["a", "b", "c", "alpha", "beta", "gamma"])
    with st.expander("Lattice Parameters", expanded=False):
        st.table(df_latt_params)

    # Display lattice vectors
    lattice_vectors = structure.lattice.matrix
    df_vectors = pd.DataFrame(lattice_vectors, columns=["X", "Y", "Z"], index=["a", "b", "c"])
    with st.expander("Lattice Vectors", expanded=True):
        # st.write("Lattice Vectors:")
        st.table(df_vectors)

    # Create a list of atomic coordinates
    with st.expander("Atomic Coordinates", expanded=False):
        coord_type = st.selectbox('Coordinate type', ['Cartesian', 'Fractional/Crystal'], key=key)
        if coord_type=='Cartesian':
            atomic_coords = []
            for site in structure.sites:
                atomic_coords.append([site.species_string] + list(site.coords))
        else:
            atomic_coords = []
            for site in structure.sites:
                atomic_coords.append([site.species_string] + list(site.frac_coords))
        
        # Create a Pandas DataFrame from the atomic coordinates list
        df_coords = pd.DataFrame(atomic_coords, columns=["Element", "X", "Y", "Z"])

    
        # Display the atomic coordinates as a table
        # st.write("Atomic Coordinates:")
        st.table(df_coords)

def orthogonalize_cif(cif_content):
    # Read the structure from CIF content
    atoms = read(StringIO(cif_content), format='cif')
    
    # Check if the cell is already orthogonal
    if is_cell_orthogonal(atoms):
        st.warning("The cell is already orthogonal.")
        return atoms, None
    
    # Perform the conversion to an orthogonal cell
    orthogonal_atoms, strain = orthogonalize_cell(atoms, max_repetitions=5, return_transform=True)
    
    return orthogonal_atoms, strain


# Function to convert a structure to CIF
def convert_to_cif(structure, filename):
    cif_writer = CifWriter(structure)
    cif_writer.write_file(filename)

# return filecontents
def read_file(filename):
    with open(filename, 'r') as file:
        return file.read()

st.title('Surface Cell Orthogonalization Tool')

st.write('You can either paste the CIF file contents below or upload the source file')
cif_contents = st.text_area(label='Enter the contents of the CIF file here', value='', placeholder='Put your text here',
                        height=400, key='input_text_area')
# Create a file uploader widget
file = st.file_uploader("or Upload the CIF file")

if file is not None:
    # If a file is uploaded, read its contents
    # contents = file.read()
    # To read file as bytes:
    bytes_data = file.getvalue()

    # To convert to a string based IO:
    stringio = StringIO(file.getvalue().decode("utf-8"))

    # To read file as string:
    cif_contents = stringio.read()
    # st.write(contensts)

if cif_contents != '':
    st.subheader("Original Structure")
    original_atoms = read(StringIO(cif_contents), format='cif')
    original_structure = AseAtomsAdaptor.get_structure(original_atoms)
    
    col1, col2 = st.columns(2)
    with col1:
        visualize_structure(original_structure, "viz_original.html")
    with col2:
        display_structure_info(original_structure)
    
    if st.button("Orthogonalize Cell"):
        orthogonal_atoms, strain = orthogonalize_cif(cif_contents)
        
        if strain is not None:
            st.subheader("Orthogonalized Structure")
            orthogonal_structure = AseAtomsAdaptor.get_structure(orthogonal_atoms)
            
            col1, col2 = st.columns(2)
            with col1:
                visualize_structure(orthogonal_structure, "viz_orthogonal.html")
            with col2:
                display_structure_info(orthogonal_structure, key='orthgonal')
            
            st.write("Strain:")
            st.write(strain)
            
            # Save orthogonalized CIF 
            convert_to_cif(orthogonal_structure, "cell.cif")
            st.download_button('Download Cell CIF', data=read_file("cell.cif"), file_name='cell.cif', key='cell_cif_button')
        else:
            st.info("The cell is already orthogonal. No changes were made.")
