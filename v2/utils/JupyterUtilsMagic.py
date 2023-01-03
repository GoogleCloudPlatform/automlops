"""Jupyter Magics to be imported into notebook."""
import os

from IPython import get_ipython
from IPython.core.magic import Magics, cell_magic, magics_class

from . import BuilderUtils

@magics_class
class JupyterUtilsMagic(Magics):
    """Magics for writing imports and components cells."""
    @cell_magic
    def define_imports(self, _, cell: str):
        """Use for imports cells, saves and runs the cell."""
        make_tmpfiles_dir()
        with open(BuilderUtils.IMPORTS_TMPFILE, 'w', encoding='utf-8') as file:
            file.write(cell)
        self.shell.run_cell(cell)

    @cell_magic
    def define_component(self, _, cell: str):
        """Use for component cells, saves and runs the cell."""
        make_tmpfiles_dir()
        with open(BuilderUtils.CELL_TMPFILE, 'w', encoding='utf-8') as file:
            file.write(cell)
        # Execute just the makeComponent function call from the cell
        code_to_exec = cell[
            cell.find('AutoMLOps.makeComponent('):cell.find(')')+1
        ]
        self.shell.run_cell(code_to_exec)

    @cell_magic
    def define_kfp_pipeline(self, _, cell: str):
        """Use for component cells, saves and runs the cell."""
        make_tmpfiles_dir()
        with open(BuilderUtils.PIPELINE_TMPFILE, 'w', encoding='utf-8') as file:
            file.write(cell)
        self.shell.run_cell(cell)

def make_tmpfiles_dir():
    """Creates a tmpfiles directory to store intermediate files."""
    try:
        os.makedirs(BuilderUtils.TMPFILES_DIR)
    except FileExistsError:
        pass

try:
    ipy = get_ipython()
    ipy.register_magics(JupyterUtilsMagic)
    make_tmpfiles_dir()

except AttributeError as err:
    raise Exception(f'Cannot load JupyterUtilsMagic, '
                    f'this is not a notebook. {err}') from err
