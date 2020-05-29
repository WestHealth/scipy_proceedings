#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import docutils.core as dc
import os
import os.path
import sys
import re
import tempfile
import glob
import shutil
import io

from distutils import dir_util

from writer import writer, Translator
from conf import papers_dir, output_dir, status_file, static_dir
from collections import OrderedDict

import options

header = r'''
.. role:: ref

.. role:: label

.. role:: cite(raw)
   :format: latex

.. raw::  latex

    \InputIfFileExists{page_numbers.tex}{}{}
    \newcommand*{\docutilsroleref}{\ref}
    \newcommand*{\docutilsrolelabel}{\label}
    \newcommand*\DUrolecode[1]{#1}
    \providecommand*\DUrolecite[1]{\cite{#1}}

.. |---| unicode:: U+2014  .. em dash, trimming surrounding whitespace
    :trim:

.. |--| unicode:: U+2013   .. en dash
    :trim:


'''
from docutils.writers.latex2e import LaTeXTranslator

class ArxivTranslator(Translator):
    def __init__(self, *args, **kwargs):
        Translator.__init__(self, *args, **kwargs)
        self.addresses={"Gary and Mary West Health Institute": "La Jolla, CA 92037"}

    def visit_paragraph(self, node):
        self.end_open_abstract(node)

        if 'abstract' in node['classes'] and not self.abstract_in_progress:
            self.out.append('\\begin{abstract}')
            self.abstract_text.append(self.encode(node.astext()))
            self.abstract_in_progress = True

        elif 'keywords' in node['classes']:
            self.keywords = self.encode(node.astext())
            self.out.append('\\keywords{'+self.keywords+'}')

        elif self.non_breaking_paragraph:
            self.non_breaking_paragraph = False

        else:
            if self.active_table.is_open():
                self.out.append('\n')
            else:
                self.out.append('\n\n')

    def depart_paragraph(self, node):
        pass
    
    def depart_document(self, node):
        LaTeXTranslator.depart_document(self, node)

        ## Generate footmarks

        # build map: institution -> (author1, author2)
        institution_authors = OrderedDict()
        for auth in self.author_institution_map:
            for inst in self.author_institution_map[auth]:
                institution_authors.setdefault(inst, []).append(auth)


        # Build a footmark for the corresponding author
        corresponding_footmark = self.footmark(1)

        # Build a footmark for equal contributors
        equal_footmark = self.footmark(2)

        # Build one footmark for each institution
        institute_footmark = {}
        for i, inst in enumerate(institution_authors):
            institute_footmark[inst] = self.footmark(i + 3)

        footmark_template = r'\thanks{%(footmark)s %(instutions)}'
        corresponding_auth_template = r'''%%
          %(footmark_counter)s\thanks{%(footmark)s %%
          Corresponding author: \protect\href{mailto:%(email)s}{%(email)s}}'''

        equal_contrib_template = r'''%%
          %(footmark_counter)s\thanks{%(footmark)s %%
          These authors contributed equally.}'''

        title = self.paper_title
        authors = []
        institutions_mentioned = set()
        equal_authors_mentioned = False
        corr_emails = []
        if len(self.corresponding) == 0:
            self.corresponding = [self.author_names[0]]
        for n, auth in enumerate(self.author_names):
            if auth in self.corresponding:
                corr_emails.append(self.author_emails[n])

        for n, auth in enumerate(self.author_names):
            inst = ''.join(self.author_institution_map[auth])
            address = self.addresses[inst]
            email = self.author_emails[n]
            authors.append(f"{auth}\\\\\n{inst}\\\\\n{address}\\\\\n\\texttt{{{email}}}\\\\\n")

        ## Set up title and page headers

        if not self.latex_video_url:
            video_template = ''
        else:
            video_template = '\\\\\\vspace{5mm}\\tt\\url{%s}\\vspace{-5mm}' % self.latex_video_url

        title_template = r'\title{%s}\author{%s' \
                r'%s}\maketitle'
        title_template = title_template % (title, '\\And '.join(authors),
                                           video_template)

        self.body_pre_docinfo = [title_template]

        # Save paper stats
        self.document.stats = {'title': title,
                               'authors': ', '.join(self.author_names),
                               'author': self.author_names,
                               'author_email': self.author_emails,
                               'author_institution': self.author_institutions,
                               'author_institution_map' : self.author_institution_map,
                               'abstract': self.abstract_text,
                               'keywords': self.keywords,
                               'video': self.video_url,
                               'bibliography':self.bibliography}

        if hasattr(self, 'bibtex') and self.bibtex:
            self.document.stats.update({'bibliography': self.bibtex[1]})

