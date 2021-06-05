
:author: Haw-minn Lu
:email: hlu@westhealth.org
:institution: Gary and Mary West Health Institute
:bibliography: ourbib

=============================================================================
How PDFrw and fillable forms improves throughput at a Covid-19 Vaccine Clinic
=============================================================================

.. class:: abstract

PDFrw was used to prepopulate Covid-19 vaccination forms to improve the efficiency and integrity of the vaccination process in terms of federal and state privacy requirements.  We will describe the vaccination process from the initial appointment, through the vaccination delivery, to the creation of subsequent required documentation. It turns out that  although Python modules for PDF generation are common, they are deficient in a number of key areas for fillable form creation and management.   For example, when a named fillable field appears multiple times in a form, they do not show up using the standard techniques as   Additionally field types such as checkboxes, radio buttons, lists and combo boxes are not straightforward to programmatically fill. Another challenge is combining multiple *filled* forms while maintaining the integrity of the values of the fillable fields. Additionally, HIPAA compliance issues are discussed.

.. class:: keywords

   machine learning, classification, categorical encoding

Introduction
------------

The coronavirus pandemic has been perhaps one of the most disruptive events experienced since World War 2. The frail, vulnerable and elderly are disproportionately affected particularly in the number of deaths and serious hospitalizations. While the near miraculous pace of development of effective vaccines was potential salvation from the situation. The logictical challenges are immense particularly when it comes to the elderly.

When vaccination centers and clinics began to be established, all required appointments and nearly all appointments had to be made online. Providing vaccines to the most vulnerable population especially in the early stages of the vaccine rollouts proved challenging as seniors are less likely to be tech saavy, have the persistences online to keep trying and even some are transportationally challenged.

As a personal anecdote, when vaccinations were open to all people 65 and older, I ventured to get my parents vaccinated. I periodically pinged the vaccination appointment site for a vaccine supercenter and after week of trying, I got through. Getting the appointment boiled down to observing the pattern of when new appointment slots opened up. Needless to say my parents who are not completely tech ignorant would have had extreme difficulty.

To address this the WestPACE center established a pop-up point of distribution (POD) for the covid-19 vaccine :cite:`pr` specifically for the elderly with emphasis on those who are most vulnerable. The success in the POD was touted in the local news media and caught the attention of the state who asked WestPACE's sister organization the West Health Institute to develop a playbook for the deploying a pop-up (POD).

This paper gives a little more background in the effort. Next the overall infrastructure and information flow is descried. Finally, a very detailed discussion on the use of python and the :code:`PDFrw` library to address a major bottleneck and volunteer pain point.

Background
----------

Coding methods can be categorized as *classic*, *contrast*,
*Bayesian* and *word embeddings*. Classic, contrast and Bayseian
encoding are given a good overview treatment by Hale's blog
:cite:`Hale2018` with examples to be found as part of the ``scikit-learn`` category
encoding package :cite:`scikit`. Both
contrast encoding and Bayesian encoding use the statistics of the data
to facilitate encoding. These two categories may be of use when more
statistical analysis is required, however there has not been widespread
adoption of these encoding techniques for machine learning.

Word embeddings are their own special category. 
:cite:`wiki:wordembeddings`. Word embeddings 
are used to represent words, phrases or even entire documents as a
vector so that similar meanings/concepts are mapped to
vectors that are close in the target vector space. Additionally, it is
adapted for encoding a large categorical features (i.e., words) into a
relatively lower dimensional space.

The remainder of the section will describe some common classic
categorical encodings

.. figure:: diagram.pdf

   Vaccination Pipeline :label:`fig:infrastructure`


Introduction and Background
---------------------------

With the goal of providing a senior friendly vaccine experience, Gary
and Mary West PACE which stood up a small
senior oriented covid vaccine clinic desires to mitigate the amount of
paperwork a frail senior is subjected to. Quite a lot of data is
repeatedly asked for to make appointments, on consent forms and in
reminder cards. While the idea of using pre-populated fillable PDF forms
is a simple one, implementation is full of challenges as many common
programmatic PDF tools do not properly work with filled forms. To meet
the challenges, PDF forms have repeated fields with same name,
checkboxes and radio buttons are used. Furthermore, to make life easier
for the staff, PDF forms for multiple patients needed to be consolidated
into a single PDF.

