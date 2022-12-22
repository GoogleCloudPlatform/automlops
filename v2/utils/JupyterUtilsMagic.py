from IPython import get_ipython
from IPython.core.magic import Magics, cell_magic, magics_class

# consider dumping files to a tmpfiles dir
IMPORTS_TMPFILE = '.imports.py'
CELL_TMPFILE = '.cell.py'

@magics_class
class JupyterUtilsMagic(Magics):
    @cell_magic
    def define_imports(self, line, cell):
        """TODO"""
        with open(IMPORTS_TMPFILE, 'wt') as fd:
            fd.write(cell)
        self.shell.run_cell(cell)
    
    @cell_magic
    def define_component(self, line, cell):
        'Run and save python code block to a file'
        with open(CELL_TMPFILE, 'wt') as fd:
            fd.write(cell)
        code_to_exec = cell[cell.find("AutoMLOps.makeComponent("):cell.find(")")+1]
        self.shell.run_cell(code_to_exec)

try:
    ipy = get_ipython()
    ipy.register_magics(JupyterUtilsMagic)

except AttributeError:
    print("Can not load JupyterUtilsMagic because this is not a notebook")