writer.translator_class=ArxivTranslator
def rst2tex(in_path, out_path):

    dir_util.copy_tree(in_path, out_path)
    
    status_file   = os.path.join(static_dir, "ready.sty")
    base_dir = os.path.dirname(__file__)
    out_file = shutil.copy(status_file, out_path)
    os.rename(out_file, os.path.join(out_path, 'status.sty'))
    arxiv_style = os.path.join(base_dir, '_static/arxiv.sty')
    shutil.copy(arxiv_style, out_path)
    scipy_style = os.path.join(base_dir, '_static/scipy.sty')
    shutil.copy(scipy_style, out_path)
    preamble = u'''\\usepackage{arxiv}\n\\usepackage{scipy}'''

    # Add the LaTeX commands required by Pygments to do syntax highlighting

    pygments = None

    try:
        import pygments
    except ImportError:
        import warnings
        warnings.warn(RuntimeWarning('Could not import Pygments. '
                                     'Syntax highlighting will fail.'))

    if pygments:
        from pygments.formatters import LatexFormatter
        from writer.sphinx_highlight import SphinxStyle

        preamble += LatexFormatter(style=SphinxStyle).get_style_defs()
        
    settings = {'documentclass': 'article',
                'use_verbatim_when_possible': True,
                'use_latex_citations': True,
                'latex_preamble': preamble,
                'documentoptions': '',
                'halt_level': 3,  # 2: warn; 3: error; 4: severe
                }

    try:
        rst, = glob.glob(os.path.join(in_path, '*.rst'))
    except ValueError:
        raise RuntimeError("Found more than one input .rst--not sure which "
                           "one to use.")

    with io.open(rst, mode='r', encoding='utf-8') as f:
        content = header + f.read()
    
    tex = dc.publish_string(source=content, writer=writer,
                            settings_overrides=settings)

    stats_file = os.path.join(out_path, 'paper_stats.json')
    d = options.cfg2dict(stats_file)
    try:
        d.update(writer.document.stats)
        options.dict2cfg(d, stats_file)
    except AttributeError:
        print("Error: no paper configuration found")

    tex_file = os.path.join(out_path, 'paper.tex')
    with io.open(tex_file, mode='wb') as f:
        try:
            tex = tex.encode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            pass
        f.write(tex)


def tex2pdf(out_path):

    # Sometimes Latex want us to rebuild because labels have changed.
    # We will try at most 5 times.
    for i in range(5):
        out, retry = tex2pdf_singlepass(out_path)
        if not retry:
            # Building succeeded or failed outright
            break
    return out


def tex2pdf_singlepass(out_path):
    """
    Returns
    -------
    out : str
        LaTeX output.
    retry : bool
        Whether another round of building is needed.
    """

    import subprocess
    command_line = 'pdflatex -halt-on-error paper.tex'

    # -- dummy tempfile is a hacky way to prevent pdflatex
    #    from asking for any missing files via stdin prompts,
    #    which mess up our build process.
    dummy = tempfile.TemporaryFile()

    run = subprocess.Popen(command_line, shell=True,
            stdin=dummy,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=out_path,
            )
    out, err = run.communicate()

    if b"Fatal" in out or run.returncode:
        print("PDFLaTeX error output:")
        print("=" * 80)
        print(out.decode('utf-8'))
        print("=" * 80)
        if err:
            print(err.decode('utf-8'))
            print("=" * 80)

        # Errors, exit early
        return out, False

    # Compile BiBTeX if available
    stats_file = os.path.join(out_path, 'paper_stats.json')
    d = options.cfg2dict(stats_file)
    bib_file = os.path.join(out_path, d["bibliography"] + '.bib')

    if os.path.exists(bib_file):
        bibtex_cmd = 'bibtex paper && ' + command_line
        run = subprocess.Popen(bibtex_cmd, shell=True,
                stdin=dummy,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=out_path,
                )
        out_bib, err = run.communicate()
        if err or b'Error' in out_bib:
            print("Error compiling BiBTeX")
            print("bibtex error output:")
            print("=" * 80)
            print(out_bib)
            print("=" * 80)
            return out_bib, False

    if b"Label(s) may have changed." in out:
        return out, True

    return out, False


def page_count(pdflatex_stdout, paper_dir):
    """
    Parse pdflatex output for paper count, and store in a .ini file.
    """
    if pdflatex_stdout is None:
        print("*** WARNING: PDFLaTeX failed to generate output.")
        return

    regexp = re.compile(b'Output written on paper.pdf \((\d+) pages')
    cfgname = os.path.join(paper_dir, 'paper_stats.json')

    d = options.cfg2dict(cfgname)

    for line in pdflatex_stdout.splitlines():
        m = regexp.match(line)
        if m:
            pages = m.groups()[0]
            d.update({'pages': int(pages)})
            break
    options.dict2cfg(d, cfgname)


def build_paper(paper_id, start=1):
    out_path = os.path.join(output_dir, paper_id)
    in_path = os.path.join(papers_dir, paper_id)
    print("Building:", paper_id)
    
    
    options.mkdir_p(out_path)
    page_number_file = os.path.join(out_path, 'page_numbers.tex')
    with io.open(page_number_file, 'w', encoding='utf-8') as f:
        f.write('\setcounter{page}{%s}' % start)

    rst2tex(in_path, out_path)
    pdflatex_stdout = tex2pdf(out_path)
    page_count(pdflatex_stdout, out_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: build_paper.py paper_directory")
        sys.exit(-1)

    in_path = os.path.normpath(sys.argv[1])
    if not os.path.isdir(in_path):
        print("Cannot open directory: %s" % in_path)
        sys.exit(-1)

    paper_id = os.path.basename(in_path)
    build_paper(paper_id)