Programatically filling in PDF forms can be a quick and accurate way to
disseminate forms. Bits and pieces can be found throughout the Internet
and places like Stack Overflow. No single source provides a complete
answer, however, this `blog post in Medium by Vivsvaan
Sharma <https://medium.com/@vivsvaan/filling-editable-pdf-in-python-76712c3ce99>`__
is a good starting place. The blog post is long on python practices and
a bit short on PDF details. Another useful resource is the `PDF 1.7
specification <https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf>`__,
but it is well over 750 pages!.

The scope of this series applies to PDF 1.7 at this time no
investigation as to whether techniques apply to PDF 2.0 or forms
designed with Adobe LifeCycle. The forms are confirmed to work with
Acrobat Reader, but not tested across the board with different readers.

We will cover the basics of using PDFrw to explore fillable forms and
look at basic data types within PDFrw. We will first look at text form
fields and discuss how to access fields that are repeated. We will then
look at checkboxes, radio buttons, combo boxes and lists. Finally, we'll
offer a solution for consolidating multiple filled forms into a single
PDF while preserving the filled forms (and maintain editability).

Finding Your Way Around PDFrw and fillable forms
------------------------------------------------

If you search the internet, including the above mentioned *Medium* blog
post, you will find a snippet of code which might look like the
following:

.. code:: python

    pdf = pdfrw.PdfReader(file_path)
    for page in pdf.pages:
        annotations = page['/Annots']
        if annotations is None:
            continue
        
        for annotation in annotations:
            if annotation['/Subtype']=='/Widget':
                if annotation['/T']:
                    key = annotation['/T'].to_unicode()
                    print (key)

The type of ``annotation['/T']`` is ``pdfString`` while some sources use
[1:-1] to extract the string from ``pdfString`` the ``.to_unicode()``
method is the proper way to extract the string. According to the PDF 1.7
specification § 12.5.6.19 all fillable forms use are widget annotation,
so the check for the ``annotation['/SubType']`` filters the annotation
to only widget annotations.

As an example take the file ``sample_form1.pdf`` located at here at
github. It has a fields for a person to enter their name and address
information, plus we added a checkbox for an called ``opt in``. If we
run the segment of code on this file, the output looks like:

::

    Name
    Address
    City
    State
    Zip
    Opt in

So in this way we can figure out which ``annotation`` contains the
fields All we have to do is set the value. Well almost as we'll explain
below. To set the value, first we need to create a ``PDFString`` with
our value with the ``encode`` method then update the ``annotation`` as
shown in this code snippet.

.. code:: python

    annotation.update(pdfrw.PdfDict(V=pdfrw.objects.pdfstring.PdfString.encode(value)))

This converts your ``value`` into a ``PdfString`` and updates the
``annotation`` creating a value for. ``annotation['/V'``].

As mentioned above, this won't quite do it. At the top level of your
``PdfReader`` object ``pdf`` you also need to set the
``NeedAppearances`` property in the interactive from dictionary,
``AcroForm`` (See § 12.7,2). Without this, the fields are updated but
will not necessarily display. In our example, the corresponding snippet
of code is

.. code:: python

    pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

To recap, we can write a simple form filler with the following block of
code for text fields. We will discuss checkboxes below.

