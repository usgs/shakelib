#!/usr/bin/env python
"""
Program to generate API docs from doc strings and put the results
into the docs directory.
"""

import argparse
import os.path
import sys
import tempfile
from distutils.dir_util import copy_tree

from impactutils.io.cmd import get_command_output

def main(args):
    """
    Generate API docs.

    Args:
        args: Output of argparse. Currently only holds the verbose flag.

    Returns:
        Nothing. Function will exit upon success or failure.

    """

    #-------------------------------------------------------------
    # where should .rst files, Makefile, _build folder be written?
    #-------------------------------------------------------------
    API_DIR = tempfile.TemporaryDirectory().name
    print('Building in %s' % API_DIR)

    #-------------------------------------------------------------
    # Some additional useful directories
    #-------------------------------------------------------------
    REPO_DIR = os.path.dirname(os.path.abspath(__file__))
    DOC_DIR = os.path.join(REPO_DIR, 'docs')
    PACKAGE_DIR = os.path.join(REPO_DIR, 'shakelib')

    #-------------------------------------------------------------
    # what is the package called and who are the authors
    #-------------------------------------------------------------
    PACKAGE = "shakelib"
    AUTHORS = 'Bruce Worden, Eric Thompson, Mike Hearne'

    # find the make command on this system
    res, stdout, stderr = get_command_output('which make')
    if not res:
        print('Could not find the "make" command on your system. Exiting.')
        sys.exit(1)
    make_cmd = stdout.decode().strip()

    #-------------------------------------------------------------
    # run the api doc command; this creates the .rst files
    #-------------------------------------------------------------
    verstr = '4.0a'
    sys.stderr.write('Building shakelib API documentation (REST)...\n')
    sphinx_cmd = 'sphinx-apidoc -o %s -f -e -l -d 12 -F -H %s -A "%s"'\
                 ' -V %s %s' % (API_DIR, PACKAGE, AUTHORS, verstr,
                                PACKAGE_DIR)

    res, stdout, stderr = get_command_output(sphinx_cmd)

    if not res:
        raise Exception('Could not build Shakelib API documentation'
                        ' - error "%s".' % stderr)

    # Change name of API documentation in index.rst
    cmd = "sed -i -e 's/Welcome to shakemap.*/ShakeMap 4.0 API/g' "\
          "%s/index.rst" % API_DIR
    res, stdout, stderr = get_command_output(cmd)

    #--------------------------------------------
    # try to clean up some of the excess labeling
    #--------------------------------------------
    clean_cmd = "sed -i -e 's/ module//g' `find %s/*.rst -type f "\
                "-maxdepth 0 -print`" % API_DIR
    res, stdout, stderr = get_command_output(clean_cmd)
    clean_cmd = "sed -i -e 's/ package//g' `find %s/*.rst -type f "\
                "-maxdepth 0 -print`" % API_DIR
    res, stdout, stderr = get_command_output(clean_cmd)
    clean_cmd = "sed -i -e '/Subpackages/d' `find %s/*.rst -type f "\
                "-maxdepth 0 -print`" % API_DIR
    res, stdout, stderr = get_command_output(clean_cmd)
    clean_cmd = "sed -i -e '/-.*-/d' `find %s/*.rst -type f "\
                "-maxdepth 0 -print`" % API_DIR
    res, stdout, stderr = get_command_output(clean_cmd)

    #-------------------------------------------------------------
    # Edit the conf.py file to include the theme.
    #-------------------------------------------------------------
    fname = os.path.join(API_DIR, 'conf.py')
    f = open(fname, 'at')
    f.write("sys.path.insert(0, os.path.abspath('%s'))\n" % (REPO_DIR))

    #-------------------------------------
    # Built in theme:
    #-------------------------------------
#    f.write("html_theme = 'haiku'\n")
    #-------------------------------------

    #-------------------------------------
    # RTD theme
    #-------------------------------------
    f.write("import sphinx_rtd_theme\n")
    f.write("html_theme = 'sphinx_rtd_theme'\n")
    f.write("html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]\n")
    f.write("html_theme_options = {\n")
    f.write("    'collapse_navigation': False,\n")
    f.write("}\n")
    #-------------------------------------

    #-------------------------------------
    # Bootstrap theme
    #-------------------------------------
#    f.write("import sphinx_bootstrap_theme\n")
#    f.write("html_theme = 'bootstrap'\n")
#    f.write("html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()\n")
#    f.write("html_theme_options = {\n")
#    f.write("    'bootswatch_theme': \"Sandstone\",\n")
#    f.write("    'navbar_site_name': \"API Documentation\",\n")
#    f.write("    'navbar_sidebarrel': False,\n")
#    f.write("    'navbar_pagenav': False,\n")
#    f.write("    'navbar_links': [\n")
#    f.write("        (\"Manual\", \"../shake_index.html\", 1),\n")
#    f.write("    ],\n")
#    f.write("}\n")
    #-------------------------------------

    # Napolean extension? Supports Google and Numpy style docstrings, but it
    # also has some side effects such as restrictions on what sections are
    # allowed and it seems to suppress the [source] link to code; maybe this
    # is a configurable option though.
#    f.write("extensions = ['sphinx.ext.autodoc', 'sphinxcontrib.napoleon']\n")

    # This line is needed to inclue __init__ methods in documentation
    f.write("autoclass_content = 'both'\n")
    f.write("autodoc_member_order = 'bysource'\n")
    f.write("html_show_copyright = False\n")
    f.write("extensions = extensions + [ 'sphinx.ext.autodoc', "\
            "'sphinx.ext.napoleon', 'sphinx.ext.todo' ] \n")
    f.write("napoleon_include_special_with_doc = False\n")
    f.write("todo_include_todos = True\n")
    f.close()

    #-------------------------------------------------------------
    # Go to the api directory and build the html
    #-------------------------------------------------------------
    sys.stderr.write('Building shakelib pages (HTML)...\n')
    os.chdir(API_DIR)
    res, stdout, stderr = get_command_output('%s html' % make_cmd)
    if not res:
        raise Exception('Could not build HTML for API documentation. - '
                        'error "%s"' % stderr)
    if args.verbose:
        print(stdout.decode('utf-8'))
        print(stderr.decode('utf-8'))

    #-------------------------------------------------------------
    # Copy the generated content to the gh-pages branch we created
    # earlier
    #-------------------------------------------------------------
    htmldir = os.path.join(API_DIR, '_build', 'html')
    copy_tree(htmldir, DOC_DIR)
    nojekyll_file = os.path.join(DOC_DIR, '.nojekyll')
    res, stdout, stderr = get_command_output('touch %s' % (nojekyll_file))


if __name__ == '__main__':
    desc = 'Create API documentation for shakeelib.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Produce more output to the screen. ')

    pargs = parser.parse_args()
    main(pargs)