.. code:: python

    def form_filler(in_path, data, out_path):
        pdf = pdfrw.PdfReader(in_path)
        for page in pdf.pages:
            annotations = page['/Annots']
            if annotations is None:
                continue

            for annotation in annotations:
                if annotation['/Subtype'] == '/Widget':
                    key = annotation['/T'].to_unicode()
                    if key in data:
                        pdfstr = pdfrw.objects.pdfstring.PdfString.encode(data[key])
                        annotation.update(pdfrw.PdfDict(V=pdfstr))
            pdf.Root.AcroForm.update(
                pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
            pdfrw.PdfWriter().write(out_path, pdf)

Multiple Fields with Same Name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For text fields: Simple? Well not quite. Take a look at
``sample_form2.pdf``. This form differs from ``sample_form1.pdf`` only
in that the ``Name`` field appears twice. Once in the information block
at the top where name and address information is filled out, but also at
the bottom in the signature block. If we were to run the first code
block to examine the annotations, we get the following:

::

    Address
    City
    State
    Zip
    Opt in

So what happened to the ``Name`` field. Turns out whenever the multiple
fields occur with the same name the situation is more complicated. One
way to deal with this is to simply rename the fields to be different
such as ``Name-1`` and ``Name-2``, which is fine if the sole use of the
form is for automated form filling. However, if the form is also to be
used for manual filling, this would require the user to enter the
``Name`` multiple times.

With a little sleuthing and experimentation, you will see that there are
some widget annotations without the ``/T`` field but with a ``/Parent``
field. As it turns out this ``/Parent`` contains the field name ``\T``
as well as the default value ``\V``. So for our examples there is one
``\Parent`` and two ``\Kids``. With a simple modification to our code by
inserting the lines:

.. code:: python

    if not annotation['/T']:
        annotation=annotation['/Parent']

That can allow us to inspect and modify annotations that appear more
than once. With this modification, the result of our inspection code
yields:

.. code:: python

    pdf = pdfrw.PdfReader(file_path)
    for page in pdf.pages:
        annotations = page['/Annots']
        if annotations is None:
            continue
        
        for annotation in annotations:
            if annotation['/Subtype']=='/Widget':
                if not annotation['/T']:
                    annotation=annotation['/Parent']
                if annotation['/T']:
                    key = annotation['/T'].to_unicode()
                    print (key)

It should be noted that ``Name`` now appears twice, once for each
instance, but they both point to the same ``/Parent``. With this
modification, the form filler will actually fill the ``/Parent`` value
twice, but this has no impact since it is overwriting the default value
with the same value while keeping the code simple.


Checkboxes
----------

In accordance to §12.7.4.2.3 the you can set the checkbox state as
follows:

.. code:: python

    def checkbox(annotation, value):
        if value:
            val_str = pdfrw.objects.pdfname.BasePdfName('/Yes')
        else:
            val_str = pdfrw.objects.pdfname.BasePdfName('/Off')
        annotation.update(pdfrw.PdfDict(V=val_str))

This will work especially when the export value of the checkbox is
``Yes``, but doesn't need to be. The easiest solution if you designed
the form or can use acrobat to edit the form is to ensure that the
export value of the checkbox is ``Yes`` and the default state of the box
is unchecked. In fact the recommendation in the specification is that it
be set to ``Yes``. However, you may not have the luxury and upon closer
inspection of a form where the export value is not set to ``Yes.`` You
will see that the ``/V`` and ``/AS`` fields are set to the export value
not ``Yes``.

If you are using the form not only for automatic filling but also for
manual filling you may wish the box to be checked as a default. In that
case, while the code does work, we feel the the best solution is to
delete the ``/V`` as well as the ``/AS``\ field from the dictionary. If
you do not have acrobat and can not find the export value, you can
discover it by looking at appearance dictionary ``/AP`` and specifically
at the ``/N`` field. Each annotation has up to 3 appearances in it's
appearance dictionary ``/N``, ``/R`` and ``/D``, standing for *normal*,
*rollover*, and *down* (§12.5.5). The latter two has to do with
appearance in interacting with the mouse, the normal appearance has to
do with how the form is printed. You can find the export value by
examining the normal appearance keys are set to the export value and
``/Off``. For example if you run,

.. code:: python

    print (annotation['/AP']['/N'].keys())

you will get annotations something like

.. code:: python

    ['/Export', '/Off']

where ``Export`` is the export value. The resulting sophisticated
version of function should be more this.

.. code:: python

    def checkbox(annotation, value, export=None):
        if export:
            export = '/' + export
        else:
            keys = annotation['/AP']['/N'].keys()
            keys.remove('/Off')
            export = keys[0]
        if value:
            annotation.update(pdfrw.PdfDict(V=export, AS=export))
        else:
            del annotation['/V']
            del annotation['/AS']

According to the PDF specification for checkboxes, the appearance stream
``/AS`` should be set to the same value ``/V``. Failure to do so may
mean in some circumstances the checkboxes do not appear. It should be
noted that there isn't really strict enforcement within PDF readers, so
it is best not to tempt fate and enter a value other than the export
value for a checked value. Additionally, all these complicated
machinations with the appearance dictionary come into play when dealing
with more complex form elements.

More Complex Forms
------------------

For the purpose of the vaccine clinic application, filling text fields
and checkboxes along with the discussion of consolidation files below
are sufficient. However, in the interest of not leaving a partial
solution. We'll take this topic further and address filling in all other
form fields.

Radio Buttons
~~~~~~~~~~~~~

Radio buttons are by far the most complex of the form entries types.
Each widget links to ``/Kids`` which represent the other buttons in the
radio group. But each widget in a radio group will link to the same
'kids'. Much like the 'parents' for the repeated forms fields with the
same name, you need only update each once, but it can't hurt to apply
the same update multiple times if it simplifies your code.

In a nutshell, the value ``/V`` of each widget in a radio group needs to
be set to the export value of the button selected. In each kid, the
appearance stream ``/AS`` should be set to ``/Off`` except for the kid
corresponding to the export value. In order to identify the kid with its
corresponding export value, we need to look again to the ``/N`` field of
the appearance dictionary ``/AP`` just as was done with the checkboxes.

The resulting code could look like the following:

.. code:: python

    def radio_button(annotation, value):
        for each in annotation['/Kids']:
            # determine the export value of each kid
            keys = each['/AP']['/N'].keys()
            keys.remove('/Off')
            export = keys[0]

            if f'/{value}' == export:
                val_str = pdfrw.objects.pdfname.BasePdfName(f'/{value}')
            else:
                val_str = pdfrw.objects.pdfname.BasePdfName(f'/Off')
            each.update(pdfrw.PdfDict(AS=val_str))

        annotation.update(pdfrw.PdfDict(V=pdfrw.objects.pdfname.BasePdfName(f'/{value}')))

Combo Boxes and Lists
~~~~~~~~~~~~~~~~~~~~~

Both combo boxes and lists are forms of the choice form type. The combo
boxes resemble drop down menus and lists are similar to list pickers in
HTML. Functionally they are very similar as for form filling. The value
``/V`` and appearance stream ``/AS`` need to be set to their exported
values. The ``/Op`` yields a list of lists associating the exported
value with the value that appears in the widget. For example if you
examine the ``/Opt`` field of the gender form field in
``sample-form3.pdf`` you'll see:

.. code:: python

    [['(Male-Value)', '(Male)'], ['(Female-Value)', '(Female)']]

where the exported values ``Male-Value`` and ``Female-Value`` are
associated with the text ``Male`` and ``Female``.

To set the combo box, you simply need to set the value to the export
value.

.. code:: python

    def combobox(annotation, value):
        export=None
        for each in annotation['/Opt']:
            if each[1].to_unicode()==value:
                export = each[0].to_unicode()
        if export is None:
            raise KeyError(f"Export Value: {value} Not Found")
        pdfstr = pdfrw.objects.pdfstring.PdfString.encode(export)
        annotation.update(pdfrw.PdfDict(V=pdfstr, AS=pdfstr))

Lists are structurally very similar. The list of exported values can be
found in the ``/Opt`` field. The main difference is that lists based on
their configuration can take multiple values. Multiple values can be set
with Pdfrw by setting ``\V`` and ``\AS`` to a list of ``PdfString``\ s.
We write it as separate helpers, but of course, you could combine the
code into one function.

.. code:: python

    def listbox(annotation, values):
        pdfstrs=[]
        for value in values:
            export=None
            for each in annotation['/Opt']:
                if each[1].to_unicode()==value:
                    export = each[0].to_unicode()
            if export is None:
                raise KeyError(f"Export Value: {value} Not Found")
            pdfstrs.append(pdfrw.objects.pdfstring.PdfString.encode(export))
        annotation.update(pdfrw.PdfDict(V=pdfstrs, AS=pdfstrs))

Putting it all together
~~~~~~~~~~~~~~~~~~~~~~~

Now that we have shown how to fill in all the specific types of form
elements in a PDF field. (With the exception of the signature form,
which probably should not be filled programatically). Let's put this all
together. If you have access to the forms themselves, you will know what
type of form field each corresponds to each label. However, it would be
nice to be able to determine the field type and work appropriately.

Determining Form Field Types Programmatically
'''''''''''''''''''''''''''''''''''''''''''''

To address the missing ingredient, it is important to understand that
fillable forms fall into 4 form types, button (push button, checkboxes
and radio buttons), text, choice (combo box and list box) and signature.
They correspond to following values of the ``/FT`` form type field of
our annotation, ``/Btn``, ``/Tx``, ``/Ch`` and ``/Sig``, respectively.
We will omit the signature type as we do not support filling in
signature. Furthermore, the push button is a widget which can cause an
action but is not fillable.

To distinguish the types of buttons and choices, we can examine the form
flags ``/Ff`` field. For radio buttons, the 16th bit is set. For combo
box the 18th bit is set. Please note that ``annotation['/Ff']`` returns
a ``PdfObject`` when returned and must be coerced into an ``int`` for
bit testing.

.. code:: python

    def field_type(annotation):
        ft = annotation['/FT']
        ff = annotation['/Ff']

        if ft == '/Tx':
            return 'text'
        if ft == '/Ch':
            if ff and int(ff) & 1 << 17:  # test 18th bit
                return 'combo'
            else:
                return 'list'
        if ft == '/Btn':
            if ff and int(ff) & 1 << 15:  # test 16th bit
                return 'radio'
            else:
                return 'checkbox'

For completeness, we should present a text\_form filler helper.

.. code:: python

    def text_form(annotation, value):
        pdfstr = pdfrw.objects.pdfstring.PdfString.encode(value)
        annotation.update(pdfrw.PdfDict(V=pdfstr, AS=pdfstr))

So now we have all the building blocks to put an automatic form filler
together. The finished form filler can be found in our github repository
at.

Consolidating Multiple Filled Forms
-----------------------------------

There are two problems with consolidating multiple filled forms. The
first problem is that when two PDF files are merged matching names are
associated with each other. For instance, if I had John Doe entered in
one form and Jane Doe in the second, when I combine them John Doe will
override the second form's name field and John Doe would appear in both
forms. The second problem is that most simple command line or
programmatic methods of combining two or more PDF files lose form data.
One solution is to "flatten" the each PDF file. This is equivalent to
printing the file to PDF. In effect, this bakes in the filled form
values and does not permit the editing the fields. Going even further,
one could render the PDFs as images if the only requirement is that the
combined files be printable. However, at the surface tools like
``ghostscript`` and ``imagemagick`` don't do a good job of preserving
form data. Other tools like PDFUnite don't solve any of these problems.

Form Field Name Collisions
~~~~~~~~~~~~~~~~~~~~~~~~~~

In our use case of the vaccine clinic, we have the same form being
filled out for multiple patients. So to combine a batch of these
requires all form field names to be different. The solution is quite
simple, in the process of filling out the form using the code above, we
can also rename (set) the value of ``/T``.

.. code:: python

    def form_filler(in_path, data, out_path, suffix):
        pdf = pdfrw.PdfReader(in_path)
        for page in pdf.pages:
            annotations = page['/Annots']
            if annotations is None:
                continue

            for annotation in annotations:
                if annotation['/SubType'] == '/Widget':
                    key = annotation['/T'].to_unicode()
                    if key in data:
                        pdfstr = pdfrw.objects.pdfstring.PdfString.encode(data[key])
                        new_key = key + suffix
                        annotation.update(pdfrw.PdfDict(V=pdfstr, T=new_key))
            pdf.Root.AcroForm.update(
                pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
            pdfrw.PdfWriter().write(out_path, pdf)

So all you have to do is supply a unique suffix to each form. In our
case, we simply number the batch so the suffix is just a sequential
number.

Combining the files
~~~~~~~~~~~~~~~~~~~

If you search the internet for combine PDF files using pdfrw, you'll get
a recipe like the following.

.. code:: python

    writer = PdfWriter()
    for fname in files:
        r = PdfReader(fname)
        writer.addpages(r.pages)
    writer.write("output.pdf")

While you don't lose the form data per se, you lose rendering
information and hence the combined PDF fails to show the fields. The
problem comes from the fact that the written PDF does not have an
interactive form dictionary (see §12.7.2 of the PDF 1.7 specification).
In particular the interactive forms dictionary contains the boolean
``NeedAppearances`` to be set in order for fields to be shown. If the
forms being combined have different interactive form dictionaries, they
will need to be merged. This is beyond the scope of this blog and the
issues has not really been addressed though the `stackoverflow
article <https://stackoverflow.com/questions/57008782/pypdf2-pdffilemerger-loosing-pdf-module-in-merged-file>`__
endeavors to make a first attempt. For our purposes since the source
form is identical amongst the various copies, any ``AcroForm``
dictionary can be used.

After obtaining the dictionary, from ``pdf.Root.AcroForm`` (assuming the
reader is stored in ``pdf``), it is not clear how to add it to the
``PdfWriter`` object. The clue comes from a simple recipe for copying a
pdf file.

.. code:: python

    pdf = PdfReader(in_file)
    PdfWriter().write(out_file, pdf)

If one examines, these source code, the second parameter is set to the
attribute ``trailer``, so assuming ``acro_form`` contains the
interactive forms ``PdfDict`` you can set it by
``writer.trailer.Root.AcroForm = acro_form``.

Double Sided Printing
~~~~~~~~~~~~~~~~~~~~~

This issue is less about ``pdfrw`` than just making sure certain issues
are taken into consideration. For example, in the clinic example, we
wanted to pre-populate vaccination cards provided from a digital
template from the CDC. Each card has a front and back but there are 6
cards per sheet. You must insure the information for the front of one
card corresponds to the correct back of the card. In our case with 6
cards, if the front is arrayed like this:

+-----+-----+
| 1   | 3   |
+=====+=====+
| 3   | 4   |
+-----+-----+
| 5   | 6   |
+-----+-----+

Then the back needs to be arranged as follows provided you are printing
with the "flip along the long side" option which you should use unless
the back is intentionally printed upside down relative to the front.

+-----+-----+
| 2   | 1   |
+=====+=====+
| 4   | 3   |
+-----+-----+
| 6   | 5   |
+-----+-----+

Another consideration when printing double sided is that if you document
has an odd number of pages you will need to insert a blank page
somewhere to make the page count even. Otherwise, when you print a
bundle, the first page of the second document will be on the back of
last page of the first.

Blank Page
~~~~~~~~~~

While the ``pdfrw`` library does not have a method for producing a blank
page, but there is a simple recipe taken from this
`article <https://www.binpress.com/pdfrw-python-pdf-library/>`__.

.. code:: python

    def blank_page():
        blank = pdfrw.PageMerge()
        blank.mbox = [0, 0, 612, 792] # 8.5 x 11
        blank = blank.render()
        return blank

Please note that the mbox specifies the page dimensions in points. In
our case, all documents are letter size. Of course, it is easy to turn
``blank_page`` into a function which takes page size as a parameter and
generates a blank page. It should also be noted that the ``pages``
attribute of the ``PdfReader`` object returned by ``PdfReader`` is
merely a list so it is easy to insert the blank page where desired. In
our particular example, the last two pages were meant to be printed back
to back so we needed to insert the blank page before the last two. The
code ended up looking like the following

.. code:: python

    pages = PdfReader(doc_name).pages
    if len(pages)%2==1 and double_sided: # Odd number of pages
        writer.addpages(pages[0:-2])
        writer.addpage(blank_page())
        writer.addpages(pages[-2:])

where :code:`double_sided` was a flag indicating whether we wanted to go
into "double sided mode."

Conclusion
----------

A complete functional version of this PDF form filler can be found in
our github repository. This process was able to produce large quantities
of pre filled forms for seniors seeking Covid vaccinations relieving one
of the bottlenecks that have plagued many other vaccine clinics.
